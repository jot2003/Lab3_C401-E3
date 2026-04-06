import json
import os
import time
from typing import Any, Dict, Optional, Tuple

import requests

AMADEUS_TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_OFFERS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

_token: Optional[str] = None
_token_expires_at: float = 0.0


def _amadeus_credentials() -> Tuple[str, str]:
    cid = os.getenv("AMADEUS_CLIENT_ID", "").strip()
    secret = os.getenv("AMADEUS_CLIENT_SECRET", "").strip()
    return cid, secret


def _get_amadeus_token() -> str:
    global _token, _token_expires_at
    cid, secret = _amadeus_credentials()
    if not cid or not secret:
        raise ValueError("AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET missing")

    now = time.time()
    if _token and now < _token_expires_at - 60:
        return _token

    r = requests.post(
        AMADEUS_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": secret,
        },
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    _token = data["access_token"]
    _token_expires_at = now + int(data.get("expires_in", 1700))
    return _token


def search_flights(origin: str, destination: str, departure_date: str) -> str:
    """
    Amadeus Test API: IATA codes (e.g. HAN, DAD, SGN), departure_date YYYY-MM-DD.
    Sandbox returns sample offers; dates must be in the future per Amadeus rules.
    """
    if not _amadeus_credentials()[0]:
        return json.dumps(
            {
                "error": "Missing AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET",
                "hint": "https://developers.amadeus.com/ — create an app, use test keys.",
            },
            ensure_ascii=False,
        )

    origin = origin.strip().upper()
    destination = destination.strip().upper()
    departure_date = departure_date.strip()

    try:
        token = _get_amadeus_token()
    except Exception as e:
        return json.dumps({"error": "Amadeus auth failed", "detail": str(e)}, ensure_ascii=False)

    headers = {"Authorization": f"Bearer {token}"}
    params: Dict[str, Any] = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": 1,
        "max": 5,
        "currencyCode": "VND",
    }

    try:
        r = requests.get(AMADEUS_OFFERS_URL, headers=headers, params=params, timeout=25)
        if r.status_code >= 400:
            return json.dumps(
                {
                    "error": "Amadeus flight search failed",
                    "status": r.status_code,
                    "body": r.text[:2000],
                },
                ensure_ascii=False,
            )
        data = r.json()
    except requests.RequestException as e:
        return json.dumps({"error": "Amadeus request failed", "detail": str(e)}, ensure_ascii=False)

    offers = []
    for item in data.get("data", [])[:5]:
        price = (item.get("price") or {}).get("grandTotal") or (item.get("price") or {}).get("total")
        currency = (item.get("price") or {}).get("currency", "VND")
        itineraries = item.get("itineraries") or []
        first = itineraries[0] if itineraries else {}
        segs = first.get("segments") or []
        first_seg = segs[0] if segs else {}
        last_seg = segs[-1] if segs else {}
        offers.append(
            {
                "price": price,
                "currency": currency,
                "departure_at": first_seg.get("departure", {}).get("at"),
                "arrival_at": last_seg.get("arrival", {}).get("at"),
                "carrier_code": (first_seg.get("carrierCode") or ""),
                "number_of_stops": max(0, len(segs) - 1),
            }
        )

    if not offers:
        return json.dumps(
            {
                "message": "No offers returned (common in sandbox for some routes/dates).",
                "raw_dictionaries": bool(data.get("dictionaries")),
            },
            ensure_ascii=False,
        )

    return json.dumps({"offers": offers, "source": "amadeus_test"}, ensure_ascii=False)
