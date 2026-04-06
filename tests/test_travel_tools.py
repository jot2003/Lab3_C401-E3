import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.tools.registry import execute_tool, get_tool_specs


def test_get_tool_specs_has_three_tools():
    specs = get_tool_specs()
    names = {s["name"] for s in specs}
    assert names == {"get_weather", "search_flights", "calculate_travel_budget"}


def test_calculate_travel_budget_execute():
    raw = execute_tool(
        "calculate_travel_budget",
        "8000000, 2400000, 900000, 2",
    )
    data = json.loads(raw)
    assert data["remaining_vnd"] == 8000000 - 2400000 - 1800000
    assert data["feasible"] is True


def test_unknown_tool():
    raw = execute_tool("fake_tool", "")
    data = json.loads(raw)
    assert "error" in data
