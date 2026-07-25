#!/bin/bash
#
# Run evaluation for all Twophase runs (gpt5 + gpt5mini)
# Results are moved to evaluation_results/Twophase/{model}/ after each run
#

set -euo pipefail
cd "$(dirname "$0")"

MAX_WORKERS=12
INPUT_BASE="inference_output/Twophase"
OUTPUT_BASE="evaluation_results/Twophase"

MODELS=("gpt5" "gpt5mini")

for model in "${MODELS[@]}"; do
    model_input_dir="${INPUT_BASE}/${model}"
    model_output_dir="${OUTPUT_BASE}/${model}"
    mkdir -p "${model_output_dir}"

    for jsonl in "${model_input_dir}"/*.jsonl; do
        filename=$(basename "$jsonl" .jsonl)
        run_id="${filename}"

        echo ""
        echo "============================================"
        echo "  Evaluating: ${model}/${filename}"
        echo "============================================"

        uv run -m src.main \
            --dataset_name princeton-nlp/SWE-bench_Verified \
            --predictions_path "${jsonl}" \
            --max_workers ${MAX_WORKERS} \
            --run_id "${run_id}" \
            --patch_types vanilla \
            --build_mode api

        # Move result file to structured output directory
        result_file=$(ls evaluation_results/*."${run_id}".json 2>/dev/null | head -1)
        if [ -n "${result_file}" ]; then
            mv "${result_file}" "${model_output_dir}/"
            echo "[DONE] Moved to ${model_output_dir}/$(basename ${result_file})"
        else
            echo "[WARN] No result file found for ${run_id}"
        fi
    done
done

echo ""
echo "=== All evaluations complete ==="
echo "Results in: ${OUTPUT_BASE}/"
