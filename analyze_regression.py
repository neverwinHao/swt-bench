import os
import re

# Regression instances: without_graph 成功，with_graph 失败
instances = [
    'pallets__flask-5014', 'django__django-11066', 'django__django-11820',
    'django__django-15161', 'django__django-15277', 'astropy__astropy-13579',
    'django__django-12858', 'django__django-11728', 'sphinx-doc__sphinx-10449',
    'django__django-12741', 'django__django-16527', 'astropy__astropy-13977',
    'django__django-11119', 'django__django-12276', 'django__django-11206',
    'pydata__xarray-4966', 'sympy__sympy-14248', 'django__django-14122',
    'django__django-15741', 'django__django-15280', 'django__django-16139',
    'sympy__sympy-22714', 'scikit-learn__scikit-learn-14894', 'django__django-15037',
    'sympy__sympy-14531', 'django__django-14373', 'sphinx-doc__sphinx-9658',
    'django__django-13410', 'django__django-11749', 'django__django-15022',
    'django__django-12125', 'pytest-dev__pytest-7324', 'sympy__sympy-13615',
    'django__django-16631', 'django__django-11163', 'pytest-dev__pytest-6202',
    'django__django-11400', 'django__django-14089', 'django__django-12406',
    'django__django-17029', 'django__django-15916', 'django__django-16642',
    'django__django-13837'
]

base_path = "/home/v-haoliu3/swt-bench/run_instance_swt_logs/5-mini-graph/pred_post__with_graph"

results = {
    'format_error': [],      # Ran 0 tests - 测试格式错误（独立函数而非TestCase类）
    'import_error': [],      # ImportError/ModuleNotFoundError - 导入路径错误
    'test_code_error': [],   # RuntimeError/AttributeError等 - 测试代码编写错误
    'assertion_error': [],   # AssertionError - 测试逻辑错误或测试范围过度
    'not_found': [],         # 日志不存在
    'other': []              # 其他
}

details = {}

for inst_id in instances:
    log_path = os.path.join(base_path, inst_id, "test_output.txt")

    if not os.path.exists(log_path):
        results['not_found'].append(inst_id)
        continue

    with open(log_path, 'r', errors='ignore') as f:
        content = f.read()

    # 提取关键错误信息
    error_detail = ""

    # 检查不同错误类型
    if 'Ran 0 tests' in content:
        results['format_error'].append(inst_id)
        error_detail = "Ran 0 tests - 测试未被发现（可能是独立函数格式）"
    elif 'ImportError' in content or 'ModuleNotFoundError' in content:
        results['import_error'].append(inst_id)
        # 提取具体的导入错误
        match = re.search(r'(ImportError|ModuleNotFoundError)[^\n]*\n?[^\n]*', content)
        if match:
            error_detail = match.group(0)[:200]
    elif 'AssertionError' in content:
        results['assertion_error'].append(inst_id)
        # 提取断言错误详情
        match = re.search(r'AssertionError[^\n]*', content)
        if match:
            error_detail = match.group(0)[:200]
    elif re.search(r'(RuntimeError|AttributeError|TypeError|NameError|KeyError|ValueError):', content):
        results['test_code_error'].append(inst_id)
        # 提取具体错误
        match = re.search(r'(RuntimeError|AttributeError|TypeError|NameError|KeyError|ValueError):[^\n]*', content)
        if match:
            error_detail = match.group(0)[:200]
    elif 'ERROR' in content or 'FAILED' in content:
        # 检查是否有测试运行
        ran_match = re.search(r'Ran (\d+) test', content)
        if ran_match and int(ran_match.group(1)) > 0:
            results['other'].append(inst_id)
            error_detail = f"Ran {ran_match.group(1)} tests but had errors"
        else:
            results['other'].append(inst_id)
            error_detail = "ERROR/FAILED but unclear cause"
    else:
        results['other'].append(inst_id)
        error_detail = "Unknown - need manual inspection"

    details[inst_id] = error_detail

# 输出结果
print("=" * 80)
print("1. FORMAT ERROR (Ran 0 tests - 测试格式错误，如独立函数而非TestCase类)")
print("=" * 80)
for inst in sorted(results['format_error']):
    print(f"  - {inst}")
print(f"\nTotal: {len(results['format_error'])}")

print("\n" + "=" * 80)
print("2. IMPORT ERROR (ImportError/ModuleNotFoundError - 导入路径错误)")
print("=" * 80)
for inst in sorted(results['import_error']):
    print(f"  - {inst}")
    if inst in details:
        print(f"    Error: {details[inst][:100]}...")
print(f"\nTotal: {len(results['import_error'])}")

print("\n" + "=" * 80)
print("3. TEST CODE ERROR (RuntimeError/AttributeError等 - 测试代码编写错误)")
print("=" * 80)
for inst in sorted(results['test_code_error']):
    print(f"  - {inst}")
    if inst in details:
        print(f"    Error: {details[inst][:100]}...")
print(f"\nTotal: {len(results['test_code_error'])}")

print("\n" + "=" * 80)
print("4. ASSERTION ERROR (AssertionError - 测试断言失败/测试范围过度)")
print("=" * 80)
for inst in sorted(results['assertion_error']):
    print(f"  - {inst}")
    if inst in details:
        print(f"    Error: {details[inst][:100]}...")
print(f"\nTotal: {len(results['assertion_error'])}")

print("\n" + "=" * 80)
print("5. NOT FOUND (日志不存在)")
print("=" * 80)
for inst in sorted(results['not_found']):
    print(f"  - {inst}")
print(f"\nTotal: {len(results['not_found'])}")

print("\n" + "=" * 80)
print("6. OTHER (其他错误)")
print("=" * 80)
for inst in sorted(results['other']):
    print(f"  - {inst}")
    if inst in details:
        print(f"    Error: {details[inst][:100]}...")
print(f"\nTotal: {len(results['other'])}")

# 汇总
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
total = sum(len(v) for v in results.values())
print(f"Total instances analyzed: {total}")
print(f"  - Format Error (Ran 0 tests): {len(results['format_error'])}")
print(f"  - Import Error: {len(results['import_error'])}")
print(f"  - Test Code Error: {len(results['test_code_error'])}")
print(f"  - Assertion Error: {len(results['assertion_error'])}")
print(f"  - Not Found: {len(results['not_found'])}")
print(f"  - Other: {len(results['other'])}")
