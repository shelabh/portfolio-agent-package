#!/usr/bin/env python3
"""
Local RAG Demo

This script demonstrates a complete local RAG pipeline using:
- Hugging Face embeddings (local inference)
- FAISS vector store
- Document ingestion and chunking
- Similarity search and retrieval

Usage:
    python examples/local_rag_demo.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from portfolio_agent.embeddings import HuggingFaceEmbedder
from portfolio_agent.vector_stores import FAISSVectorStore, VectorDocument
from portfolio_agent.ingestion import GenericIngestor, TextChunker
from portfolio_agent.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalRAGDemo:
    """Local RAG demonstration class."""
    
    def __init__(self, index_path: str = "local_rag_index"):
        """Initialize the demo.
        
        Args:
            index_path: Path to save the FAISS index
        """
        self.index_path = index_path
        self.embedder = None
        self.vector_store = None
        self.chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        
    def setup(self):
        """Set up the embedding model and vector store."""
        logger.info("Setting up local RAG components...")
        
        # Initialize Hugging Face embedder (local inference)
        self.embedder = HuggingFaceEmbedder(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"  # Use CPU for compatibility
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
        
        logger.info("Setup complete!")
    
    def ingest_documents(self, document_paths: list):
        """Ingest documents from file paths.
        
        Args:
            document_paths: List of file paths to ingest
        """
        logger.info(f"Ingesting {len(document_paths)} documents...")
        
        ingestor = GenericIngestor()
        all_chunks = []
        
        for doc_path in document_paths:
            logger.info(f"Processing: {doc_path}")
            
            try:
                # Ingest document
                chunks = ingestor.ingest(doc_path, redact_pii=True)
                all_chunks.extend(chunks)
                logger.info(f"  -> Extracted {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"  -> Error processing {doc_path}: {e}")
        
        logger.info(f"Total chunks extracted: {len(all_chunks)}")
        return all_chunks
    
    def generate_embeddings_and_store(self, chunks: list):
        """Generate embeddings for chunks and store in vector database.
        
        Args:
            chunks: List of text chunks with metadata
        """
        logger.info("Generating embeddings and storing in vector database...")
        
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embedding_result = self.embedder.embed_texts(texts, {"source": "local_rag_demo"})
        
        logger.info(f"Generated {len(embedding_result.embeddings)} embeddings in {embedding_result.processing_time:.2f}s")
        
        # Create vector documents
        vector_docs = []
        for i, (text, vector, metadata) in enumerate(zip(texts, embedding_result.embeddings, metadatas)):
            doc = VectorDocument(
                id=f"chunk_{i}",
                content=text,
                vector=vector,
                metadata=metadata,
                created_at=embedding_result.metadata.get("processed_at", ""),
                updated_at=embedding_result.metadata.get("processed_at", "")
            )
            vector_docs.append(doc)
        
        # Store in vector database
        logger.info("Storing in vector database...")
        added_ids = self.vector_store.add_documents(vector_docs)
        
        logger.info(f"Stored {len(added_ids)} documents in vector database")
        
        # Save the index
        self.vector_store.save()
        logger.info(f"Saved vector index to {self.index_path}")
    
    def search(self, query: str, k: int = 5) -> list:
        """Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for: '{query}'")
        
        results = self.vector_store.search_by_text(
            query, 
            self.embedder, 
            k=k
        )
        
        logger.info(f"Found {len(results)} results")
        return results
    
    def display_results(self, results: list):
        """Display search results in a formatted way.
        
        Args:
            results: List of search results
        """
        print("\n" + "="*80)
        print("SEARCH RESULTS")
        print("="*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result.score:.4f}")
            print(f"   Source: {result.document.metadata.get('source', 'Unknown')}")
            print(f"   Content: {result.document.content[:200]}...")
            if len(result.document.content) > 200:
                print("   [Content truncated]")
            print("-" * 40)
    
    def get_stats(self):
        """Get and display system statistics."""
        embedder_info = self.embedder.get_model_info()
        store_stats = self.vector_store.get_stats()
        
        print("\n" + "="*80)
        print("SYSTEM STATISTICS")
        print("="*80)
        print(f"Embedding Model: {embedder_info['model_name']}")
        print(f"Embedding Dimension: {embedder_info['embedding_dimension']}")
        print(f"Device: {embedder_info['device']}")
        print(f"Total Documents: {store_stats['total_documents']}")
        print(f"Index Type: {store_stats['index_type']}")
        print(f"Index Size: {store_stats['index_size']}")
        print("="*80)

