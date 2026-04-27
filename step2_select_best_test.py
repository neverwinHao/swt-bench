"""
Step 2: For each instance, select the best test patch.

Uses step1 output (f2p-filtered). For each instance, aggregate each test patch's
performance across all code patches, then rank by:
  1. Number of code patches where resolved=True (higher is better)
  2. Average coverage_pred as tie-breaker (higher is better)

Output: test_selection_step2_best_test.json
"""

import json
from collections import defaultdict

INPUT = "test_selection_step1_f2p.json"
OUTPUT = "test_selection_step2_best_test.json"

with open(INPUT) as f:
    data = json.load(f)

output = {}

for inst_id, inst in data.items():
    by_test = defaultdict(list)
    for combo_key, result in inst["results"].items():
        by_test[result["test_patch_source"]].append(result)

    scored = []
    for tp_source, combos in by_test.items():
        resolved_count = sum(1 for c in combos if c["resolved"])
        coverages = [c["coverage_pred"] for c in combos if c["coverage_pred"] is not None]
        avg_coverage = sum(coverages) / len(coverages) if coverages else 0.0
        scored.append({
            "test_patch_source": tp_source,
            "resolved_count": resolved_count,
            "avg_coverage": round(avg_coverage, 4),
            "num_code_patches": len(combos),
        })

    scored.sort(key=lambda x: (x["resolved_count"], x["avg_coverage"]), reverse=True)
    best = scored[0]

    output[inst_id] = {
        "instance_id": inst["instance_id"],
        "selected_test_patch": best["test_patch_source"],
        "resolved_count": best["resolved_count"],
        "avg_coverage": best["avg_coverage"],
        "has_f2p": inst["has_f2p"],
        "all_candidates": scored,
    }

with open(OUTPUT, "w") as f:
    json.dump(output, f, indent=2)

# Stats
resolved_counts = [v["resolved_count"] for v in output.values()]
print(f"Instances: {len(output)}")
print(f"Selected test resolved on 3/3 code patches: {sum(1 for r in resolved_counts if r == 3)}")
print(f"Selected test resolved on 2/3 code patches: {sum(1 for r in resolved_counts if r == 2)}")
print(f"Selected test resolved on 1/3 code patches: {sum(1 for r in resolved_counts if r == 1)}")
print(f"Selected test resolved on 0/3 code patches: {sum(1 for r in resolved_counts if r == 0)}")
print(f"Output: {OUTPUT}")
