# ai-agent/agents/reranker.py
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
from ..utils import llm_chat

def reranker_agent(state: MessagesState) -> Command[Literal["persona","critic","end"]]:
    """
    Rerank retrieved docs by asking a small reranker model which docs are most relevant.
    Expects state.retrieved to be a list of dicts with 'id' and 'content' fields.
    """
    retrieved = state.__dict__.get("retrieved", []) or []
    if not retrieved:
        return Command(goto="persona", update={})

    # build a prompt that lists doc ids + short content and asks for ranking
    doc_list = "\n\n".join([f"ID:{d['id']}\n{d['content'][:300]}" for d in retrieved])
    prompt = [
        {"role":"system","content":"You are a reranker. Given the user query and candidate doc snippets, output a JSON array of doc ids ordered by relevance."},
        {"role":"user","content": f"User Query: {state.messages[-1]['content']}\n\nDocs:\n{doc_list}\n\nReturn: [\"id1\",\"id2\",...]"}
    ]
    resp = llm_chat(prompt, max_tokens=256)
    # attempt parse
    import json
    try:
        order = json.loads(resp.strip())
    except Exception:
        # fallback: naive keep order
        order = [d["id"] for d in retrieved]
    # reorder
    id_map = {d["id"]: d for d in retrieved}
    ordered = [id_map[i] for i in order if i in id_map]
    # append any remaining
    for d in retrieved:
        if d["id"] not in order:
            ordered.append(d)
    return Command(goto="persona", update={"ranked": ordered})
