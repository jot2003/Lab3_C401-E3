import json
from typing import Any, Callable, Dict, List, Tuple

from src.tools.budget import calculate_travel_budget
from src.tools.flights import search_flights
from src.tools.weather import get_weather

ToolFn = Callable[..., str]

_REGISTRY: Dict[str, Tuple[ToolFn, List[str]]] = {
    "get_weather": (get_weather, ["city"]),
    "search_flights": (search_flights, ["origin", "destination", "departure_date"]),
    "calculate_travel_budget": (
        calculate_travel_budget,
        ["total_budget_vnd", "flight_cost_vnd", "hotel_per_night_vnd", "num_nights"],
    ),
}

TOOL_NAMES = list(_REGISTRY.keys())


def get_tool_specs() -> List[Dict[str, Any]]:
    """Schemas for ReAct system prompt (name + description + argument names)."""
    return [
        {
            "name": "get_weather",
            "description": (
                "Lấy thời tiết hiện tại và vài mốc dự báo (OpenWeatherMap). "
                "Tham số: city — tên thành phố tiếng Anh hoặc 'Da Nang, VN', ví dụ: Da Nang"
            ),
            "args": ["city"],
        },
        {
            "name": "search_flights",
            "description": (
                "Tìm vé máy bay (Amadeus TEST API). "
                "origin, destination: mã IATA 3 chữ (HAN, DAD, SGN). "
                "departure_date: YYYY-MM-DD (ngày trong tương lai, theo quy tắc sandbox)."
            ),
            "args": ["origin", "destination", "departure_date"],
        },
        {
            "name": "calculate_travel_budget",
            "description": (
                "Tính tiền còn lại sau khi trừ vé và phòng khách sạn. "
                "total_budget_vnd, flight_cost_vnd, hotel_per_night_vnd là số VND; "
                "num_nights là số đêm ở lại (số nguyên)."
            ),
            "args": ["total_budget_vnd", "flight_cost_vnd", "hotel_per_night_vnd", "num_nights"],
        },
    ]


def _split_args(arg_string: str) -> List[str]:
    """Split top-level commas; respect double-quoted segments."""
    parts: List[str] = []
    buf: List[str] = []
    in_quotes = False
    for ch in arg_string:
        if ch == '"':
            in_quotes = not in_quotes
            buf.append(ch)
        elif ch == "," and not in_quotes:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        return raw[1:-1]
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def execute_tool(name: str, arg_string: str) -> str:
    if name not in _REGISTRY:
        return json.dumps({"error": f"Unknown tool: {name}", "known": TOOL_NAMES}, ensure_ascii=False)

    fn, param_names = _REGISTRY[name]
    parts = _split_args(arg_string) if arg_string.strip() else []

    if len(parts) != len(param_names):
        return json.dumps(
            {
                "error": "Wrong number of arguments",
                "tool": name,
                "expected_params": param_names,
                "got_count": len(parts),
                "hint": f'Action format: {name}({", ".join(param_names)})',
            },
            ensure_ascii=False,
        )

    kwargs = {k: _parse_value(v) for k, v in zip(param_names, parts)}
    try:
        return fn(**kwargs)
    except Exception as e:
        return json.dumps({"error": str(e), "tool": name}, ensure_ascii=False)
