# Portfolio Agent Architecture

## Overview

The Portfolio Agent is a production-ready RAG (Retrieval-Augmented Generation) pipeline built with a modular, extensible architecture. It provides a comprehensive solution for building AI assistants with memory, tool integration, and quality assurance.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingestors     │    │   Embeddings    │    │  Vector Stores  │
│                 │    │                 │    │                 │
│ • GitHub        │───▶│ • OpenAI        │───▶│ • FAISS         │
│ • Resume PDF    │    │ • Hugging Face  │    │ • Pinecone      │
│ • Website HTML  │    │ • Local Models  │    │ • OpenSearch    │
│ • Generic Files │    │                 │    │ • pgvector      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Pipeline                                │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Retriever  │─▶│  Reranker   │─▶│  Response   │            │
│  │             │  │             │  │  Pipeline   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Backends  │    │    Agents       │    │   Persistence   │
│                 │    │                 │    │                 │
│ • OpenAI        │    │ • Persona       │    │ • Redis         │
│ • Hugging Face  │    │ • Recruiter     │    │ • SQLite        │
│ • AWS Bedrock   │    │ • Assistant     │    │ • Memory        │
│ • vLLM          │    │ • Tools         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Ingestion Layer (`ingestion/`)

Responsible for ingesting content from various sources:

- **GitHubIngestor**: Fetches repository data, README files, and code
- **ResumeIngestor**: Processes PDF resumes with PII redaction
- **WebsiteIngestor**: Scrapes and processes web content
- **GenericIngestor**: Handles various file formats (PDF, TXT, MD, HTML, JSON)

**Key Features:**
- Automatic PII redaction
- Chunking with configurable overlap
- Metadata extraction
- Format validation

### 2. Embeddings Layer (`embeddings/`)

Provides unified interface for different embedding providers:

- **OpenAIEmbedder**: Uses OpenAI's embedding models
- **HuggingFaceEmbedder**: Local sentence-transformers models
- **Custom Embedders**: Extensible for other providers

**Key Features:**
- Batch processing
- Caching support
- Dimension validation
- Provider abstraction

### 3. Vector Stores (`vectorstores/`)

Manages vector storage and retrieval:

- **FAISSStore**: Local, fast vector search
- **PineconeStore**: Managed cloud vector database
- **OpenSearchStore**: Enterprise-grade search
- **pgvector**: PostgreSQL with vector extensions

**Key Features:**
- Namespace support
- ACL metadata
- Batch operations
- Similarity search

### 4. LLM Backends (`llm_backends/`)

Unified interface for different LLM providers:

- **OpenAIClient**: GPT models via OpenAI API
- **HuggingFaceClient**: Local and hosted HF models
- **BedrockClient**: AWS Bedrock integration
- **vLLMClient**: High-performance local serving

**Key Features:**
- Streaming support
- Token counting
- Error handling
- Provider abstraction

### 5. RAG Pipeline (`rag/`)

Core retrieval and generation logic:

- **Retriever**: Vector similarity search
- **Reranker**: Relevance-based reranking
- **PromptTemplates**: Configurable prompt management
- **ResponsePipeline**: Citation and quality control

**Key Features:**
- Multi-stage retrieval
- Citation tracking
- Quality validation
- Response formatting

### 6. Agent System (`agents/`)

Specialized agents for different use cases:

- **PersonaAgent**: Professional portfolio assistant
- **RecruiterAgent**: Candidate evaluation and assessment
- **PersonalAssistant**: General-purpose assistant
- **Tool Agents**: Calendly, email, notes integration

**Key Features:**
- Memory management
- Context awareness
- Tool integration
- Quality assurance

### 7. Persistence (`persistence/`)

Data storage and memory management:

- **RedisMemory**: Conversation and context storage
- **SQLiteStore**: Local data persistence
- **Checkpointing**: State management for agents

**Key Features:**
- TTL support
- Compression
- Backup/restore
- Query optimization

## Data Flow

### 1. Ingestion Flow
```
Source → Ingestor → Chunking → PII Redaction → Metadata → Storage
```

### 2. Query Flow
```
Query → Embedding → Vector Search → Reranking → LLM → Response
```

### 3. Agent Flow
```
Input → Memory → Router → [RAG|Tools|Direct] → Persona → Critic → Output
```

## Security & Privacy

### Safe-by-Default Configuration
- `LOCAL_ONLY=true`: No external API calls by default
- `REDACT_PII=true`: Automatic PII detection and redaction
- `AUTO_EMAIL=false`: Manual approval for email sending
- `CONSENT_REQUIRED=true`: Explicit consent for data processing

### Data Protection
- PII redaction pipeline
- Retention controls
- Access logging
- Encryption at rest

### Compliance
- GDPR-ready data handling
- Configurable retention periods
- Audit trail support
- Consent management

## Scalability

### Horizontal Scaling
- Stateless agent design
- Redis-based session management
- Load balancer ready
- Container-friendly

### Performance Optimization
- Vector index optimization
- Embedding caching
- Batch processing
- Async operations

## Extensibility

### Plugin Architecture
- Modular component design
- Interface-based contracts
- Easy provider swapping
- Custom agent development

### Configuration
- YAML-based configuration
- Environment variable support
- Runtime configuration updates
- Validation and defaults

## Monitoring & Observability

### Logging
- Structured logging
- Audit trails
- Performance metrics
- Error tracking

### Health Checks
- Component health monitoring
- Dependency checks
- Resource utilization
- Alert integration

## Deployment Options

### Local Development
- Docker Compose setup
- Local vector stores
- Mock external services
- Development tools

### Production
- Kubernetes deployment
- Managed services
- Auto-scaling
- High availability

## Future Enhancements

### Planned Features
- Multi-modal support (images, audio)
- Advanced fine-tuning pipelines
- Real-time collaboration
- Enterprise SSO integration

### Research Areas
- Advanced reranking algorithms
- Multi-agent coordination
- Federated learning
- Privacy-preserving ML
