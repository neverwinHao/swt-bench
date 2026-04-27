"""
Golden Test Evaluation

Evaluates code patch quality by running golden test patches (ground truth from dataset)
against model-generated code patches.

Directly mirrors the standard SWT evaluation in run_evaluation.py,
but replaces golden_code_patch with model-generated code_patch.

Standard SWT 6 phases:
  pred_pre:  model_test + no code          (model test on buggy code)
  pred_post: model_test + golden_code      (model test on fixed code)
  gold_pre:  golden_test + no code         (golden test on buggy code)
  gold_post: golden_test + golden_code     (golden test on fixed code)
  base_pre:  no test + no code             (baseline)
  base_post: no test + golden_code         (baseline with fix)

Our 4 phases (replacing golden_code with model code_patch):
  pred_pre:  golden_test + no code         (golden test on buggy code)
  pred_post: golden_test + model_code      (golden test on model fix)
  base_pre:  no test + no code             (baseline)
  base_post: no test + model_code          (baseline with model fix)

Directives always derived from golden_test (fallback), matching standard SWT logic:
  exec_spec.test_directives = get_test_directives(
      golden_test if test_patch is None else test_patch, repo)

Usage:
    python -m src.golden_test_eval \
        --code_preds_paths /path/to/preds1.json /path/to/preds2.json \
        --dataset_name eth-sri/SWT-bench_Verified_bm25_27k_zsp \
        --output_path golden_test_metadata.json \
        --run_id golden_eval_v1 --max_workers 4

    # Incremental run (skip already-completed combos)
    python -m src.golden_test_eval \
        --code_preds_paths /path/to/more/preds.json \
        --output_path golden_test_metadata.json \
        --run_id golden_eval_v2 --merge
"""

import json
import os
import re
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
from src.utils import get_test_directives, str2bool, extract_changed_files


def infer_code_patch_source(preds_path: str) -> str:
    parts = Path(preds_path).resolve().parts
    parent = parts[-2]
    if re.match(r"^run_\d+$", parent) and len(parts) >= 3:
        grandparent = parts[-3]
        return f"{grandparent}__{parent}"
    return parent


def load_code_preds(preds_path: str) -> Dict[str, dict]:
    with open(preds_path, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {pred["instance_id"]: pred for pred in data}
    return data


def run_golden_test_instance(
    instance: dict,
    code_patch: str,
    golden_test: str,
    code_patch_source: str,
    run_id: str,
    compute_coverage: bool,
    timeout: int,
    force_rebuild: bool = False,
    build_mode: str = "api",
) -> Dict[str, Any]:
    """
    Run 4-phase golden test evaluation for a single (instance, code_patch).

    Mirrors standard SWT run_evaluation.py logic:
      - test_directives: from golden_test when test_patch is present,
        fallback to golden_test when test_patch is None (same as standard SWT
        falling back to model_patch)
      - coverage_files: includes both golden_test files and code_patch files
      - patch_list: [code_patch] + [test_patch], matching standard ordering
    """
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    safe_cp = code_patch_source.replace("/", "__").replace(" ", "_")

    result = {
        "instance_id": instance_id,
        "code_patch_source": code_patch_source,
        "test_patch_source": "golden_test",
        "patch_successfully_applied": False,
        "resolved": False,
        "added_f2p": 0,
        "coverage_pred": None,
        "coverage_delta_pred": None,
        "tests_pred": {},
        "tests_base": {},
    }

    if not golden_test.strip():
        logging.warning(f"No golden test patch for {instance_id}, skipping")
        return result

    try:
        exec_spec = make_exec_spec(instance)
        exec_spec.timeout = timeout
        exec_spec.force_rebuild = force_rebuild
        exec_spec.compute_coverage = compute_coverage
        exec_spec.rm_image = False
        exec_spec.run_id = run_id

        code_patch_files = extract_changed_files(code_patch)
        if exec_spec.coverage_files:
            exec_spec.coverage_files = list(set(exec_spec.coverage_files + code_patch_files))
        else:
            exec_spec.coverage_files = code_patch_files

        # 4 phases, matching standard SWT structure (run_evaluation.py L176-192)
        #   test_patches:  [golden_test, golden_test, None,       None]
        #   code_patches:  [None,        code_patch,  None,       code_patch]
        patch_ids = [
            f"golden__pred_pre__{safe_cp}",
            f"golden__pred_post__{safe_cp}",
            f"golden__base_pre__{safe_cp}",
            f"golden__base_post__{safe_cp}",
        ]
        test_patches = [golden_test, golden_test, None, None]
        code_patches = [None, code_patch, None, code_patch]

        test_results_list = []
        coverage_list = []
        first_applied = None

        for test_patch, cp, pid in zip(test_patches, code_patches, patch_ids):
            # Directives: from test_patch if present, fallback to golden_test
            # This matches standard SWT: get_test_directives(model_patch if test_patch is None else test_patch, repo)
            directive_source = golden_test if test_patch is None else test_patch
            exec_spec.test_directives = get_test_directives(directive_source, repo)

            exec_spec.patch_list = []
            if cp:
                exec_spec.patch_list.append(cp)
            if test_patch:
                exec_spec.patch_list.append(test_patch)

            exec_spec.patch_id = pid

            if not exec_spec.test_directives:
                test_results_list.append({})
                coverage_list.append({})
                continue

            _, test_output_path = run_eval_exec_spec(
                exec_spec, code_patch, build_mode=build_mode
            )

            tr, patch_applied = get_logs_eval(test_output_path, repo, exec_mode="unit_test")
            cov = get_coverage_eval(test_output_path) if compute_coverage else {}

            test_results_list.append(tr)
            coverage_list.append(cov)

            if first_applied is None:
                first_applied = patch_applied

        if not first_applied:
            return result

        result["patch_successfully_applied"] = True

        tr_pred_pre, tr_pred_post, tr_base_pre, tr_base_post = test_results_list
        cov_pred_pre, cov_pred_post, cov_base_pre, cov_base_post = coverage_list

        report_pred = get_eval_report(tr_pred_pre, tr_pred_post)
        report_base = get_eval_report(tr_base_pre, tr_base_post)

        resolved, added_f2p = get_resolution_success(report_pred, report_base)
        result["resolved"] = resolved
        result["added_f2p"] = added_f2p
        result["tests_pred"] = report_pred
        result["tests_base"] = report_base

        if compute_coverage and code_patch:
            try:
                patch_str = code_patch if code_patch.endswith('\n') else code_patch + '\n'
                removed_lines, added_lines = extract_changed_lines_from_patch(patch_str)
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
            f"Error evaluating {instance_id} (cp={code_patch_source}): {e}"
        )
        traceback.print_exc()

    return result


