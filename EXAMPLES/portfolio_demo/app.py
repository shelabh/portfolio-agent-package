#!/usr/bin/env python3
"""
Portfolio Demo Application

A polished demo showcasing the Portfolio Agent as a personal portfolio assistant
with an interactive web interface.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from portfolio_agent.api.server import create_app as create_api_app
from portfolio_agent.config import settings
from portfolio_agent.rag_pipeline import RAGPipeline
from portfolio_agent.embeddings.openai_embedder import OpenAIEmbedder
from portfolio_agent.vector_stores.faiss_store import FAISSVectorStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Portfolio Agent Demo",
    description="Interactive demo of the Portfolio Agent system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Global RAG pipeline
rag_pipeline: RAGPipeline = None

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG pipeline on startup."""
    global rag_pipeline
    
    try:
        logger.info("Initializing Portfolio Agent Demo...")
        
        # Initialize components
        embedder = OpenAIEmbedder()
        vector_store = FAISSVectorStore()
        
        # Create RAG pipeline
        rag_pipeline = RAGPipeline(
            embedder=embedder,
            vector_store=vector_store,
            llm_client=None  # Will be initialized when needed
        )
        
        # Load sample portfolio data
        await load_sample_data()
        
        logger.info("Portfolio Agent Demo initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize demo: {e}")
        raise

async def load_sample_data():
    """Load sample portfolio data."""
    try:
        # Sample portfolio content
        sample_content = """
        # John Doe - Software Engineer
        
        ## About Me
        I'm a passionate software engineer with 5+ years of experience in full-stack development.
        I specialize in Python, JavaScript, and cloud technologies.
        
        ## Skills
        - **Programming Languages**: Python, JavaScript, TypeScript, Java, Go
        - **Frameworks**: Django, FastAPI, React, Vue.js, Node.js
        - **Cloud Platforms**: AWS, Google Cloud, Azure
        - **Databases**: PostgreSQL, MongoDB, Redis
        - **DevOps**: Docker, Kubernetes, CI/CD
        
        ## Experience
        
        ### Senior Software Engineer - Tech Corp (2022-Present)
        - Led development of microservices architecture serving 1M+ users
        - Implemented CI/CD pipelines reducing deployment time by 60%
        - Mentored junior developers and conducted code reviews
        
        ### Software Engineer - StartupXYZ (2020-2022)
        - Built RESTful APIs using Python and FastAPI
        - Developed React frontend applications
        - Collaborated with cross-functional teams in agile environment
        
        ## Projects
        
        ### Portfolio Agent (2024)
        A production-ready RAG pipeline with multi-agent architecture for portfolio management.
        Built with Python, FastAPI, and advanced AI technologies.
        
        ### E-commerce Platform (2023)
        Full-stack e-commerce solution with payment integration and inventory management.
        Technologies: Python, Django, React, PostgreSQL, Stripe API.
        
        ## Education
        - **Bachelor of Science in Computer Science** - University of Technology (2019)
        - **AWS Certified Solutions Architect** (2023)
        - **Google Cloud Professional Developer** (2022)
        
        ## Contact
        - Email: john.doe@example.com
        - LinkedIn: linkedin.com/in/johndoe
        - GitHub: github.com/johndoe
        """
        
        # Add sample content to vector store
        result = await rag_pipeline.add_document(
            content=sample_content,
            document_type="md",
            source="portfolio.md",
            metadata={
                "title": "John Doe Portfolio",
                "type": "portfolio",
                "created_at": "2024-01-01"
            }
        )
        
        logger.info(f"Loaded sample portfolio data: {result.get('chunks_created', 0)} chunks")
        
    except Exception as e:
        logger.error(f"Failed to load sample data: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with portfolio overview."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Portfolio Agent Demo"
    })

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Interactive chat page."""
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "title": "Chat with Portfolio Agent"
    })

@app.post("/api/chat")
async def chat_endpoint(
    message: str = Form(...),
    user_id: str = Form("demo_user"),
    session_id: str = Form("demo_session")
):
    """Chat API endpoint."""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
        
        # Process the query
        result = await rag_pipeline.process_query(
            query=message,
            query_type="rag",
            user_id=user_id,
            session_id=session_id,
            max_results=5,
            include_sources=True
        )
        
        return JSONResponse({
            "response": result.get('response', ''),
            "sources": result.get('sources', []),
            "confidence": result.get('confidence', 0.0),
            "processing_time": result.get('processing_time', 0.0)
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio information."""
    try:
        # Search for portfolio documents
        results = await rag_pipeline.search_documents(
            query="portfolio skills experience",
            limit=10
        )
        
        return JSONResponse({
            "documents": results.get('documents', []),
            "total": results.get('total', 0)
        })
        
    except Exception as e:
        logger.error(f"Portfolio retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("uploaded")
):
    """Upload and process a document."""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
        
        # Read file content
        content = await file.read()
        
        # Determine document type
        document_type = "txt"
        if file.filename:
            ext = file.filename.lower().split('.')[-1]
            if ext in ['pdf', 'md', 'html', 'json', 'docx']:
                document_type = ext
        
        # Process the document
        result = await rag_pipeline.add_document(
            content=content.decode('utf-8', errors='ignore'),
            document_type=document_type,
            source=source or file.filename,
            metadata={
                "filename": file.filename,
                "uploaded_at": "2024-01-01"
            }
        )
        
        return JSONResponse({
            "message": "Document uploaded successfully",
            "document_id": result.get('document_id'),
            "chunks_created": result.get('chunks_created', 0)
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "rag_pipeline": "initialized" if rag_pipeline else "not_initialized",
        "version": "1.0.0"
    })

@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    """Demo showcase page."""
    return templates.TemplateResponse("demo.html", {
        "request": request,
        "title": "Portfolio Agent Demo Showcase"
    })

@app.get("/features", response_class=HTMLResponse)
async def features_page(request: Request):
    """Features page."""
    return templates.TemplateResponse("features.html", {
        "request": request,
        "title": "Features - Portfolio Agent"
    })

@app.get("/api", response_class=RedirectResponse)
async def api_redirect():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")

# Mount the API app
api_app = create_api_app()
app.mount("/api/v1", api_app)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
