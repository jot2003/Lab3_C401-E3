import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_summarize_logs_script(tmp_path):
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
    root = Path(__file__).resolve().parent.parent
    script = root / "scripts" / "summarize_logs.py"
    r = subprocess.run(
        [sys.executable, str(script), "--log-dir", str(log_dir), "--out-dir", str(out_dir)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert (out_dir / "llm_metrics.csv").is_file()
    assert (out_dir / "sessions_summary.csv").is_file()
