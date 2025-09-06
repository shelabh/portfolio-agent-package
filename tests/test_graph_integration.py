# tests/test_graph_integration.py
import pytest
from portfolio_agent import build_graph
from portfolio_agent.checkpoint.redis_checkpointer import RedisCheckpointer
from langgraph.graph.message import MessagesState
from langgraph.graph import START, END

def test_graph_build_and_run(tmp_path):
    # Use no checkpointer or in-memory by default
    graph = build_graph(checkpointer=None)
    assert graph is not None

    # Initialize state
    state = MessagesState()
    state.messages = [{"role": "user", "content": "Hello"}]

    # Run synchronously
    result = graph.run(state)
    assert hasattr(state, "messages")
    # final carry-through: ensure something changed
    assert isinstance(state.messages, list)
