"""
Test Selection Metadata Builder

Builds metadata for test selection by running candidate test patches against
candidate code patches with pre/post comparison (aligned with SWT-bench report format).

For each (test_patch, code_patch) combination, runs 4 evaluations:
  - pred_pre:  test_patch only (no code patch) — bug still present
  - pred_post: code_patch + test_patch — after fix
  - base_pre:  no patches — baseline
  - base_post: code_patch only — baseline with fix

Then computes FAIL_TO_PASS, resolved, coverage_pred, coverage_delta_pred, etc.

Usage:
    python -m src.test_selection \
        --code_patch_dirs /path/to/Code-Patch-5.2 /path/to/Code-Patch-5.4mini \
        --test_preds_paths /path/to/preds_a.json /path/to/preds_b.json \
        --dataset_name princeton-nlp/SWE-bench \
        --instance_ids django__django-10880 sympy__sympy-12096 \
        --output_path test_selection_metadata.json \
        --run_id test_sel_v1

    # Merge into existing output
    python -m src.test_selection \
        --code_patch_dirs /path/to/Code-Patch-sonnet \
        --test_preds_paths /path/to/preds_c.json \
        --output_path test_selection_metadata.json \
        --run_id test_sel_v2 --merge
"""

import json
import os
import resource
import traceback
import logging

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from tqdm import tqdm
from typing import List, Optional, Dict, Any, Tuple

from src.dataset import load_swebench_dataset
from src.exec_spec import make_exec_spec, ExecSpec
from src.grading import (
    get_logs_eval,
    get_coverage_eval,
    get_eval_report,
    get_resolution_success,
    extract_changed_lines_from_patch,
    extract_executable_lines,
    get_restricted_coverage,
    get_coverage_delta,
    count_covered_lines,
)
from src.run_evaluation import run_eval_exec_spec
from src.utils import get_test_directives, str2bool


def load_code_patch(code_patch_dir: str, instance_id: str) -> Optional[str]:
    """Load a code patch from Code-Patch-X/<instance_id>/<instance_id>.patch"""
    patch_file = os.path.join(code_patch_dir, instance_id, f"{instance_id}.patch")
    if not os.path.isfile(patch_file):
        return None
    with open(patch_file, "r") as f:
        return f.read().strip()


