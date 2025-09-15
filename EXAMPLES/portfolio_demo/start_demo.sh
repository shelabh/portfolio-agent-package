#!/bin/bash

# Portfolio Agent Demo Startup Script
# This script sets up and runs the portfolio demo

set -e

echo "🚀 Starting Portfolio Agent Demo..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install portfolio-agent in development mode
echo "📥 Installing portfolio-agent..."
pip install -e ".[all]"

# Check if config file exists
if [ ! -f "config.yaml" ]; then
    echo "⚙️  Creating config file from example..."
    cp config.example.yaml config.yaml
    echo "📝 Please edit config.yaml with your API keys and preferences"
    echo "   Required: OPENAI_API_KEY (if using OpenAI)"
    echo "   Optional: PINECONE_API_KEY (if using Pinecone)"
    exit 1
fi

# Create sample data directory
echo "📁 Setting up sample data..."
mkdir -p data/sample

# Download sample resume if it doesn't exist
if [ ! -f "data/sample/resume_redacted.pdf" ]; then
    echo "📄 Creating sample resume..."
    # Create a simple text file as placeholder
    cat > data/sample/resume_redacted.pdf << EOF
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Sample Resume - Redacted) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF
EOF
fi

# Create sample GitHub data
if [ ! -f "data/sample/github_projects.json" ]; then
    echo "💻 Creating sample GitHub data..."
    cat > data/sample/github_projects.json << EOF
{
  "projects": [
    {
      "name": "portfolio-agent",
      "description": "A production-ready RAG pipeline with multi-agent architecture",
      "language": "Python",
      "stars": 42,
      "topics": ["rag", "langgraph", "ai", "agent"],
      "readme": "This is a sample project description for demonstration purposes."
    },
    {
      "name": "sample-web-app",
      "description": "A sample web application built with React and Node.js",
      "language": "JavaScript",
      "stars": 15,
      "topics": ["react", "nodejs", "web"],
      "readme": "A modern web application showcasing best practices."
    }
  ]
}
EOF
fi

# Start the demo server
echo "🌐 Starting demo server..."
echo "   Access the demo at: http://localhost:8000"
echo "   API docs at: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop"
echo ""

# Run the demo
python -c "
import uvicorn
from portfolio_agent import create_demo_app

app = create_demo_app()
uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
"
