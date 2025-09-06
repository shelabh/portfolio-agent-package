# ai-agent/agents/tools/notes_agent.py
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
from ...utils import upsert_vector
import uuid

def notes_agent(state: MessagesState) -> Command[Literal["end"]]:
    """
    Persist a short summary of the interaction to your notes store (Postgres+pgvector).
    Saves the final_answer and metadata (user_id, timestamp).
    """
    final = state.__dict__.get("final_answer") or state.__dict__.get("candidate_answer", "")
    user_id = getattr(state, "user_id", "anon")
    note_id = f"note-{uuid.uuid4().hex}"
    metadata = {"user_id": user_id, "source": "interaction", "content": final}
    # For memory we embed the note content and upsert into vector table (simplified)
    import openai
    from ...config import settings
    openai.api_key = settings.OPENAI_API_KEY
    emb = openai.Embedding.create(model=settings.EMBEDDING_MODEL, input=final)
    vec = emb["data"][0]["embedding"]
    upsert_vector(note_id, metadata, vec)
    return Command(goto="end", update={"note_id": note_id})
