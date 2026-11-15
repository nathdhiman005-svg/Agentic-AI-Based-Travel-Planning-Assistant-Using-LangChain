"""
End-to-end persona validation test suite.
Validates the AI travel assistant across 3 diverse travel scenarios:
1. Solo Budget Traveler
2. Family Vacation
3. Heritage & Cultural Getaway
"""

import time
from src.agents.travel_agent import travel_agent


def run_persona_tests():
    print("=" * 65)
    print("STARTING END-TO-END PERSONA VALIDATION SUITE")
    print("=" * 65)

    scenarios = [
        {
            "name": "Scenario A: Solo Budget Traveler",
            "destination": "Delhi",
            "origin": "Hyderabad",
            "duration_days": 3,
            "budget_limit": 12000.0,
            "num_travelers": 1,
            "travel_style": "Budget Explorer",
            "preferences": "Focus on lowest airfare and affordable stay",
        },
        {
            "name": "Scenario B: Family Vacation",
            "destination": "Kolkata",
            "origin": "Delhi",
            "duration_days": 4,
            "budget_limit": 40000.0,
            "num_travelers": 3,
            "travel_style": "Luxury & Leisure",
            "preferences": "Family-friendly 4+ star hotel with breakfast",
        },
        {
            "name": "Scenario C: Heritage & Cultural Getaway",
            "destination": "Jaipur",
            "origin": "Delhi",
            "duration_days": 3,
            "budget_limit": 20000.0,
            "num_travelers": 2,
            "travel_style": "Heritage & Cultural",
            "preferences": "Focus on historic forts and local bazaars",
        },
    ]

    results_summary = []

    for i, s in enumerate(scenarios, 1):
        print(f"\n--- Running {s['name']} ---")
        print(f"Route: {s['origin']} -> {s['destination']} ({s['duration_days']} Days, {s['num_travelers']} Pax)")
        print(f"Target Budget: ₹{s['budget_limit']:,.0f} | Style: {s['travel_style']}")

        t0 = time.time()
        session_id = f"persona_test_{i}"

        result = travel_agent.plan_trip(
            destination=s["destination"],
            origin=s["origin"],
            duration_days=s["duration_days"],
            budget_limit=s["budget_limit"],
            num_travelers=s["num_travelers"],
            travel_style=s["travel_style"],
            preferences=s["preferences"],
            session_id=session_id,
        )
        elapsed = round(time.time() - t0, 2)

        if not result["success"]:
            print(f"FAILED: {result.get('error')}")
            results_summary.append((s["name"], "FAILED", elapsed, 0, 0, 0))
            continue

        structured = travel_agent.parse_to_structured_itinerary(
            raw_markdown=result["raw_markdown"],
            destination=s["destination"],
            origin=s["origin"],
            duration_days=s["duration_days"],
            budget_limit=s["budget_limit"],
            num_travelers=s["num_travelers"],
        )

        flight_name = f"{structured.flight.airline} ({structured.flight.flight_id})" if structured.flight else "Transit"
        hotel_name = f"{structured.hotel.hotel_name} ({structured.hotel.stars}*)" if structured.hotel else "Local Stay"
        total_budget = structured.budget.total_budget
        is_ok = structured.budget.is_within_budget

        print(f"SUCCESS in {elapsed}s (Tools called: {len(result['tools_called'])})")
        print(f" - Flight: {flight_name} (₹{structured.budget.flight_expense:,.0f})")
        print(f" - Hotel: {hotel_name} (₹{structured.budget.hotel_expense:,.0f})")
        print(f" - Grand Total: ₹{total_budget:,.0f} (Within Budget: {is_ok})")

        results_summary.append((s["name"], "PASSED", elapsed, len(result["tools_called"]), total_budget, is_ok))

    print("\n" + "=" * 65)
    print("PERSONA VALIDATION SUMMARY REPORT")
    print("=" * 65)
    for name, status, elapsed, tools_cnt, total, is_ok in results_summary:
        print(f"{name:<38} | {status} | Time: {elapsed:>5.1f}s | Tools: {tools_cnt} | Total: ₹{total:>7,.0f}")
    print("=" * 65)


if __name__ == "__main__":
    run_persona_tests()
