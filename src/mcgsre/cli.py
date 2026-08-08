"""Command-line interface for the reference evaluator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import evaluate, load_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate multi-cloud policy drift")
    parser.add_argument("--catalog", required=True, help="Path to the normalized control catalog")
    parser.add_argument("--observations", required=True, help="Path to normalized cloud observations")
    parser.add_argument("--output", help="Write the JSON report to this path (stdout when omitted)")
    parser.add_argument("--fail-on-drift", action="store_true", help="Exit with status 2 when drift exists")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = evaluate(load_json(args.catalog), load_json(args.observations))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 2 if args.fail_on_drift and report["summary"]["drifted"] else 0
