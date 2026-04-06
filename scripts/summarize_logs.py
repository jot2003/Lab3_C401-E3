#!/usr/bin/env python3
"""CLI wrapper cho src.reporting.log_summary.summarize_logs_to_csv."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.reporting.log_summary import summarize_logs_to_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Tong hop logs lab -> CSV")
    parser.add_argument("--log-dir", type=Path, default=ROOT / "logs")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "report" / "exports")
    parser.add_argument("--glob", type=str, default="*.log")
    args = parser.parse_args()

    res = summarize_logs_to_csv(args.log_dir, args.out_dir, args.glob)
    for m in res["messages"]:
        print(m)
    if not res["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
