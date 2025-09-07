# agents/router.py - FIXED
from typing import Literal
from langgraph.types import Command
from langgraph.graph import MessagesState
from ..config import settings
from ..utils import llm_chat

def router_agent(state: MessagesState) -> Command[Literal["retriever_agent","calendly_agent","persona_agent","end"]]:
    """
    Inspect last user message and decide route:
     - 'calendly_agent' for tool usage  
     - 'retriever_agent' for RAG
     - 'persona_agent' for direct LLM answer (no retrieval)
    """
    messages = state.messages if hasattr(state, "messages") else []
    last_user = None
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content")
            break
    if not last_user:
        return Command(goto="end", update={})

    # Short classifier prompt (low-cost model)
    prompt = [
        {"role":"system","content":"Classify the user's intent into one of: tool, retriever, direct."},
        {"role":"user","content": f"USER: {last_user}\nAnswer: tool|retriever|direct"}
    ]
    resp = llm_chat(prompt, max_tokens=32)
    choice = resp.strip().lower()
    if "tool" in choice:
        goto = "calendly_agent"  # Updated to match graph node name
    elif "retriever" in choice:
        goto = "retriever_agent"  # Updated to match graph node name
    else:
        goto = "persona_agent"  # Updated to match graph node name

    return Command(goto=goto, update={"last_intent": choice})