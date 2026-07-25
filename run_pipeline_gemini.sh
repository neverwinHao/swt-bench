#!/bin/bash
cd /home/v-haoliu3/swt-bench-verified/swt-bench

uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/pipeline-model/gemini-2.5-pro/preds.jsonl \
    --max_workers 12 \
    --run_id pipeline-gemini-2.5-pro \
    --patch_types vanilla \
    --build_mode api
