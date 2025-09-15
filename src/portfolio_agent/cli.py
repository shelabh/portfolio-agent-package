#!/usr/bin/env python3
"""
Portfolio Agent CLI

A command-line interface for the Portfolio Agent system.
"""

import argparse
import sys
import os
from typing import Optional
from langgraph.graph.message import MessagesState

from . import build_graph, RedisCheckpointer
from .config import settings
from .api.server import create_app


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Portfolio Agent - A production-ready RAG pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  portfolio-agent --query "What are your skills?"
  portfolio-agent --query "Schedule a meeting" --user-id user123
  portfolio-agent --interactive
        """
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Query to ask the agent"
    )
    
    parser.add_argument(
        "--user-id", "-u",
        type=str,
        help="User ID for memory management"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--redis-url",
        type=str,
        default="redis://localhost:6379/0",
        help="Redis URL for persistence (default: redis://localhost:6379/0)"
    )
    
    parser.add_argument(
        "--no-persistence",
        action="store_true",
        help="Run without Redis persistence"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--serve", "-s",
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
    
    # Validate configuration
    if not settings.OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not set. Please set it as an environment variable.")
        sys.exit(1)
    
    if not settings.DATABASE_URL:
        print("Error: DATABASE_URL not set. Please set it as an environment variable.")
        sys.exit(1)
    
    # Build graph
    try:
        if args.no_persistence:
            graph = build_graph()
            print("Built graph without persistence")
        else:
            checkpointer = RedisCheckpointer(redis_url=args.redis_url)
            graph = build_graph(checkpointer=checkpointer)
            print(f"Built graph with Redis persistence at {args.redis_url}")
    except Exception as e:
        print(f"Error building graph: {e}")
        sys.exit(1)
    
    if args.serve:
        run_server(args.host, args.port, args.reload)
    elif args.interactive:
        run_interactive(graph, args.user_id)
    elif args.query:
        run_single_query(graph, args.query, args.user_id)
    else:
        parser.print_help()


def run_single_query(graph, query: str, user_id: Optional[str] = None):
    """Run a single query and print the result."""
    try:
        state = MessagesState()
        state.messages = [{"role": "user", "content": query}]
        if user_id:
            state.user_id = user_id
        
        print(f"Query: {query}")
        print("Processing...")
        
        result = graph.run(state)
        
        # Find the assistant's response
        for message in reversed(result.messages):
            if message.get("role") == "assistant":
                print(f"\nResponse: {message.get('content')}")
                break
        else:
            print("\nNo response generated.")
            
    except Exception as e:
        print(f"Error running query: {e}")
        sys.exit(1)


def run_interactive(graph, user_id: Optional[str] = None):
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
            
            state = MessagesState()
            state.messages = [{"role": "user", "content": query}]
            if user_id:
                state.user_id = user_id
            
            print("Agent: ", end="", flush=True)
            result = graph.run(state)
            
            # Find the assistant's response
            for message in reversed(result.messages):
                if message.get("role") == "assistant":
                    print(message.get('content'))
                    break
            else:
                print("I'm sorry, I couldn't generate a response.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def run_server(host: str, port: int, reload: bool):
    """Run the FastAPI server."""
    try:
        import uvicorn
        
        app = create_app()
        
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
            log_level="info" if settings.LOCAL_ONLY else "warning"
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
  "What are your skills?"
  "Schedule a meeting with me"
  "Draft an email to a recruiter"
  "Tell me about your experience"
    """)


if __name__ == "__main__":
    main()

