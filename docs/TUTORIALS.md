# Portfolio Agent Tutorials

This collection of tutorials will guide you through various use cases and advanced features of the Portfolio Agent.

## Table of Contents

1. [Getting Started Tutorial](#getting-started-tutorial)
2. [Building Your First Portfolio Agent](#building-your-first-portfolio-agent)
3. [Advanced Configuration](#advanced-configuration)
4. [Custom Prompts and Fine-tuning](#custom-prompts-and-fine-tuning)
5. [Security and Privacy](#security-and-privacy)
6. [Performance Optimization](#performance-optimization)
7. [Integration Examples](#integration-examples)

## Getting Started Tutorial

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Basic knowledge of Python

### Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/portfolio-agent-package.git
cd portfolio-agent-package

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Step 2: Basic Setup

```python
# basic_setup.py
import os
from portfolio_agent import PortfolioAgent

# Set your API key
os.environ['OPENAI_API_KEY'] = 'your-openai-api-key'

# Initialize the agent
agent = PortfolioAgent()

print("Portfolio Agent initialized successfully!")
```

### Step 3: Your First Query

```python
# first_query.py
import asyncio
from portfolio_agent import PortfolioAgent

async def main():
    agent = PortfolioAgent()
    
    # Send your first query
    response = await agent.query("Hello, can you introduce yourself?")
    print(f"Response: {response.response}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Building Your First Portfolio Agent

### Step 1: Prepare Your Documents

Create a sample resume document:

```markdown
# John Doe - Software Engineer

## Contact Information
- Email: john.doe@example.com
- Phone: (555) 123-4567
- LinkedIn: linkedin.com/in/johndoe
- GitHub: github.com/johndoe

## Professional Summary
Experienced software engineer with 5+ years of experience in full-stack development, 
machine learning, and cloud technologies.

## Technical Skills
- Programming Languages: Python, JavaScript, TypeScript, Java
- Frameworks: Django, FastAPI, React, Node.js
- Databases: PostgreSQL, MongoDB, Redis
- Cloud Platforms: AWS, Google Cloud, Azure
- Machine Learning: TensorFlow, PyTorch, Scikit-learn

## Work Experience

### Senior Software Engineer - TechCorp (2021-Present)
- Led development of microservices architecture serving 1M+ users
- Implemented machine learning pipelines for recommendation systems
- Mentored junior developers and conducted code reviews

### Software Engineer - StartupXYZ (2019-2021)
- Developed full-stack web applications using React and Django
- Built RESTful APIs and integrated third-party services
- Collaborated with product team to define technical requirements

## Education
- Bachelor of Science in Computer Science - University of Technology (2019)

## Projects
- **AI Chatbot**: Built a conversational AI using NLP and deep learning
- **E-commerce Platform**: Full-stack application with payment integration
- **Data Analytics Dashboard**: Real-time analytics using Python and React
```

Save this as `resume.md`.

### Step 2: Create Your Portfolio Agent

```python
# portfolio_agent_setup.py
import asyncio
from portfolio_agent import PortfolioAgent
from portfolio_agent.ingestion import GenericIngestor

async def setup_portfolio_agent():
    # Initialize the agent
    agent = PortfolioAgent()
    
    # Ingest your resume
    ingestor = GenericIngestor()
    document = await ingestor.ingest_file("resume.md")
    
    # Add to agent's knowledge base
    await agent.add_document(document)
    
    print("Portfolio agent setup complete!")
    return agent

async def test_queries(agent):
    # Test various queries
    queries = [
        "What are your main technical skills?",
        "Tell me about your work experience",
        "What projects have you worked on?",
        "How can I contact you?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = await agent.query(query)
        print(f"Response: {response.response}")

async def main():
    agent = await setup_portfolio_agent()
    await test_queries(agent)

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Run the Agent

```bash
python portfolio_agent_setup.py
```

## Advanced Configuration

### Custom Vector Store Configuration

```python
# custom_vector_store.py
from portfolio_agent import PortfolioAgent
from portfolio_agent.vector_stores import FAISSVectorStore
from portfolio_agent.embeddings import OpenAIEmbedder

# Custom configuration
config = {
    "rag": {
        "vector_store": {
            "provider": "faiss",
            "index_path": "./my_custom_index",
            "dimension": 1536
        },
        "embeddings": {
            "provider": "openai",
            "model": "text-embedding-3-small"
        },
        "retrieval": {
            "top_k": 10,
            "similarity_threshold": 0.8,
            "rerank": True
        }
    }
}

agent = PortfolioAgent(config=config)
```

### Multiple Document Sources

```python
# multiple_sources.py
import asyncio
from portfolio_agent import PortfolioAgent
from portfolio_agent.ingestion import (
    GenericIngestor, 
    GitHubIngestor, 
    WebsiteIngestor
)

async def ingest_multiple_sources():
    agent = PortfolioAgent()
    
    # Ingest local documents
    local_ingestor = GenericIngestor()
    documents = await local_ingestor.ingest_directory("./documents/")
    for doc in documents:
        await agent.add_document(doc)
    
    # Ingest GitHub repositories
    github_ingestor = GitHubIngestor()
    github_docs = await github_ingestor.ingest("https://github.com/username/repo")
    await agent.add_document(github_docs)
    
    # Ingest website
    website_ingestor = WebsiteIngestor()
    website_docs = await website_ingestor.ingest("https://yourwebsite.com")
    await agent.add_document(website_docs)
    
    print("All sources ingested successfully!")

if __name__ == "__main__":
    asyncio.run(ingest_multiple_sources())
```

## Custom Prompts and Fine-tuning

### Creating Custom Prompt Templates

```python
# custom_prompts.py
from portfolio_agent.finetuning import PromptTemplate, AdvancedPromptTemplate

# Simple prompt template
simple_template = PromptTemplate(
    name="portfolio_intro",
    template="""
    You are {name}, a {role} with {experience} years of experience.
    
    Question: {question}
    
    Answer in a professional and engaging way that showcases your expertise.
    """,
    variables=["name", "role", "experience", "question"]
)

# Advanced prompt template with examples
advanced_template = AdvancedPromptTemplate(
    name="technical_skills",
    template="""
    You are a technical expert. Answer questions about your skills and experience.
    
    Context: {context}
    Question: {question}
    
    Examples:
    Q: What programming languages do you know?
    A: I'm proficient in Python, JavaScript, and Java, with 5+ years of experience in each.
    
    Q: What frameworks have you used?
    A: I've worked extensively with Django, React, and Spring Boot for building scalable applications.
    
    Now answer the user's question:
    """,
    variables=["context", "question"]
)

# Use the templates
response = simple_template.format(
    name="John Doe",
    role="Software Engineer",
    experience="5",
    question="What are your main skills?"
)
```

### Fine-tuning with PEFT/LoRA

```python
# fine_tuning.py
from portfolio_agent.finetuning import PEFTTrainer, PEFTConfig

# Prepare training data
training_data = [
    {
        "input": "What are your technical skills?",
        "output": "I have extensive experience with Python, JavaScript, and cloud technologies..."
    },
    {
        "input": "Tell me about your projects",
        "output": "I've worked on several interesting projects including an AI chatbot and e-commerce platform..."
    }
]

# Configure PEFT training
config = PEFTConfig(
    model_name="gpt-3.5-turbo",
    task_type="CAUSAL_LM",
    r=16,
    lora_alpha=32,
    lora_dropout=0.1
)

# Initialize trainer
trainer = PEFTTrainer(config=config)

# Train the model
result = await trainer.train(
    training_data=training_data,
    num_epochs=3,
    learning_rate=2e-4
)

print(f"Training completed. Model saved to: {result.model_path}")
```

## Security and Privacy

### PII Detection and Redaction

```python
# pii_security.py
from portfolio_agent.security import AdvancedPIIDetector

# Initialize PII detector
pii_detector = AdvancedPIIDetector()

# Detect PII in text
text = "My email is john.doe@example.com and my phone is 555-123-4567"
entities = pii_detector.detect_pii(text)

print("Detected PII entities:")
for entity in entities:
    print(f"- {entity.entity_type}: {entity.value} (confidence: {entity.confidence})")

# Redact PII
redacted_text, detections = pii_detector.redact_pii(text)
print(f"Redacted text: {redacted_text}")
```

### Data Encryption

```python
# data_encryption.py
from portfolio_agent.security import DataEncryption

# Initialize encryption
encryption = DataEncryption()

# Encrypt sensitive data
sensitive_data = "This is confidential information"
encrypted_data = encryption.encrypt_data(sensitive_data)

print(f"Encrypted data: {encrypted_data}")

# Decrypt data
decrypted_data = encryption.decrypt_data(encrypted_data)
print(f"Decrypted data: {decrypted_data}")
```

### Consent Management

```python
# consent_management.py
from portfolio_agent.security import ConsentManager, DataCategory, ProcessingPurpose

# Initialize consent manager
consent_manager = ConsentManager()

# Record user consent
consent_record = consent_manager.record_consent(
    subject_id="user123",
    data_categories=[DataCategory.PERSONAL_DATA, DataCategory.BEHAVIORAL_DATA],
    processing_purposes=[ProcessingPurpose.ANALYTICS, ProcessingPurpose.PERSONALIZATION]
)

print(f"Consent recorded: {consent_record.consent_id}")

# Check consent
has_consent = consent_manager.has_consent(
    subject_id="user123",
    data_category=DataCategory.PERSONAL_DATA,
    processing_purpose=ProcessingPurpose.ANALYTICS
)

print(f"Has consent: {has_consent}")
```

## Performance Optimization

### Caching Implementation

```python
# performance_optimization.py
from portfolio_agent.finetuning import PerformanceOptimizer, CacheManager

# Initialize performance optimizer
optimizer = PerformanceOptimizer()

# Configure caching
cache_manager = CacheManager(
    cache_type="redis",  # or "memory"
    ttl=3600,  # 1 hour
    max_size=1000
)

# Enable caching for the agent
agent = PortfolioAgent()
agent.enable_caching(cache_manager)

# Queries will now be cached
response1 = await agent.query("What are your skills?")  # First query - not cached
response2 = await agent.query("What are your skills?")  # Second query - cached
```

### Batch Processing

```python
# batch_processing.py
from portfolio_agent.finetuning import BatchProcessor

# Initialize batch processor
batch_processor = BatchProcessor(batch_size=10)

# Process multiple documents
documents = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
results = await batch_processor.process_documents(documents)

print(f"Processed {len(results)} documents")
```

### Async Processing

```python
# async_processing.py
import asyncio
from portfolio_agent import PortfolioAgent

async def process_multiple_queries():
    agent = PortfolioAgent()
    
    queries = [
        "What are your skills?",
        "Tell me about your experience",
        "What projects have you worked on?",
        "How can I contact you?"
    ]
    
    # Process queries concurrently
    tasks = [agent.query(query) for query in queries]
    responses = await asyncio.gather(*tasks)
    
    for query, response in zip(queries, responses):
        print(f"Q: {query}")
        print(f"A: {response.response}\n")

if __name__ == "__main__":
    asyncio.run(process_multiple_queries())
```

## Integration Examples

### FastAPI Integration

```python
# fastapi_integration.py
from fastapi import FastAPI, HTTPException
from portfolio_agent import PortfolioAgent

app = FastAPI()
agent = PortfolioAgent()

@app.post("/query")
async def query_agent(query: str, user_id: str = "default"):
    try:
        response = await agent.query(query, user_id=user_id)
        return {
            "response": response.response,
            "citations": response.citations,
            "metadata": response.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_document(file: UploadFile):
    try:
        result = await agent.upload_document(file)
        return {"document_id": result.document_id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Slack Bot Integration

```python
# slack_bot.py
import os
from slack_bolt import App
from portfolio_agent import PortfolioAgent

# Initialize Slack app
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Initialize portfolio agent
agent = PortfolioAgent()

@app.message(".*")
def handle_message(message, say):
    try:
        # Get the query from the message
        query = message["text"]
        
        # Get response from portfolio agent
        response = await agent.query(query, user_id=message["user"])
        
        # Send response back to Slack
        say(response.response)
        
    except Exception as e:
        say(f"Sorry, I encountered an error: {str(e)}")

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
```

### Discord Bot Integration

```python
# discord_bot.py
import discord
from discord.ext import commands
from portfolio_agent import PortfolioAgent

# Initialize Discord bot
bot = commands.Bot(command_prefix='!')

# Initialize portfolio agent
agent = PortfolioAgent()

@bot.command(name='ask')
async def ask_question(ctx, *, question):
    try:
        response = await agent.query(question, user_id=str(ctx.author.id))
        await ctx.send(response.response)
    except Exception as e:
        await ctx.send(f"Sorry, I encountered an error: {str(e)}")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

if __name__ == "__main__":
    bot.run('your-discord-bot-token')
```

### Web Scraping Integration

```python
# web_scraping.py
import asyncio
import aiohttp
from portfolio_agent import PortfolioAgent
from portfolio_agent.ingestion import WebsiteIngestor

async def scrape_and_ingest():
    agent = PortfolioAgent()
    website_ingestor = WebsiteIngestor()
    
    # List of websites to scrape
    websites = [
        "https://yourwebsite.com",
        "https://yourblog.com",
        "https://yourportfolio.com"
    ]
    
    for website in websites:
        try:
            # Scrape and ingest website
            document = await website_ingestor.ingest(website)
            await agent.add_document(document)
            print(f"Successfully ingested: {website}")
        except Exception as e:
            print(f"Failed to ingest {website}: {e}")

if __name__ == "__main__":
    asyncio.run(scrape_and_ingest())
```

## Advanced Use Cases

### Multi-Language Support

```python
# multilingual_support.py
from portfolio_agent import PortfolioAgent

# Configure for multiple languages
config = {
    "rag": {
        "llm": {
            "model": "gpt-4",
            "temperature": 0.7
        },
        "embeddings": {
            "model": "text-embedding-3-small"
        }
    }
}

agent = PortfolioAgent(config=config)

# Query in different languages
queries = [
    "What are your technical skills?",  # English
    "¿Cuáles son tus habilidades técnicas?",  # Spanish
    "Quelles sont vos compétences techniques?",  # French
    "你的技术技能是什么？"  # Chinese
]

for query in queries:
    response = await agent.query(query)
    print(f"Q ({query[:20]}...): {response.response[:100]}...")
```

### Custom Evaluation Metrics

```python
# custom_metrics.py
from portfolio_agent.finetuning import QualityAssessor, QualityMetrics

# Initialize quality assessor
assessor = QualityAssessor()

# Define custom metrics
custom_metrics = QualityMetrics(
    relevance_weight=0.4,
    coherence_weight=0.3,
    fluency_weight=0.2,
    completeness_weight=0.1
)

# Evaluate response quality
response = "I have experience with Python, JavaScript, and cloud technologies."
quality_score = assessor.evaluate_response(
    response=response,
    query="What are your technical skills?",
    metrics=custom_metrics
)

print(f"Quality score: {quality_score.overall_score}")
```

## Troubleshooting Common Issues

### Issue 1: API Rate Limits

```python
# rate_limit_handling.py
import asyncio
import time
from portfolio_agent import PortfolioAgent

async def handle_rate_limits():
    agent = PortfolioAgent()
    
    queries = ["Query 1", "Query 2", "Query 3", "Query 4", "Query 5"]
    
    for i, query in enumerate(queries):
        try:
            response = await agent.query(query)
            print(f"Query {i+1}: {response.response[:50]}...")
        except Exception as e:
            if "rate limit" in str(e).lower():
                print(f"Rate limit hit, waiting 60 seconds...")
                await asyncio.sleep(60)
                # Retry the query
                response = await agent.query(query)
                print(f"Query {i+1} (retry): {response.response[:50]}...")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(handle_rate_limits())
```

### Issue 2: Memory Management

```python
# memory_management.py
import gc
from portfolio_agent import PortfolioAgent

def optimize_memory():
    agent = PortfolioAgent()
    
    # Process documents in batches
    batch_size = 10
    documents = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]  # Your documents
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        
        # Process batch
        for doc in batch:
            agent.upload_document(doc)
        
        # Force garbage collection
        gc.collect()
        
        print(f"Processed batch {i//batch_size + 1}")

if __name__ == "__main__":
    optimize_memory()
```

## Conclusion

These tutorials provide a comprehensive guide to using the Portfolio Agent effectively. Start with the basic tutorials and gradually work your way up to the advanced features. Remember to:

1. **Start simple**: Begin with basic setup and gradually add complexity
2. **Test thoroughly**: Always test your configuration before deploying
3. **Monitor performance**: Keep an eye on response times and resource usage
4. **Stay updated**: Keep your dependencies and models updated
5. **Document your setup**: Keep track of your configuration and customizations

For more help, refer to the main documentation or reach out to the community for support.
