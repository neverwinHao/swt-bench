#!/bin/bash

cd /home/v-haoliu3/swt-bench

echo "=== [1/3] no_rpg ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/Ablation/gpt-5-mini/pipeline_phase_agent_no_rpg_all1/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_phase_agent_no_rpg_all1-20260325-only-test"
echo "=== [1/3] Done ==="

echo "=== [2/3] only_search_retrieve ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/Ablation/gpt-5-mini-2/pipeline_phase_agent_only_search_retrieve_all1/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_phase_agent_only_search_retrieve_all1-20260325-only-test"
echo "=== [2/3] Done ==="

echo "=== [3/3] no_summary ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/Ablation/gpt-5-mini-3/pipeline_phase_agent_no_summary_all1/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_phase_agent_no_summary_all1-20260325-only-test"
echo "=== [3/3] Done ==="

echo "=== All 3 runs completed! ==="
