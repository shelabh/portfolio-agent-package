# ai-agent/agents/persona.py
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
from ..config import settings
from ..utils import llm_chat

def persona_agent(state: MessagesState) -> Command[Literal["critic","end"]]:
    """
    Finalizes the response applying formal persona, citations, and polish.
    Expects state.ranked to exist (list of docs) or fallback to direct LLM.
    """
    persona_prompt = settings.PERSONA_PROMPT
    user_msg = state.messages[-1]["content"]

    context_excerpt = ""
    ranked = state.__dict__.get("ranked", [])
    if ranked:
        # include top 3 citations
        for d in ranked[:3]:
            src = d.get("metadata", {}).get("source", d.get("id"))
            context_excerpt += f"\n[[{src}]]: {d.get('content')[:400]}"

    # Build conversation for the LLM
    messages = [
        {"role":"system","content": persona_prompt},
        {"role":"user","content": f"User asked: {user_msg}\n\nContext: {context_excerpt}\n\nAnswer formally and include citations where appropriate."}
    ]
    answer = llm_chat(messages, max_tokens=512)
    return Command(goto="critic", update={"candidate_answer": answer})
