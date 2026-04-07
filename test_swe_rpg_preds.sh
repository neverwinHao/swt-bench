#!/bin/bash

echo "=== [1/3] Running swe_rpg_only_test ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-RPG/gpt-5-mini/swe_rpg_f2p/preds.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "swe_rpg_preds-20260308-preds"
echo "=== [1/3] Done ==="

echo "=== [2/3] Running swe_subagent_f2p_2 preds ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-RPG/gpt-5-mini/test_subagent_f2p_2/preds.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "swe_subagent_f2p_2-20260307-preds"
echo "=== [2/3] Done ==="

echo "=== [3/3] Running swe_subagent_f2p_2 preds_only_test ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-RPG/gpt-5-mini/test_subagent_f2p_2/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "swe_subagent_f2p_2-20260307-preds_only_test"
echo "=== [3/3] Done ==="

echo "All 3 runs completed."