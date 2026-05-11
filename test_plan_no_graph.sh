python -m src.main \
    --predictions_path "/home/xinzhang3/haoliu/baselines-swt/e-otter/inference_outputs/claude_e_otter_plus_verified.json" \
    --max_workers 12 \
    --cache_level "none" \
    --clean true \
    --run_id "claude_e_otter_plus_verified"



python -m src.main \
    --predictions_path "/home/xinzhang3/haoliu/gpt-5-no-th.json" \
    --max_workers 12 \
    --cache_level "none" \
    --clean true \
    --run_id "gpt-5-no-th"