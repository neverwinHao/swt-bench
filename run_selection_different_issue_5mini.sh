#!/bin/bash
#
# Test Selection for Different-Issue experiment
# 3 code patches (preds.json) x 5 test patches
# /home/v-haoliu3/haoliu/SWE_result/claude-opus-4.5/run_1/preds.json

set -euo pipefail
cd "$(dirname "$0")"

# ---------- Code patches (preds.json format) ----------
CODE_PREDS_PATHS=(
    "/home/v-haoliu3/haoliu/SWE_result/gpt-5.4-mini-20260317/preds.json"
    "/home/v-haoliu3/haoliu/SWE_result/gpt-5.4-mini-20260317-run2/preds.json"
    "/home/v-haoliu3/haoliu/SWE_result/gpt-5.4-mini-20260317-run3/preds.json"
    "/home/v-haoliu3/haoliu/SWE_result/claude-opus-4.5/run_1/preds.json"
    "/home/v-haoliu3/haoliu/SWE_result/claude-opus-4.5/run_2/preds.json"
    "/home/v-haoliu3/haoliu/SWE_result/claude-opus-4.5/run_3/preds.json"
)

# ---------- Test patches ----------
TEST_PREDS_PATHS=(
    "/home/v-haoliu3/SWT-RESULTS-Different-Issues/gpt-5-mini/pipeline_dropCode_all/preds_only_test.json"
    "/home/v-haoliu3/SWT-RESULTS-Different-Issues/gpt-5-mini/pipeline_initPatch_all/preds_only_test.json"
    "/home/v-haoliu3/SWT-RESULTS-Different-Issues/gpt-5-mini/pipeline_initTest_all/preds_only_test.json"
    "/home/v-haoliu3/SWT-RESULTS-Different-Issues/gpt-5-mini/pipeline_simple_all/preds_only_test.json"
    "/home/v-haoliu3/SWT-RESULTS-Different-Issues/gpt-5-mini/pipeline_standard_all/preds_only_test.json"
    "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini-4/pipeline_phase_agent_all/preds_only_test.json"
)

# ---------- Output ----------
OUTPUT_PATH="test_selection_different_issue.json"
RUN_ID="test_sel_diff_issue_$(date +%Y%m%d_%H%M%S)"
MAX_WORKERS=4
TIMEOUT=1800

echo "=== Test Selection (Different Issue) ==="
echo "Code patches (preds.json): ${CODE_PREDS_PATHS[*]}"
echo "Test patches: ${TEST_PREDS_PATHS[*]}"
echo "Output: ${OUTPUT_PATH}"
echo "Run ID: ${RUN_ID}"
echo ""

python -m src.test_selection \
    --code_preds_paths ${CODE_PREDS_PATHS[@]} \
    --test_preds_paths ${TEST_PREDS_PATHS[@]} \
    --output_path "${OUTPUT_PATH}" \
    --run_id "${RUN_ID}" \
    --max_workers ${MAX_WORKERS} \
    --timeout ${TIMEOUT} \
    --compute_coverage True \
    --merge

echo ""
echo "=== 完成 ==="
echo "结果写入: ${OUTPUT_PATH}"
