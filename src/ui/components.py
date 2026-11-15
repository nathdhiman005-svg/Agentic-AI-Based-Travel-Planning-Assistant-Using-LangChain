"""
UI Component Library for the Agentic AI Travel Assistant.
Provides modular, modern visual cards for Flights, Hotels, Weather, Daily Itineraries, and Budgets.
"""

from typing import List, Optional
import streamlit as st
import pandas as pd
from src.agents.schemas import (
    TravelItineraryOutput,
    SelectedFlight,
    SelectedHotel,
    DailyWeather,
    DailyPlan,
    BudgetBreakdown,
)


def render_trip_header(itinerary: TravelItineraryOutput):
    """Renders the top summary banner with destination and quick metrics."""
    st.markdown(f"## 🌍 {itinerary.trip_title}")
    if itinerary.summary:
        st.markdown(f"> *{itinerary.summary}*")

    st.markdown(
        f"""
        <div style="margin-bottom: 1.2rem;">
            <span class="badge-pill">📍 {itinerary.destination}</span>
            <span class="badge-pill">⏱️ {itinerary.duration_days} Days / {max(1, itinerary.duration_days - 1)} Nights</span>
            <span class="badge-pill">✈️ Origin: {itinerary.origin or 'Direct'}</span>
            <span class="badge-pill">💰 Total: ₹{itinerary.budget.total_budget:,.0f}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_flight_card(flight: Optional[SelectedFlight]):
    """Renders a modern airline ticket summary card."""
    st.markdown("### ✈️ Flight Selection")
    if not flight:
        st.info("ℹ️ No direct flight available in the catalog for this specific route. Travelers can consider train, road, or connecting transit via a nearby hub.")
        return

    col1, col2, col3 = st.columns([2, 2, 1.5])
    with col1:
        st.markdown(f"**Airline:** {flight.airline}")
        st.caption(f"Flight Number: `{flight.flight_id}`")
    with col2:
        st.markdown(f"**Departure:** {flight.departure_time}")
        st.caption(f"Arrival: {flight.arrival_time}")
    with col3:
        st.metric(label="Airfare", value=f"₹{flight.fare:,.0f}")

    if flight.why_selected:
        st.info(f"💡 **Selection Reason:** {flight.why_selected}")


def render_hotel_card(hotel: Optional[SelectedHotel]):
    """Renders an accommodation card with stars, tariffs, and amenities."""
    st.markdown("### 🏨 Accommodation Booked")
    if not hotel:
        st.info("ℹ️ No specific hotel matched the strict filters in our catalog. Try relaxing star rating or price limits in preferences.")
        return

    stars_str = "⭐" * hotel.stars
    col1, col2, col3 = st.columns([2, 2, 1.5])
    with col1:
        st.markdown(f"**{hotel.hotel_name}** ({stars_str})")
        st.caption(f"Category: {hotel.stars}-Star Property")
    with col2:
        st.markdown(f"**Nightly Tariff:** ₹{hotel.price_per_night:,.0f}")
        st.caption(f"Total Stay Cost: ₹{hotel.total_price:,.0f}")
    with col3:
        st.metric(label="Total Lodging", value=f"₹{hotel.total_price:,.0f}")

    if hotel.amenities:
        st.markdown(
            "**Amenities Included:** "
            + " ".join([f"`{a.capitalize()}`" for a in hotel.amenities])
        )

    if hotel.why_selected:
        st.info(f"💡 **Selection Reason:** {hotel.why_selected}")


def render_weather_strip(weather_forecast: List[DailyWeather]):
    """Renders a horizontal forecast strip for each day of the journey."""
    st.markdown("### 🌦️ Destination Weather Forecast")
    if not weather_forecast:
        st.caption("Live weather forecast was not retrieved.")
        return

    num_days = len(weather_forecast)
    cols = st.columns(num_days)
    for i, w in enumerate(weather_forecast):
        with cols[i]:
            st.markdown(
                f"""
                <div style="background-color:rgba(34, 197, 94, 0.12); border-radius:10px; padding:0.85rem; text-align:center; border:1px solid rgba(34, 197, 94, 0.3);">
                    <div style="font-weight:700; color:#4ADE80; font-size:0.95rem;">Day {w.day_number}</div>
                    <div style="font-size:0.85rem; color:#E2E8F0; margin:0.3rem 0;">{w.condition}</div>
                    <div style="font-size:1.15rem; font-weight:800; color:#86EFAC;">{w.temperature_c or 'Pleasant'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_daily_itinerary(itinerary_days: List[DailyPlan]):
    """Renders an expandable day-by-day activity timeline."""
    st.markdown("### 🗺️ Day-Wise Itinerary")
    if not itinerary_days:
        st.info("No detailed daily schedule generated.")
        return

    for day in itinerary_days:
        with st.expander(f"📍 Day {day.day_number}: {day.title}", expanded=True):
            col_m, col_a, col_e = st.columns(3)
            with col_m:
                st.markdown("##### 🌅 Morning")
                st.markdown(day.morning_activity)
            with col_a:
                st.markdown("##### ☀️ Afternoon")
                st.markdown(day.afternoon_activity)
            with col_e:
                st.markdown("##### 🌙 Evening")
                st.markdown(day.evening_activity)


def render_budget_breakdown(budget: BudgetBreakdown, target_budget: Optional[float] = None):
    """Renders visual metric cards, bar chart, and budget feasibility breakdown."""
    st.markdown("### 💰 Budget Breakdown & Estimation")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✈️ Flights", f"₹{budget.flight_expense:,.0f}")
    with col2:
        st.metric("🏨 Lodging", f"₹{budget.hotel_expense:,.0f}")
    with col3:
        st.metric("🍽️ Food & Local", f"₹{budget.local_expenses:,.0f}")
    with col4:
        st.metric("💵 Total Cost", f"₹{budget.total_budget:,.0f}")

    # Budget feasibility banner
    if target_budget:
        if budget.total_budget <= target_budget:
            buffer = target_budget - budget.total_budget
            st.success(
                f"🎉 **Within Target Budget!** Target: ₹{target_budget:,.0f} | "
                f"Remaining Buffer: ₹{buffer:,.0f}"
            )
        else:
            deficit = budget.total_budget - target_budget
            st.warning(
                f"⚠️ **Exceeds Target Budget by ₹{deficit:,.0f}!** "
                f"(Target: ₹{target_budget:,.0f} | Total: ₹{budget.total_budget:,.0f})"
            )

    # Cost Distribution Chart
    df = pd.DataFrame(
        {
            "Expense Category": ["Flights", "Hotel Lodging", "Food & Local Transport"],
            "Amount (INR)": [
                budget.flight_expense,
                budget.hotel_expense,
                budget.local_expenses,
            ],
        }
    )
    st.bar_chart(df, x="Expense Category", y="Amount (INR)", color="#1E88E5", height=280)
