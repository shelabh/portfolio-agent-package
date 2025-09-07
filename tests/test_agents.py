# tests/test_agents.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from portfolio_agent.agents.router import router_agent
from portfolio_agent.agents.retriever import retriever_agent
from portfolio_agent.agents.reranker import reranker_agent
from portfolio_agent.agents.persona import persona_agent
from portfolio_agent.agents.critic import critic_agent
from portfolio_agent.agents.memory_manager import memory_agent

class TestRouterAgent:
    def test_router_agent_tool_intent(self):
        """Test router correctly identifies tool intent."""
        state = Mock()
        state.messages = [{"role": "user", "content": "Schedule a meeting with me"}]
        
        with patch('portfolio_agent.agents.router.llm_chat') as mock_llm:
            mock_llm.return_value = "tool"
            result = router_agent(state)
            # Command objects have .update dict attribute
            assert result.update.get("last_intent") == "tool"
            assert result.goto == "tool"

    def test_router_agent_retriever_intent(self):
        """Test router correctly identifies retriever intent."""
        state = Mock()
        state.messages = [{"role": "user", "content": "What are your skills?"}]
        
        with patch('portfolio_agent.agents.router.llm_chat') as mock_llm:
            mock_llm.return_value = "retriever"
            result = router_agent(state)
            assert result.update.get("last_intent") == "retriever"
            assert result.goto == "retriever"

    def test_router_agent_direct_intent(self):
        """Test router correctly identifies direct intent."""
        state = Mock()
        state.messages = [{"role": "user", "content": "Hello, how are you?"}]
        
        with patch('portfolio_agent.agents.router.llm_chat') as mock_llm:
            mock_llm.return_value = "direct"
            result = router_agent(state)
            assert result.update.get("last_intent") == "direct"
            assert result.goto == "direct"

    def test_router_agent_no_messages(self):
        """Test router handles empty messages gracefully."""
        state = Mock()
        state.messages = []
        
        result = router_agent(state)
        assert result.goto == "end"
        assert result.update == {}

class TestRetrieverAgent:
    @patch('portfolio_agent.agents.retriever.openai')
    def test_retriever_agent_success(self, mock_openai):
        """Test retriever agent successfully retrieves documents."""
        state = Mock()
        state.messages = [{"role": "user", "content": "What are your skills?"}]
        
        mock_hits = [
            {"id": "doc1", "content": "Python programming", "metadata": {"source": "skills.md"}},
            {"id": "doc2", "content": "Machine learning", "metadata": {"source": "experience.md"}}
        ]
        
        with patch('portfolio_agent.agents.retriever.llm_chat') as mock_llm, \
             patch('portfolio_agent.agents.retriever.nearest_neighbors') as mock_nn:
            
            mock_llm.return_value = "skills programming"
            # Mock the embeddings response
            mock_openai.Embedding.create.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            mock_nn.return_value = mock_hits
            
            result = retriever_agent(state)
            assert result.update.get("retrieved") == mock_hits
            assert result.goto == "reranker"

class TestRerankerAgent:
    def test_reranker_agent_success(self):
        """Test reranker agent successfully reranks documents."""
        state = Mock()
        state.messages = [{"role": "user", "content": "What are your skills?"}]
        state.__dict__ = {
            "retrieved": [
                {"id": "doc1", "content": "Python programming skills"},
                {"id": "doc2", "content": "Machine learning experience"}
            ]
        }
        
        with patch('portfolio_agent.agents.reranker.llm_chat') as mock_llm:
            mock_llm.return_value = '["doc1", "doc2"]'
            
            result = reranker_agent(state)
            assert "ranked" in result.update
            assert result.goto == "persona"

    def test_reranker_agent_no_documents(self):
        """Test reranker agent handles empty retrieved documents."""
        state = Mock()
        state.__dict__ = {"retrieved": []}
        
        result = reranker_agent(state)
        assert result.goto == "persona"
        assert result.update == {}

class TestPersonaAgent:
    def test_persona_agent_with_context(self):
        """Test persona agent generates response with context."""
        state = Mock()
        state.messages = [{"role": "user", "content": "What are your skills?"}]
        state.__dict__ = {
            "ranked": [
                {"id": "doc1", "content": "Python programming", "metadata": {"source": "skills.md"}}
            ]
        }
        
        with patch('portfolio_agent.agents.persona.llm_chat') as mock_llm:
            mock_llm.return_value = "I have expertise in Python programming [[skills.md]]."
            
            result = persona_agent(state)
            assert "candidate_answer" in result.update
            assert result.goto == "critic"

    def test_persona_agent_with_memory_context(self):
        """Test persona agent uses memory context."""
        state = Mock()
        state.messages = [{"role": "user", "content": "Tell me about yourself"}]
        state.__dict__ = {
            "memories": [
                {"id": "mem1", "content": "Previous conversation about Python"}
            ],
            "conversation_context": [
                {"role": "user", "content": "Hello", "timestamp": "2024-01-01"}
            ]
        }
        
        with patch('portfolio_agent.agents.persona.llm_chat') as mock_llm:
            mock_llm.return_value = "Based on our previous conversation about Python..."
            
            result = persona_agent(state)
            assert "candidate_answer" in result.update
            assert result.goto == "critic"

class TestCriticAgent:
    def test_critic_agent_valid_response(self):
        """Test critic agent validates good response."""
        state = Mock()
        state.__dict__ = {
            "candidate_answer": "I have Python skills [[doc1]].",
            "ranked": [
                {"id": "doc1", "content": "Python programming skills"}
            ]
        }
        
        with patch('portfolio_agent.agents.critic.llm_chat') as mock_llm:
            mock_llm.return_value = '{"valid": true, "issues": []}'
            
            result = critic_agent(state)
            assert result.update.get("final_answer") == state.__dict__["candidate_answer"]
            assert result.goto == "notes_agent"

    def test_critic_agent_invalid_response(self):
        """Test critic agent rejects invalid response."""
        state = Mock()
        state.__dict__ = {
            "candidate_answer": "I have unicorn riding skills.",
            "ranked": [
                {"id": "doc1", "content": "Python programming skills"}
            ]
        }
        
        with patch('portfolio_agent.agents.critic.llm_chat') as mock_llm:
            mock_llm.return_value = '{"valid": false, "issues": ["No evidence for unicorn skills"]}'
            
            result = critic_agent(state)
            assert "I can't fully verify" in result.update.get("final_answer", "")
            assert result.goto == "end"

class TestMemoryAgent:
    @patch('portfolio_agent.agents.memory_manager.openai')
    def test_memory_agent_with_user_id(self, mock_openai):
        """Test memory agent fetches user-specific memories."""
        state = Mock()
        state.user_id = "user123"
        state.messages = [{"role": "user", "content": "What did we discuss before?"}]
        
        mock_memories = [
            {"id": "mem1", "content": "Previous discussion about Python"}
        ]
        
        with patch('portfolio_agent.agents.memory_manager.nearest_neighbors') as mock_nn:
            mock_openai.Embedding.create.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            mock_nn.return_value = mock_memories
            
            result = memory_agent(state)
            assert "memories" in result.update
            assert "conversation_context" in result.update
            assert result.goto == "router"

    def test_memory_agent_no_user_id(self):
        """Test memory agent handles missing user_id gracefully."""
        state = Mock()
        state.user_id = None
        state.messages = [{"role": "user", "content": "Hello"}]
        
        result = memory_agent(state)
        assert result.update.get("memories") == []
        assert result.update.get("conversation_context") == []
        assert result.goto == "router"