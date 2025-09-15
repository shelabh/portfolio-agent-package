"""
Enhanced configuration system for portfolio-agent.

Provides safe-by-default settings with comprehensive environment variable support,
YAML configuration loading, and security-first defaults.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Enhanced settings with security-first defaults and comprehensive configuration options."""
    
    # ===== SECURITY & PRIVACY (Safe-by-default) =====
    LOCAL_ONLY: bool = Field(default=True, description="Only use local services, no external APIs")
    REDACT_PII: bool = Field(default=True, description="Automatically redact PII from content")
    AUTO_EMAIL: bool = Field(default=False, description="Allow automatic email sending")
    RETENTION_DAYS: int = Field(default=30, description="Data retention period in days")
    CONSENT_REQUIRED: bool = Field(default=True, description="Require explicit consent for data processing")
    
    # ===== LLM BACKENDS =====
    LLM_PROVIDER: str = Field(default="openai", description="LLM provider: openai, hf, bedrock, vllm")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, description="Hugging Face API key")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS access key")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS secret key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    VLLM_BASE_URL: Optional[str] = Field(default=None, description="vLLM server URL")
    DEFAULT_MODEL: str = Field(default="gpt-4o-mini", description="Default LLM model")
    
    # ===== EMBEDDINGS =====
    EMBEDDING_PROVIDER: str = Field(default="openai", description="Embedding provider: openai, hf, local")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Embedding model")
    EMBEDDING_DIMENSION: int = Field(default=1536, description="Embedding dimension")
    
    # ===== VECTOR STORES =====
    VECTOR_STORE: str = Field(default="faiss", description="Vector store: faiss, pinecone, opensearch, pgvector")
    FAISS_INDEX_PATH: str = Field(default="./faiss_index", description="Path to FAISS index files")
    FAISS_INDEX_TYPE: str = Field(default="flat", description="FAISS index type: flat, ivf, hnsw")
    FAISS_METRIC: str = Field(default="cosine", description="FAISS distance metric: cosine, l2, ip")
    PINECONE_API_KEY: Optional[str] = Field(default=None, description="Pinecone API key")
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None, description="Pinecone environment")
    OPENSEARCH_URL: Optional[str] = Field(default=None, description="OpenSearch cluster URL")
    OPENSEARCH_USERNAME: Optional[str] = Field(default=None, description="OpenSearch username")
    OPENSEARCH_PASSWORD: Optional[str] = Field(default=None, description="OpenSearch password")
    
    # ===== DATABASE =====
    DATABASE_URL: Optional[str] = Field(default=None, description="Database connection URL")
    VECTOR_TABLE: str = Field(default="documents", description="Vector storage table name")
    
    # ===== INGESTION =====
    CHUNK_SIZE: int = Field(default=1000, description="Text chunk size for processing")
    CHUNK_OVERLAP: int = Field(default=200, description="Overlap between chunks")
    MAX_FILE_SIZE_MB: int = Field(default=10, description="Maximum file size in MB")
    SUPPORTED_FORMATS: List[str] = Field(default=["pdf", "txt", "md", "html", "json"], description="Supported file formats")
    
    # ===== PERSONA & PROMPTS =====
    PERSONA_PROMPT: str = Field(
        default="You are a professional portfolio assistant. Maintain a formal, concise tone. "
                "Cite sources when providing factual claims using [[source_id]] notation.",
        description="Default persona prompt"
    )
    RECRUITER_PROMPT: str = Field(
        default="You are a recruiter assistant helping evaluate candidates. "
                "Provide objective, professional assessments based on available information.",
        description="Recruiter agent prompt"
    )
    ASSISTANT_PROMPT: str = Field(
        default="You are a helpful personal assistant. Be friendly, efficient, and proactive.",
        description="Personal assistant prompt"
    )
    
    # ===== RAG PIPELINE =====
    TOP_K_RETRIEVAL: int = Field(default=10, description="Number of documents to retrieve")
    TOP_K_RERANK: int = Field(default=3, description="Number of documents to rerank")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, description="Minimum similarity threshold")
    INCLUDE_CITATIONS: bool = Field(default=True, description="Include source citations in responses")
    
    # ===== MEMORY & PERSISTENCE =====
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    CHECKPOINT_DIR: str = Field(default="./.agent_checkpoints", description="Checkpoint directory")
    MEMORY_TTL_HOURS: int = Field(default=24, description="Memory time-to-live in hours")
    
    # ===== TOOLS =====
    CALENDLY_API_KEY: Optional[str] = Field(default=None, description="Calendly API key")
    EMAIL_FROM: Optional[str] = Field(default=None, description="Default email sender")
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASS: Optional[str] = Field(default=None, description="SMTP password")
    
    # ===== FINE-TUNING =====
    FINE_TUNE_ENABLED: bool = Field(default=False, description="Enable fine-tuning features")
    LORA_RANK: int = Field(default=16, description="LoRA rank for fine-tuning")
    LORA_ALPHA: int = Field(default=32, description="LoRA alpha for fine-tuning")
    TRAINING_EPOCHS: int = Field(default=3, description="Number of training epochs")
    
    # ===== LOGGING & MONITORING =====
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENABLE_AUDIT_LOG: bool = Field(default=True, description="Enable audit logging")
    METRICS_ENABLED: bool = Field(default=False, description="Enable metrics collection")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    @validator('LOCAL_ONLY', pre=True)
    def validate_local_only(cls, v):
        """Ensure LOCAL_ONLY is properly set based on environment."""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    @validator('REDACT_PII', pre=True)
    def validate_redact_pii(cls, v):
        """Ensure REDACT_PII is properly set."""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    @classmethod
    def load_from_yaml(cls, yaml_path: str) -> 'Settings':
        """Load settings from YAML file."""
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f"YAML config file not found: {yaml_path}")
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Override environment variables with YAML values
        for key, value in config_data.items():
            if key.upper() in os.environ:
                continue  # Environment variables take precedence
            os.environ[key.upper()] = str(value)
        
        return cls()
    
    def get_safe_config(self) -> Dict[str, Any]:
        """Get configuration dict with sensitive values redacted."""
        config_dict = self.dict()
        sensitive_keys = [
            'OPENAI_API_KEY', 'HUGGINGFACE_API_KEY', 'AWS_ACCESS_KEY_ID', 
            'AWS_SECRET_ACCESS_KEY', 'PINECONE_API_KEY', 'OPENSEARCH_PASSWORD',
            'SMTP_PASS', 'CALENDLY_API_KEY'
        ]
        
        for key in sensitive_keys:
            if key in config_dict and config_dict[key]:
                config_dict[key] = "***REDACTED***"
        
        return config_dict
    
    def validate_required_config(self) -> List[str]:
        """Validate that required configuration is present."""
        errors = []
        
        # Check LLM configuration
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        
        if self.LLM_PROVIDER == "hf" and not self.HUGGINGFACE_API_KEY:
            errors.append("HUGGINGFACE_API_KEY is required when LLM_PROVIDER=hf")
        
        # Check vector store configuration
        if self.VECTOR_STORE == "pinecone" and not self.PINECONE_API_KEY:
            errors.append("PINECONE_API_KEY is required when VECTOR_STORE=pinecone")
        
        if self.VECTOR_STORE == "opensearch" and not self.OPENSEARCH_URL:
            errors.append("OPENSEARCH_URL is required when VECTOR_STORE=opensearch")
        
        # Check database configuration for pgvector
        if self.VECTOR_STORE == "pgvector" and not self.DATABASE_URL:
            errors.append("DATABASE_URL is required when VECTOR_STORE=pgvector")
        
        return errors


# Global settings instance
settings = Settings()

# Validate configuration on import
config_errors = settings.validate_required_config()
if config_errors and not settings.LOCAL_ONLY:
    import warnings
    for error in config_errors:
        warnings.warn(f"Configuration warning: {error}", UserWarning)
