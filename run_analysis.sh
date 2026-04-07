python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-RPG/gpt-5-mini/test_rpg_analysis_subagent_f2p_3/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "swe_rpg_analysis_subagent_f2p_3-20260311-only-test"



python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini/pipeline_3/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "swe_pipeline_3-20260311-only-test"


python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini/pipeline_1/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "swe_pipeline_1-20260311-only-test"