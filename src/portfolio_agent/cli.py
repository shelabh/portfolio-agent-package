#!/usr/bin/env python3
"""CLI for the supported PortfolioAgent SDK path."""

import argparse
import sys
from typing import Optional

from .api.server import create_app
from .sdk import PortfolioAgent


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Portfolio Agent - persona-grounded RAG toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  portfolio-agent --query "What are your skills?"
  portfolio-agent --query "Tell me about your work" --session-id user123
  portfolio-agent --add-file ./resume.md --query "What are your core skills?"
  portfolio-agent --interactive
        """
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Query to ask the agent"
    )
    
    parser.add_argument(
        "--session-id", "-s",
        type=str,
        help="Session ID for conversation memory"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--add-file",
        type=str,
        help="Path to a file to ingest before querying"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the FastAPI server"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    try:
        agent = PortfolioAgent.from_settings()
    except Exception as e:
        print(f"Error initializing PortfolioAgent: {e}")
        print("Hint: for a fast repository smoke test, run `python scripts/manual_e2e.py --mode smoke`.")
        print("If you are using the default local HF path, the first run may need to download the embedding model.")
        print("If you recently changed embedding providers or dimensions, use a fresh FAISS_INDEX_PATH or remove old index files.")
        sys.exit(1)

    if args.add_file:
        try:
            result = agent.add_file(args.add_file)
            print(f"Indexed {result.chunks_created} chunks from {args.add_file}")
        except Exception as e:
            print(f"Error indexing file: {e}")
            sys.exit(1)
    
    if args.serve:
        run_server(agent, args.host, args.port, args.reload)
    elif args.interactive:
        run_interactive(agent, args.session_id)
    elif args.query:
        run_single_query(agent, args.query, args.session_id)
    else:
        parser.print_help()


def run_single_query(agent: PortfolioAgent, query: str, session_id: Optional[str] = None):
    """Run a single query and print the result."""
    try:
        print(f"Query: {query}")
        print("Processing...")

        result = agent.query(query, session_id=session_id or "default")
        print(f"\nResponse: {result.response}")
        if result.sources:
            print("\nSources:")
            for source in result.sources:
                print(f"- {source.get('source') or source.get('id')}")
    except Exception as e:
        print(f"Error running query: {e}")
        sys.exit(1)


def run_interactive(agent: PortfolioAgent, session_id: Optional[str] = None):
    """Run in interactive mode."""
    print("Portfolio Agent Interactive Mode")
    print("Type 'quit' or 'exit' to stop, 'help' for commands")
    print("-" * 50)
    
    while True:
        try:
            query = input("\nYou: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if query.lower() == 'help':
                print_help()
                continue
            
            if not query:
                continue
            
            print("Agent: ", end="", flush=True)
            result = agent.query(query, session_id=session_id or "interactive")
            print(result.response)
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def run_server(agent: PortfolioAgent, host: str, port: int, reload: bool):
    """Run the FastAPI server."""
    try:
        import uvicorn

        app = create_app(agent=agent)
        
        print(f"Starting Portfolio Agent API server...")
        print(f"Server will be available at: http://{host}:{port}")
        print(f"API documentation: http://{host}:{port}/docs")
        print(f"Health check: http://{host}:{port}/api/v1/health")
        print("Press Ctrl+C to stop the server")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except ImportError:
        print("Error: uvicorn is required to run the server.")
        print("Install it with: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


def print_help():
    """Print help information."""
    print("""
Available commands:
  help          - Show this help message
  quit/exit/q   - Exit the interactive mode
  
Example queries:
  "What are your core skills?"
  "Tell me about your recent projects"
  "Summarize the indexed documents"
    """)


if __name__ == "__main__":
    main()
