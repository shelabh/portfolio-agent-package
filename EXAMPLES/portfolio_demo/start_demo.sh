#!/bin/bash

# Portfolio Agent Demo Startup Script
# This script sets up and starts the portfolio agent demo

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_status "Python version: $PYTHON_VERSION"
        
        # Check if version is 3.8 or higher
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
            print_success "Python version is compatible"
        else
            print_error "Python 3.8 or higher is required"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
}

# Function to check if virtual environment exists
check_venv() {
    if [ -d "venv" ]; then
        print_status "Virtual environment found"
        return 0
    else
        print_warning "Virtual environment not found"
        return 1
    fi
}

# Function to create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
}

# Function to activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install the package in development mode
    pip install -e .
    
    # Install additional demo dependencies
    pip install fastapi uvicorn python-multipart jinja2 python-dotenv
    
    print_success "Dependencies installed"
}

# Function to check configuration
check_config() {
    if [ ! -f "config.yaml" ]; then
        if [ -f "config.example.yaml" ]; then
            print_warning "config.yaml not found, copying from config.example.yaml"
            cp config.example.yaml config.yaml
            print_warning "Please edit config.yaml with your API keys and settings"
        else
            print_error "No configuration file found"
            exit 1
        fi
    else
        print_success "Configuration file found"
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p data/processed
    mkdir -p data/faiss_index
    mkdir -p logs
    mkdir -p static/uploads
    print_success "Directories created"
}

# Function to check API keys
check_api_keys() {
    print_status "Checking API keys..."
    
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY environment variable not set"
        print_warning "Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'"
        print_warning "Or add it to your config.yaml file"
    else
        print_success "OpenAI API key found"
    fi
}

# Function to prepare sample data
prepare_sample_data() {
    print_status "Preparing sample data..."
    
    # Create a sample resume if none exists
    if [ ! -f "data/resume.pdf" ]; then
        print_warning "No resume.pdf found in data/ directory"
        print_warning "Please add your resume.pdf to the data/ directory for the demo"
        
        # Create a sample text file instead
        cat > data/sample_resume.txt << EOF
# John Doe - Software Engineer

## Contact Information
- Email: john.doe@example.com
- Phone: (555) 123-4567
- LinkedIn: linkedin.com/in/johndoe
- GitHub: github.com/johndoe

## Professional Summary
Experienced software engineer with 5+ years of experience in full-stack development, 
machine learning, and cloud technologies. Passionate about building scalable 
applications and solving complex problems.

## Technical Skills
- Programming Languages: Python, JavaScript, TypeScript, Java, Go
- Frameworks: Django, FastAPI, React, Node.js, Spring Boot
- Databases: PostgreSQL, MongoDB, Redis
- Cloud Platforms: AWS, Google Cloud, Azure
- Machine Learning: TensorFlow, PyTorch, Scikit-learn
- DevOps: Docker, Kubernetes, CI/CD, Terraform

## Work Experience

### Senior Software Engineer - Tech Corp (2021-Present)
- Led development of microservices architecture serving 1M+ users
- Implemented machine learning pipelines for recommendation systems
- Mentored junior developers and conducted code reviews
- Technologies: Python, FastAPI, PostgreSQL, AWS, Docker

### Software Engineer - StartupXYZ (2019-2021)
- Developed full-stack web applications using React and Django
- Built RESTful APIs and integrated third-party services
- Collaborated with product team to define technical requirements
- Technologies: Python, Django, React, PostgreSQL, Redis

## Education
- Bachelor of Science in Computer Science - University of Technology (2019)
- Relevant Coursework: Data Structures, Algorithms, Machine Learning, Database Systems

## Projects
- **AI Chatbot**: Built a conversational AI using NLP and deep learning
- **E-commerce Platform**: Full-stack application with payment integration
- **Data Analytics Dashboard**: Real-time analytics using Python and React
EOF
        print_success "Sample resume text created"
    fi
}

# Function to start the demo
start_demo() {
    print_status "Starting Portfolio Agent Demo..."
    
    # Check if port is available
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        print_warning "Port 8000 is already in use"
        print_warning "Please stop the service using port 8000 or change the port in config.yaml"
        exit 1
    fi
    
    # Start the FastAPI server
    print_status "Starting FastAPI server on http://localhost:8000"
    print_status "API documentation available at http://localhost:8000/docs"
    print_status "Demo interface available at http://localhost:8000/demo"
    print_status "Press Ctrl+C to stop the server"
    
    # Run the demo app
    python app.py
}

# Function to show help
show_help() {
    echo "Portfolio Agent Demo Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --setup     Set up the demo environment (install dependencies, create directories)"
    echo "  --start     Start the demo server"
    echo "  --full      Full setup and start (default)"
    echo "  --help      Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  OPENAI_API_KEY     Your OpenAI API key (required for LLM functionality)"
    echo "  HUGGINGFACE_API_KEY Your Hugging Face API key (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 --setup    # Set up the environment"
    echo "  $0 --start    # Start the demo"
    echo "  $0 --full     # Full setup and start"
}

# Main function
main() {
    echo "🚀 Portfolio Agent Demo Startup Script"
    echo "======================================"
    
    # Parse command line arguments
    case "${1:-full}" in
        --setup)
            print_status "Setting up demo environment..."
            check_python_version
            if ! check_venv; then
                create_venv
            fi
            activate_venv
            install_dependencies
            check_config
            create_directories
            prepare_sample_data
            check_api_keys
            print_success "Setup complete! Run '$0 --start' to start the demo"
            ;;
        --start)
            print_status "Starting demo..."
            if ! check_venv; then
                print_error "Virtual environment not found. Run '$0 --setup' first"
                exit 1
            fi
            activate_venv
            check_config
            check_api_keys
            start_demo
            ;;
        --full)
            print_status "Running full setup and start..."
            check_python_version
            if ! check_venv; then
                create_venv
            fi
            activate_venv
            install_dependencies
            check_config
            create_directories
            prepare_sample_data
            check_api_keys
            start_demo
            ;;
        --help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"