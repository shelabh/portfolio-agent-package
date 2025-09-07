# Portfolio Agent

A production-ready RAG (Retrieval-Augmented Generation) pipeline built with LangGraph and Redis persistence. This package provides a sophisticated multi-agent system for building professional AI assistants with memory, tool integration, and quality assurance.

## Features

- **Multi-Agent Architecture**: Sophisticated pipeline with specialized agents for routing, retrieval, reranking, response generation, and quality control
- **Memory Management**: Enhanced user context and conversation history tracking
- **Tool Integration**: Built-in support for Calendly scheduling, email drafting, and note-taking
- **Quality Assurance**: Built-in critic agent to prevent hallucinations and ensure factual accuracy
- **Redis Persistence**: Production-ready state management with Redis checkpointer
- **Flexible LLM Support**: Compatible with OpenAI and vLLM providers
- **Vector Search**: pgvector integration for efficient document retrieval
- **Error Handling**: Robust retry mechanisms and graceful error recovery

## Installation

### Basic Installation

```bash
pip install portfolio-agent
```

### With Optional Dependencies

```bash
# For LLM functionality
pip install portfolio-agent[llm]

# For vector database support
pip install portfolio-agent[vector]

# For PostgreSQL support
pip install portfolio-agent[postgres]

# All optional dependencies
pip install portfolio-agent[llm,vector,postgres]
```

## Quick Start

### Basic Usage

```python
from portfolio_agent import build_graph, RedisCheckpointer

# Build the graph
graph = build_graph()

# Or with Redis persistence
checkpointer = RedisCheckpointer(redis_url="redis://localhost:6379/0")
graph = build_graph(checkpointer=checkpointer)

# Run the agent
from langgraph.graph.message import MessagesState

state = MessagesState()
state.messages = [{"role": "user", "content": "What are your skills?"}]

result = graph.run(state)
print(result.messages[-1]["content"])
```

### With Configuration

```python
import os
from portfolio_agent import build_graph, RedisCheckpointer

# Set environment variables
os.environ["OPENAI_API_KEY"] = "your-api-key"
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

# Build with persistence
checkpointer = RedisCheckpointer()
graph = build_graph(checkpointer=checkpointer)

# Run with user context
state = MessagesState()
state.messages = [{"role": "user", "content": "Tell me about your experience"}]
state.user_id = "user123"  # For memory management

result = graph.run(state)
```

## Configuration

The agent uses environment variables for configuration. Create a `.env` file or set these variables:

### Required Configuration

```bash
# Database connection for vector storage
DATABASE_URL=postgresql://user:password@localhost:5432/database

# LLM Provider
OPENAI_API_KEY=your-openai-api-key
```

### Optional Configuration

```bash
# LLM Settings
LLM_PROVIDER=openai  # or 'vllm'
DEFAULT_MODEL=gpt-4o-mini
VLLM_BASE_URL=http://localhost:8000/v1  # for vLLM

# Embeddings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

# Database
VECTOR_TABLE=documents

# Persona
PERSONA_PROMPT="You are a professional assistant. Maintain a formal, concise tone."

# Tools
CALENDLY_API_KEY=your-calendly-key
EMAIL_FROM=assistant@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=username
SMTP_PASS=password

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Architecture

### Agent Pipeline

The system implements a sophisticated multi-agent pipeline:

1. **Memory Manager**: Fetches user context and conversation history
2. **Router**: Determines the appropriate response path (RAG, tools, or direct)
3. **Retriever**: Searches for relevant documents using vector similarity
4. **Reranker**: Reranks retrieved documents by relevance
5. **Persona**: Generates formal responses with citations
6. **Critic**: Validates responses for accuracy and prevents hallucinations
7. **Notes**: Persists interaction summaries for future reference

### Tool Integration

The system includes built-in tools:

- **Calendly Agent**: Creates scheduling links and manages availability
- **Email Agent**: Drafts and sends professional emails
- **Notes Agent**: Saves interaction summaries to vector database

### Conditional Routing

The router intelligently determines the response path:

- **RAG Path**: For questions requiring document retrieval
- **Tool Path**: For scheduling, email, or note-taking requests
- **Direct Path**: For simple conversational responses

## Advanced Usage

### Custom Persona

```python
import os
os.environ["PERSONA_PROMPT"] = "You are a specialized technical consultant. Provide detailed, technical responses with code examples when appropriate."
```

### Memory Management

```python
# The system automatically tracks user interactions
state = MessagesState()
state.messages = [{"role": "user", "content": "What did we discuss about Python?"}]
state.user_id = "user123"  # Enables memory retrieval

result = graph.run(state)
```

### Tool Usage

```python
# Scheduling
state = MessagesState()
state.messages = [{"role": "user", "content": "Schedule a meeting with me"}]
result = graph.run(state)

# Email drafting
state = MessagesState()
state.messages = [{"role": "user", "content": "Draft an email to a recruiter about my Python skills"}]
result = graph.run(state)

# Email sending (requires SMTP configuration)
state = MessagesState()
state.messages = [{"role": "user", "content": "Send email to recruiter@company.com"}]
state.allow_send = True
state.email_to = "recruiter@company.com"
state.email_subject = "Job Application"
result = graph.run(state)
```

## Database Setup

### PostgreSQL with pgvector

```sql
-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the documents table
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(1536)  -- Adjust dimension based on your embedding model
);

-- Create an index for efficient vector search
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

## Error Handling

The system includes comprehensive error handling:

- **Retry Logic**: Automatic retries with exponential backoff for API calls
- **Graceful Degradation**: Fallback responses when services are unavailable
- **Validation**: Built-in critic agent prevents hallucinated responses
- **Logging**: Comprehensive logging for debugging and monitoring

## Testing

Run the test suite:

```bash
pytest tests/
```

The test suite includes:
- Unit tests for all agents
- Integration tests for the complete pipeline
- Tool functionality tests
- Error handling tests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the documentation
- Review the test examples
- Open an issue on GitHub
