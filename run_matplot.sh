EVAL_JSON="/home/v-haoliu3/swt-bench/evaluation_results/gpt_5_pipeline_phase_agent_all_2.gpt-5_2-gpt_5_pipeline_phase_agent_all_2-20260405.json"

# Extract run_id from filename: {pred_name}.{run_id}.json
FILENAME=$(basename "$EVAL_JSON" .json)
RUN_ID="${FILENAME#*.}"

echo "Run ID: $RUN_ID"

python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-RPG/gpt-5-mini/test_rpg_analysis_subagent_f2p_all/preds_only_test.json" \
    --max_workers 8 \
    --cache_level "none" \
    --clean true \
    --run_id "$RUN_ID"





EVAL_JSON="/home/v-haoliu3/swt-bench/evaluation_results/naive_no_thinking_all_1.naive_no_thinking_all_1-20260320-only-test.json"

# Extract run_id from filename: {pred_name}.{run_id}.json
FILENAME=$(basename "$EVAL_JSON" .json)
RUN_ID="${FILENAME#*.}"

echo "Run ID: $RUN_ID"

python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-NAIVE/gpt-5-mini/naive_no_thinking_all_1/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "$RUN_ID"



EVAL_JSON="/home/v-haoliu3/swt-bench/evaluation_results/naive_no_thinking_all_2.naive_no_thinking_all_2-20260320-only-test.json"

# Extract run_id from filename: {pred_name}.{run_id}.json
FILENAME=$(basename "$EVAL_JSON" .json)
RUN_ID="${FILENAME#*.}"

echo "Run ID: $RUN_ID"

python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-NAIVE/gpt-5-mini/naive_no_thinking_all_2/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "$RUN_ID"



EVAL_JSON="/home/v-haoliu3/swt-bench/evaluation_results/pipeline_phase_agent_all_5mini_none.pipeline_phase_agent_all_5mini_none-20260320-only-test.json"

# Extract run_id from filename: {pred_name}.{run_id}.json
FILENAME=$(basename "$EVAL_JSON" .json)
RUN_ID="${FILENAME#*.}"

echo "Run ID: $RUN_ID"

python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini-4/pipeline_phase_agent_all_5mini_none/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "$RUN_ID"


