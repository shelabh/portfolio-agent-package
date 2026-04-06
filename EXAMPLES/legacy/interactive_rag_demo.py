#!/usr/bin/env python3
"""
Interactive RAG Demo

This script demonstrates the complete RAG orchestration pipeline with
interactive conversation interface using all agents.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from portfolio_agent.embeddings import HuggingFaceEmbedder
from portfolio_agent.vector_stores import FAISSVectorStore
from portfolio_agent.ingestion import GenericIngestor
from portfolio_agent.agents import (
    RouterAgent, RetrieverAgent, RerankerAgent, PersonaAgent, MemoryManager,
    PersonaType, RerankingStrategy
)
from portfolio_agent.rag_pipeline import RAGPipeline, RAGRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractiveRAGDemo:
    """Interactive RAG demonstration class."""
    
    def __init__(self, index_path: str = "interactive_rag_index"):
        """Initialize the demo."""
        self.index_path = index_path
        self.session_id = str(uuid.uuid4())
        
        # Initialize components
        self.embedder = None
        self.vector_store = None
        self.rag_pipeline = None
        
    def setup(self):
        """Set up the RAG pipeline components."""
        logger.info("Setting up interactive RAG components...")
        
        # Initialize Hugging Face embedder
        self.embedder = HuggingFaceEmbedder(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )
        
        # Get embedding dimension
        dimension = self.embedder.get_embedding_dimension()
        logger.info(f"Using embedding dimension: {dimension}")
        
        # Initialize FAISS vector store
        self.vector_store = FAISSVectorStore(
            index_path=self.index_path,
            dimension=dimension,
            index_type="flat",
            metric="cosine"
        )
        
        # Load existing index if available
        if os.path.exists(f"{self.index_path}.faiss"):
            self.vector_store.load()
            logger.info(f"Loaded existing vector store with {len(self.vector_store.documents)} documents")
        
        # Initialize agents
        router_agent = RouterAgent()
        retriever_agent = RetrieverAgent(self.vector_store, self.embedder)
        reranker_agent = RerankerAgent()
        persona_agent = PersonaAgent()
        memory_manager = MemoryManager()
        
        # Create RAG pipeline
        self.rag_pipeline = RAGPipeline(
            router_agent=router_agent,
            retriever_agent=retriever_agent,
            reranker_agent=reranker_agent,
            persona_agent=persona_agent,
            memory_manager=memory_manager
        )
        
        logger.info("Setup complete!")
    
    def ingest_documents(self, document_paths: list):
        """Ingest documents from file paths."""
        logger.info(f"Ingesting {len(document_paths)} documents...")
        
        ingestor = GenericIngestor()
        all_chunks = []
        
        for doc_path in document_paths:
            logger.info(f"Processing: {doc_path}")
            
            try:
                chunks = ingestor.ingest(doc_path, redact_pii=True)
                all_chunks.extend(chunks)
                logger.info(f"  -> Extracted {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"  -> Error processing {doc_path}: {e}")
        
        logger.info(f"Total chunks extracted: {len(all_chunks)}")
        return all_chunks
    
    def generate_embeddings_and_store(self, chunks: list):
        """Generate embeddings for chunks and store in vector database."""
        logger.info("Generating embeddings and storing in vector database...")
        
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embedding_result = self.embedder.embed_texts(texts, {"source": "interactive_rag_demo"})
        
        logger.info(f"Generated {len(embedding_result.embeddings)} embeddings in {embedding_result.processing_time:.2f}s")
        
        # Store in vector database
        logger.info("Storing in vector database...")
        added_ids = self.vector_store.add_texts(texts, embedding_result.embeddings, metadatas)
        
        logger.info(f"Stored {len(added_ids)} documents in vector database")
        
        # Save the index
        self.vector_store.save()
        logger.info(f"Saved vector index to {self.index_path}")
    
    def process_query(self, query: str, persona_type: PersonaType = PersonaType.PROFESSIONAL) -> dict:
        """Process a query through the RAG pipeline."""
        logger.info(f"Processing query: {query[:100]}...")
        
        # Create RAG request
        request = RAGRequest(
            query=query,
            session_id=self.session_id,
            persona_type=persona_type,
            max_documents=5,
            reranking_strategy=RerankingStrategy.HYBRID,
            include_sources=True
        )
        
        # Process through pipeline
        response = self.rag_pipeline.process_query(request)
        
        return {
            "response": response.response,
            "sources": response.sources,
            "processing_time": response.processing_time,
            "metadata": response.metadata
        }
    
    def display_response(self, result: dict):
        """Display the response in a formatted way."""
        print("\n" + "="*80)
        print("RAG RESPONSE")
        print("="*80)
        print(f"Response: {result['response']}")
        print(f"Processing Time: {result['processing_time']:.3f}s")
        
        if result['sources']:
            print(f"\nSources ({len(result['sources'])}):")
            for i, source in enumerate(result['sources'], 1):
                print(f"  {i}. {source.get('source', 'Unknown')} (Score: {source.get('score', 0):.3f})")
        
        if result['metadata']:
            print(f"\nMetadata:")
            for key, value in result['metadata'].items():
                if key != 'error' or value:
                    print(f"  {key}: {value}")
        
        print("="*80)
    
    def get_conversation_history(self) -> list:
        """Get conversation history."""
        context = self.rag_pipeline.memory_manager.get_conversation_context(self.session_id)
        if context:
            return context.turns
        return []
    
    def display_conversation_history(self):
        """Display conversation history."""
        turns = self.get_conversation_history()
        
        if not turns:
            print("No conversation history yet.")
            return
        
        print("\n" + "="*80)
        print("CONVERSATION HISTORY")
        print("="*80)
        
        for i, turn in enumerate(turns, 1):
            print(f"\nTurn {i}:")
            print(f"  User: {turn.user_query}")
            print(f"  Agent: {turn.agent_response[:100]}...")
            print(f"  Time: {turn.timestamp}")
        
        print("="*80)
    
    def get_system_stats(self):
        """Get and display system statistics."""
        pipeline_stats = self.rag_pipeline.get_pipeline_stats()
        
        print("\n" + "="*80)
        print("SYSTEM STATISTICS")
        print("="*80)
        
        # Vector store stats
        store_stats = pipeline_stats['retriever_stats']['vector_store_stats']
        print(f"Vector Store:")
        print(f"  Total Documents: {store_stats['total_documents']}")
        print(f"  Index Type: {store_stats['index_type']}")
        print(f"  Dimension: {store_stats['dimension']}")
        
        # Memory stats
        memory_stats = pipeline_stats['memory_stats']
        print(f"\nMemory:")
        print(f"  Active Sessions: {memory_stats['active_sessions']}")
        print(f"  Total Turns: {memory_stats['total_turns']}")
        
        # Agent stats
        print(f"\nAgents:")
        print(f"  Router Patterns: {pipeline_stats['router_stats']['total_patterns']}")
        print(f"  Reranker Strategies: {len(pipeline_stats['reranker_stats']['available_strategies'])}")
        print(f"  Persona Types: {len(pipeline_stats['persona_stats']['available_personas'])}")
        
        print("="*80)

def create_sample_documents():
    """Create sample documents for demonstration."""
    sample_dir = Path("sample_docs")
    sample_dir.mkdir(exist_ok=True)
    
    # Sample documents
    documents = {
        "portfolio.txt": """
