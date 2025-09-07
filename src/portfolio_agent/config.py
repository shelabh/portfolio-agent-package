# ai-agent/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model / LLM
    LLM_PROVIDER: str = "openai"  # 'openai' or 'vllm'
    OPENAI_API_KEY: str | None = None
    VLLM_BASE_URL: str | None = None  # e.g. "http://localhost:8000/v1"
    DEFAULT_MODEL: str = "gpt-4o-mini"  # change as needed

    # Embeddings
    EMBEDDING_PROVIDER: str = "openai"  # or 'local'
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # or bge-m3

    # Postgres / pgvector
    DATABASE_URL: str  # e.g. postgres://user:pass@host:port/db
    VECTOR_TABLE: str = "documents"

    # Persona
    PERSONA_PROMPT: str = (
        "You are Shelabh's professional portfolio assistant. Maintain a formal, concise tone. "
        "Cite sources when providing factual claims using [[source_id]] notation."
    )

    # LangGraph
    CHECKPOINT_DIR: str = "./.agent_checkpoints"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
