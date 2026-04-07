#!/usr/bin/env python3
"""
分析 subset_new_tools 的失败案例
包括 unresolved (16个) 和 error (7个) 共 23 个案例
"""
import os
import re
import json

# 从 evaluation_results JSON 文件中读取失败的实例
eval_results_path = "/home/v-haoliu3/swt-bench/evaluation_results/subset_new_tools.5-mini-subset-new-tools.json"
with open(eval_results_path, 'r') as f:
    eval_data = json.load(f)

unresolved_ids = eval_data['unresolved_ids']
error_ids = eval_data['error_ids']

print(f"Unresolved instances: {len(unresolved_ids)}")
print(f"Error instances: {len(error_ids)}")
print(f"Total to analyze: {len(unresolved_ids) + len(error_ids)}\n")

# 合并所有需要分析的实例
all_failed_ids = unresolved_ids + error_ids

base_path = "/home/v-haoliu3/swt-bench/run_instance_swt_logs/5-mini-subset-new-tools/pred_post__subset_new_tools"

# 分类结果
results = {
    'test_not_found': [],           # Ran 0 tests (测试未被发现)
    'import_error': [],             # ImportError/ModuleNotFoundError (导入错误)
    'test_location_wrong': [],      # 测试位置错误（应该是相对于 /testbed 的）
    'test_code_wrong': [],          # 测试代码写错（测试文件路径不对或测试文件内容有问题）
    'test_failed': [],              # 测试运行了但失败（assertions failed）
    'environment_error': [],        # 环境问题（timeout, database, etc.）
    'patch_apply_error': [],        # patch 无法应用
    'not_found': [],                # 日志文件不存在
    'other': []                     # 其他情况
}

# 详细信息（用于进一步分析）
details = {}

for inst_id in all_failed_ids:
    log_path = os.path.join(base_path, inst_id, "test_output.txt")

    if not os.path.exists(log_path):
        results['not_found'].append(inst_id)
        details[inst_id] = "Log file not found"
        continue

    with open(log_path, 'r', errors='ignore') as f:
        content = f.read()

    # 提取关键信息
    detail_info = []

    # 检查不同错误类型
    if 'Ran 0 tests' in content:
        # 测试未被发现
        if 'RuntimeError: Model class' in content and "doesn't declare an explicit app_label" in content:
            results['test_location_wrong'].append(inst_id)
            detail_info.append("Model app_label issue - likely test location wrong")
        elif 'No module named' in content or 'ModuleNotFoundError' in content:
            results['import_error'].append(inst_id)
            detail_info.append("Import error with 0 tests")
        elif 'ImportError' in content:
            results['import_error'].append(inst_id)
            detail_info.append("Import error with 0 tests")
        elif "couldn't import module" in content.lower():
            results['test_code_wrong'].append(inst_id)
            detail_info.append("Couldn't import test module - likely wrong test path")
        elif 'tests/generated_tests.py' in content or 'tests/invalid_models_tests/generated_tests.py' in content:
            results['test_code_wrong'].append(inst_id)
            detail_info.append("Generated test file in wrong location")
        else:
            results['test_not_found'].append(inst_id)
            detail_info.append("Ran 0 tests - test not discovered")

    elif 'ImportError' in content or 'ModuleNotFoundError' in content:
        # 导入错误
        results['import_error'].append(inst_id)
        import_match = re.search(r'(ImportError|ModuleNotFoundError): (.+)', content)
        if import_match:
            detail_info.append(f"Import error: {import_match.group(2)[:100]}")
        else:
            detail_info.append("Import error")

    elif 'error: unrecognized input' in content or 'error: patch failed' in content:
        # patch 应用失败
        results['patch_apply_error'].append(inst_id)
        detail_info.append("Patch apply error")

    elif 'FAILED' in content or 'FAIL:' in content:
        # 检查测试是否真的运行了
        ran_match = re.search(r'Ran (\d+) test', content)
        if ran_match and int(ran_match.group(1)) > 0:
            # 测试运行了但失败
            results['test_failed'].append(inst_id)
            # 尝试找到失败的原因
            if 'AssertionError' in content:
                assert_match = re.search(r'AssertionError: (.+)', content)
                if assert_match:
                    detail_info.append(f"Assertion failed: {assert_match.group(1)[:100]}")
                else:
                    detail_info.append("Assertion failed")
            elif 'AttributeError' in content:
                detail_info.append("AttributeError in test")
            else:
                detail_info.append("Test failed")
        else:
            results['test_not_found'].append(inst_id)
            detail_info.append("FAILED but 0 tests ran")

    elif 'ERROR' in content:
        # 检查是测试错误还是环境错误
        ran_match = re.search(r'Ran (\d+) test', content)
        if ran_match and int(ran_match.group(1)) > 0:
            results['test_failed'].append(inst_id)
            detail_info.append("Test ERROR")
        elif 'TimeoutError' in content or 'timeout' in content.lower():
            results['environment_error'].append(inst_id)
            detail_info.append("Timeout error")
        elif 'Database' in content or 'database' in content:
            results['environment_error'].append(inst_id)
            detail_info.append("Database error")
        else:
            results['other'].append(inst_id)
            detail_info.append("ERROR but unclear what type")

    elif 'OK' in content:
        # 测试通过但被标记为 unresolved - 可能是没有覆盖到 fail_to_pass 的测试
        ran_match = re.search(r'Ran (\d+) test', content)
        if ran_match and int(ran_match.group(1)) > 0:
            results['test_failed'].append(inst_id)
            detail_info.append(f"Tests passed ({ran_match.group(1)} tests) but didn't cover fail-to-pass")
        else:
            results['test_not_found'].append(inst_id)
            detail_info.append("OK but 0 tests")
    else:
        results['other'].append(inst_id)
        detail_info.append("Unknown error type")

    details[inst_id] = "; ".join(detail_info) if detail_info else "No details"

