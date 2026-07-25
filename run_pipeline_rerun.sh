#!/bin/bash
# Re-run evaluation for an existing pipeline result using swt-bench-verified
# Usage: bash run_pipeline_rerun.sh [MODEL_NAME]
# Example: bash run_pipeline_rerun.sh gemini-2.5-pro

set -euo pipefail

MODEL_NAME=${1:-"gemini-2.5-pro"}
SOURCE_DIR="/home/v-haoliu3/SWT-RESULTS-PIPELINE/${MODEL_NAME}/pipeline_all"
INFERENCE_DIR="/home/v-haoliu3/swt-bench-verified/swt-bench/inference_output/pipeline-model/${MODEL_NAME}"
RUN_ID="pipeline-${MODEL_NAME}"

echo "=== Pipeline Rerun Evaluation ==="
echo "Model: ${MODEL_NAME}"
echo "Source: ${SOURCE_DIR}"
echo "Inference dir: ${INFERENCE_DIR}"
echo ""

# ============================================================
# Step 1: Copy and convert format (dict json -> jsonl)
# ============================================================
echo "=== Step 1: Copy & convert format ==="

PRED_JSON="${SOURCE_DIR}/preds_only_test.json"
if [ ! -f "${PRED_JSON}" ]; then
    echo "ERROR: ${PRED_JSON} not found"
    exit 1
fi

mkdir -p "${INFERENCE_DIR}"
cp "${PRED_JSON}" "${INFERENCE_DIR}/"

python3 -c "
import json
d = json.load(open('${INFERENCE_DIR}/preds_only_test.json'))
with open('${INFERENCE_DIR}/preds.jsonl', 'w') as f:
    for k, v in d.items():
        f.write(json.dumps(v) + '\n')
print(f'Converted {len(d)} instances to jsonl')
"

# ============================================================
# Step 2: Run evaluation
# ============================================================
echo ""
echo "=== Step 2: Run evaluation ==="

cd /home/v-haoliu3/swt-bench-verified/swt-bench

uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path "${INFERENCE_DIR}/preds.jsonl" \
    --max_workers 12 \
    --run_id "${RUN_ID}" \
    --patch_types vanilla \
    --build_mode api

echo ""
echo "=== Evaluation Done ==="
echo "Results: evaluation_results/*${RUN_ID}*"
