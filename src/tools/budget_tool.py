"""
Budget estimation and arithmetic calculation tool for the Agentic Travel Assistant.
Ensures 100% mathematical accuracy for trip expense calculations, itemized breakdowns,
and budget feasibility checks.
"""

import math
from typing import Optional, Dict, Any
from langchain_core.tools import tool


def compute_trip_budget(
    flight_cost_per_person: float,
    hotel_cost_per_night: float,
    trip_days: int = 3,
    num_nights: Optional[int] = None,
    num_people: int = 1,
    daily_expenses_per_person: float = 1000.0,
    is_round_trip: bool = False,
    user_budget_limit: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculates exact itemized and cumulative trip expenses."""
    trip_days = max(1, trip_days)
    num_people = max(1, num_people)
    nights = num_nights if num_nights is not None else max(1, trip_days - 1)

    # Number of rooms needed (standard: up to 2 persons per room)
    rooms_needed = math.ceil(num_people / 2)

    # Flight multiplier
    flight_multiplier = 2 if is_round_trip else 1
    total_flight = flight_cost_per_person * flight_multiplier * num_people

    # Lodging total
    total_hotel = hotel_cost_per_night * nights * rooms_needed

    # Daily food, local transit, entry tickets
    total_local = daily_expenses_per_person * trip_days * num_people

    grand_total = total_flight + total_hotel + total_local

    remaining_buffer = None
    is_within_budget = None
    if user_budget_limit is not None and user_budget_limit > 0:
        remaining_buffer = user_budget_limit - grand_total
        is_within_budget = remaining_buffer >= 0

    return {
        "num_people": num_people,
        "trip_days": trip_days,
        "num_nights": nights,
        "rooms_needed": rooms_needed,
        "is_round_trip": is_round_trip,
        "flight_cost_per_person": flight_cost_per_person,
        "total_flight_cost": total_flight,
        "hotel_cost_per_night": hotel_cost_per_night,
        "total_hotel_cost": total_hotel,
        "daily_expenses_per_person": daily_expenses_per_person,
        "total_local_expenses": total_local,
        "grand_total": grand_total,
        "user_budget_limit": user_budget_limit,
        "remaining_buffer": remaining_buffer,
        "is_within_budget": is_within_budget,
    }


@tool
def calculate_budget(
    flight_cost_per_person: float,
    hotel_cost_per_night: float,
    trip_days: int = 3,
    num_nights: Optional[int] = None,
    num_people: int = 1,
    daily_expenses_per_person: float = 1000.0,
    is_round_trip: bool = False,
    user_budget_limit: Optional[float] = None,
) -> str:
    """
    Perform accurate budget calculations and generate an itemized cost breakdown.
    Use this tool whenever finalizing the trip plan or verifying if an itinerary fits within the traveler's budget.

    Args:
        flight_cost_per_person: Price of selected flight ticket per person in INR.
        hotel_cost_per_night: Price of selected hotel room per night in INR.
        trip_days: Total duration of the trip in days (e.g. 3, 5, 7). Default is 3.
        num_nights: Optional number of hotel nights. If omitted, defaults to trip_days - 1.
        num_people: Number of travelers (default is 1).
        daily_expenses_per_person: Estimated daily allowance for food, local transport, and tickets (default is ₹1,000/day).
        is_round_trip: True if flight price needs to be doubled for return journey, False if already total/one-way.
        user_budget_limit: Optional total budget specified by the traveler in INR.

    Returns:
        A structured, human-readable budget breakdown table with total cost and budget surplus/deficit analysis.
    """
    res = compute_trip_budget(
        flight_cost_per_person=flight_cost_per_person,
        hotel_cost_per_night=hotel_cost_per_night,
        trip_days=trip_days,
        num_nights=num_nights,
        num_people=num_people,
        daily_expenses_per_person=daily_expenses_per_person,
        is_round_trip=is_round_trip,
        user_budget_limit=user_budget_limit,
    )

    flight_type = "Round-trip" if res["is_round_trip"] else "One-way"
    lines = [
        f"Trip Budget Breakdown ({res['trip_days']} Days, {res['num_nights']} Nights for {res['num_people']} Traveler(s)):",
        f"- Flights ({flight_type}, {res['num_people']} pax @ ₹{res['flight_cost_per_person']:,.0f}): ₹{res['total_flight_cost']:,.0f}",
        f"- Accommodation ({res['num_nights']} night(s), {res['rooms_needed']} room(s) @ ₹{res['hotel_cost_per_night']:,.0f}/night): ₹{res['total_hotel_cost']:,.0f}",
        f"- Food, Local Transit & Activities ({res['trip_days']} days @ ₹{res['daily_expenses_per_person']:,.0f}/day): ₹{res['total_local_expenses']:,.0f}",
        "--------------------------------------------------",
        f"Grand Total Estimated Cost: ₹{res['grand_total']:,.0f}",
    ]

    if res["user_budget_limit"] is not None:
        if res["is_within_budget"]:
            lines.append(
                f"\nBudget Status: WITHIN BUDGET! (Target: ₹{res['user_budget_limit']:,.0f} | Remaining Buffer: ₹{res['remaining_buffer']:,.0f})"
            )
        else:
            deficit = abs(res["remaining_buffer"])
            lines.append(
                f"\nBudget Status: OVER BUDGET by ₹{deficit:,.0f} (Target: ₹{res['user_budget_limit']:,.0f}). "
                f"Suggestion: Select a more affordable hotel or flight option to stay within limit."
            )

    return "\n".join(lines)
