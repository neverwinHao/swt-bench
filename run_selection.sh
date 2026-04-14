#!/bin/bash
#
# Test Selection Metadata Builder
#
# 功能：对每个 instance，把候选 test patch 跑在候选 code patch 上，
#       产出 SWT 对齐的 metadata（resolved, FAIL_TO_PASS, coverage 等），
#       用于后续 test selection 模型训练。
#
# 原理：对每个 (test_patch, code_patch) 组合跑 4 次 docker 评测：
#       pred_pre  = 只 apply test patch（bug 还在）
#       pred_post = apply code patch + test patch（bug 修复后）
#       base_pre  = 什么都不 apply（基线）
#       base_post = 只 apply code patch（基线+修复）
#       然后对比 pre/post 得到 FAIL_TO_PASS, resolved, coverage 等指标。
#
# ============================================================
# 使用方式
# ============================================================
#
# 1) 直接运行整个脚本（跑下面配置好的所有任务）:
#       bash test_selection.sh
#
# 2) 也可以手动调用 python 命令，参数说明：
#
#   必选参数：
#     --code_patch_dirs   code patch 目录，可传多个，空格分隔
#                         目录结构：<dir>/<instance_id>/<instance_id>.patch
#     --test_preds_paths  test patch 的 preds JSON 文件，可传多个
#                         格式：{instance_id: {model_patch: "diff ...", ...}}
#     --output_path       输出 JSON 文件路径
#     --run_id            本次运行的唯一 ID（用于日志目录隔离）
#
#   可选参数：
#     --dataset_name      数据集名，默认 princeton-nlp/SWE-bench
#     --split             数据集 split，默认 test
#     --instance_ids      指定要跑的 instance（空格分隔），不填则跑所有匹配的
#     --max_workers       并行 worker 数，默认 4
#     --timeout           单次 docker 运行超时秒数，默认 1800
#     --compute_coverage  是否计算 coverage，默认 True
#     --force_rebuild     是否强制重建 docker 镜像，默认 False
#     --build_mode        docker build 模式 api/cli，默认 api
#     --merge             追加模式：把新结果 merge 到已有 output 文件
#     --open_file_limit   文件打开数限制，默认 4096
#
# ============================================================
# 输出格式
# ============================================================
#
#   {
#     "django__django-10880": {
#       "instance_id": "django__django-10880",
#       "results": {
#         "Code-Patch-5.2__preds_pipeline": {
#           "code_patch_source": "Code-Patch-5.2",
#           "test_patch_source": "preds_pipeline",
#           "patch_successfully_applied": true,
#           "resolved": true,              <-- test 能否判定 code patch 修复了 bug
#           "added_f2p": 1,                <-- 新增的 fail->pass test 数量
#           "coverage_pred": 0.778,        <-- test 对 golden patch 改动行的覆盖率
#           "coverage_delta_pred": 0.778,  <-- 相比 base 的 coverage 增量
#           "tests_pred": {                <-- pre/post 对比结果
#             "FAIL_TO_PASS": ["test_xxx (module.Class)"],
#             "PASS_TO_PASS": ["test_yyy (module.Class)"],
#             "FAIL_TO_FAIL": [],
#             "PASS_TO_FAIL": []
#           },
#           "tests_base": { ... }
#         }
#       }
#     }
#   }
#
# ============================================================

set -euo pipefail
cd "$(dirname "$0")"

# ---------- 路径配置（按需修改） ----------

# Code patch 目录（每个目录下是 <instance_id>/<instance_id>.patch）
CODE_PATCH_DIRS=(
    "/home/v-haoliu3/haoliu/CodePatch/Code-Patch-5.2"
    "/home/v-haoliu3/haoliu/CodePatch/Code-Patch-5.4mini"
)

# Test patch 预测文件（JSON，key=instance_id）
TEST_PREDS_PATHS=(
    "/home/v-haoliu3/haoliu/SWT-Results/gpt-5-mini/naive_no_thinking_rpg_json/preds_different_issue.json"
    "/home/v-haoliu3/haoliu/SWT-Results/gpt-5-mini/naive_no_thinking_rpg_json/preds_pipeline.json"
)

# 输出文件
OUTPUT_PATH="test_selection_metadata.json"

# 运行配置
RUN_ID="test_sel_$(date +%Y%m%d_%H%M%S)"
MAX_WORKERS=4
TIMEOUT=1800

# ---------- 运行方式选择 ----------

# ============================
# 方式一：一次跑所有组合
# ============================
echo "=== 一次跑所有 code patch x test patch 组合 ==="
echo "Code patches: ${CODE_PATCH_DIRS[*]}"
echo "Test patches:  ${TEST_PREDS_PATHS[*]}"
echo "Output:        ${OUTPUT_PATH}"
echo "Run ID:        ${RUN_ID}"
echo ""

python -m src.test_selection \
    --code_patch_dirs ${CODE_PATCH_DIRS[@]} \
    --test_preds_paths ${TEST_PREDS_PATHS[@]} \
    --output_path "${OUTPUT_PATH}" \
    --run_id "${RUN_ID}" \
    --max_workers ${MAX_WORKERS} \
    --timeout ${TIMEOUT} \
    --compute_coverage True

echo ""
echo "=== 完成 ==="
echo "结果写入: ${OUTPUT_PATH}"

# ============================
# 方式二：分批跑 + merge（取消注释使用）
# ============================
# 适用场景：先跑一批 code patch，后面有新的 code patch 再追加
#
# # 第一批
# python -m src.test_selection \
#     --code_patch_dirs /home/v-haoliu3/haoliu/CodePatch/Code-Patch-5.2 \
#     --test_preds_paths ${TEST_PREDS_PATHS[@]} \
#     --output_path "${OUTPUT_PATH}" \
#     --run_id "test_sel_batch1"
#
# # 第二批（--merge 追加到同一个输出文件）
# python -m src.test_selection \
#     --code_patch_dirs /home/v-haoliu3/haoliu/CodePatch/Code-Patch-5.4mini \
#     --test_preds_paths ${TEST_PREDS_PATHS[@]} \
#     --output_path "${OUTPUT_PATH}" \
#     --run_id "test_sel_batch2" \
#     --merge

# ============================
# 方式三：只跑指定的 instance（取消注释使用）
# ============================
# python -m src.test_selection \
#     --code_patch_dirs ${CODE_PATCH_DIRS[@]} \
#     --test_preds_paths ${TEST_PREDS_PATHS[@]} \
#     --instance_ids django__django-10880 sympy__sympy-12096 django__django-11087 \
#     --output_path "${OUTPUT_PATH}" \
#     --run_id "${RUN_ID}"