I am a software engineer with 5+ years of experience in full-stack development.
My expertise includes Python, JavaScript, React, Node.js, and cloud technologies.

Key Projects:
- E-commerce platform with microservices architecture
- Machine learning pipeline for data analysis
- Real-time chat application with WebSocket
- Mobile app with React Native

Technologies: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL, MongoDB
        """,
        
        "experience.txt": """
Professional Experience:

Senior Software Engineer (2022-Present)
- Led development of scalable web applications
- Implemented CI/CD pipelines and automated testing
- Mentored junior developers and conducted code reviews

Software Engineer (2020-2022)
- Developed RESTful APIs and microservices
- Worked with cloud platforms (AWS, Azure)
- Collaborated with cross-functional teams

Education:
- Bachelor's in Computer Science from University of Technology
- Certifications in AWS Solutions Architect and Google Cloud Professional
        """,
        
        "skills.txt": """
Technical Skills:

Programming Languages:
- Python (Expert): Django, Flask, FastAPI, pandas, numpy, scikit-learn
- JavaScript (Expert): React, Node.js, Express, TypeScript
- Java (Intermediate): Spring Boot, Maven
- Go (Intermediate): Gin, Gorilla

Databases:
- SQL: PostgreSQL, MySQL, SQLite
- NoSQL: MongoDB, Redis, Elasticsearch

