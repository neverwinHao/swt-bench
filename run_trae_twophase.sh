#!/bin/bash

uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/trae-agent_gpt5_twophase_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_gpt5_twophase --patch_types vanilla --build_mode api \