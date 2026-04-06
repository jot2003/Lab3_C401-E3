"""
Tổng hợp file log JSON Lines -> CSV (dùng từ CLI và Streamlit).
"""
from __future__ import annotations

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


def summarize_logs_to_csv(
    log_dir: Path,
    out_dir: Path,
    glob_pattern: str = "*.log",
) -> Dict[str, Any]:
    """
    Returns:
      ok: bool
      messages: list of status strings
      files: dict path_key -> Path (resolved)
      row_counts: dict
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    messages: List[str] = []
    files: Dict[str, Path] = {}
    row_counts: Dict[str, int] = {"llm_metrics": 0, "sessions": 0}

    paths = list(log_dir.glob(glob_pattern)) if log_dir.is_dir() else []
    if not paths:
        return {
            "ok": False,
            "messages": [f"Khong thay file log trong {log_dir} ({glob_pattern})."],
            "files": {},
            "row_counts": row_counts,
        }

    session_id = 0
    mode: Optional[str] = None
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

    llm_path = out_dir / "llm_metrics.csv"
    if llm_rows:
        keys = list(llm_rows[0].keys())
        with llm_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(llm_rows)
        files["llm_metrics"] = llm_path
        row_counts["llm_metrics"] = len(llm_rows)
        messages.append(f"llm_metrics.csv: {len(llm_rows)} dong.")
    else:
        messages.append("Khong co LLM_METRIC trong log.")

    sum_path = out_dir / "sessions_summary.csv"
    if agent_rows:
        keys = list(agent_rows[0].keys())
        with sum_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(agent_rows)
        files["sessions_summary"] = sum_path
        row_counts["sessions"] = len(agent_rows)
        messages.append(f"sessions_summary.csv: {len(agent_rows)} dong.")
    else:
        messages.append("Khong ghi sessions_summary (trace session chua dong).")

    counts_path = out_dir / "event_counts.csv"
    with counts_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event", "count"])
        for ev, c in sorted(event_counts.items(), key=lambda x: -x[1]):
            w.writerow([ev, c])
    files["event_counts"] = counts_path
    messages.append("event_counts.csv: OK.")

    return {
        "ok": True,
        "messages": messages,
        "files": files,
        "row_counts": row_counts,
        "event_types": len(event_counts),
    }


def append_feedback(repo_root: Path, text: str, context: str = "") -> Path:
    """Ghi feedback nguoi dung vao report/ui_feedback.md (co the commit cho nhom)."""
    path = repo_root / "report" / "ui_feedback.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    line = (
        f"\n---\n**{datetime.utcnow().isoformat()}Z**"
        + (f" | {context}" if context else "")
        + f"\n\n{text.strip()}\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
    return path
