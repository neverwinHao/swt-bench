#!/bin/bash
# Delete evaluation history for a given run_id
#
# Usage:
#   bash cleanup_eval.sh --run_id "pipeline_phase_agent_all_5mini_high_2-20260323-only-test"
#   bash cleanup_eval.sh --run_id "pipeline_phase_agent_all_5mini_high_2-20260323-only-test" --delete
#
# By default runs in dry-run mode. Pass --delete to actually remove files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EVAL_DIR="$SCRIPT_DIR/evaluation_results"
LOGS_DIR="$SCRIPT_DIR/run_instance_swt_logs"

RUN_ID=""
DRY_RUN=true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --run_id) RUN_ID="$2"; shift 2 ;;
        --delete) DRY_RUN=false; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) echo "Unknown option: $1"; echo "Usage: bash $0 --run_id <run_id> [--delete]"; exit 1 ;;
    esac
done

if [ -z "$RUN_ID" ]; then
    echo "Error: --run_id is required"
    echo "Usage: bash $0 --run_id <run_id> [--delete]"
    echo ""
    echo "Available run_ids in evaluation_results:"
    ls "$EVAL_DIR" 2>/dev/null | sed 's/\.json$//' | sort
    exit 1
fi

if $DRY_RUN; then
    echo "=== DRY RUN MODE (use --delete to actually remove) ==="
else
    echo "=== DELETE MODE ==="
fi
echo "Run ID: $RUN_ID"
echo ""

found=0

# 1. Check evaluation_results/ for matching json files
echo "--- evaluation_results/ ---"
for f in "$EVAL_DIR"/*"$RUN_ID"*; do
    [ -e "$f" ] || continue
    size=$(du -sh "$f" 2>/dev/null | cut -f1)
    found=$((found + 1))
    if $DRY_RUN; then
        echo "  [DRY RUN] Would remove: $f ($size)"
    else
        echo "  Removing: $f ($size)"
        rm -f "$f"
    fi
done

# 2. Check run_instance_swt_logs/ for matching directories
echo "--- run_instance_swt_logs/ ---"
for d in "$LOGS_DIR"/*"$RUN_ID"*; do
    [ -e "$d" ] || continue
    size=$(du -sh "$d" 2>/dev/null | cut -f1)
    found=$((found + 1))
    if $DRY_RUN; then
        echo "  [DRY RUN] Would remove: $d ($size)"
    else
        echo "  Removing: $d ($size)"
        rm -rf "$d"
    fi
done

echo ""
if [ $found -eq 0 ]; then
    echo "No matching files/directories found for run_id: $RUN_ID"
    exit 1
else
    echo "Total items: $found"
    if $DRY_RUN; then
        echo ""
        echo "To actually delete, run:"
        echo "  bash $0 --run_id \"$RUN_ID\" --delete"
    else
        echo "Done."
    fi
fi
