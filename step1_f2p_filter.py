"""
Step 1: F2P filtering following e-Otter++ paper (Section 3.3).

For each instance, group results by test_patch_source.
A test patch is kept if it is fail-to-pass (added_f2p > 0) on at least one code patch.
If no test patch has f2p for an instance, all test patches are kept (paper's fallback).

Output: test_selection_step1_f2p.json
"""

import json
from collections import defaultdict

INPUT = "test_selection_different_issue.json"
OUTPUT = "test_selection_step1_f2p.json"

with open(INPUT) as f:
    data = json.load(f)

output = {}
stats = {"total_instances": 0, "total_tests_before": 0, "total_tests_after": 0, "instances_no_f2p": 0}

for inst_id, inst in data.items():
    stats["total_instances"] += 1

    by_test = defaultdict(list)
    for combo_key, result in inst["results"].items():
        by_test[result["test_patch_source"]].append((combo_key, result))

    stats["total_tests_before"] += len(by_test)

    f2p_tests = {}
    non_f2p_tests = {}
    for tp_source, combos in by_test.items():
        has_f2p = any(r["added_f2p"] > 0 for _, r in combos)
        if has_f2p:
            f2p_tests[tp_source] = combos
        else:
            non_f2p_tests[tp_source] = combos

    if f2p_tests:
        kept = f2p_tests
    else:
        kept = non_f2p_tests
        stats["instances_no_f2p"] += 1

    stats["total_tests_after"] += len(kept)

    kept_results = {}
    for tp_source, combos in kept.items():
        for combo_key, result in combos:
            kept_results[combo_key] = result

    output[inst_id] = {
        "instance_id": inst["instance_id"],
        "kept_test_patches": sorted(kept.keys()),
        "dropped_test_patches": sorted(
            set(by_test.keys()) - set(kept.keys())
        ),
        "has_f2p": bool(f2p_tests),
        "results": kept_results,
    }

with open(OUTPUT, "w") as f:
    json.dump(output, f, indent=2)

print(f"Instances: {stats['total_instances']}")
print(f"Test patches before: {stats['total_tests_before']}")
print(f"Test patches after:  {stats['total_tests_after']}")
print(f"Dropped: {stats['total_tests_before'] - stats['total_tests_after']}")
print(f"Instances with no f2p (kept all): {stats['instances_no_f2p']}")
print(f"Output: {OUTPUT}")
