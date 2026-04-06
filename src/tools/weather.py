import json
import os
from typing import Any, Dict, Optional, Tuple

import requests

from src.tools.demo_fallback import demo_travel_apis_enabled, mock_weather

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def _normalize_city(city: str) -> str:
    """Bo prefix city= neu LLM gui kieu keyword trong chuoi."""
    s = city.strip()
    if s.lower().startswith("city="):
        s = s.split("=", 1)[1].strip()
    return s


def _parse_owm_error(status_code: int, body: Any) -> str:
    if isinstance(body, dict):
        msg = body.get("message") or str(body)
        cod = body.get("cod")
        if status_code == 401 or cod == 401:
            return (
                "401 Invalid API key. Nguyen nhan thuong gap: (1) Key vua tao — cho 10 phut–2 gio de OpenWeather kich hoat. "
                "(2) Copy thieu ky tu / co dau cach trong .env. (3) Chua xac nhan email. "
                "Xem: docs/OPENWEATHER_SETUP_VI.md va https://openweathermap.org/faq#error401"
            )
        if status_code == 404 or cod == "404":
            return f"404 Khong tim thay dia diem: {msg}. Thu 'Da Nang, VN' hoac 'Hanoi, VN'."
        if status_code == 429:
            return "429 Qua nhieu request (rate limit). Doi vai phut hoac giam tan suat goi API."
        return f"HTTP {status_code}: {msg}"
    return f"HTTP {status_code}: {str(body)[:400]}"


def _fetch_json(url: str, params: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        r = requests.get(url, params=params, timeout=20)
    except requests.RequestException as e:
        return None, f"Loi mang / timeout: {e}"

    try:
        body = r.json()
    except ValueError:
        return None, f"Phan hoi khong phai JSON: {r.text[:400]}"

    if r.status_code != 200:
        return None, _parse_owm_error(r.status_code, body)

    if isinstance(body, dict) and str(body.get("cod")) == "404":
        return None, _parse_owm_error(404, body)

    return body, None


def get_weather(city: str) -> str:
    """
    Current conditions + next few slots from 5-day forecast (OpenWeatherMap).
    """
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    # Loai bo ngoac kep thua khi user paste trong .env
    if len(key) >= 2 and key[0] in "'\"" and key[-1] == key[0]:
        key = key[1:-1].strip()

    if not key:
        if demo_travel_apis_enabled():
            return mock_weather(city)
        return json.dumps(
            {
                "error": "Missing OPENWEATHER_API_KEY in .env",
                "hint": "Xem huong dan: docs/OPENWEATHER_SETUP_VI.md — hoac DEMO_TRAVEL_APIS=1 de demo.",
            },
            ensure_ascii=False,
        )

    if len(key) < 20:
        return json.dumps(
            {
                "error": "OPENWEATHER_API_KEY co ve qua ngan.",
                "hint": "Lay key tai https://home.openweathermap.org/api_keys — xem docs/OPENWEATHER_SETUP_VI.md",
                "key_length": len(key),
            },
            ensure_ascii=False,
        )

    city = _normalize_city(city)
    params: Dict[str, Any] = {"q": city, "appid": key, "units": "metric", "lang": "vi"}

    cur, err = _fetch_json(OPENWEATHER_URL, params)
    if err:
        return json.dumps(
            {
                "error": "OpenWeather: current weather failed",
                "detail": err,
                "city_query": city,
                "doc": "docs/OPENWEATHER_SETUP_VI.md",
            },
            ensure_ascii=False,
        )

    fc, fc_err = _fetch_json(FORECAST_URL, params)
    if fc_err:
        fc = {"list": []}

    main = cur.get("weather", [{}])[0].get("description", "")
    temp = cur.get("main", {}).get("temp")
    feels = cur.get("main", {}).get("feels_like")
    humidity = cur.get("main", {}).get("humidity")

    samples = []
    for item in (fc.get("list") or [])[:8]:
        samples.append(
            {
                "time_utc": item.get("dt_txt"),
                "temp_c": item.get("main", {}).get("temp"),
                "description": (item.get("weather") or [{}])[0].get("description"),
                "pop": item.get("pop"),
            }
        )

    out = {
        "source": "openweathermap.org/data/2.5",
        "city": cur.get("name"),
        "country": (cur.get("sys") or {}).get("country"),
        "current": {
            "description": main,
            "temp_c": temp,
            "feels_like_c": feels,
            "humidity_percent": humidity,
        },
        "forecast_samples_next_24h": samples,
        "forecast_note": None if not fc_err else f"Forecast skipped: {fc_err}",
    }
    return json.dumps(out, ensure_ascii=False)
