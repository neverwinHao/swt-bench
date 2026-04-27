#!/bin/bash
cd /home/v-haoliu3/swt-bench

python -m src.golden_test_eval \
    --code_preds_paths \
        /home/v-haoliu3/haoliu/SWE_result/claude-opus-4.5/run_1/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/claude-opus-4.5/run_2/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/claude-opus-4.5/run_3/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/claude-sonnet-4.5/run_1/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/claude-sonnet-4.5/run_2/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/claude-sonnet-4.5/run_3/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/claude-haiku-4.5/run_1/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/claude-haiku-4.5/run_2/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/claude-haiku-4.5/run_3/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/gpt-5.4-mini-20260317/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/gpt-5.4-mini-20260317-run2/preds.json \
        /home/v-haoliu3/haoliu/SWE_result/gpt-5.4-mini-20260317-run3/preds.json \
    --dataset_name eth-sri/SWT-bench_Verified_bm25_27k_zsp \
    --split test \
    --is_swt True \
    --output_path /home/v-haoliu3/swt-bench/code_patch_golden_test_metadata.json \
    --run_id golden_eval_v1 \
    --max_workers 4 \
    --merge
