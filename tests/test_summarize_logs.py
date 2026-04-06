import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.reporting.log_summary import summarize_logs_to_csv


def test_summarize_logs_core(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    lines = [
        {"timestamp": "t1", "event": "AGENT_START", "data": {"input": "hi", "model": "m1"}},
        {
            "timestamp": "t2",
            "event": "LLM_METRIC",
            "data": {
                "provider": "google",
                "model": "m1",
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
                "latency_ms": 500,
                "cost_estimate": 0.001,
                "completion_ratio": 0.2,
            },
        },
        {"timestamp": "t3", "event": "AGENT_END", "data": {"steps": 1, "outcome": "final_answer"}},
    ]
    p = log_dir / "2026-01-01.log"
    p.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")

    out_dir = tmp_path / "out"
    res = summarize_logs_to_csv(log_dir, out_dir, "*.log")
    assert res["ok"]
    assert (out_dir / "llm_metrics.csv").is_file()
    assert (out_dir / "sessions_summary.csv").is_file()
