#!/usr/bin/env python3
"""Convert pipeline preds_only_test.json to SWT-bench JSONL format."""

import json
from pathlib import Path


def convert(input_path: str, output_path: str, model_name: str = None):
    with open(input_path) as f:
        data = json.load(f)

    with open(output_path, "w") as out:
        for instance_id, entry in data.items():
            record = {
                "instance_id": instance_id,
                "model_name_or_path": model_name or entry.get("model_name_or_path", ""),
                "model_patch": entry.get("model_patch", ""),
            }
            out.write(json.dumps(record) + "\n")

    print(f"Converted {len(data)} entries -> {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input JSON file (preds_only_test.json)")
    parser.add_argument("-o", "--output", help="Output JSONL file path")
    parser.add_argument("-m", "--model-name", help="Override model_name_or_path")
    args = parser.parse_args()

    if args.output:
        output = args.output
    else:
        output = str(Path(args.input).with_suffix(".jsonl"))

    convert(args.input, output, args.model_name)
