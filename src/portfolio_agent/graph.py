# src/portfolio_agent/graph.py - FIXED

from langgraph.graph import StateGraph, MessagesState, START, END
from typing import Literal

from portfolio_agent.agents.router import router_agent
from portfolio_agent.agents.retriever import retriever_agent
from portfolio_agent.agents.reranker import reranker_agent
from portfolio_agent.agents.persona import persona_agent
from portfolio_agent.agents.critic import critic_agent
from portfolio_agent.agents.memory_manager import memory_agent
from portfolio_agent.agents.tools.calendly_agent import calendly_agent
from portfolio_agent.agents.tools.email_agent import email_agent
from portfolio_agent.agents.tools.notes_agent import notes_agent

def route_decision(state: MessagesState) -> Literal["retriever_agent", "calendly_agent", "persona_agent", "end"]:
    """
    Route based on the router agent's decision stored in state.
    """
    # Access state as dictionary - get the original intent, not the goto value
    last_intent = state.get("last_intent", "direct")
    
    # Map the intent to actual node names
    if last_intent == "tool":
        return "calendly_agent"
    elif last_intent == "retriever":
        return "retriever_agent"
    elif last_intent == "direct":
        return "persona_agent"
    else:
        return "end"

def tool_router(state: MessagesState) -> Literal["calendly_agent", "email_agent", "notes_agent"]:
    """
    Route to specific tool based on user intent.
    """
    messages = state.get("messages", [])
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content", "").lower()
            break
    
    if "calendly" in last_user or "schedule" in last_user or "meeting" in last_user:
        return "calendly_agent"
    elif "email" in last_user or "send" in last_user:
        return "email_agent"
    else:
        return "notes_agent"

def build_graph(checkpointer=None):
    """
    Build the LangGraph StateGraph with conditional routing:
      memory → router → [retriever → reranker → persona → critic] OR [tool] OR [direct] → notes_agent → END
    Includes proper conditional branching based on router decisions.
    Accepts an optional checkpointer (e.g. RedisCheckpointer).
    """
    builder = StateGraph(MessagesState)
    
    # Add all nodes with consistent naming
    builder.add_node("memory_agent", memory_agent)
    builder.add_node("router_agent", router_agent)
    builder.add_node("retriever_agent", retriever_agent)
    builder.add_node("reranker_agent", reranker_agent)
    builder.add_node("persona_agent", persona_agent)
    builder.add_node("critic_agent", critic_agent)
    builder.add_node("notes_agent", notes_agent)
    builder.add_node("calendly_agent", calendly_agent)
    builder.add_node("email_agent", email_agent)

    # Define main execution flow
    builder.add_edge(START, "memory_agent")
    builder.add_edge("memory_agent", "router_agent")
    
    # Conditional routing from router_agent
    builder.add_conditional_edges(
        "router_agent",
        route_decision,
        {
            "retriever_agent": "retriever_agent",
            "calendly_agent": "calendly_agent",
            "persona_agent": "persona_agent",
            "end": END
        }
    )
    
    # RAG pipeline flow
    builder.add_edge("retriever_agent", "reranker_agent")
    builder.add_edge("reranker_agent", "persona_agent")
    builder.add_edge("persona_agent", "critic_agent")
    builder.add_edge("critic_agent", "notes_agent")
    
    # Tool flows - both tools flow to notes_agent
    builder.add_edge("calendly_agent", "notes_agent")
    builder.add_edge("email_agent", "notes_agent")
    
    # All paths converge at notes_agent then END
    builder.add_edge("notes_agent", END)

    graph = builder.compile(checkpointer=checkpointer)
    return graph


if __name__ == "__main__":
    graph = build_graph()
    print("Portfolio Agent graph built:", graph)