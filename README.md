# Portfolio Agent

A production-ready RAG (Retrieval-Augmented Generation) pipeline with multi-agent architecture, memory management, and tool integration. Built with security-first principles and enterprise-grade features.

## 🚀 Features

### Core Capabilities
- **Multi-Agent Architecture**: Sophisticated pipeline with specialized agents for routing, retrieval, reranking, response generation, and quality control
- **Memory Management**: Enhanced user context and conversation history tracking with Redis persistence
- **Tool Integration**: Built-in support for Calendly scheduling, email drafting, and note-taking
- **Quality Assurance**: Built-in critic agent to prevent hallucinations and ensure factual accuracy

### Security & Privacy
- **Safe-by-Default**: LOCAL_ONLY mode, automatic PII redaction, consent management
- **Data Protection**: Encryption at rest and in transit, access controls, audit logging
- **Compliance Ready**: GDPR, CCPA, SOC 2 compliance features
- **Secret Management**: Secure handling of API keys and sensitive data

### Vector Search & Embeddings
- **Multiple Vector Stores**: FAISS (local), Pinecone (cloud), OpenSearch (enterprise), pgvector
- **Embedding Providers**: OpenAI, Hugging Face, local sentence-transformers
- **Advanced RAG**: Multi-stage retrieval, reranking, citation tracking
- **Fine-tuning**: PEFT/LoRA examples for custom model training

### LLM Backends
- **OpenAI**: GPT models via OpenAI API
- **Hugging Face**: Local and hosted HF models
- **AWS Bedrock**: Enterprise-grade AI services
- **vLLM**: High-performance local serving

### Document Processing
- **Multi-format Support**: PDF, TXT, MD, HTML, JSON, DOCX
- **Smart Ingestion**: GitHub repos, websites, resumes, generic files
- **PII Redaction**: Automatic detection and redaction of sensitive information
- **Chunking**: Configurable text chunking with overlap

## 📦 Installation

### Basic Installation

```bash
pip install portfolio-agent
```

### With Optional Dependencies

```bash
# For all features
pip install portfolio-agent[all]

# Or install specific extras
pip install portfolio-agent[llm,vector,embeddings,finetune,documents,postgres]
```

### Development Installation

```bash
git clone https://github.com/shelabhtyagi/portfolio-agent.git
cd portfolio-agent
pip install -e ".[all]"
```

## 🚀 Quick Start

### 1. Basic Usage

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

### 2. With Configuration

```python
import os
from portfolio_agent import build_graph, RedisCheckpointer

# Set environment variables
os.environ["OPENAI_API_KEY"] = "your-api-key"
os.environ["LOCAL_ONLY"] = "false"  # Enable external APIs
os.environ["REDACT_PII"] = "true"   # Automatic PII redaction

# Build with persistence
checkpointer = RedisCheckpointer()
graph = build_graph(checkpointer=checkpointer)

# Run with user context
state = MessagesState()
state.messages = [{"role": "user", "content": "Tell me about your experience"}]
state.user_id = "user123"  # For memory management

result = graph.run(state)
```

### 3. FastAPI Server

```python
from portfolio_agent import create_demo_app
import uvicorn

app = create_demo_app()
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Command Line Interface

```bash
# Set required environment variables
export OPENAI_API_KEY="your-api-key"
export DATABASE_URL="postgresql://user:pass@localhost/db"

# Run a single query
portfolio-agent --query "What are your skills?"

# Run in interactive mode
portfolio-agent --interactive

# With user context for memory
portfolio-agent --query "What did we discuss before?" --user-id user123
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

## 🏗️ Architecture

### Modular Design

The Portfolio Agent follows a modular, extensible architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingestors     │    │   Embeddings    │    │  Vector Stores  │
│ • GitHub        │───▶│ • OpenAI        │───▶│ • FAISS         │
│ • Resume PDF    │    │ • Hugging Face  │    │ • Pinecone      │
│ • Website HTML  │    │ • Local Models  │    │ • OpenSearch    │
│ • Generic Files │    │                 │    │ • pgvector      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Pipeline                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Retriever  │─▶│  Reranker   │─▶│  Response   │            │
│  │             │  │             │  │  Pipeline   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Backends  │    │    Agents       │    │   Persistence   │
│ • OpenAI        │    │ • Persona       │    │ • Redis         │
│ • Hugging Face  │    │ • Recruiter     │    │ • SQLite        │
│ • AWS Bedrock   │    │ • Assistant     │    │ • Memory        │
│ • vLLM          │    │ • Tools         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

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

## 📚 Examples & Demos

### Portfolio Demo

```bash
cd EXAMPLES/portfolio_demo
./start_demo.sh
```

Features:
- Personal portfolio assistant
- Resume and GitHub integration
- Professional Q&A with citations
- Interactive web interface

### Recruiter Demo

```bash
cd EXAMPLES/recruiter_demo
# Coming soon in Week 4
```

Features:
- Candidate evaluation
- Skills matching
- Interview scheduling
- Recruitment workflows

### Internal KB Demo

```bash
cd EXAMPLES/internal_kb_demo
# Coming soon in Week 4
```

Features:
- Document ingestion
- Knowledge search
- Team collaboration
- Access controls

## 📖 Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get up and running quickly
- [Architecture Guide](docs/ARCHITECTURE.md) - Detailed system architecture
- [Security Guide](docs/SECURITY.md) - Security best practices
- [Privacy Policy](docs/PRIVACY.md) - Data protection and privacy

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