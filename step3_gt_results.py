"""
Step 3: Build overall evaluation result from step2 selection + per-instance reports.

Output format matches the overall evaluation JSON (e.g. pipeline_initPatch_all.5mini_issue_initPatch.json).
"""

import json
import os

STEP2 = "test_selection_step2_best_test.json"
OUTPUT = "test_selection_final_results.json"

REPORT_DIRS = {
    "pipeline_dropCode_all__preds_only_test": "run_instance_swt_logs/5mini_issue_dropCode/pipeline_dropCode_all",
    "pipeline_initPatch_all__preds_only_test": "run_instance_swt_logs/5mini_issue_initPatch/pipeline_initPatch_all",
    "pipeline_initTest_all__preds_only_test": "run_instance_swt_logs/5mini_issue_initTest/pipeline_initTest_all",
    "pipeline_simple_all__preds_only_test": "run_instance_swt_logs/5mini_issue_simple/pipeline_simple_all",
    "pipeline_standard_all__preds_only_test": "run_instance_swt_logs/5mini_issue_standard/pipeline_standard_all",
    "pipeline_phase_agent_all__preds_only_test": "run_instance_swt_logs/pipeline_phase_agent_all-20260320-only-test/pipeline_phase_agent_all",
}

with open(STEP2) as f:
    step2 = json.load(f)

resolved_ids = []
unresolved_ids = []
error_ids = []
coverages = []
coverage_deltas = []

for inst_id, info in step2.items():
    tp = info["selected_test_patch"]
    report_path = os.path.join(REPORT_DIRS[tp], inst_id, "report.json")

    if not os.path.exists(report_path):
        # Fallback: try other candidates in order
        found = False
        for candidate in step2[inst_id].get("all_candidates", []):
            fallback_tp = candidate["test_patch_source"]
            report_path = os.path.join(REPORT_DIRS[fallback_tp], inst_id, "report.json")
            if os.path.exists(report_path):
                tp = fallback_tp
                found = True
                break
        if not found:
            error_ids.append(inst_id)
            continue

    with open(report_path) as f:
        report = json.load(f)

    r = report[inst_id]
    if r["resolved"]:
        resolved_ids.append(inst_id)
    else:
        unresolved_ids.append(inst_id)

    if r.get("coverage_pred") is not None:
        coverages.append(r["coverage_pred"])
    if r.get("coverage_delta_pred") is not None:
        coverage_deltas.append(r["coverage_delta_pred"])

total = len(step2)
mean_cov = sum(coverages) / len(coverages) if coverages else 0.0
mean_cov_delta = sum(coverage_deltas) / len(coverage_deltas) if coverage_deltas else 0.0

output = {
    "total_instances": total,
    "completed_instances": 0,
    "resolved_instances": len(resolved_ids),
    "unresolved_instances": len(unresolved_ids),
    "error_instances": len(error_ids),
    "Mean coverage": mean_cov,
    "Mean coverage delta": mean_cov_delta,
    "unstopped_instances": 0,
    "completed_ids": [],
    "resolved_ids": sorted(resolved_ids),
    "unresolved_ids": sorted(unresolved_ids),
    "error_ids": sorted(error_ids),
    "unstopped_containers": [],
    "unremoved_images": [],
}

with open(OUTPUT, "w") as f:
    json.dump(output, f, indent=2)

print(f"Total instances: {total}")
print(f"Resolved: {len(resolved_ids)}/{total} ({len(resolved_ids)/total*100:.1f}%)")
print(f"Unresolved: {len(unresolved_ids)}")
print(f"Error: {len(error_ids)}")
print(f"Mean coverage: {mean_cov:.4f}")
print(f"Mean coverage delta: {mean_cov_delta:.4f}")
print(f"Output: {OUTPUT}")
