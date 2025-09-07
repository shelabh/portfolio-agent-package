# agents/tools/calendly_agent.py
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
import requests
import os

CALENDLY_API_KEY = os.getenv("CALENDLY_API_KEY")
CALENDLY_BASE = "https://api.calendly.com"

def calendly_agent(state: MessagesState) -> Command[Literal["end"]]:
    """
    Simple Calendly tool: create an event link or fetch availability.
    This agent expects state.messages to include a Calendly intent (router should set).
    """
    # For security: do NOT auto-send invites. Only generate links or availability.
    # Example implementation: return a dummy link or call Calendly API if configured.
    if not CALENDLY_API_KEY:
        return Command(goto="end", update={"calendly_link": "https://calendly.com/your-profile (not configured)"})
    # Implement a real call: find user's scheduling link or create one via API
    headers = {"Authorization": f"Bearer {CALENDLY_API_KEY}", "Content-Type": "application/json"}
    # Example: fetch scheduled_event_types for the user
    resp = requests.get(f"{CALENDLY_BASE}/scheduled_event_types", headers=headers, timeout=10)
    if resp.status_code != 200:
        return Command(goto="end", update={"calendly_link": "error fetching calendly"})
    data = resp.json()
    # For demo, take first event type and create a booking link
    try:
        et = data["data"][0]
        uri = et["attributes"]["uri"]
        # Usually Calendly has a scheduling page url under attributes
        link = et["attributes"].get("scheduling_page_url") or "https://calendly.com/"
    except Exception:
        link = "https://calendly.com/"
    return Command(goto="end", update={"calendly_link": link})
