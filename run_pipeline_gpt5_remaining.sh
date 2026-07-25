#!/bin/bash
# Evaluate missing gpt-5_2 pipeline runs (k4, k5)
set -euo pipefail
cd /home/v-haoliu3/swt-bench-verified/swt-bench

INFERENCE_DIR="inference_output/pipeline-multi-run/gpt5_2"
EVAL_DIR="evaluation_results/pipeline-multi-run/gpt5_2"
SOURCE_BASE="/home/v-haoliu3/SWT-RESULTS-PIPELINE-REBUTTAL/gpt-5_2"

mkdir -p "${INFERENCE_DIR}" "${EVAL_DIR}"

# Step 1: Convert .pred files to jsonl
echo "=== Converting .pred files to jsonl ==="
python3 - <<'CONVERT_SCRIPT'
import json, os, glob

source_base = "/home/v-haoliu3/SWT-RESULTS-PIPELINE-REBUTTAL/gpt-5_2"
output_dir = "inference_output/pipeline-multi-run/gpt5_2"
os.makedirs(output_dir, exist_ok=True)

for k in [4, 5]:
    run_dir = os.path.join(source_base, f"pipeline_pass_k_{k}")
    run_id = f"gpt5_2-pipeline-k{k}"
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
CONVERT_SCRIPT

# Step 2: Evaluate
echo ""
echo "=== Running evaluations ==="
for k in 4 5; do
    RUN_ID="gpt5_2-pipeline-k${k}"
    JSONL="${INFERENCE_DIR}/${RUN_ID}.jsonl"
    echo "=== Evaluating: ${RUN_ID} ==="
    uv run -m src.main \
        --dataset_name princeton-nlp/SWE-bench_Verified \
        --predictions_path "${JSONL}" \
        --max_workers 12 \
        --run_id "${RUN_ID}" \
        --patch_types vanilla \
        --build_mode api
    result_file=$(ls evaluation_results/*."${RUN_ID}".json 2>/dev/null | head -1)
    if [ -n "${result_file}" ]; then
        mv "${result_file}" "${EVAL_DIR}/"
        echo "[DONE] -> ${EVAL_DIR}/$(basename ${result_file})"
    fi
done

echo "=== All done ==="
