#!/usr/bin/env python3
"""Merge report-v2 files into one report: merge-reports.py <out> <report>...

A baseline tag holds one report, so the annotate job merges every example's main report
into the single report it pins as `main`. Assertion ids must be unique across the inputs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

COUNTS = ("total", "passed", "soft_fail", "hard_fail", "not_evaluated")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    out, inputs = Path(argv[1]), argv[2:]
    merged: dict[str, object] = {
        "report_version": 2,
        "simulated": False,
        "summary": {key: 0 for key in COUNTS},
        "results": [],
        "tests": [],
        "tests_collected": 0,
        "total_cost": 0.0,
        "total_duration_ms": 0,
    }
    seen: dict[str, str] = {}
    summary = merged["summary"]
    assert isinstance(summary, dict)
    for path in inputs:
        report = json.loads(Path(path).read_text())
        if report.get("report_version") != 2:
            raise SystemExit(f"{path}: not a report-v2 file")
        for result in report["results"]:
            aid = result["assertion_id"]
            if aid in seen:
                raise SystemExit(f"assertion id {aid} appears in both {seen[aid]} and {path}")
            seen[aid] = path
        for key in COUNTS:
            summary[key] += report["summary"][key]
        merged["results"].extend(report["results"])  # type: ignore[union-attr]
        merged["tests"].extend(report["tests"])  # type: ignore[union-attr]
        merged["tests_collected"] += report["tests_collected"]  # type: ignore[operator]
        merged["total_cost"] += report["total_cost"]  # type: ignore[operator]
        merged["total_duration_ms"] += report["total_duration_ms"]  # type: ignore[operator]
        merged.setdefault("timestamp", report["timestamp"])
    out.write_text(json.dumps(merged))
    print(f"merged {len(inputs)} reports, {len(seen)} assertions -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
