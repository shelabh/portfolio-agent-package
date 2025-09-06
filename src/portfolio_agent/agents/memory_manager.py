# ai-agent/agents/memory_manager.py
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
from ..utils import nearest_neighbors, upsert_vector
from ..config import settings
import json
import openai

def memory_agent(state: MessagesState) -> Command[Literal["router","end"]]:
    """
    - Optionally fetch long-term memory for the user (if user_id present in state)
    - For now, we attach an empty memory list and continue
    """
    # Example: check for state.user_id and fetch memory using vector similarity
    user_id = getattr(state, "user_id", None)
    mems = []
    if user_id:
        # create a user-specific query (example)
        q_text = "recall recent interactions with this user"
        openai.api_key = settings.OPENAI_API_KEY
        emb = openai.Embedding.create(model=settings.EMBEDDING_MODEL, input=q_text)
        q_vec = emb["data"][0]["embedding"]
        mems = nearest_neighbors(q_vec, top_k=5)
    return Command(goto="router", update={"memories": mems})
