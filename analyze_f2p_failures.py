import os
import re

# instances = [
#     'django__django-13410', 'matplotlib__matplotlib-24627', 'django__django-12741',
#     'django__django-14373', 'sympy__sympy-14248', 'django__django-14122',
#     'sympy__sympy-13615', 'sphinx-doc__sphinx-10449', 'sympy__sympy-14531',
#     'matplotlib__matplotlib-24570', 'matplotlib__matplotlib-20676', 'django__django-12406',
#     'matplotlib__matplotlib-24970', 'matplotlib__matplotlib-20826', 'django__django-11400',
#     'matplotlib__matplotlib-20859', 'matplotlib__matplotlib-13989', 'django__django-16139',
#     'matplotlib__matplotlib-26208', 'django__django-13512', 'sympy__sympy-22714',
#     'matplotlib__matplotlib-22719', 'matplotlib__matplotlib-25332', 'django__django-12262',
#     'django__django-13569', 'django__django-16631', 'django__django-17087',
#     'django__django-11119', 'django__django-11206', 'django__django-15957',
#     'django__django-11820', 'django__django-11749', 'django__django-14999',
#     'django__django-11211', 'django__django-17029', 'matplotlib__matplotlib-26113',
#     'django__django-15037', 'django__django-12125', 'django__django-15277',
#     'django__django-14089', 'django__django-10880', 'sphinx-doc__sphinx-9658',
#     'django__django-13810', 'django__django-15916', 'matplotlib__matplotlib-23314',
#     'astropy__astropy-14369', 'django__django-11603', 'django__django-12276',
#     'django__django-15022', 'astropy__astropy-13977', 'pallets__flask-5014',
#     'scikit-learn__scikit-learn-13779', 'sympy__sympy-15349', 'django__django-15375',
#     'django__django-14311', 'django__django-10914', 'django__django-14534',
#     'django__django-16642', 'scikit-learn__scikit-learn-14894', 'pydata__xarray-4075',
#     'django__django-15741', 'django__django-13346', 'django__django-15280',
#     'matplotlib__matplotlib-22871', 'django__django-13837', 'django__django-13964',
#     'astropy__astropy-13579', 'pydata__xarray-4966', 'django__django-11815',
#     'matplotlib__matplotlib-26342', 'django__django-16661', 'matplotlib__matplotlib-24026',
#     'django__django-12713', 'django__django-11728', 'django__django-11163',
#     'pytest-dev__pytest-6202', 'matplotlib__matplotlib-24149', 'matplotlib__matplotlib-24637',
#     'django__django-11555', 'pytest-dev__pytest-7324', 'astropy__astropy-14539',
#     'django__django-11066', 'matplotlib__matplotlib-22865', 'django__django-13933',
#     'matplotlib__matplotlib-23476', 'django__django-12858', 'django__django-15161',
#     'sympy__sympy-16766', 'django__django-11490', 'matplotlib__matplotlib-24870',
#     'matplotlib__matplotlib-14623', 'matplotlib__matplotlib-26466', 'django__django-11740',
#     'django__django-16032', 'django__django-16527', 'django__django-13121',
#     'matplotlib__matplotlib-25122', 'psf__requests-5414'
# ]

instances = [    
    "astropy__astropy-13579",
    "django__django-11066",
    "django__django-11265",
    "django__django-12125",
    "django__django-12406",
    "django__django-12741",
    "django__django-13410",
    "django__django-14122",
    "django__django-15037",
    "django__django-15280",
    "django__django-15731",
    "django__django-15741",
    "django__django-15916",
    "django__django-16642",
    "mwaskom__seaborn-3187",
    "psf__requests-6028",
    "astropy__astropy-13977",
    "django__django-11163",
    "django__django-11400",
    "django__django-11477",
    "django__django-13837",
    "django__django-14089",
    "sphinx-doc__sphinx-11510"
    ]

base_path = "/home/v-haoliu3/swt-bench/run_instance_swt_logs/5-mini-subset-new-tools/pred_post__subset_new_tools"

results = {
    'format_error': [],      # Ran 0 tests
    'import_error': [],      # ImportError/ModuleNotFoundError
    'logic_error': [],       # Tests ran but failed/wrong assertions
    'test_passed_no_f2p': [], # Tests passed but didn't cover f2p
    'not_found': [],         # Log not found
    'other': []              # Other errors
}

for inst_id in instances:
    log_path = os.path.join(base_path, inst_id, "test_output.txt")

    if not os.path.exists(log_path):
        results['not_found'].append(inst_id)
        continue

    with open(log_path, 'r', errors='ignore') as f:
        content = f.read()

    # Check for different error types
    if 'Ran 0 tests' in content:
        results['format_error'].append(inst_id)
    elif 'ImportError' in content or 'ModuleNotFoundError' in content:
        results['import_error'].append(inst_id)
    elif 'FAILED' in content or 'ERROR' in content:
        # Check if tests actually ran
        ran_match = re.search(r'Ran (\d+) test', content)
        if ran_match and int(ran_match.group(1)) > 0:
            # Tests ran but failed - could be logic error
            if 'AssertionError' in content or 'FAIL:' in content:
                results['logic_error'].append(inst_id)
            else:
                results['other'].append((inst_id, 'ERROR but no assertion'))
        else:
            results['other'].append((inst_id, 'FAILED/ERROR but 0 tests'))
    elif 'OK' in content:
        # Tests passed
        ran_match = re.search(r'Ran (\d+) test', content)
        if ran_match and int(ran_match.group(1)) > 0:
            results['test_passed_no_f2p'].append(inst_id)
        else:
            results['format_error'].append(inst_id)
    else:
        results['other'].append((inst_id, 'unknown'))

print("=" * 60)
print("FORMAT ERROR (Ran 0 tests / wrong test format):")
print("=" * 60)
for i in results['format_error']:
    print(f"  - {i}")
print(f"\nTotal: {len(results['format_error'])}")

print("\n" + "=" * 60)
print("IMPORT ERROR (ImportError/ModuleNotFoundError):")
print("=" * 60)
for i in results['import_error']:
    print(f"  - {i}")
print(f"\nTotal: {len(results['import_error'])}")

print("\n" + "=" * 60)
print("LOGIC ERROR (Tests ran but assertions failed):")
print("=" * 60)
for i in results['logic_error']:
    print(f"  - {i}")
print(f"\nTotal: {len(results['logic_error'])}")

print("\n" + "=" * 60)
print("TESTS PASSED BUT NO F2P (Tests OK but didn't trigger f2p):")
print("=" * 60)
for i in results['test_passed_no_f2p']:
    print(f"  - {i}")
print(f"\nTotal: {len(results['test_passed_no_f2p'])}")

print("\n" + "=" * 60)
print("NOT FOUND:")
print("=" * 60)
for i in results['not_found']:
    print(f"  - {i}")
print(f"\nTotal: {len(results['not_found'])}")

print("\n" + "=" * 60)
print("OTHER:")
print("=" * 60)
for i in results['other']:
    print(f"  - {i}")
print(f"\nTotal: {len(results['other'])}")
