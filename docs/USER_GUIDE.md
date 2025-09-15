# Portfolio Agent User Guide

This comprehensive user guide will help you get started with the Portfolio Agent and make the most of its features.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Getting Started

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/portfolio-agent-package.git
   cd portfolio-agent-package
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Set up environment variables:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export HUGGINGFACE_API_KEY="your-huggingface-api-key"  # Optional
   ```

### Quick Start

1. **Run the portfolio demo:**
   ```bash
   cd EXAMPLES/portfolio_demo
   python app.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:8000` to access the web interface.

3. **Try a query:**
   Ask questions like "What are your technical skills?" or "Tell me about your recent projects."

## Basic Usage

### Web Interface

The web interface provides an intuitive way to interact with your portfolio agent:

1. **Home Page**: Overview of features and capabilities
2. **Demo Section**: Interactive chat interface
3. **Document Upload**: Add new documents to your knowledge base
4. **Settings**: Configure your agent's behavior

### Command Line Interface

Use the CLI for programmatic access:

```bash
# Start the server
portfolio-agent --serve

# Run a query
portfolio-agent --query "What are your skills?"

# Upload a document
portfolio-agent --upload resume.pdf
```

### Python API

```python
from portfolio_agent import PortfolioAgent

# Initialize the agent
agent = PortfolioAgent()

# Send a query
response = agent.query("What are your main technical skills?")
print(response.response)

# Upload a document
result = agent.upload_document("resume.pdf")
print(f"Document uploaded: {result.document_id}")
```

## Advanced Features

### Multi-Agent Architecture

The Portfolio Agent uses a sophisticated multi-agent system:

- **Router Agent**: Classifies queries and routes to appropriate agents
- **Retriever Agent**: Finds relevant documents from your knowledge base
- **Reranker Agent**: Ranks retrieved documents by relevance
- **Persona Agent**: Generates responses with your personal voice
- **Critic Agent**: Reviews and improves response quality
- **Memory Manager**: Maintains conversation context

### Document Ingestion

Support for various document types:

#### Resume/PDF Documents
```python
from portfolio_agent.ingestion import ResumeIngestor

ingestor = ResumeIngestor()
document = await ingestor.ingest_file("resume.pdf")
```

#### GitHub Repositories
```python
from portfolio_agent.ingestion import GitHubIngestor

ingestor = GitHubIngestor()
document = await ingestor.ingest("https://github.com/username/repo")
```

#### Websites
```python
from portfolio_agent.ingestion import WebsiteIngestor

ingestor = WebsiteIngestor()
document = await ingestor.ingest("https://yourwebsite.com")
```

#### Generic Files
```python
from portfolio_agent.ingestion import GenericIngestor

ingestor = GenericIngestor()
document = await ingestor.ingest_file("document.txt")
```

### Vector Stores

Choose from multiple vector store options:

#### FAISS (Local)
```python
from portfolio_agent.vector_stores import FAISSVectorStore

store = FAISSVectorStore()
store.add_documents(documents)
results = store.search(query_vector, k=5)
```

#### Pinecone (Cloud)
```python
from portfolio_agent.vector_stores import PineconeVectorStore

store = PineconeVectorStore(
    api_key="your-pinecone-api-key",
    environment="your-environment"
)
```

#### OpenSearch
```python
from portfolio_agent.vector_stores import OpenSearchVectorStore

store = OpenSearchVectorStore(
    host="localhost",
    port=9200
)
```

### Embedding Providers

#### OpenAI Embeddings
```python
from portfolio_agent.embeddings import OpenAIEmbedder

embedder = OpenAIEmbedder(api_key="your-openai-api-key")
embeddings = await embedder.embed_texts(["Hello world"])
```

#### Hugging Face Embeddings
```python
from portfolio_agent.embeddings import HuggingFaceEmbedder

