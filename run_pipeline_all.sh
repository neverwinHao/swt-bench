#!/bin/bash
# Evaluate all pipeline-multi-run results (Opus, GPT-5_2, GPT-5-mini)
# Each pipeline run has .pred files per instance that need to be assembled into a single jsonl

set -euo pipefail
cd /home/v-haoliu3/swt-bench-verified/swt-bench

INFERENCE_BASE="inference_output/pipeline-multi-run"
EVAL_RESULTS_BASE="evaluation_results/pipeline-multi-run"

# ============================================================
# Step 1: Convert .pred files to jsonl for each model/run
# ============================================================
echo "============================================"
echo "  Step 1: Converting .pred files to jsonl"
echo "============================================"

python3 - <<'CONVERT_SCRIPT'
import json
import os
import glob

configs = [
    # (source_base, run_count, model_label, output_dir)
    ("/home/v-haoliu3/SWT-RESULTS-PIPELINE-REBUTTAL/claude-opus-4.5", 5, "opus", "inference_output/pipeline-multi-run/opus"),
    ("/home/v-haoliu3/SWT-RESULTS-PIPELINE-REBUTTAL/gpt-5_2", 3, "gpt5_2", "inference_output/pipeline-multi-run/gpt5_2"),
    ("/home/v-haoliu3/SWT-RESULTS-PIPELINE-REBUTTAL/gpt-5-mini", 4, "gpt5-mini", "inference_output/pipeline-multi-run/gpt5-mini"),
]

for source_base, run_count, model_label, output_dir in configs:
    os.makedirs(output_dir, exist_ok=True)
    for k in range(1, run_count + 1):
        run_dir = os.path.join(source_base, f"pipeline_pass_k_{k}")
        run_id = f"{model_label}-pipeline-k{k}"
        output_path = os.path.join(output_dir, f"{run_id}.jsonl")

        if not os.path.isdir(run_dir):
            print(f"  [SKIP] {run_dir} does not exist")
            continue

        results = []
        pred_files = glob.glob(os.path.join(run_dir, "*", "*.pred"))
        for pred_file in sorted(pred_files):
            try:
                with open(pred_file) as f:
                    data = json.load(f)
                instance_id = data.get("instance_id", "")
                model_patch = data.get("model_patch", "")
                if instance_id and model_patch and len(model_patch) < 200000:
                    results.append({
                        "instance_id": instance_id,
                        "model_patch": model_patch,
                        "model_name_or_path": run_id,
                    })
            except (json.JSONDecodeError, IOError) as e:
                print(f"  [WARN] Failed to read {pred_file}: {e}")

        with open(output_path, "w") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")
        print(f"  [OK] {run_id}: {len(results)} instances -> {output_path}")

print("\nConversion complete.\n")
CONVERT_SCRIPT

# ============================================================
# Step 2: Run evaluation for each jsonl
# ============================================================
echo "============================================"
echo "  Step 2: Running evaluations"
echo "============================================"

evaluate_run() {
    local jsonl_path="$1"
    local run_id="$2"
    local model_label="$3"
    local eval_dir="${EVAL_RESULTS_BASE}/${model_label}"

    mkdir -p "${eval_dir}"

    echo ""
    echo "  Evaluating: ${run_id}"
    echo "    Input: ${jsonl_path}"

    uv run -m src.main \
        --dataset_name princeton-nlp/SWE-bench_Verified \
        --predictions_path "${jsonl_path}" \
        --max_workers 12 \
        --run_id "${run_id}" \
        --patch_types vanilla \
        --build_mode api

    # Move result to structured dir
    result_file=$(ls evaluation_results/*."${run_id}".json 2>/dev/null | head -1)
    if [ -n "${result_file}" ]; then
        mv "${result_file}" "${eval_dir}/"
        echo "    [DONE] -> ${eval_dir}/$(basename ${result_file})"
    else
        echo "    [WARN] No result file found for ${run_id}"
    fi
}

# --- Opus (5 runs) ---
echo ""
echo "=== Opus Pipeline (5 runs) ==="
for k in $(seq 1 5); do
    RUN_ID="opus-pipeline-k${k}"
    JSONL="${INFERENCE_BASE}/opus/${RUN_ID}.jsonl"
    if [ -f "${JSONL}" ]; then
        evaluate_run "${JSONL}" "${RUN_ID}" "opus"
    else
        echo "  [SKIP] ${JSONL} not found"
    fi
done

# --- GPT-5_2 (3 runs) ---
echo ""
echo "=== GPT-5_2 Pipeline (3 runs) ==="
for k in $(seq 1 3); do
    RUN_ID="gpt5_2-pipeline-k${k}"
    JSONL="${INFERENCE_BASE}/gpt5_2/${RUN_ID}.jsonl"
    if [ -f "${JSONL}" ]; then
        evaluate_run "${JSONL}" "${RUN_ID}" "gpt5_2"
    else
        echo "  [SKIP] ${JSONL} not found"
    fi
done

# --- GPT-5-mini (4 runs) ---
echo ""
echo "=== GPT-5-mini Pipeline (4 runs) ==="
for k in $(seq 1 4); do
    RUN_ID="gpt5-mini-pipeline-k${k}"
    JSONL="${INFERENCE_BASE}/gpt5-mini/${RUN_ID}.jsonl"
    if [ -f "${JSONL}" ]; then
        evaluate_run "${JSONL}" "${RUN_ID}" "gpt5-mini"
    else
        echo "  [SKIP] ${JSONL} not found"
    fi
done

echo ""
echo "============================================"
echo "  All evaluations complete!"
echo "============================================"
echo "Results:"
echo "  Opus:      ${EVAL_RESULTS_BASE}/opus/"
echo "  GPT-5_2:   ${EVAL_RESULTS_BASE}/gpt5_2/"
echo "  GPT-5-mini: ${EVAL_RESULTS_BASE}/gpt5-mini/"
