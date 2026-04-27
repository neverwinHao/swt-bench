#!/bin/bash

PREDS=(
    "/home/v-haoliu3/SWT_ALL_RUN_RESULT/aider/aider_claude-opus-4.5_20260421_193411/2026-04-21__19-34-13/preds_only_test.json"
    "/home/v-haoliu3/SWT_ALL_RUN_RESULT/aider/aider_gpt-5-high_20260420_193539/2026-04-20__19-35-41/preds_only_test.json"
    "/home/v-haoliu3/SWT_ALL_RUN_RESULT/aider/aider_gpt-5-mini-high_20260419_192721/2026-04-19__19-27-23/preds_only_test.json"
    "/home/v-haoliu3/SWT_ALL_RUN_RESULT/terminus_2/terminus_claude-opus-4.5_20260421_193416/2026-04-21__19-34-18/preds_only_test.json"
    "/home/v-haoliu3/SWT_ALL_RUN_RESULT/terminus_2/terminus_gpt-5_2-high_20260420_193552/2026-04-20__19-35-54/preds_only_test.json"
    "/home/v-haoliu3/SWT_ALL_RUN_RESULT/terminus_2/terminus_gpt-5-mini-2-high_20260419_193328/2026-04-19__19-33-29/preds_only_test.json"
)

for pred in "${PREDS[@]}"; do
    run_id=$(basename "$(dirname "$(dirname "$pred")")")
    echo "========== Running: $run_id =========="
    python -m src.main \
        --predictions_path "$pred" \
        --max_workers 4 \
        --cache_level "none" \
        --clean true \
        --run_id "$run_id" || exit 1
    echo ""
done