def create_sample_documents():
    """Create sample documents for demonstration."""
    sample_dir = Path("sample_docs")
    sample_dir.mkdir(exist_ok=True)
    
    # Sample documents
    documents = {
        "ai_basics.txt": """
Artificial Intelligence (AI) is a branch of computer science that aims to create 
intelligent machines that can perform tasks that typically require human intelligence. 
These tasks include learning, reasoning, problem-solving, perception, and language understanding.

Machine Learning is a subset of AI that focuses on algorithms that can learn and 
make decisions from data without being explicitly programmed for every task. 
Deep Learning is a subset of machine learning that uses neural networks with 
multiple layers to model and understand complex patterns in data.

AI applications include natural language processing, computer vision, robotics, 
expert systems, and autonomous vehicles. The field has seen rapid advancement 
in recent years due to increased computational power, large datasets, and 
improved algorithms.
        """,
        
        "python_programming.txt": """
Python is a high-level, interpreted programming language known for its simplicity 
and readability. It was created by Guido van Rossum and first released in 1991.

Python's design philosophy emphasizes code readability with its notable use of 
significant whitespace. Its language constructs and object-oriented approach 
aim to help programmers write clear, logical code for small and large-scale projects.

Python is dynamically typed and garbage-collected. It supports multiple programming 
paradigms, including procedural, object-oriented, and functional programming. 
Python is often described as a "batteries included" language due to its 
comprehensive standard library.

Popular Python frameworks include Django and Flask for web development, 
NumPy and Pandas for data science, TensorFlow and PyTorch for machine learning, 
and many others.
        """,
        
        "data_science.txt": """
Data Science is an interdisciplinary field that uses scientific methods, processes, 
algorithms and systems to extract knowledge and insights from structured and 
unstructured data. It combines domain expertise, programming skills, and knowledge 
of mathematics and statistics.

The data science process typically involves:
1. Data collection and cleaning
2. Exploratory data analysis
3. Feature engineering
4. Model building and validation
5. Deployment and monitoring

Common tools in data science include Python (with libraries like pandas, numpy, 
scikit-learn), R, SQL, and visualization tools like matplotlib and seaborn. 
Big data technologies like Hadoop and Spark are also important for handling 
large-scale datasets.

Data scientists work across various industries including technology, finance, 
healthcare, marketing, and government to solve complex problems using data-driven 
approaches.
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
    print("🚀 Local RAG Demo - Complete Pipeline")
    print("="*50)
    
    # Create sample documents
    print("Creating sample documents...")
    document_paths = create_sample_documents()
    print(f"Created {len(document_paths)} sample documents")
    
    # Initialize demo
    demo = LocalRAGDemo()
    
    try:
        # Setup components
        demo.setup()
        
        # Ingest documents
        chunks = demo.ingest_documents(document_paths)
        
        if not chunks:
            print("No chunks extracted. Exiting.")
            return
        
        # Generate embeddings and store
        demo.generate_embeddings_and_store(chunks)
        
        # Display stats
        demo.get_stats()
        
        # Interactive search
        print("\n🔍 Interactive Search")
        print("="*30)
        print("Enter search queries (type 'quit' to exit):")
        
        while True:
            query = input("\nQuery: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # Search and display results
            results = demo.search(query, k=3)
            demo.display_results(results)
        
        print("\n👋 Demo complete!")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    main()