def build_golden_test_metadata(
    code_preds_paths: List[str],
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
    is_swt: bool = False,
):
    resource.setrlimit(resource.RLIMIT_NOFILE, (open_file_limit, open_file_limit))

    dataset = load_swebench_dataset(dataset_name, split, is_swt=is_swt)
    dataset_map = {inst["instance_id"]: inst for inst in dataset}

    code_sources = {}
    for cp_path in code_preds_paths:
        cp_name = infer_code_patch_source(cp_path)
        code_sources[cp_name] = load_code_preds(cp_path)

    if instance_ids:
        target_ids = instance_ids
    else:
        all_cp_ids = set()
        for cp_data in code_sources.values():
            all_cp_ids.update(cp_data.keys())
        target_ids = sorted(all_cp_ids & set(dataset_map.keys()))

    all_results = {}
    if merge and os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
        with open(output_path, "r") as f:
            all_results = json.load(f)
        print(f"Loaded {len(all_results)} existing instance results for merging")

    skipped = 0
    work_items = []
    for inst_id in target_ids:
        if inst_id not in dataset_map:
            print(f"Warning: {inst_id} not in dataset, skipping")
            continue
        instance = dataset_map[inst_id]
        if is_swt:
            golden_test = instance.get("golden_code_patch", "")
        else:
            golden_test = instance.get("golden_test_patch", "")

        for cp_name, cp_data in code_sources.items():
            if inst_id not in cp_data:
                continue
            code_patch = cp_data[inst_id].get("model_patch", "")
            if not code_patch.strip():
                continue
            combo_key = f"{cp_name}__golden_test"
            if inst_id in all_results and combo_key in all_results[inst_id].get("results", {}):
                skipped += 1
                continue
            work_items.append((instance, code_patch, golden_test, cp_name))

    print(f"Processing {len(target_ids)} instances x {len(code_sources)} code patch sources")
    print(f"Total work items: {len(work_items)} (skipped {skipped} already-completed combos)")

    results_lock = Lock()

    with tqdm(total=len(work_items), desc="Golden Test Eval") as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    run_golden_test_instance,
                    inst, cp, gt, cp_name,
                    run_id, compute_coverage, timeout, force_rebuild, build_mode,
                ): (inst["instance_id"], cp_name, cp, gt)
                for inst, cp, gt, cp_name in work_items
            }

            for future in as_completed(futures):
                inst_id, cp_name, cp, gt = futures[future]
                pbar.update(1)

                e = future.exception()
                if e is not None:
                    print(f"Error for {inst_id} (cp={cp_name}): {e}")
                    continue

                result = future.result()
                with results_lock:
                    if inst_id not in all_results:
                        all_results[inst_id] = {
                            "instance_id": inst_id,
                            "results": {},
                        }
                    combo_key = f"{cp_name}__golden_test"
                    all_results[inst_id]["results"][combo_key] = {
                        "code_patch_source": result["code_patch_source"],
                        "test_patch_source": result["test_patch_source"],
                        "code_patch": cp,
                        "test_patch": gt,
                        "patch_successfully_applied": result["patch_successfully_applied"],
                        "resolved": result["resolved"],
                        "added_f2p": result["added_f2p"],
                        "coverage_pred": result["coverage_pred"],
                        "coverage_delta_pred": result["coverage_delta_pred"],
                        "tests_pred": result["tests_pred"],
                        "tests_base": result["tests_base"],
                    }
                    with open(output_path, "w") as f:
                        json.dump(all_results, f, indent=2)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)

    total_resolved = sum(
        1 for inst in all_results.values()
        for combo in inst["results"].values()
        if combo.get("resolved")
    )
    total_combos = sum(len(inst["results"]) for inst in all_results.values())
    print(f"\nResults written to {output_path}")
    print(f"Instances: {len(all_results)}, Combos: {total_combos}, Resolved: {total_resolved}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Evaluate code patches using golden test patches")
    parser.add_argument(
        "--code_preds_paths", nargs="+", required=True,
        help="Paths to code patch prediction JSON files (preds.json format)",
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
    parser.add_argument("--is_swt", type=str2bool, default=False,
        help="Set True for SWT-bench datasets where patch/test_patch fields are swapped")
    parser.add_argument("--open_file_limit", type=int, default=4096)

    args = parser.parse_args()
    build_golden_test_metadata(
        code_preds_paths=args.code_preds_paths,
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
        is_swt=args.is_swt,
    )
