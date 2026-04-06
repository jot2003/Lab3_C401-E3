#!/usr/bin/env python3
"""
Đọc file log JSON Lines trong thư mục logs/, xuất CSV phục vụ báo cáo (Evaluation / rubric).

Chạy từ thư mục gốc repo:
  python scripts/summarize_logs.py
  python scripts/summarize_logs.py --log-dir logs --out-dir report/exports
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterator, List, Optional


def iter_log_records(log_paths: List[Path]) -> Iterator[Dict[str, Any]]:
    for path in sorted(log_paths):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line[0] != "{":
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Tổng hợp logs lab → CSV (LLM metrics, agent runs)")
    parser.add_argument("--log-dir", type=Path, default=root / "logs", help="Thư mục chứa *.log")
    parser.add_argument("--out-dir", type=Path, default=root / "report" / "exports", help="Thư mục ghi CSV")
    parser.add_argument("--glob", type=str, default="*.log", help="Pattern file log")
    args = parser.parse_args()

    log_dir: Path = args.log_dir
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = list(log_dir.glob(args.glob)) if log_dir.is_dir() else []
    if not paths:
        print(f"Không thấy file log trong {log_dir} (pattern {args.glob}).")
        print("Chạy agent/chatbot ít nhất một lần để tạo logs/YYYY-MM-DD.log")
        return

    session_id = 0
    mode: Optional[str] = None  # "agent" | "chatbot"
    agent_run: Optional[Dict[str, Any]] = None

    llm_rows: List[Dict[str, Any]] = []
    agent_rows: List[Dict[str, Any]] = []
    event_counts: DefaultDict[str, int] = defaultdict(int)

    for rec in iter_log_records(paths):
        event = rec.get("event", "")
        ts = rec.get("timestamp", "")
        data = rec.get("data") or {}
        event_counts[event] += 1

        if event == "AGENT_START":
            session_id += 1
            mode = "agent"
            agent_run = {
                "session_id": session_id,
                "mode": "agent",
                "started_at": ts,
                "model": data.get("model"),
                "input_preview": (data.get("input") or "")[:200],
                "llm_calls": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_latency_ms": 0,
                "tools_used": [],
                "outcome": None,
                "steps": None,
            }
        elif event == "CHATBOT_START":
            session_id += 1
            mode = "chatbot"
            agent_run = {
                "session_id": session_id,
                "mode": "chatbot",
                "started_at": ts,
                "model": data.get("model"),
                "input_preview": (data.get("input") or "")[:200],
                "llm_calls": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_latency_ms": 0,
                "tools_used": [],
                "outcome": "chatbot_single_shot",
                "steps": 1,
            }
        elif event == "LLM_METRIC":
            pt = int(data.get("prompt_tokens") or 0)
            ct = int(data.get("completion_tokens") or 0)
            lat = int(data.get("latency_ms") or 0)
            ratio = round(ct / max(pt, 1), 6)
            llm_rows.append(
                {
                    "session_id": session_id,
                    "mode": mode or "",
                    "timestamp": ts,
                    "event": event,
                    "model": data.get("model"),
                    "provider": data.get("provider"),
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "total_tokens": data.get("total_tokens"),
                    "latency_ms": lat,
                    "completion_ratio": ratio,
                    "cost_estimate": data.get("cost_estimate"),
                }
            )
            if agent_run is not None:
                agent_run["llm_calls"] += 1
                agent_run["total_prompt_tokens"] += pt
                agent_run["total_completion_tokens"] += ct
                agent_run["total_latency_ms"] += lat
        elif event == "AGENT_TOOL_CALL":
            if agent_run is not None:
                tool = data.get("tool")
                if tool and tool not in agent_run["tools_used"]:
                    agent_run["tools_used"].append(tool)
        elif event == "AGENT_END":
            if agent_run is not None:
                agent_run["ended_at"] = ts
                agent_run["outcome"] = data.get("outcome")
                agent_run["steps"] = data.get("steps")
                agent_run["tools_used_str"] = "|".join(agent_run["tools_used"])
                agent_rows.append({k: v for k, v in agent_run.items() if k != "tools_used"})
            agent_run = None
            mode = None
        elif event == "CHATBOT_END":
            if agent_run is not None:
                agent_run["ended_at"] = ts
                agent_rows.append({k: v for k, v in agent_run.items() if k != "tools_used"})
            agent_run = None
            mode = None

    # LLM metrics CSV
    llm_path = out_dir / "llm_metrics.csv"
    if llm_rows:
        keys = list(llm_rows[0].keys())
        with llm_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(llm_rows)
        print(f"Wrote {len(llm_rows)} rows -> {llm_path}")
    else:
        print("Không có sự kiện LLM_METRIC trong log.")

    # Sessions summary
    sum_path = out_dir / "sessions_summary.csv"
    if agent_rows:
        keys = list(agent_rows[0].keys())
        with sum_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(agent_rows)
        print(f"Wrote {len(agent_rows)} rows -> {sum_path}")
    else:
        print("Không ghi sessions_summary (thiếu cặp AGENT_END/CHATBOT_END đầy đủ trong file đọc được).")

    # Event counts
    counts_path = out_dir / "event_counts.csv"
    with counts_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event", "count"])
        for ev, c in sorted(event_counts.items(), key=lambda x: -x[1]):
            w.writerow([ev, c])
    print(f"Wrote event counts -> {counts_path}")


if __name__ == "__main__":
    main()
