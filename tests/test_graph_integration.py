# tests/test_graph_integration.py
import pytest
from portfolio_agent import build_graph
from portfolio_agent.checkpoint.redis_checkpointer import RedisCheckpointer
from langgraph.graph.message import MessagesState
from langgraph.graph import START, END
from unittest.mock import patch, Mock

def test_graph_build_and_run():
    """Test graph builds and runs without checkpointer."""
    graph = build_graph(checkpointer=None)
    assert graph is not None

    # Initialize state - MessagesState should be a dict-like object
    state = {"messages": [{"role": "user", "content": "Hello"}]}

    # Mock all the external dependencies that would cause issues
    with patch('portfolio_agent.agents.memory_manager.openai') as mock_openai, \
         patch('portfolio_agent.agents.router.llm_chat') as mock_router_llm, \
         patch('portfolio_agent.agents.persona.llm_chat') as mock_persona_llm, \
         patch('portfolio_agent.agents.critic.llm_chat') as mock_critic_llm, \
         patch('portfolio_agent.agents.tools.notes_agent.openai') as mock_notes_openai, \
         patch('portfolio_agent.agents.tools.notes_agent.upsert_vector') as mock_upsert:
        
        # Set up mocks
        mock_openai.Embedding.create.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        mock_notes_openai.Embedding.create.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        mock_router_llm.return_value = "direct"
        mock_persona_llm.return_value = "Hello! How can I help you?"
        mock_critic_llm.return_value = '{"valid": true, "issues": []}'
        
        # Test that graph can be invoked
        result = graph.invoke(state)
        assert result is not None
        assert "messages" in result