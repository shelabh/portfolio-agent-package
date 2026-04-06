# portfolio_agent/utils.py
import json
import logging
import time
from typing import List, Dict, Any, Optional

import requests
from openai import OpenAI

from .config import settings

logger = logging.getLogger(__name__)

# Lazily initialize the OpenAI client so importing this module does not require
# OPENAI_API_KEY during test collection or local-only workflows.
client = None


def _get_openai_client():
    """Return a cached OpenAI client or create one when configuration is present."""
    global client

    if client is not None:
        return client

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required to call the OpenAI chat backend.")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return client

def call_openai_chat(messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens=512, retries=3) -> str:
    """
    Call OpenAI chat completion with retry logic and error handling.
    """
    model = model or settings.DEFAULT_MODEL
    active_client = _get_openai_client()
    
    for attempt in range(retries):
        try:
            response = active_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"OpenAI API call failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

def call_vllm_chat(messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens=512, retries=3) -> str:
    """
    Call a vLLM OpenAI-compatible server hosted at VLLM_BASE_URL with retry logic.
    """
    base = settings.VLLM_BASE_URL
    if not base:
        raise RuntimeError("VLLM_BASE_URL not configured")
    
    payload = {"model": model or settings.DEFAULT_MODEL, "messages": messages, "max_tokens": max_tokens}
    
    for attempt in range(retries):
        try:
            resp = requests.post(f"{base}/chat/completions", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"vLLM API call failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

def llm_chat(messages: List[Dict[str, str]], **kwargs) -> str:
    if settings.LLM_PROVIDER == "vllm":
        return call_vllm_chat(messages, **kwargs)
    return call_openai_chat(messages, **kwargs)

# Simple pgvector helper (SQLAlchemy)
# Only create engine if DATABASE_URL is provided and dependencies are available
engine = None
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    
    if settings.DATABASE_URL:
        engine = create_engine(settings.DATABASE_URL, future=True)
except ImportError:
    # SQLAlchemy or database drivers not available
    engine = None

def upsert_vector(id: str, metadata: Dict[str, Any], vector: List[float], retries=3):
    """
    Upsert into documents (id text primary key, content text, embedding vector) with retry logic.
    """
    if not engine:
        logger.warning("Database engine not configured. Skipping vector upsert.")
        return
        
    for attempt in range(retries):
        try:
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
            return
        except Exception as e:
            logger.warning(f"Vector upsert failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

def nearest_neighbors(query_vector: List[float], top_k: int = 4, retries=3):
    """
    Example using pgvector cosine distance with retry logic. Assumes embedding column named 'embedding'.
    """
    if not engine:
        logger.warning("Database engine not configured. Cannot perform vector search.")
        return []
        
    for attempt in range(retries):
        try:
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
        except Exception as e:
            logger.warning(f"Vector search failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
