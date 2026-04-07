#!/bin/bash

cd /home/v-haoliu3/swt-bench

echo "=== [1/6] pipeline_v3_1 ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini/pipeline_v3_1/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_v3_1_final_20260314_only_test"
echo "=== [1/6] Done ==="

echo "=== [2/6] pipeline_v3_2 ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini/pipeline_v3_2/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_v3_2_final_20260314_only_test"
echo "=== [2/6] Done ==="

echo "=== [3/6] pipeline_v3_3 ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini/pipeline_v3_3/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_v3_3_final_20260314_only_test"
echo "=== [3/6] Done ==="

echo "=== [4/6] pipeline_v3_ablation_1 ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini/pipeline_v3_ablation1/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_v3_1_ablation_final_20260314_only_test"
echo "=== [4/6] Done ==="


echo "=== [5/6] pipeline_v3_ablation_2 ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini/pipeline_v3_ablation2/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_v3_2_ablation_final_20260314_only_test"
echo "=== [5/6] Done ==="

echo "=== [6/6] pipeline_v3_ablation_3 ==="
python -m src.main \
    --predictions_path "/home/v-haoliu3/SWT-RESULTS-PIPELINE/gpt-5-mini/pipeline_v3_ablation3/preds_only_test.json" \
    --max_workers 4 \
    --cache_level "none" \
    --clean true \
    --run_id "pipeline_v3_3_ablation_final_20260314_only_test"
echo "=== [6/6] Done ==="

echo "=== All 6 runs completed! ==="
