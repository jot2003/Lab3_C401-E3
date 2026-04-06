import json
import os
from typing import Any, Dict, List

import requests

from src.tools.demo_fallback import demo_travel_apis_enabled, mock_flights

DUFFEL_OFFER_REQUEST_URL = "https://api.duffel.com/air/offer_requests"
DUFFEL_VERSION = os.getenv("DUFFEL_API_VERSION", "v2")


def _duffel_token() -> str:
    return os.getenv("DUFFEL_ACCESS_TOKEN", "").strip()


def _extract_duffel_offers(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = body.get("data") or {}
    offers = data.get("offers")
    if isinstance(offers, list):
        return offers

    included = body.get("included") or []
    if isinstance(included, list):
        return [x for x in included if isinstance(x, dict) and x.get("type") == "offer"]
    return []


def _offer_request_resource_url(offer_request_id: Any) -> str:
    if isinstance(offer_request_id, str) and offer_request_id.strip():
        return f"{DUFFEL_OFFER_REQUEST_URL}/{offer_request_id.strip()}"
    return ""


def search_flights(origin: str, destination: str, departure_date: str) -> str:
    """
    Duffel Air API: IATA codes (e.g. HAN, DAD, SGN), departure_date YYYY-MM-DD.
    """
    token = _duffel_token()
    if not token:
        if demo_travel_apis_enabled():
            return mock_flights(origin, destination, departure_date)
        return json.dumps(
            {
                "error": "Missing DUFFEL_ACCESS_TOKEN",
                "hint": "https://duffel.com/docs/api/overview — hoặc DEMO_TRAVEL_APIS=1 trong .env để demo không cần Duffel.",
            },
            ensure_ascii=False,
        )

    origin = origin.strip().upper()
    destination = destination.strip().upper()
    departure_date = departure_date.strip()

    headers = {
        "Authorization": f"Bearer {token}",
        "Duffel-Version": DUFFEL_VERSION,
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "data": {
            "slices": [
                {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                }
            ],
            "passengers": [{"type": "adult"}],
            "cabin_class": "economy",
            "max_connections": 1,
        }
    }

    try:
        r = requests.post(DUFFEL_OFFER_REQUEST_URL, headers=headers, json=payload, timeout=30)
        if r.status_code >= 400:
            return json.dumps(
                {
                    "error": "Duffel flight search failed",
                    "status": r.status_code,
                    "body": r.text[:3000],
                },
                ensure_ascii=False,
            )
        body = r.json()
    except requests.RequestException as e:
        return json.dumps({"error": "Duffel request failed", "detail": str(e)}, ensure_ascii=False)
    except ValueError:
        return json.dumps({"error": "Duffel response is not valid JSON", "body": r.text[:1000]}, ensure_ascii=False)

    raw_offers = _extract_duffel_offers(body)
    offers = []
    for item in raw_offers[:5]:
        slices = item.get("slices") or []
        first_slice = slices[0] if slices else {}
        segs = first_slice.get("segments") or []
        first_seg = segs[0] if segs else {}
        last_seg = segs[-1] if segs else {}
        offers.append(
            {
                "price": item.get("total_amount"),
                "currency": item.get("total_currency", "VND"),
                "departure_at": (first_seg.get("departing_at") if isinstance(first_seg, dict) else None),
                "arrival_at": (last_seg.get("arriving_at") if isinstance(last_seg, dict) else None),
                "carrier_code": (
                    (first_seg.get("marketing_carrier") or {}).get("iata_code")
                    if isinstance(first_seg, dict)
                    else ""
                ),
                "number_of_stops": max(0, len(segs) - 1),
            }
        )

    offer_request_id = (body.get("data") or {}).get("id")
    resource_url = _offer_request_resource_url(offer_request_id)

    if not offers:
        return json.dumps(
            {
                "message": "No offers returned for this route/date.",
                "duffel_offer_request_id": offer_request_id,
                "duffel_offer_request_url": resource_url or None,
                "source": "duffel",
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "offers": offers,
            "duffel_offer_request_id": offer_request_id,
            "duffel_offer_request_url": resource_url or None,
            "source": "duffel",
        },
        ensure_ascii=False,
    )