# 打印结果
print("=" * 80)
print("错误分类结果")
print("=" * 80)

categories = [
    ('test_not_found', '测试未被发现 (Ran 0 tests)',
     '测试没有被测试框架发现，可能是测试文件路径错误或测试格式不对'),
    ('import_error', '导入错误 (ImportError/ModuleNotFoundError)',
     '测试代码中的导入语句失败'),
    ('test_location_wrong', '测试位置错误',
     '测试文件位置不对，导致模型无法正确加载'),
    ('test_code_wrong', '测试代码写错',
     '测试文件路径或内容有问题'),
    ('test_failed', '测试运行但失败',
     '测试被正确运行但断言失败或测试通过但没覆盖 fail-to-pass'),
    ('environment_error', '环境错误',
     'timeout、数据库等环境问题'),
    ('patch_apply_error', 'Patch 应用失败',
     '生成的 patch 无法应用到代码库'),
    ('not_found', '日志未找到',
     '找不到测试输出日志'),
    ('other', '其他情况',
     '未分类的其他错误')
]

summary_table = []

for key, title, description in categories:
    count = len(results[key])
    if count > 0:
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"数量: {count}")
        print(f"说明: {description}")
        print(f"{'='*80}")
        for inst_id in results[key]:
            print(f"  - {inst_id}")
            if inst_id in details and details[inst_id]:
                print(f"    详情: {details[inst_id]}")
        summary_table.append((title, count))

# 打印汇总表格
print("\n" + "=" * 80)
print("汇总表格")
print("=" * 80)
print(f"{'错误类型':<40} | {'数量':>6}")
print("-" * 80)
for title, count in summary_table:
    print(f"{title:<40} | {count:>6}")
print("-" * 80)
print(f"{'总计':<40} | {len(all_failed_ids):>6}")
print("=" * 80)

# 保存详细结果到文件
output_file = "/home/v-haoliu3/swt-bench/analysis_subset_new_tools_failures.json"
with open(output_file, 'w') as f:
    json.dump({
        'summary': {k: len(v) for k, v in results.items()},
        'details': results,
        'instance_details': details
    }, f, indent=2, ensure_ascii=False)

print(f"\n详细结果已保存到: {output_file}")
