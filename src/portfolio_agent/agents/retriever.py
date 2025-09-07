# agents/retriever.py - FIXED  
from langgraph.types import Command
from langgraph.graph import MessagesState
from ..utils import llm_chat, nearest_neighbors, client
from ..config import settings
from typing import Literal

def retriever_agent(state: MessagesState) -> Command[Literal["reranker_agent","persona_agent","end"]]:
    """
    - Create a retrieval query from the last user message
    - Call embeddings (via external service) to get query vector
    - Query pgvector for nearest chunks
    - Store results in state and forward to reranker
    """

    messages = state.messages
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content")
            break

    # lightweight prompt to make a retrieval query
    prompt = [{"role":"system","content":"Create a concise retrieval query from user input."},
              {"role":"user","content": last_user}]
    q = llm_chat(prompt, max_tokens=64)

    # Use the client from utils for consistency
    emb_model = settings.EMBEDDING_MODEL
    emb_res = client.embeddings.create(model=emb_model, input=q)
    q_vec = emb_res.data[0].embedding

    hits = nearest_neighbors(q_vec, top_k=6)
    return Command(goto="reranker_agent", update={"retrieved": hits})