Cloud & DevOps:
- AWS: EC2, S3, Lambda, RDS, CloudFormation
- Docker, Kubernetes, Jenkins, GitHub Actions
- Linux, Bash scripting

Soft Skills:
- Team leadership and mentoring
- Agile/Scrum methodologies
- Problem-solving and critical thinking
- Communication and collaboration
        """
    }
    
    # Write sample documents
    for filename, content in documents.items():
        file_path = sample_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
    
    return [str(sample_dir / filename) for filename in documents.keys()]

def main():
    """Main demonstration function."""
    print("🚀 Interactive RAG Demo - Complete Orchestration Pipeline")
    print("="*60)
    
    # Create sample documents
    print("Creating sample documents...")
    document_paths = create_sample_documents()
    print(f"Created {len(document_paths)} sample documents")
    
    # Initialize demo
    demo = InteractiveRAGDemo()
    
    try:
        # Setup components
        demo.setup()
        
        # Check if we need to ingest documents
        if len(demo.vector_store.documents) == 0:
            print("\nNo existing documents found. Ingesting sample documents...")
            chunks = demo.ingest_documents(document_paths)
            
            if chunks:
                demo.generate_embeddings_and_store(chunks)
            else:
                print("No chunks extracted. Exiting.")
                return
        else:
            print(f"\nFound existing vector store with {len(demo.vector_store.documents)} documents.")
        
        # Display system stats
        demo.get_system_stats()
        
        # Interactive conversation
        print("\n💬 Interactive Conversation")
        print("="*40)
        print("Available commands:")
        print("  - Ask any question about the portfolio")
        print("  - Type 'history' to see conversation history")
        print("  - Type 'stats' to see system statistics")
        print("  - Type 'persona <type>' to change persona (professional, friendly, technical)")
        print("  - Type 'quit' to exit")
        print("\nStart chatting!")
        
        current_persona = PersonaType.PROFESSIONAL
        
        while True:
            try:
                user_input = input(f"\n[{current_persona.value}] You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() == 'history':
                    demo.display_conversation_history()
                    continue
                
                if user_input.lower() == 'stats':
                    demo.get_system_stats()
                    continue
                
                if user_input.lower().startswith('persona '):
                    persona_name = user_input.split(' ', 1)[1].lower()
                    try:
                        current_persona = PersonaType(persona_name)
                        print(f"Switched to {persona_name} persona")
                    except ValueError:
                        print(f"Invalid persona. Available: {[p.value for p in PersonaType]}")
                    continue
                
                # Process the query
                result = demo.process_query(user_input, current_persona)
                demo.display_response(result)
                
            except KeyboardInterrupt:
                print("\n\nDemo interrupted by user.")
                break
            except Exception as e:
                logger.error(f"Error processing input: {e}")
                print(f"Error: {e}")
        
        print("\n👋 Demo complete!")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    main()
