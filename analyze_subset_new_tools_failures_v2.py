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

# 两个可能的日志路径
test_output_base = "/home/v-haoliu3/swt-bench/run_instance_swt_logs/5-mini-subset-new-tools/pred_post__subset_new_tools"
agent_log_base = "/home/v-haoliu3/SWT-RESULTS-LOC/gpt-5-mini/subset_new_tools"

# 分类结果
results = {
    'agent_timeout': [],            # Agent 执行超时
    'agent_error': [],              # Agent 执行过程中出错
    'test_not_found': [],           # Ran 0 tests (测试未被发现)
    'import_error': [],             # ImportError/ModuleNotFoundError (导入错误)
    'test_location_wrong': [],      # 测试位置错误
    'test_code_wrong': [],          # 测试代码写错
    'test_failed': [],              # 测试运行但失败
    'environment_error': [],        # 环境问题
    'patch_apply_error': [],        # patch 无法应用
    'not_found': [],                # 日志文件不存在
    'other': []                     # 其他情况
}

# 详细信息
details = {}

def check_agent_logs(inst_id):
    """检查 agent 日志以了解执行过程中的错误"""
    info_log_path = os.path.join(agent_log_base, inst_id, f"{inst_id}.info.log")
    debug_log_path = os.path.join(agent_log_base, inst_id, f"{inst_id}.debug.log")

    error_info = []

    # 检查 info.log
    if os.path.exists(info_log_path):
        with open(info_log_path, 'r', errors='ignore') as f:
            content = f.read()

        if 'CommandTimeoutError' in content or 'timeout after' in content:
            return 'timeout', 'Agent command timeout during execution'
        elif 'ERROR' in content and 'swea-agent' in content:
            # 提取错误信息
            error_matches = re.findall(r'ERROR.*?- (.+)', content)
            if error_matches:
                return 'agent_error', f"Agent error: {error_matches[-1][:150]}"

    return None, None

for inst_id in all_failed_ids:
    test_log_path = os.path.join(test_output_base, inst_id, "test_output.txt")
    detail_info = []

    # 首先检查测试输出日志
    if os.path.exists(test_log_path):
        with open(test_log_path, 'r', errors='ignore') as f:
            content = f.read()

        # 检查不同错误类型
        if 'Ran 0 tests' in content:
            # 测试未被发现
            if 'RuntimeError: Model class' in content and "doesn't declare an explicit app_label" in content:
                results['test_location_wrong'].append(inst_id)
                detail_info.append("Model app_label issue - test location likely wrong")
            elif 'No module named' in content or 'ModuleNotFoundError' in content:
                results['import_error'].append(inst_id)
                detail_info.append("Import error with 0 tests")
            elif 'ImportError' in content:
                results['import_error'].append(inst_id)
                detail_info.append("Import error with 0 tests")
            elif "couldn't import module" in content.lower():
                results['test_code_wrong'].append(inst_id)
                detail_info.append("Couldn't import test module")
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
            ran_match = re.search(r'Ran (\d+) test', content)
            if ran_match and int(ran_match.group(1)) > 0:
                results['test_failed'].append(inst_id)
                detail_info.append("Test ERROR")
            elif 'TimeoutError' in content or 'timeout' in content.lower():
                results['environment_error'].append(inst_id)
                detail_info.append("Timeout error")
            else:
                results['other'].append(inst_id)
                detail_info.append("ERROR but unclear type")

        elif 'OK' in content:
            # 测试通过但标记为 unresolved
            ran_match = re.search(r'Ran (\d+) test', content)
            if ran_match and int(ran_match.group(1)) > 0:
                results['test_failed'].append(inst_id)
                detail_info.append(f"Tests passed ({ran_match.group(1)}) but didn't cover fail-to-pass")
            else:
                results['test_not_found'].append(inst_id)
                detail_info.append("OK but 0 tests")
        else:
            results['other'].append(inst_id)
            detail_info.append("Unknown error type in test output")

    else:
        # 测试输出日志不存在，检查 agent 日志
        error_type, error_msg = check_agent_logs(inst_id)

        if error_type == 'timeout':
            results['agent_timeout'].append(inst_id)
            detail_info.append(error_msg)
        elif error_type == 'agent_error':
            results['agent_error'].append(inst_id)
            detail_info.append(error_msg)
        else:
            results['not_found'].append(inst_id)
            detail_info.append("No test output or agent log found")

    details[inst_id] = "; ".join(detail_info) if detail_info else "No details"

# 打印结果
print("=" * 80)
print("错误分类结果")
print("=" * 80)

categories = [
    ('agent_timeout', 'Agent 执行超时',
     'Agent 在运行过程中命令超时（通常是pytest等命令超过30秒）'),
    ('agent_error', 'Agent 执行错误',
     'Agent 在执行过程中遇到其他错误'),
    ('test_not_found', '测试未被发现 (Ran 0 tests)',
     '测试没有被测试框架发现，可能是测试文件路径错误或测试格式不对'),
    ('import_error', '导入错误 (ImportError/ModuleNotFoundError)',
     '测试代码中的导入语句失败'),
    ('test_location_wrong', '测试位置错误',
     '测试文件位置不对，导致模型无法正确加载（如 app_label 问题）'),
    ('test_code_wrong', '测试代码写错',
     '测试文件路径或内容有问题'),
    ('test_failed', '测试运行但失败',
     '测试被正确运行但断言失败，或测试通过但没覆盖 fail-to-pass'),
    ('environment_error', '环境错误',
     'timeout、数据库等环境问题'),
    ('patch_apply_error', 'Patch 应用失败',
     '生成的 patch 无法应用到代码库'),
    ('not_found', '日志未找到',
     '找不到任何相关日志'),
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
print(f"{'错误类型':<45} | {'数量':>6} | {'占比':>7}")
print("-" * 80)
total = len(all_failed_ids)
for title, count in summary_table:
    percentage = (count / total * 100) if total > 0 else 0
    print(f"{title:<45} | {count:>6} | {percentage:>6.1f}%")
print("-" * 80)
print(f"{'总计':<45} | {total:>6} | {'100.0%':>7}")
print("=" * 80)

# 对比上次的结果
print("\n" + "=" * 80)
print("与上次结果对比")
print("=" * 80)
print("上次总计: 43 个失败案例")
print("本次总计: 23 个失败案例 (减少了 20 个，下降 46.5%)")
print()
print("上次的主要错误类型:")
print("  - 测试未被发现: 12个 (27.9%)")
print("  - 导入错误: 8个 (18.6%)")
print("  - test位置写错: 4个 (9.3%)")
print("  - 测试代码写错: 8个 (18.6%)")
print("  - 其他情况: 10个 (23.3%)")
print()
print("本次的主要错误类型:")
for title, count in summary_table[:5]:  # 只显示前5个
    percentage = (count / total * 100) if total > 0 else 0
    print(f"  - {title}: {count}个 ({percentage:.1f}%)")

# 保存详细结果到文件
output_file = "/home/v-haoliu3/swt-bench/analysis_subset_new_tools_failures_v2.json"
with open(output_file, 'w') as f:
    json.dump({
        'summary': {k: len(v) for k, v in results.items()},
        'details': results,
        'instance_details': details,
        'comparison': {
            'previous_total': 43,
            'current_total': total,
            'improvement': 43 - total,
            'improvement_percentage': (43 - total) / 43 * 100
        }
    }, f, indent=2, ensure_ascii=False)

print(f"\n详细结果已保存到: {output_file}")
