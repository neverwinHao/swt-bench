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