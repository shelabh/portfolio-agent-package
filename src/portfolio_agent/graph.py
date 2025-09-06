# src/portfolio_agent/graph.py

from langgraph.graph import StateGraph, MessagesState, START, END

from portfolio_agent.agents.router import router_agent
from portfolio_agent.agents.retriever import retriever_agent
from portfolio_agent.agents.reranker import reranker_agent
from portfolio_agent.agents.persona import persona_agent
from portfolio_agent.agents.critic import critic_agent
from portfolio_agent.agents.memory_manager import memory_agent
from portfolio_agent.agents.tools.calendly_agent import calendly_agent
from portfolio_agent.agents.tools.email_agent import email_agent
from portfolio_agent.agents.tools.notes_agent import notes_agent

def build_graph(checkpointer=None):
    """
    Build the LangGraph StateGraph with your pipeline:
      memory → router → retriever → reranker → persona → critic → END.
    Includes tools as callable nodes.
    Accepts an optional checkpointer (e.g. RedisCheckpointer).
    """
    builder = StateGraph(MessagesState)
    # Add nodes
    builder.add_node(memory_agent)
    builder.add_node(router_agent)
    builder.add_node(retriever_agent)
    builder.add_node(reranker_agent)
    builder.add_node(persona_agent)
    builder.add_node(critic_agent)
    builder.add_node(notes_agent)
    builder.add_node(calendly_agent)
    builder.add_node(email_agent)

    # Define main execution flow
    builder.add_edge(START, "memory_agent")
    builder.add_edge("memory_agent", "router_agent")
    builder.add_edge("router_agent", "retriever_agent")
    builder.add_edge("retriever_agent", "reranker_agent")
    builder.add_edge("reranker_agent", "persona_agent")
    builder.add_edge("persona_agent", "critic_agent")
    builder.add_edge("critic_agent", END)

    graph = builder.compile(checkpointer=checkpointer)
    return graph


if __name__ == "__main__":
    graph = build_graph()
    print("Portfolio Agent graph built:", graph)
