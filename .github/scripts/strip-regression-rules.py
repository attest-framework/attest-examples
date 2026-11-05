"""Usage: strip-regression-rules.py <policy.yaml|policy.json> <output.json>

Writes the policy without its top-level `block_on_regression` and `regression` rules.
attest exits 3 when either rule runs without a baseline. The output is JSON, which the
engine reads as YAML.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

RULES = ("block_on_regression", "regression")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    source, target = Path(argv[1]), Path(argv[2])
    text = source.read_text(encoding="utf-8")
    policy = json.loads(text) if source.suffix == ".json" else yaml.safe_load(text)
    if not isinstance(policy, dict):
        print(f"{source}: policy must be a mapping, got {type(policy).__name__}", file=sys.stderr)
        return 1
    for rule in RULES:
        policy.pop(rule, None)
    target.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
