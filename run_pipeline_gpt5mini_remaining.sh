#!/bin/bash
# Evaluate missing gpt5-mini pipeline runs (k4, k5)
set -euo pipefail
cd /home/v-haoliu3/swt-bench-verified/swt-bench

for k in 4 5; do
    RUN_ID="gpt5-mini-pipeline-k${k}"
    JSONL="inference_output/pipeline-multi-run/gpt5-mini/${RUN_ID}.jsonl"
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
        mv "${result_file}" "evaluation_results/pipeline-multi-run/gpt5-mini/"
        echo "[DONE] -> evaluation_results/pipeline-multi-run/gpt5-mini/$(basename ${result_file})"
    fi
done

echo "=== All done ==="