embedder = HuggingFaceEmbedder(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = await embedder.embed_texts(["Hello world"])
```

#### Local Embeddings
```python
from portfolio_agent.embeddings import LocalEmbedder

embedder = LocalEmbedder(model_path="./models/embedding-model")
embeddings = await embedder.embed_texts(["Hello world"])
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM and embeddings | Required |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | Optional |
| `PINECONE_API_KEY` | Pinecone API key | Optional |
| `REDACT_PII` | Enable PII redaction | `true` |
| `ENABLE_RATE_LIMITING` | Enable rate limiting | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Configuration File

Create a `config.yaml` file:

```yaml
# Server Configuration
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

# RAG Pipeline Configuration
rag:
  llm:
    provider: "openai"
    model: "gpt-3.5-turbo"
    temperature: 0.7
    max_tokens: 1000
  
  embeddings:
    provider: "openai"
    model: "text-embedding-3-small"
  
  vector_store:
    provider: "faiss"
    index_path: "./data/faiss_index"
  
  retrieval:
    top_k: 5
    similarity_threshold: 0.7
    rerank: true

# Security Configuration
security:
  enable_pii_redaction: true
  enable_rate_limiting: true
  rate_limit_requests: 100
  rate_limit_window: 3600
```

### Custom Prompts

Customize the agent's behavior with custom prompts:

```python
from portfolio_agent.finetuning import PromptTemplate

# Create a custom prompt template
template = PromptTemplate(
    name="portfolio_response",
    template="""
    You are a professional portfolio assistant. 
    Answer questions about {user_name}'s skills, experience, and projects.
    
    Context: {context}
    Question: {question}
    
    Provide a helpful, professional response that showcases {user_name}'s expertise.
    """,
    variables=["user_name", "context", "question"]
)

# Use the template
response = template.format(
    user_name="John Doe",
    context="Software engineer with 5 years experience",
    question="What are your main skills?"
)
```

## Troubleshooting

### Common Issues

#### 1. API Key Errors
**Problem**: "Invalid API key" or "Authentication failed"
**Solution**: 
- Verify your API key is correct
- Check that the API key has sufficient credits
- Ensure the environment variable is set correctly

#### 2. Document Upload Failures
**Problem**: Documents fail to upload or process
**Solution**:
- Check file format is supported (PDF, TXT, DOCX, MD)
- Verify file size is under the limit (10MB)
- Ensure the file is not corrupted

#### 3. Poor Response Quality
**Problem**: Responses are irrelevant or low quality
**Solution**:
- Add more relevant documents to your knowledge base
- Adjust the similarity threshold in configuration
- Enable reranking for better results
- Fine-tune the prompts for your use case

#### 4. Slow Performance
**Problem**: Queries take too long to process
**Solution**:
- Use a faster embedding model
- Optimize your vector store configuration
- Enable caching for frequently asked questions
- Consider using a more powerful server

#### 5. Memory Issues
**Problem**: High memory usage or out of memory errors
**Solution**:
- Reduce the number of documents in your knowledge base
- Use a more efficient vector store (e.g., FAISS)
- Implement document chunking to reduce memory usage
- Monitor and optimize your system resources

### Debug Mode

Enable debug mode for detailed logging:

```bash
export LOG_LEVEL=DEBUG
portfolio-agent --serve
```

### Health Checks

Monitor your agent's health:

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check readiness
curl http://localhost:8000/api/v1/ready
```

## Best Practices

### Document Organization

1. **Use descriptive filenames**: `john_doe_resume_2024.pdf`
2. **Add metadata**: Include tags, categories, and descriptions
3. **Keep documents updated**: Regularly update your portfolio materials
4. **Organize by type**: Separate resumes, projects, and other documents

### Query Optimization

1. **Be specific**: "What Python frameworks have you used?" vs "What do you know?"
2. **Use context**: Reference specific projects or experiences
3. **Ask follow-up questions**: Build on previous responses
4. **Test different phrasings**: Try various ways to ask the same question

### Security

1. **Enable PII redaction**: Protect sensitive information
2. **Use rate limiting**: Prevent abuse and ensure fair usage
3. **Regular updates**: Keep dependencies and models updated
4. **Monitor usage**: Track API usage and costs

### Performance

1. **Optimize embeddings**: Use appropriate embedding models for your use case
2. **Cache frequently**: Cache common queries and responses
3. **Batch operations**: Process multiple documents together
4. **Monitor metrics**: Track performance and optimize bottlenecks

### Maintenance

1. **Regular backups**: Backup your vector store and configuration
2. **Update documents**: Keep your knowledge base current
3. **Monitor logs**: Check logs for errors and performance issues
4. **Test regularly**: Verify functionality after updates

## Examples

### Personal Portfolio

```python
from portfolio_agent import PortfolioAgent

# Initialize agent
agent = PortfolioAgent()

# Add your resume
agent.upload_document("resume.pdf")

# Add project documentation
agent.upload_document("project_readme.md")

# Add GitHub repositories
agent.ingest_github("https://github.com/yourusername/yourrepo")

# Query your portfolio
response = agent.query("What are my strongest technical skills?")
print(response.response)
```

### Team Knowledge Base

```python
from portfolio_agent import PortfolioAgent

# Initialize agent for team use
agent = PortfolioAgent(
    config={
        "rag": {
            "llm": {"model": "gpt-4"},
            "retrieval": {"top_k": 10}
        }
    }
)

# Add team documents
agent.upload_document("team_handbook.pdf")
agent.upload_document("project_guidelines.md")
agent.ingest_website("https://company-docs.com")

# Team queries
response = agent.query("What is our code review process?")
print(response.response)
```

### Recruiter Tool

```python
from portfolio_agent import PortfolioAgent

# Initialize agent for recruitment
agent = PortfolioAgent(
    config={
        "rag": {
            "llm": {"model": "gpt-4"},
            "retrieval": {"similarity_threshold": 0.8}
        }
    }
)

# Add candidate materials
agent.upload_document("candidate_resume.pdf")
agent.ingest_github("https://github.com/candidate/repo")

# Evaluate candidate
response = agent.query("How well does this candidate match our Python developer role?")
print(response.response)
```

## Support

For additional help:

1. **Documentation**: Check the main documentation and API reference
2. **Examples**: Review the example scripts and demos
3. **Community**: Join our community forum for discussions
4. **Issues**: Report bugs and request features on GitHub
5. **Contact**: Reach out to the development team for support

## Changelog

### Version 1.0.0
- Initial release
- Multi-agent RAG architecture
- Multiple vector store support
- Security and privacy features
- Web interface and API
- Comprehensive documentation