def load_test_preds(test_preds_path: str) -> Dict[str, dict]:
    """Load test predictions from a JSON file. Returns dict keyed by instance_id."""
    with open(test_preds_path, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {pred["instance_id"]: pred for pred in data}
    return data


def _run_single_eval(
    instance: dict,
    test_patch: Optional[str],
    code_patch: Optional[str],
    patch_id: str,
    run_id: str,
    compute_coverage: bool,
    timeout: int,
    force_rebuild: bool,
    build_mode: str,
) -> Tuple[dict, dict, bool]:
    """
    Run a single evaluation (one of pred_pre/pred_post/base_pre/base_post).

    Returns (test_results_dict, coverage_dict, patch_applied).
    """
    repo = instance["repo"]
    exec_spec = make_exec_spec(instance)
    exec_spec.timeout = timeout
    exec_spec.force_rebuild = force_rebuild
    exec_spec.compute_coverage = compute_coverage
    exec_spec.rm_image = False
    exec_spec.run_id = run_id
    exec_spec.patch_id = patch_id

    # Build patch_list: code_patch first (if any), then test_patch (if any)
    exec_spec.patch_list = []
    if code_patch:
        exec_spec.patch_list.append(code_patch)
    if test_patch:
        exec_spec.patch_list.append(test_patch)

    # Test directives from test_patch (or code_patch if no test_patch for base runs)
    directive_source = test_patch if test_patch else code_patch
    if directive_source:
        exec_spec.test_directives = get_test_directives(directive_source, repo)
    else:
        exec_spec.test_directives = []

    if not exec_spec.test_directives:
        return {}, {}, False

    _, test_output_path = run_eval_exec_spec(
        exec_spec, code_patch or "", build_mode=build_mode
    )

    test_results, patch_applied = get_logs_eval(test_output_path, repo, exec_mode="unit_test")
    coverage = get_coverage_eval(test_output_path) if compute_coverage else {}

    return test_results, coverage, patch_applied


def run_test_selection_instance(
    instance: dict,
    code_patch: str,
    test_patch: str,
    golden_code_patch: str,
    code_patch_name: str,
    test_patch_name: str,
    run_id: str,
    compute_coverage: bool,
    timeout: int,
    force_rebuild: bool = False,
    build_mode: str = "api",
) -> Dict[str, Any]:
    """
    Run pre/post evaluation for a single (code_patch, test_patch) combination.

    Runs 4 evaluations:
      pred_pre:  test_patch only
      pred_post: code_patch + test_patch
      base_pre:  no patches (test directives from test_patch)
      base_post: code_patch only (test directives from test_patch)

    Then computes FAIL_TO_PASS, resolved, coverage metrics.
    """
    instance_id = instance["instance_id"]
    safe_cp = code_patch_name.replace("/", "__").replace(" ", "_")
    safe_tp = test_patch_name.replace("/", "__").replace(" ", "_")

    result = {
        "instance_id": instance_id,
        "code_patch_source": code_patch_name,
        "test_patch_source": test_patch_name,
        "patch_successfully_applied": False,
        "resolved": False,
        "added_f2p": 0,
        "coverage_pred": None,
        "coverage_delta_pred": None,
        "tests_pred": {},
        "tests_base": {},
    }

    try:
        # 1. pred_pre: test_patch only (no code patch)
        tr_pred_pre, cov_pred_pre, applied_pred_pre = _run_single_eval(
            instance, test_patch, None,
            f"tsel__pred_pre__{safe_cp}__{safe_tp}", run_id,
            compute_coverage, timeout, force_rebuild, build_mode,
        )

        # 2. pred_post: code_patch + test_patch
        tr_pred_post, cov_pred_post, applied_pred_post = _run_single_eval(
            instance, test_patch, code_patch,
            f"tsel__pred_post__{safe_cp}__{safe_tp}", run_id,
            compute_coverage, timeout, force_rebuild, build_mode,
        )

        if not applied_pred_pre:
            # test patch didn't apply cleanly
            return result

        result["patch_successfully_applied"] = True

        # 3. base_pre: no patches (use test_patch directives)
        tr_base_pre, cov_base_pre, _ = _run_single_eval(
            instance, None, None,
            f"tsel__base_pre__{safe_cp}__{safe_tp}", run_id,
            compute_coverage, timeout, force_rebuild, build_mode,
        )

        # 4. base_post: code_patch only (use test_patch directives)
        tr_base_post, cov_base_post, _ = _run_single_eval(
            instance, None, code_patch,
            f"tsel__base_post__{safe_cp}__{safe_tp}", run_id,
            compute_coverage, timeout, force_rebuild, build_mode,
        )

        # Compare pre vs post to get FAIL_TO_PASS etc.
        report_pred = get_eval_report(tr_pred_pre, tr_pred_post)
        report_base = get_eval_report(tr_base_pre, tr_base_post)

        # Determine resolved status
        resolved, added_f2p = get_resolution_success(report_pred, report_base)
        result["resolved"] = resolved
        result["added_f2p"] = added_f2p
        result["tests_pred"] = report_pred
        result["tests_base"] = report_base

        # Compute coverage metrics (relative to golden_code_patch changed lines)
        if compute_coverage and golden_code_patch:
            try:
                removed_lines, added_lines = extract_changed_lines_from_patch(golden_code_patch)
                executable_removed = extract_executable_lines(
                    removed_lines, [cov_pred_pre, cov_base_pre]
                )
                executable_added = extract_executable_lines(
                    added_lines, [cov_pred_post, cov_base_post]
                )
                n_executable = len(executable_removed) + len(executable_added)

                if n_executable > 0:
                    cov_pred_removed = get_restricted_coverage(executable_removed, cov_pred_pre)
                    cov_pred_added = get_restricted_coverage(executable_added, cov_pred_post)
                    cov_base_removed = get_restricted_coverage(executable_removed, cov_base_post)
                    cov_base_added = get_restricted_coverage(executable_added, cov_base_post)

                    n_cov_pred = count_covered_lines(cov_pred_removed, cov_pred_added)
                    result["coverage_pred"] = n_cov_pred / n_executable

                    delta_removed = get_coverage_delta(executable_removed, cov_base_removed, cov_pred_removed)
                    delta_added = get_coverage_delta(executable_added, cov_base_added, cov_pred_added)
                    n_cov_delta = count_covered_lines(delta_removed, delta_added)
                    result["coverage_delta_pred"] = n_cov_delta / n_executable
            except Exception as e:
                logging.warning(f"Coverage computation failed for {instance_id}: {e}")

    except Exception as e:
        logging.warning(
            f"Error evaluating {instance_id} (cp={code_patch_name}, tp={test_patch_name}): {e}"
        )
        traceback.print_exc()

    return result


def build_test_selection_metadata(
    code_patch_dirs: List[str],
    test_preds_paths: List[str],
    dataset_name: str,
    split: str,
    instance_ids: Optional[List[str]],
    max_workers: int,
    timeout: int,
    output_path: str,
    compute_coverage: bool,
    run_id: str,
    force_rebuild: bool = False,
    build_mode: str = "api",
    merge: bool = False,
    open_file_limit: int = 4096,
):
    """
    Main entry point: build test selection metadata.

    For each instance, for each (code_patch_dir, test_preds) combination,
    runs pre/post evaluation and computes SWT-aligned metrics.
    """
    resource.setrlimit(resource.RLIMIT_NOFILE, (open_file_limit, open_file_limit))

    # Load dataset
    dataset = load_swebench_dataset(dataset_name, split)
    dataset_map = {inst["instance_id"]: inst for inst in dataset}

    # Load code patches per source
    code_patch_sources = {}
    for cp_dir in code_patch_dirs:
        cp_name = os.path.basename(cp_dir.rstrip("/"))
        code_patch_sources[cp_name] = cp_dir

    # Load test patch predictions per source
    test_patch_sources = {}
    for tp_path in test_preds_paths:
        tp_name = os.path.splitext(os.path.basename(tp_path))[0]
        test_patch_sources[tp_name] = load_test_preds(tp_path)

    # Determine which instances to process
    if instance_ids:
        target_ids = instance_ids
    else:
        # Union of all instances that appear in at least one code patch + one test patch source
        all_cp_ids = set()
        for cp_name, cp_dir in code_patch_sources.items():
            for d in os.listdir(cp_dir):
                if os.path.isdir(os.path.join(cp_dir, d)):
                    all_cp_ids.add(d)
        all_tp_ids = set()
        for tp_name, tp_data in test_patch_sources.items():
            all_tp_ids.update(tp_data.keys())
        target_ids = sorted(all_cp_ids & all_tp_ids & set(dataset_map.keys()))

    # Build work items
    work_items = []
    for inst_id in target_ids:
        if inst_id not in dataset_map:
            print(f"Warning: {inst_id} not in dataset, skipping")
            continue
        instance = dataset_map[inst_id]
        golden_code_patch = instance.get("golden_code_patch", "")

        for cp_name, cp_dir in code_patch_sources.items():
            code_patch = load_code_patch(cp_dir, inst_id)
            if code_patch is None:
                continue
            for tp_name, tp_data in test_patch_sources.items():
                if inst_id not in tp_data:
                    continue
                test_patch = tp_data[inst_id].get("model_patch", "")
                if not test_patch.strip():
                    continue
                work_items.append(
                    (instance, code_patch, test_patch, golden_code_patch, cp_name, tp_name)
                )

    print(f"Processing {len(target_ids)} instances x {len(code_patch_sources)} code patches x {len(test_patch_sources)} test patches")
    print(f"Total work items: {len(work_items)} (each = 4 docker runs: pred_pre/post + base_pre/post)")

    # Load existing results if merging
    if merge and os.path.isfile(output_path):
        with open(output_path, "r") as f:
            all_results = json.load(f)
        print(f"Loaded {len(all_results)} existing instance results for merging")
    else:
        all_results = {}

    # Run evaluations in parallel
    results_lock = Lock()
    count = 0
    count_lock = Lock()

    with tqdm(total=len(work_items), desc="Test Selection") as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    run_test_selection_instance,
                    inst, cp, tp, gcp, cp_name, tp_name,
                    run_id, compute_coverage, timeout, force_rebuild, build_mode,
                ): (inst["instance_id"], cp_name, tp_name)
                for inst, cp, tp, gcp, cp_name, tp_name in work_items
            }

            for future in as_completed(futures):
                inst_id, cp_name, tp_name = futures[future]
                pbar.update(1)
                with count_lock:
                    count += 1

                e = future.exception()
                if e is not None:
                    print(f"Error for {inst_id} (cp={cp_name}, tp={tp_name}): {e}")
                    continue

                result = future.result()
                with results_lock:
                    if inst_id not in all_results:
                        all_results[inst_id] = {
                            "instance_id": inst_id,
                            "results": {},
                        }
                    combo_key = f"{cp_name}__{tp_name}"
                    all_results[inst_id]["results"][combo_key] = {
                        "code_patch_source": result["code_patch_source"],
                        "test_patch_source": result["test_patch_source"],
                        "patch_successfully_applied": result["patch_successfully_applied"],
                        "resolved": result["resolved"],
                        "added_f2p": result["added_f2p"],
                        "coverage_pred": result["coverage_pred"],
                        "coverage_delta_pred": result["coverage_delta_pred"],
                        "tests_pred": result["tests_pred"],
                        "tests_base": result["tests_base"],
                    }

    # Write output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    total_resolved = sum(
        1 for inst in all_results.values()
        for combo in inst["results"].values()
        if combo.get("resolved")
    )
    total_combos = sum(len(inst["results"]) for inst in all_results.values())
    print(f"\nResults written to {output_path}")
    print(f"Instances: {len(all_results)}, Combos: {total_combos}, Resolved: {total_resolved}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Build test selection metadata")
    parser.add_argument(
        "--code_patch_dirs", nargs="+", required=True,
        help="Directories containing code patches (e.g., Code-Patch-5.2 Code-Patch-5.4mini)",
    )
    parser.add_argument(
        "--test_preds_paths", nargs="+", required=True,
        help="Paths to test patch prediction JSON files",
    )
    parser.add_argument("--dataset_name", default="princeton-nlp/SWE-bench", type=str)
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--instance_ids", nargs="+", type=str, default=None)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--run_id", type=str, required=True)
    parser.add_argument("--max_workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--compute_coverage", type=str2bool, default=True)
    parser.add_argument("--force_rebuild", type=str2bool, default=False)
    parser.add_argument("--build_mode", choices=["cli", "api"], default="api")
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--open_file_limit", type=int, default=4096)

    args = parser.parse_args()
    build_test_selection_metadata(
        code_patch_dirs=args.code_patch_dirs,
        test_preds_paths=args.test_preds_paths,
        dataset_name=args.dataset_name,
        split=args.split,
        instance_ids=args.instance_ids,
        max_workers=args.max_workers,
        timeout=args.timeout,
        output_path=args.output_path,
        compute_coverage=args.compute_coverage,
        run_id=args.run_id,
        force_rebuild=args.force_rebuild,
        build_mode=args.build_mode,
        merge=args.merge,
        open_file_limit=args.open_file_limit,
    )
