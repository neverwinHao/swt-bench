#!/usr/bin/env python3
"""Calculate weighted coverage metrics that penalize failed/error cases with 0."""

import json
import os
import sys
from pathlib import Path


def main(eval_json_path, reports_dir):
    with open(eval_json_path) as f:
        eval_data = json.load(f)

    resolved_ids = set(eval_data.get("resolved_ids", []))
    unresolved_ids = set(eval_data.get("unresolved_ids", []))
    error_ids = set(eval_data.get("error_ids", []))
    completed_ids = set(eval_data.get("completed_ids", []))

    total_coverage_pred = 0.0
    total_coverage_delta_gold = 0.0
    weighted_coverage_pred = 0.0
    weighted_coverage_delta_gold = 0.0
    count = 0

    for case_dir in sorted(Path(reports_dir).iterdir()):
        report_file = case_dir / "report.json"
        if not report_file.exists():
            continue
        with open(report_file) as f:
            report = json.load(f)

        for instance_id, info in report.items():
            count += 1
            cp = info.get("coverage_pred") or 0.0
            cdg = info.get("coverage_delta_gold") or 0.0

            total_coverage_pred += cp
            total_coverage_delta_gold += cdg

            if instance_id in resolved_ids:
                weight = 1
            else:
                weight = 0

            weighted_coverage_pred += cp * weight
            weighted_coverage_delta_gold += cdg * weight

    raw_cp = total_coverage_pred / count
    raw_cdg = total_coverage_delta_gold / count
    w_cp = weighted_coverage_pred / count
    w_cdg = weighted_coverage_delta_gold / count
    hack_cp = (raw_cp - w_cp) / raw_cp if raw_cp > 0 else 0.0
    hack_cdg = (raw_cdg - w_cdg) / raw_cdg if raw_cdg > 0 else 0.0

    print(f"Total cases: {count}")
    print(f"Resolved: {len(resolved_ids)}, Unresolved: {len(unresolved_ids)}, Error: {len(error_ids)}")
    print()
    print(f"{'Metric':<30} {'Raw Mean':>10} {'Weighted Mean':>15} {'Hacking Rate':>15}")
    print("-" * 73)
    print(f"{'coverage_pred':<30} {raw_cp:>10.4f} {w_cp:>15.4f} {hack_cp:>14.2%}")
    print(f"{'coverage_delta_gold':<30} {raw_cdg:>10.4f} {w_cdg:>15.4f} {hack_cdg:>14.2%}")


if __name__ == "__main__":
    eval_json = sys.argv[1] if len(sys.argv) > 1 else "/home/v-haoliu3/swt-bench/evaluation_results/terminus_claude-opus-4.5_20260421_193416.terminus_claude-opus-4.5_20260421_193416.json"
    reports = sys.argv[2] if len(sys.argv) > 2 else "/home/v-haoliu3/swt-bench/run_instance_swt_logs/terminus_claude-opus-4.5_20260421_193416/terminus_claude-opus-4.5_20260421_193416"
    main(eval_json, reports)
# gpt5: Weighted Mea, Hacking Rate
# gpt5.trae-gpt5-experiment: 0.6059 17.97% 
# minisweagent: 0.4194 21.28%s
# SWE-Agent: 0.6784 18.35
# Aider: 0.2659 34.72%
# Ours: 0.6802 17.22%

# gpt5mini: Weighted Mea, Hacking Rate
# trae: 0.4723 23.85%
# minisweagent: 0.3502 31.97%
# SWE-Agent：0.5630 18.65%
# Aider: 0.3062 30.43%
# Ours: 0.6781 16.58%


# claude: Weighted Mea, Hacking Rate
# trae: 59.75 15.70%
# minisweagent: 0.6685 17.68%
# OpenHands: 0.5534 13.26%
# Claude Code: 0.5535 18.86%
# SWE-Agent: 0.6977 18.34%
# Aider: 35.97 36.94%
# Terminus:
# Ours: 0.7377 16.82%
