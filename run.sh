uv run -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path inference_output/openhands_gpt-5-mini_CI_SETUP_verified.jsonl \
    --max_workers 12 \
    --run_id openhands_verified_gpt5-mini-2  --patch_types vanilla  --build_mode api


uv run -m src.report \
    run_instance_swt_logs/openhands_verified_gpt5-mini-2/"OpenHands__CodeActAgent__gpt-5-mini-2025-08-07"/ \
    --dataset verified

uv run -m src.report \
    /home/v-haoliu3/swt-bench-verified/swt-bench/run_instance_swt_logs/trae-agent_gpt5_twophase/trae-agent_gpt5_twophase \
    --dataset verified