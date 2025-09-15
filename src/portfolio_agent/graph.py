# src/portfolio_agent/graph.py - Legacy graph for backward compatibility

from langgraph.graph import StateGraph, MessagesState, START, END
from typing import Literal

# Import the new RAG pipeline instead
from portfolio_agent.rag_pipeline import RAGPipeline

def build_graph(checkpointer=None):
    """
    Build the LangGraph StateGraph for backward compatibility.
    For new implementations, use RAGPipeline directly.
    """
    # For backward compatibility, return a simple graph
    graph = StateGraph(MessagesState)
    
    # Add a simple persona node
    def simple_persona_node(state: MessagesState) -> MessagesState:
        """Simple persona node for backward compatibility."""
        # This is a placeholder - use RAGPipeline for full functionality
        return state
    
    graph.add_node("persona_agent", simple_persona_node)
    graph.set_entry_point("persona_agent")
    graph.add_edge("persona_agent", END)
    
    return graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    graph = build_graph()
    print("Portfolio Agent graph built:", graph)