import json


def calculate_travel_budget(
    total_budget_vnd: float,
    flight_cost_vnd: float,
    hotel_per_night_vnd: float,
    num_nights: int,
) -> str:
    """
    Simple trip cashflow: total budget minus flight and estimated hotel nights.
    """
    num_nights = int(num_nights)
    hotel_total = float(hotel_per_night_vnd) * num_nights
    spent = float(flight_cost_vnd) + hotel_total
    remaining = float(total_budget_vnd) - spent
    per_day_remaining = remaining / max(num_nights, 1)

    out = {
        "total_budget_vnd": float(total_budget_vnd),
        "flight_cost_vnd": float(flight_cost_vnd),
        "hotel_per_night_vnd": float(hotel_per_night_vnd),
        "num_nights": num_nights,
        "hotel_total_vnd": hotel_total,
        "spent_vnd": spent,
        "remaining_vnd": remaining,
        "remaining_per_day_vnd": round(per_day_remaining, 0),
        "feasible": remaining >= 0,
    }
    return json.dumps(out, ensure_ascii=False)
