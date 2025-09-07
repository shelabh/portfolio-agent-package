# agents/critic.py - FIXED
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
from ..utils import llm_chat

def critic_agent(state: MessagesState) -> Command[Literal["end","notes_agent"]]:
    """
    Sanity checks candidate_answer for hallucinations and asserts that any factual claim
    is supported by the retrieved sources. If flagged, returns 'end' with a safe fallback.
    """
    candidate = state.__dict__.get("candidate_answer", "")
    ranked = state.__dict__.get("ranked", [])

    prompt = [
        {"role":"system","content":"You are a critic that verifies whether the assistant's answer is supported by the provided evidence. Respond with JSON: {valid: true|false, issues: []}."},
        {"role":"user","content": f"Answer: {candidate}\n\nEvidence snippets: {[(d.get('id'), d.get('content')[:300]) for d in ranked]}\n\nIs the answer supported?"}
    ]
    resp = llm_chat(prompt, max_tokens=128)
    import json
    try:
        verdict = json.loads(resp.strip())
    except Exception:
        # be conservative
        verdict = {"valid": False, "issues": ["Could not parse critic response."]}
    if not verdict.get("valid"):
        fallback = "I can't fully verify that information right now. Would you like me to show the sources or request a human review?"
        return Command(goto="end", update={"final_answer": fallback})
    # otherwise persist note or optionally call notes agent to log the interaction
    return Command(goto="notes_agent", update={"final_answer": candidate})
