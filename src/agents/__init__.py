"""
Agent package: LangChain agent definition, prompt templates, and reasoning orchestration.
"""

from src.agents.travel_agent import travel_agent, TravelPlannerAgent
from src.agents.prompts import TRAVEL_AGENT_SYSTEM_PROMPT, build_trip_user_prompt
from src.agents.schemas import TravelItineraryOutput, SelectedFlight, SelectedHotel, DailyPlan, BudgetBreakdown

__all__ = [
    "travel_agent",
    "TravelPlannerAgent",
    "TRAVEL_AGENT_SYSTEM_PROMPT",
    "build_trip_user_prompt",
    "TravelItineraryOutput",
    "SelectedFlight",
    "SelectedHotel",
    "DailyPlan",
    "BudgetBreakdown",
]
