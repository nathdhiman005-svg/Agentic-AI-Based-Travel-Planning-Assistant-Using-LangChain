"""
LangChain Travel Planner Agent Orchestrator with Multi-Turn Conversational Memory.
Assembles tools, prompt guidelines, and local Ollama LLM into an autonomous agent graph.
Supports interactive itinerary refinement (e.g. changing hotels, extending days),
live step tracking, and execution telemetry logging in Neon Tech PostgreSQL.
"""

import time
import re
from typing import Dict, Any, Optional, List, Callable
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage

from src.utils.config import settings
from src.tools import ALL_TRAVEL_TOOLS
from src.agents.prompts import TRAVEL_AGENT_SYSTEM_PROMPT, build_trip_user_prompt
from src.agents.schemas import (
    TravelItineraryOutput,
    SelectedFlight,
    SelectedHotel,
    DailyPlan,
    BudgetBreakdown,
)
from src.database.db_service import db_service


class TravelPlannerAgent:
    """Autonomous LangChain agent with conversation memory for travel planning and refinement."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
    ):
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.temperature = temperature

        # In-memory session message histories for multi-turn chats
        self._session_histories: Dict[str, List[BaseMessage]] = {}

        # Initialize local LLM with expanded context window for multi-turn chats
        self.llm = ChatOllama(
            model=self.model_name,
            base_url=self.base_url,
            temperature=self.temperature,
            num_ctx=8192,
        )

        # Assemble modern LangChain agent graph
        self.agent = create_agent(
            model=self.llm,
            tools=ALL_TRAVEL_TOOLS,
            system_prompt=TRAVEL_AGENT_SYSTEM_PROMPT,
        )

    def get_session_history(self, session_id: str = "default") -> List[BaseMessage]:
        """Returns the conversation messages for a given session ID."""
        return self._session_histories.get(session_id, [])

    def clear_session(self, session_id: str = "default"):
        """Clears accumulated conversation memory for a session."""
        if session_id in self._session_histories:
            del self._session_histories[session_id]

    def plan_trip(
        self,
        destination: str,
        origin: str = "Delhi",
        duration_days: int = 3,
        budget_limit: float = 15000.0,
        num_travelers: int = 1,
        travel_style: str = "Balanced",
        preferences: str = "",
        session_id: str = "default",
        step_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Executes initial itinerary generation, resetting session memory.
        """
        user_prompt = build_trip_user_prompt(
            destination=destination,
            origin=origin,
            duration_days=duration_days,
            budget_limit=budget_limit,
            num_travelers=num_travelers,
            travel_style=travel_style,
            preferences=preferences,
        )

        # Reset session history for new primary trip plan
        self._session_histories[session_id] = [HumanMessage(content=user_prompt)]

        return self._execute_agent(
            session_id=session_id,
            query_label=f"Initial Plan: {duration_days}-day trip to {destination} from {origin}",
            step_callback=step_callback,
            extra_meta={
                "destination": destination,
                "origin": origin,
                "duration_days": duration_days,
                "budget_limit": budget_limit,
                "num_travelers": num_travelers,
            },
        )

    def refine_plan(
        self,
        user_message: str,
        session_id: str = "default",
        step_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Appends user modification query to ongoing session history and refines the itinerary.
        E.g.: 'Change the hotel to a cheaper one' or 'Add more heritage monuments'.
        """
        if session_id not in self._session_histories or not self._session_histories[session_id]:
            # No prior history; start fresh
            self._session_histories[session_id] = [HumanMessage(content=user_message)]
        else:
            self._session_histories[session_id].append(HumanMessage(content=user_message))

        return self._execute_agent(
            session_id=session_id,
            query_label=f"Refinement: {user_message[:60]}",
            step_callback=step_callback,
        )

    def _execute_agent(
        self,
        session_id: str,
        query_label: str,
        step_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Core execution loop with telemetry logging and state retention."""
        start_time = time.time()
        tools_called: List[str] = []
        status = "SUCCESS"
        error_msg = None
        final_markdown = ""

        # Prepare clean messages: for multi-turn chats, retain conversational summaries
        # and avoid passing bloated raw tool dumps from older completed turns
        raw_history = self._session_histories[session_id]
        if len(raw_history) > 6:
            clean_messages = [
                m for m in raw_history
                if isinstance(m, HumanMessage) or (isinstance(m, AIMessage) and not getattr(m, "tool_calls", None))
            ]
            messages_to_send = clean_messages if len(clean_messages) >= 2 else raw_history[-4:]
        else:
            messages_to_send = raw_history

        try:
            if step_callback:
                step_callback("start", {"message": query_label})

            result = self.agent.invoke({"messages": messages_to_send}, config={"recursion_limit": 15})
            updated_messages = result.get("messages", [])

            # Save full conversation back to session history for future turns
            self._session_histories[session_id] = updated_messages

            # Extract tool calls from newly added messages
            for msg in updated_messages[len(messages_to_send) - 1:]:
                if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tname = tc.get("name", "tool")
                        if tname not in tools_called:
                            tools_called.append(tname)
                        if step_callback:
                            step_callback("tool_call", {"tool": tname, "args": tc.get("args", {})})

                elif isinstance(msg, ToolMessage):
                    if step_callback:
                        step_callback("tool_result", {"tool": getattr(msg, "name", "tool")})

            if updated_messages:
                last_msg = updated_messages[-1]
                final_markdown = (
                    last_msg.content
                    if isinstance(last_msg, AIMessage)
                    else str(last_msg)
                )

        except Exception as e:
            status = "FAILED"
            error_msg = str(e)
            final_markdown = f"An error occurred while generating your itinerary: {error_msg}"

        latency = round(time.time() - start_time, 2)

        # Log telemetry to Neon Tech PostgreSQL
        db_service.log_query(
            user_query=query_label,
            tool_calls=", ".join(tools_called) if tools_called else "none",
            latency_seconds=latency,
            status=status,
            error_message=error_msg,
        )

        response = {
            "success": status == "SUCCESS",
            "raw_markdown": final_markdown,
            "tools_called": tools_called,
            "latency_seconds": latency,
            "session_id": session_id,
            "history_length": len(self._session_histories.get(session_id, [])),
            "error": error_msg,
        }
        if extra_meta:
            response.update(extra_meta)
        return response

    def parse_to_structured_itinerary(
        self,
        raw_markdown: str,
        destination: str,
        origin: str,
        duration_days: int,
        budget_limit: float,
        num_travelers: int = 1,
        *args,
        **kwargs,
    ) -> TravelItineraryOutput:
        """
        Parses the agent's markdown output into a validated TravelItineraryOutput Pydantic model.
        Uses resilient multi-pattern regexes and mathematical fallbacks to guarantee non-zero,
        realistic flight, hotel, and budget totals.
        """
        import math

        num_travelers = max(1, num_travelers)
        nights = max(1, duration_days - 1)
        rooms = math.ceil(num_travelers / 2)

        # 1. Title
        title_match = re.search(r"^#\s+(.+)$", raw_markdown, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f"Your {duration_days}-Day Trip to {destination}"

        # 2. Resilient Flight Parsing
        flight = None
        # Pattern handles: - **IndiGo (FL0019)** – ₹5,918 OR - **IndiGo** (FL0019) – ₹5,918 OR - IndiGo (FL0019) - 5918
        flight_match = re.search(
            r"Flight Selected:.*?\n[-*]\s*\**([^*()]+?)(?:\s*\(([^)]+)\))?\**\s*[–-]\s*₹?([\d,]+)",
            raw_markdown,
            re.DOTALL,
        )
        if flight_match:
            try:
                airline = flight_match.group(1).strip()
                fid = flight_match.group(2).strip() if flight_match.group(2) else "Direct"
                fare = float(flight_match.group(3).replace(",", ""))
                flight = SelectedFlight(
                    airline=airline,
                    flight_id=fid,
                    origin=origin,
                    destination=destination,
                    departure_time="Scheduled",
                    arrival_time="Scheduled",
                    fare=fare,
                )
            except Exception:
                pass

        # If flight was not extracted from markdown, query database for route fallback
        if not flight:
            available_flights = db_service.get_flights(source=origin, destination=destination)
            if available_flights:
                best_flight = available_flights[0]
                flight = SelectedFlight(
                    airline=best_flight.airline,
                    flight_id=best_flight.flight_id,
                    origin=origin,
                    destination=destination,
                    departure_time=best_flight.departure_time,
                    arrival_time=best_flight.arrival_time,
                    fare=best_flight.price,
                    why_selected="Selected best available flight from database catalog.",
                )

        # 3. Resilient Hotel Parsing
        hotel = None
        # Pattern handles: - **Royal Heritage** (₹6,303/night, 5-star) OR - **Royal Heritage** (5-star, ₹6,303/night)
        hotel_match = re.search(
            r"Hotel Booked:.*?\n[-*]\s*\**([^*()]+?)\**\s*\((?:₹?([\d,]+)/night,\s*(\d+)[- ]star|(\d+)[- ]star,\s*₹?([\d,]+)/night)\)",
            raw_markdown,
            re.DOTALL,
        )
        if hotel_match:
            try:
                hname = hotel_match.group(1).strip()
                rate_str = hotel_match.group(2) or hotel_match.group(5)
                star_str = hotel_match.group(3) or hotel_match.group(4)
                rate = float(rate_str.replace(",", ""))
                stars = int(star_str)
                hotel = SelectedHotel(
                    hotel_name=hname,
                    stars=stars,
                    price_per_night=rate,
                    total_price=rate * nights * rooms,
                )
            except Exception:
                pass

        # If hotel was not extracted from markdown, query database for city fallback
        if not hotel:
            available_hotels = db_service.get_hotels(city=destination)
            if available_hotels:
                best_hotel = available_hotels[0]
                hotel = SelectedHotel(
                    hotel_name=best_hotel.name,
                    stars=best_hotel.stars,
                    price_per_night=best_hotel.price_per_night,
                    total_price=best_hotel.price_per_night * nights * rooms,
                    amenities=best_hotel.amenities,
                    why_selected="Selected top recommended hotel from database catalog.",
                )

        # 4. Resilient Budget Extraction & Mathematical Validation
        flight_cost_per_person = flight.fare if flight else 0.0
        calculated_flight_total = flight_cost_per_person * num_travelers

        hotel_nightly_rate = hotel.price_per_night if hotel else 0.0
        calculated_hotel_total = hotel_nightly_rate * nights * rooms

        calculated_local_total = 1000.0 * duration_days * num_travelers

        # Check if text contained explicit budget figures
        f_cost_match = re.search(r"Flight[s]?:\s*₹?\s*([\d,]+)", raw_markdown)
        h_cost_match = re.search(r"(?:Hotel|Accommodation)[^:\n]*:\s*₹?\s*([\d,]+)", raw_markdown)
        l_cost_match = re.search(r"(?:Food|Travel|Local)[^:\n]*:\s*₹?\s*([\d,]+)", raw_markdown)
        total_match = re.search(r"Total(?:\s*Cost|\s*Budget)?:\s*\**₹?\s*([\d,]+)\**", raw_markdown)

        text_flight = float(f_cost_match.group(1).replace(",", "")) if f_cost_match else None
        text_hotel = float(h_cost_match.group(1).replace(",", "")) if h_cost_match else None
        text_local = float(l_cost_match.group(1).replace(",", "")) if l_cost_match else None
        text_total = float(total_match.group(1).replace(",", "")) if total_match else None

        # Prioritize accurate text values, but mathematically enforce non-zero sanity
        final_flight_cost = text_flight if (text_flight is not None and text_flight > 0) else calculated_flight_total
        final_hotel_cost = text_hotel if (text_hotel is not None and text_hotel > 0) else calculated_hotel_total
        final_local_cost = text_local if (text_local is not None and text_local > 0) else calculated_local_total

        final_grand_total = text_total if (text_total is not None and text_total >= (final_flight_cost + final_hotel_cost)) else (final_flight_cost + final_hotel_cost + final_local_cost)

        budget = BudgetBreakdown(
            flight_expense=final_flight_cost,
            hotel_expense=final_hotel_cost,
            local_expenses=final_local_cost,
            total_budget=final_grand_total,
            is_within_budget=final_grand_total <= budget_limit,
            budget_notes=f"Target Budget: ₹{budget_limit:,.0f} for {num_travelers} traveler(s)",
        )

        daily_plans: List[DailyPlan] = []
        day_blocks = re.findall(
            r"\*\*Day (\d+):?\s*([^*]*)\*\*\s*\n(.*?)(?=\*\*Day \d+|\#\#\#|\Z)",
            raw_markdown,
            re.DOTALL,
        )
        for d_num, d_title, d_content in day_blocks:
            morning = re.search(r"-\s*\*?Morning:\*?\s*([^\n]+)", d_content)
            afternoon = re.search(r"-\s*\*?Afternoon:\*?\s*([^\n]+)", d_content)
            evening = re.search(r"-\s*\*?Evening:\*?\s*([^\n]+)", d_content)

            daily_plans.append(
                DailyPlan(
                    day_number=int(d_num),
                    title=d_title.strip() if d_title.strip() else f"Exploring {destination}",
                    morning_activity=morning.group(1).strip()
                    if morning
                    else "Morning sightseeing and local breakfast",
                    afternoon_activity=afternoon.group(1).strip()
                    if afternoon
                    else "Afternoon cultural attraction visit",
                    evening_activity=evening.group(1).strip()
                    if evening
                    else "Evening leisure walk and dinner",
                )
            )

        return TravelItineraryOutput(
            trip_title=title,
            destination=destination,
            origin=origin,
            duration_days=duration_days,
            summary=f"Curated {duration_days}-day itinerary to {destination} from {origin}.",
            flight=flight,
            hotel=hotel,
            itinerary=daily_plans,
            budget=budget,
            reasoning=f"Selected options optimizing quality within the ₹{budget_limit:,.0f} budget limit.",
        )


# Singleton travel agent instance
travel_agent = TravelPlannerAgent()
