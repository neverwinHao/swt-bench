#!/bin/bash
cd /home/v-haoliu3/swt-bench-verified/swt-bench

# gpt-5mini simple
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/gpt-5mini/trae-agent_gpt-5mini_simple_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_gpt-5mini_simple --patch_types vanilla --build_mode api

# gpt-5mini standard
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/gpt-5mini/trae-agent_gpt-5mini_standard_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_gpt-5mini_standard --patch_types vanilla --build_mode api

# gpt-5mini dropCode
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/gpt-5mini/trae-agent_gpt-5mini_dropCode_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_gpt-5mini_dropCode --patch_types vanilla --build_mode api

# gpt-5mini initPatch
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/gpt-5mini/trae-agent_gpt-5mini_initPatch_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_gpt-5mini_initPatch --patch_types vanilla --build_mode api

# gpt-5mini initTest
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/gpt-5mini/trae-agent_gpt-5mini_initTest_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_gpt-5mini_initTest --patch_types vanilla --build_mode api

# opus simple
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/opus/trae-agent_opus_simple_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_opus_simple --patch_types vanilla --build_mode api

# opus standard
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/opus/trae-agent_opus_standard_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_opus_standard --patch_types vanilla --build_mode api

# opus dropCode
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/opus/trae-agent_opus_dropCode_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_opus_dropCode --patch_types vanilla --build_mode api

# opus initPatch
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/opus/trae-agent_opus_initPatch_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_opus_initPatch --patch_types vanilla --build_mode api

# opus initTest
uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/Different-Issue/opus/trae-agent_opus_initTest_verified.jsonl \
    --max_workers 12 \
    --run_id trae-agent_opus_initTest --patch_types vanilla --build_mode api
