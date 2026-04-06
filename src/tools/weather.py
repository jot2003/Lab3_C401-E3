import json
import os
from typing import Any, Dict

import requests

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_weather(city: str) -> str:
    """
    Current conditions + next few slots from 5-day forecast (OpenWeatherMap).
    """
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not key:
        return json.dumps(
            {
                "error": "Missing OPENWEATHER_API_KEY in .env",
                "hint": "https://openweathermap.org/api — free tier is enough.",
            },
            ensure_ascii=False,
        )

    city = city.strip()
    params: Dict[str, Any] = {"q": city, "appid": key, "units": "metric", "lang": "vi"}

    try:
        r = requests.get(OPENWEATHER_URL, params=params, timeout=15)
        r.raise_for_status()
        cur = r.json()
    except requests.RequestException as e:
        return json.dumps({"error": "OpenWeather request failed", "detail": str(e)}, ensure_ascii=False)

    try:
        r2 = requests.get(FORECAST_URL, params=params, timeout=15)
        r2.raise_for_status()
        fc = r2.json()
    except requests.RequestException:
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
        "city": cur.get("name"),
        "country": (cur.get("sys") or {}).get("country"),
        "current": {
            "description": main,
            "temp_c": temp,
            "feels_like_c": feels,
            "humidity_percent": humidity,
        },
        "forecast_samples_next_24h": samples,
    }
    return json.dumps(out, ensure_ascii=False)
