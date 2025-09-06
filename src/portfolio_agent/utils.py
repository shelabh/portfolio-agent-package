# ai-agent/utils.py
import os
import json
import requests
from typing import List, Dict, Any, Optional
from .config import settings
import openai

openai.api_key = settings.OPENAI_API_KEY

def call_openai_chat(messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens=512) -> str:
    model = model or settings.DEFAULT_MODEL
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return resp.choices[0].message.content

def call_vllm_chat(messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens=512) -> str:
    """
    Call a vLLM OpenAI-compatible server hosted at VLLM_BASE_URL.
    """
    base = settings.VLLM_BASE_URL
    if not base:
        raise RuntimeError("VLLM_BASE_URL not configured")
    payload = {"model": model or settings.DEFAULT_MODEL, "messages": messages, "max_tokens": max_tokens}
    resp = requests.post(f"{base}/chat/completions", json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def llm_chat(messages: List[Dict[str, str]], **kwargs) -> str:
    if settings.LLM_PROVIDER == "vllm":
        return call_vllm_chat(messages, **kwargs)
    return call_openai_chat(messages, **kwargs)

# Simple pgvector helper (SQLAlchemy)
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
engine: Engine = create_engine(settings.DATABASE_URL, future=True)

def upsert_vector(id: str, metadata: Dict[str, Any], vector: List[float]):
    """
    Upsert into documents (id text primary key, content text, embedding vector)
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                INSERT INTO {settings.VECTOR_TABLE} (id, content, metadata, embedding)
                VALUES (:id, :content, :metadata::jsonb, :embedding)
                ON CONFLICT (id) DO UPDATE SET content=EXCLUDED.content, metadata=EXCLUDED.metadata, embedding=EXCLUDED.embedding
                """
            ),
            {"id": id, "content": metadata.get("content") or "", "metadata": json.dumps(metadata), "embedding": vector},
        )

def nearest_neighbors(query_vector: List[float], top_k: int = 4):
    """
    Example using pgvector cosine distance. Assumes embedding column named 'embedding'.
    """
    with engine.connect() as conn:
        sql = text(
            f"""
            SELECT id, content, metadata, embedding <#> :q AS distance
            FROM {settings.VECTOR_TABLE}
            ORDER BY embedding <#> :q
            LIMIT :k
            """
        )
        rows = conn.execute(sql, {"q": query_vector, "k": top_k}).fetchall()
        results = []
        for r in rows:
            results.append({"id": r.id, "content": r.content, "metadata": json.loads(r.metadata), "distance": r.distance})
        return results
