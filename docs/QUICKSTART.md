# Quick Start Guide

Get up and running with Portfolio Agent in minutes!

## Prerequisites

- Python 3.12 or higher
- pip or Poetry package manager
- (Optional) Redis server for persistence
- (Optional) PostgreSQL with pgvector for vector storage

## Installation

### Option 1: Basic Installation

```bash
pip install portfolio-agent
```

### Option 2: With Optional Dependencies

```bash
# For all features
pip install portfolio-agent[all]

# Or install specific extras
pip install portfolio-agent[llm,vector,embeddings]
```

### Option 3: Development Installation

```bash
git clone https://github.com/shelabhtyagi/portfolio-agent.git
cd portfolio-agent
pip install -e ".[all]"
```

## Configuration

### 1. Environment Variables

Create a `.env` file in your project directory:

```bash
# Required for OpenAI
OPENAI_API_KEY=your-openai-api-key

# Optional: Database for vector storage
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Optional: Redis for persistence
REDIS_URL=redis://localhost:6379/0

# Security settings (recommended)
LOCAL_ONLY=false  # Set to true for local-only mode
REDACT_PII=true   # Automatic PII redaction
```

### 2. YAML Configuration

Create a `config.yaml` file:

```yaml
# Basic configuration
LLM_PROVIDER: "openai"
EMBEDDING_PROVIDER: "openai"
VECTOR_STORE: "faiss"  # or "pinecone", "opensearch"

# Security settings
LOCAL_ONLY: false
REDACT_PII: true
AUTO_EMAIL: false

# RAG settings
TOP_K_RETRIEVAL: 10
TOP_K_RERANK: 3
SIMILARITY_THRESHOLD: 0.7
```

## Basic Usage

### 1. Simple Python Script

```python
from portfolio_agent import build_graph, RedisCheckpointer

# Build the agent graph
graph = build_graph()

# Run a query
from langgraph.graph.message import MessagesState

state = MessagesState()
state.messages = [{"role": "user", "content": "What are your skills?"}]

result = graph.run(state)
print(result.messages[-1]["content"])
```

### 2. Command Line Interface

```bash
# Single query
portfolio-agent --query "What are your skills?"

# Interactive mode
portfolio-agent --interactive

# With user context for memory
portfolio-agent --query "What did we discuss before?" --user-id user123
```

### 3. FastAPI Server

```python
from portfolio_agent import create_demo_app
import uvicorn

app = create_demo_app()
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Adding Your Data

### 1. Resume/PDF Documents

```python
from portfolio_agent.ingestion import ResumeIngestor

ingestor = ResumeIngestor()
chunks = ingestor.ingest("path/to/resume.pdf")
```

### 2. GitHub Repositories

```python
from portfolio_agent.ingestion import GitHubIngestor

ingestor = GitHubIngestor()
chunks = ingestor.ingest("https://github.com/username/repo")
```

### 3. Website Content

```python
from portfolio_agent.ingestion import WebsiteIngestor

ingestor = WebsiteIngestor()
chunks = ingestor.ingest("https://example.com")
```

### 4. Generic Files

```python
from portfolio_agent.ingestion import GenericIngestor

ingestor = GenericIngestor()
chunks = ingestor.ingest("path/to/document.txt")
```

## Vector Storage Setup

### Option 1: Local FAISS (Default)

No additional setup required. FAISS will create local index files.

### Option 2: Pinecone (Cloud)

```bash
# Install Pinecone
pip install portfolio-agent[vector]

# Set environment variables
export PINECONE_API_KEY=your-pinecone-key
export PINECONE_ENVIRONMENT=your-environment
```

```python
# Configure in code
from portfolio_agent.config import settings
settings.VECTOR_STORE = "pinecone"
```

### Option 3: PostgreSQL with pgvector

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(1536)
);

-- Create vector index
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

## Demo Examples

### 1. Portfolio Demo

```bash
cd EXAMPLES/portfolio_demo
./start_demo.sh
```

This will:
- Set up a virtual environment
- Install dependencies
- Create sample data
- Start a demo server at http://localhost:8000

### 2. Recruiter Demo

```bash
cd EXAMPLES/recruiter_demo
# Coming soon in Week 4
```

### 3. Internal KB Demo

```bash
cd EXAMPLES/internal_kb_demo
# Coming soon in Week 4
```

## Advanced Configuration

### Custom Persona

```python
import os
os.environ["PERSONA_PROMPT"] = """
You are a specialized technical consultant. 
Provide detailed, technical responses with code examples when appropriate.
Focus on best practices and industry standards.
"""
```

### Memory Management

```python
# Enable memory with user context
state = MessagesState()
state.messages = [{"role": "user", "content": "What did we discuss about Python?"}]
state.user_id = "user123"  # Enables memory retrieval

result = graph.run(state)
```

### Tool Integration

```python
# Scheduling
state = MessagesState()
state.messages = [{"role": "user", "content": "Schedule a meeting with me"}]
result = graph.run(state)

# Email drafting
state = MessagesState()
state.messages = [{"role": "user", "content": "Draft an email to a recruiter"}]
result = graph.run(state)
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Make sure you have the right dependencies
pip install portfolio-agent[all]

# Check Python version
python --version  # Should be 3.12+
```

#### 2. API Key Issues

```bash
# Check environment variables
echo $OPENAI_API_KEY

# Test API connection
python -c "import openai; print('API key valid')"
```

#### 3. Vector Store Issues

```bash
# For FAISS, check file permissions
ls -la .faiss_index/

# For Pinecone, check API key and environment
echo $PINECONE_API_KEY
echo $PINECONE_ENVIRONMENT
```

#### 4. Memory Issues

```bash
# Check Redis connection
redis-cli ping

# Check Redis URL
echo $REDIS_URL
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
portfolio-agent --query "test" --verbose
```

### Performance Issues

```python
# Reduce chunk size for large documents
from portfolio_agent.config import settings
settings.CHUNK_SIZE = 500
settings.CHUNK_OVERLAP = 100

# Use local models for faster processing
settings.EMBEDDING_PROVIDER = "local"
settings.LLM_PROVIDER = "local"
```

## Next Steps

### 1. Explore Examples

- Check out the `EXAMPLES/` directory
- Run the portfolio demo
- Experiment with different configurations

### 2. Read Documentation

- [Architecture Guide](ARCHITECTURE.md)
- [Security Guide](SECURITY.md)
- [Privacy Policy](PRIVACY.md)

### 3. Join the Community

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas
- Contributing: Help improve the project

### 4. Advanced Features

- Fine-tuning with LoRA
- Custom embeddings
- Multi-modal support
- Enterprise integrations

## Support

### Getting Help

1. **Documentation**: Check the docs first
2. **Examples**: Look at working examples
3. **Issues**: Search existing GitHub issues
4. **Community**: Ask in discussions

### Reporting Issues

When reporting issues, please include:

- Python version
- Package version
- Error messages
- Steps to reproduce
- Configuration (redact secrets)

### Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Ready to build amazing AI assistants? Let's get started!** 🚀
