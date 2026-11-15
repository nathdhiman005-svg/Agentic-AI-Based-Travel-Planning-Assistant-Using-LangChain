"""
Streamlit Web Application: Agentic AI Travel Planning Assistant.
Phase 5 Complete: Full interactive UI, sidebar controls, live progress tracking,
dashboard cards, budget chart, Neon PostgreSQL persistence, downloads, and chat refinement.
"""

from datetime import date, timedelta
import uuid
import streamlit as st

from src.utils.config import settings
from src.database.db_service import db_service
from src.agents.travel_agent import travel_agent
from src.ui.components import (
    render_trip_header,
    render_flight_card,
    render_hotel_card,
    render_weather_strip,
    render_daily_itinerary,
    render_budget_breakdown,
)

# 1. Page Configuration
st.set_page_config(
    page_title=f"{settings.APP_TITLE} | AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS Styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(120deg, #1E88E5, #004D40);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        background-color: rgba(56, 189, 248, 0.15);
        color: #38BDF8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .card-box {
        border-radius: 12px;
        padding: 1.25rem;
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .card-box h4 {
        color: #38BDF8 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin-top: 0 !important;
        margin-bottom: 0.4rem !important;
    }
    .card-box p {
        color: #E2E8F0 !important;
        font-size: 0.9rem !important;
        line-height: 1.4 !important;
        margin: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initializes persistent session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "itinerary_result" not in st.session_state:
        st.session_state.itinerary_result = None
    if "structured_itinerary" not in st.session_state:
        st.session_state.structured_itinerary = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "saved_id" not in st.session_state:
        st.session_state.saved_id = None


def render_sidebar():
    """Renders the interactive sidebar with travel planning parameters."""
    with st.sidebar:
        st.markdown("## ✈️ Trip Preferences")
        st.caption("Configure your journey details for the AI Travel Agent.")

        available_cities = db_service.get_available_cities()
        if not available_cities:
            available_cities = [
                "Bangalore",
                "Chennai",
                "Delhi",
                "Goa",
                "Hyderabad",
                "Jaipur",
                "Kolkata",
                "Mumbai",
            ]

        col_orig, col_dest = st.columns(2)
        with col_orig:
            origin_default_idx = (
                available_cities.index("Hyderabad")
                if "Hyderabad" in available_cities
                else 0
            )
            origin = st.selectbox(
                "From (Origin)",
                options=available_cities,
                index=origin_default_idx,
                help="City you are traveling from",
            )
        with col_dest:
            dest_default_idx = (
                available_cities.index("Delhi")
                if "Delhi" in available_cities
                else min(1, len(available_cities) - 1)
            )
            destination = st.selectbox(
                "To (Destination)",
                options=available_cities,
                index=dest_default_idx,
                help="City you want to visit",
            )

        if origin == destination:
            st.warning("⚠️ Origin and destination cannot be the same city.")

        # Dates & Duration
        st.markdown("### 📅 Dates & Duration")
        today = date.today()
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input(
                "Departure Date",
                value=today + timedelta(days=7),
                min_value=today,
            )
        with col_end:
            end_date = st.date_input(
                "Return Date",
                value=today + timedelta(days=10),
                min_value=start_date,
            )

        trip_days = max(1, (end_date - start_date).days + 1)
        st.caption(f"⏱️ **Trip Duration:** {trip_days} Day(s) ({max(1, trip_days - 1)} Nights)")

        # Travelers & Budget
        st.markdown("### 💰 Travelers & Budget")
        col_pax, col_empty = st.columns([1, 1])
        with col_pax:
            num_travelers = st.number_input(
                "Travelers", min_value=1, max_value=8, value=1, step=1
            )

        budget_limit = st.slider(
            "Max Target Budget (₹ INR)",
            min_value=5000,
            max_value=100000,
            value=15000,
            step=1000,
            format="₹%d",
            help="Total maximum spending budget for all travelers combined",
        )

        # Travel Style & Preferences
        st.markdown("### 🎨 Travel Persona & Style")
        travel_style = st.selectbox(
            "Travel Style",
            options=[
                "Balanced (Sightseeing & Relaxation)",
                "Budget Explorer (Cost-saving & Value)",
                "Luxury & Leisure (Premium Stays & Comfort)",
                "Heritage & Cultural (Forts, Temples & Museums)",
                "Adventure & Scenic (Beaches, Lakes & Nature)",
            ],
            index=0,
        )

        preferences = st.text_area(
            "Special Requests (Optional)",
            placeholder="e.g., Prefer 4-star hotel with pool, focus on local food, beach walks...",
            max_chars=200,
        )

        st.markdown("---")
        generate_clicked = st.button(
            "✨ Generate AI Itinerary",
            type="primary",
            use_container_width=True,
            disabled=(origin == destination),
        )

        # Reset button if itinerary exists
        if st.session_state.itinerary_result:
            if st.button("🔄 Plan Another Trip", use_container_width=True):
                st.session_state.itinerary_result = None
                st.session_state.structured_itinerary = None
                st.session_state.chat_messages = []
                st.session_state.saved_id = None
                travel_agent.clear_session(st.session_state.session_id)
                st.rerun()

        # Engine badges in sidebar footer
        st.markdown("---")
        st.markdown(
            f"""
            <div style="font-size:0.8rem; color:#78909C;">
                <div>🤖 <b>Model:</b> {settings.OLLAMA_MODEL}</div>
                <div>🗄️ <b>Database:</b> {'Neon Tech PostgreSQL' if settings.is_postgres else 'SQLite'}</div>
                <div>🌦️ <b>Weather API:</b> Open-Meteo Live</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return {
            "origin": origin,
            "destination": destination,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "trip_days": trip_days,
            "num_travelers": num_travelers,
            "budget_limit": float(budget_limit),
            "travel_style": travel_style,
            "preferences": preferences,
            "generate_clicked": generate_clicked,
        }


def render_hero_banner():
    """Renders the main hero banner when no itinerary has been generated yet."""
    st.markdown('<div class="main-title">🌍 WanderWise: Agentic AI Travel Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Autonomous travel planning powered by LangChain ReAct reasoning, Neon Tech PostgreSQL, and live Open-Meteo weather intelligence.</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            """
            <div class="card-box">
                <h4>✈️ Flight Search</h4>
                <p style="font-size:0.9rem; color:#546E7A;">Autonomous ranking by airfare and travel duration from Neon database.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="card-box">
                <h4>🏨 Hotels & Stays</h4>
                <p style="font-size:0.9rem; color:#546E7A;">Smart matching by star ratings, nightly limits, and desired amenities.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="card-box">
                <h4>🌦️ Live Weather</h4>
                <p style="font-size:0.9rem; color:#546E7A;">Real-time Open-Meteo weather forecasts and daily packing advisories.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """
            <div class="card-box">
                <h4>💰 Budget Validation</h4>
                <p style="font-size:0.9rem; color:#546E7A;">Deterministic cost breakdown and surplus/deficit arithmetic.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def execute_agent_with_progress(trip_params: dict):
    """Executes the agentic planner with real-time UI status updates using st.status."""
    status_container = st.status(
        f"🤖 WanderWise Agent is curating your {trip_params['trip_days']}-day journey to {trip_params['destination']}...",
        expanded=True,
    )

    tool_labels = {
        "get_weather_forecast": "🌦️ Fetching live Open-Meteo weather forecast & packing advice...",
        "search_flights": f"✈️ Searching flights from {trip_params['origin']} to {trip_params['destination']} in Neon PostgreSQL...",
        "recommend_hotels": f"🏨 Evaluating top hotels in {trip_params['destination']} within budget...",
        "discover_places": f"🏛️ Discovering top-rated attractions and heritage sights in {trip_params['destination']}...",
        "calculate_budget": "💰 Performing exact arithmetic and budget feasibility check...",
    }

    def on_agent_step(event_type: str, data: dict):
        if event_type == "tool_call":
            tool_name = data.get("tool", "")
            label = tool_labels.get(tool_name, f"⚙️ Invoking agent tool: {tool_name}...")
            status_container.write(label)
        elif event_type == "start":
            status_container.write(f"🚀 Initializing WanderWise reasoning graph for {trip_params['destination']}...")

    try:
        result = travel_agent.plan_trip(
            destination=trip_params["destination"],
            origin=trip_params["origin"],
            duration_days=trip_params["trip_days"],
            budget_limit=trip_params["budget_limit"],
            num_travelers=trip_params["num_travelers"],
            travel_style=trip_params["travel_style"],
            preferences=trip_params["preferences"],
            session_id=st.session_state.session_id,
            step_callback=on_agent_step,
        )

        if result.get("success"):
            status_container.update(
                label=f"✅ Itinerary successfully generated in {result['latency_seconds']}s! (Tools invoked: {len(result['tools_called'])})",
                state="complete",
                expanded=False,
            )
            st.session_state.itinerary_result = result
            st.session_state.structured_itinerary = travel_agent.parse_to_structured_itinerary(
                raw_markdown=result["raw_markdown"],
                destination=trip_params["destination"],
                origin=trip_params["origin"],
                duration_days=trip_params["trip_days"],
                budget_limit=trip_params["budget_limit"],
                num_travelers=trip_params["num_travelers"],
            )
            st.rerun()
        else:
            status_container.update(label="❌ Error generating itinerary.", state="error", expanded=True)
            st.error(result.get("error", "Unknown error during agent execution."))

    except Exception as e:
        status_container.update(label="❌ Execution failed.", state="error")
        st.error(f"Unexpected error: {e}")


def render_export_and_save_bar(structured, trip_params):
    """Renders Save to Neon Tech database and Download buttons."""
    col_save, col_dl_md, col_dl_json = st.columns([1.5, 1, 1])

    with col_save:
        if st.session_state.saved_id:
            st.success(f"✅ Saved to Neon Database (ID: #{st.session_state.saved_id})")
        else:
            if st.button("💾 Save Itinerary to Neon Database", type="secondary", use_container_width=True):
                saved_id = db_service.save_itinerary(
                    session_id=st.session_state.session_id,
                    title=structured.trip_title,
                    destination=structured.destination,
                    origin=structured.origin,
                    start_date=trip_params["start_date"],
                    end_date=trip_params["end_date"],
                    total_cost=structured.budget.total_budget,
                    itinerary_json=structured.model_dump_json(),
                )
                if saved_id:
                    st.session_state.saved_id = saved_id
                    st.success(f"🎉 Successfully saved to Neon Tech PostgreSQL! Record ID: #{saved_id}")
                    st.rerun()
                else:
                    st.error("Could not save to database. Please check connection.")

    with col_dl_md:
        st.download_button(
            label="📥 Download (.md)",
            data=structured.to_markdown(),
            file_name=f"itinerary_{structured.destination.lower()}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_dl_json:
        st.download_button(
            label="📥 Download (.json)",
            data=structured.model_dump_json(indent=2),
            file_name=f"itinerary_{structured.destination.lower()}.json",
            mime="application/json",
            use_container_width=True,
        )


def render_refinement_chat(session_id: str):
    """Interactive chat widget allowing the traveler to refine the plan in place."""
    st.markdown("### 💬 Refine Your Itinerary with WanderWise")
    st.caption("Ask questions, swap hotels, add sights, or request adjustments (e.g. 'Can we find a hotel with a gym?').")

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Type your modification or travel question here...")
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("WanderWise is analyzing your request..."):
                response = travel_agent.refine_plan(user_input, session_id=session_id)
                answer = response.get("raw_markdown", "I could not process your refinement request.")
                st.markdown(answer)
                st.session_state.chat_messages.append({"role": "assistant", "content": answer})


def main():
    initialize_session_state()
    trip_params = render_sidebar()

    if trip_params["generate_clicked"]:
        execute_agent_with_progress(trip_params)

    if not st.session_state.itinerary_result:
        render_hero_banner()
        st.info("👈 Set your origin, destination, and budget in the sidebar, then click **Generate AI Itinerary** to begin.")
    else:
        result = st.session_state.itinerary_result
        structured = st.session_state.get("structured_itinerary")

        tab_dash, tab_doc, tab_audit = st.tabs(
            ["📋 Interactive Dashboard", "📄 Itinerary Document", "⚙️ AI Reasoning & Telemetry"]
        )

        with tab_dash:
            # Self-healing: if structured was not parsed or was None from a prior run, parse on the fly
            if not structured and result.get("raw_markdown"):
                try:
                    structured = travel_agent.parse_to_structured_itinerary(
                        raw_markdown=result["raw_markdown"],
                        destination=trip_params["destination"],
                        origin=trip_params["origin"],
                        duration_days=trip_params["trip_days"],
                        budget_limit=trip_params["budget_limit"],
                        num_travelers=trip_params["num_travelers"],
                    )
                    st.session_state.structured_itinerary = structured
                except Exception as ex:
                    st.warning(f"Note: Could not build visual cards ({ex}); displaying document view below.")

            if structured:
                render_trip_header(structured)
                st.divider()

                # Action bar: Save to Neon DB + Downloads
                render_export_and_save_bar(structured, trip_params)
                st.divider()

                # Flights & Hotels
                col_fl, col_ht = st.columns(2)
                with col_fl:
                    render_flight_card(structured.flight)
                with col_ht:
                    render_hotel_card(structured.hotel)

                st.divider()

                # Weather Forecast Strip
                if structured.weather_forecast:
                    render_weather_strip(structured.weather_forecast)
                    st.divider()

                # Day-by-Day Timeline
                render_daily_itinerary(structured.itinerary)
                st.divider()

                # Budget Breakdown & Cost Distribution Bar Chart
                render_budget_breakdown(structured.budget, target_budget=trip_params["budget_limit"])
                st.divider()

                # Interactive Refinement Chat
                render_refinement_chat(st.session_state.session_id)
            else:
                st.markdown(result["raw_markdown"])

        with tab_doc:
            st.markdown("### 📄 Complete Travel Itinerary")
            if structured:
                st.markdown(structured.to_markdown())
            else:
                st.markdown(result["raw_markdown"])

        with tab_audit:
            st.markdown("### 🤖 Agent Execution & Tool Audit")
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.metric("Total Latency", f"{result.get('latency_seconds', 0)}s")
            with col_a2:
                st.metric("Tools Invoked", len(result.get("tools_called", [])))
            with col_a3:
                st.metric("Destination", result.get("destination", "N/A"))

            st.markdown("**Tools Sequence:**")
            st.write(" ➡️ ".join([f"`{t}`" for t in result.get("tools_called", [])]))

            if structured and structured.reasoning:
                st.info(f"💡 **Why This Plan Was Selected:**\n\n{structured.reasoning}")


if __name__ == "__main__":
    main()
