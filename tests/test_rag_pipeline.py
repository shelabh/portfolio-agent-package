"""
Tests for RAG pipeline and agents.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

# Test imports
try:
    from src.portfolio_agent.agents import (
        RouterAgent, RetrieverAgent, RerankerAgent, PersonaAgent, MemoryManager,
        QueryType, PersonaType, RerankingStrategy
    )
    from src.portfolio_agent.rag_pipeline import RAGPipeline, RAGRequest, RAGResponse
except ImportError:
    pytest.skip("RAG modules not available", allow_module_level=True)


class TestRouterAgent:
    """Test Router Agent."""
    
    @pytest.fixture
    def router_agent(self):
        """Create router agent for testing."""
        return RouterAgent()
    
    def test_route_technical_query(self, router_agent):
        """Test routing of technical queries."""
        query = "How do I implement machine learning algorithms in Python?"
        decision = router_agent.route_query(query)
        
        assert decision.query_type == QueryType.TECHNICAL
        assert decision.confidence > 0.5
        assert "retriever" in decision.suggested_agents
        assert "persona" in decision.suggested_agents
    
    def test_route_personal_query(self, router_agent):
        """Test routing of personal queries."""
        query = "Tell me about yourself and your interests"
        decision = router_agent.route_query(query)
        
        assert decision.query_type == QueryType.PERSONAL
        assert "persona" in decision.suggested_agents
    
    def test_route_contact_query(self, router_agent):
        """Test routing of contact queries."""
        query = "How can I get in touch with you?"
        decision = router_agent.route_query(query)
        
        assert decision.query_type == QueryType.CONTACT
        assert "persona" in decision.suggested_agents
    
    def test_route_unknown_query(self, router_agent):
        """Test routing of unknown queries."""
        query = "asdfghjkl"
        decision = router_agent.route_query(query)
        
        assert decision.query_type == QueryType.UNKNOWN
        assert decision.confidence < 0.7
    
    def test_validate_routing_decision(self, router_agent):
        """Test routing decision validation."""
        from src.portfolio_agent.agents import RoutingDecision
        
        # Valid decision
        valid_decision = RoutingDecision(
            query_type=QueryType.TECHNICAL,
            confidence=0.8,
            reasoning="Test reasoning",
            suggested_agents=["retriever", "persona"],
            metadata={}
        )
        assert router_agent.validate_routing_decision(valid_decision)
        
        # Invalid decision (invalid agent)
        invalid_decision = RoutingDecision(
            query_type=QueryType.TECHNICAL,
            confidence=0.8,
            reasoning="Test reasoning",
            suggested_agents=["invalid_agent"],
            metadata={}
        )
        assert not router_agent.validate_routing_decision(invalid_decision)


class TestRetrieverAgent:
    """Test Retriever Agent."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        mock_store = Mock()
        mock_store.search_by_text.return_value = [
            Mock(
                document=Mock(
                    id="doc1",
                    content="Test document content",
                    metadata={"source": "test.txt"}
                ),
                score=0.9,
                rank=1
            )
        ]
        return mock_store
    
    @pytest.fixture
    def mock_embedder(self):
        """Mock embedder."""
        mock_embedder = Mock()
        mock_embedder.embed_single.return_value = [0.1] * 384
        return mock_embedder
    
    @pytest.fixture
    def retriever_agent(self, mock_vector_store, mock_embedder):
        """Create retriever agent for testing."""
        return RetrieverAgent(mock_vector_store, mock_embedder)
    
    def test_retrieve_documents(self, retriever_agent):
        """Test document retrieval."""
        from src.portfolio_agent.agents import RetrievalRequest
        
        request = RetrievalRequest(
            query="test query",
            k=5
        )
        
        result = retriever_agent.retrieve_documents(request)
        
        assert len(result.documents) == 1
        assert result.documents[0]["id"] == "doc1"
        assert result.documents[0]["score"] == 0.9
        assert result.query == "test query"
        assert result.total_found == 1
    
    def test_get_document_by_id(self, retriever_agent, mock_vector_store):
        """Test getting document by ID."""
        mock_doc = Mock()
        mock_doc.id = "doc1"
        mock_doc.content = "Test content"
        mock_doc.metadata = {"source": "test.txt"}
        mock_doc.created_at = "2024-01-01T00:00:00"
        mock_doc.updated_at = "2024-01-01T00:00:00"
        
        mock_vector_store.get_document.return_value = mock_doc
        
        doc = retriever_agent.get_document_by_id("doc1")
        
        assert doc is not None
        assert doc["id"] == "doc1"
        assert doc["content"] == "Test content"


class TestRerankerAgent:
    """Test Reranker Agent."""
    
    @pytest.fixture
    def reranker_agent(self):
        """Create reranker agent for testing."""
        return RerankerAgent()
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "id": "doc1",
                "content": "This is about machine learning and Python programming",
                "score": 0.8,
                "rank": 1,
                "metadata": {"source": "ml.txt"}
            },
            {
                "id": "doc2", 
                "content": "This is about data science and algorithms",
                "score": 0.7,
                "rank": 2,
                "metadata": {"source": "ds.txt"}
            }
        ]
    
    def test_score_only_rerank(self, reranker_agent, sample_documents):
        """Test score-only reranking."""
        from src.portfolio_agent.agents import RerankingRequest
        
        request = RerankingRequest(
            documents=sample_documents,
            query="machine learning",
            strategy=RerankingStrategy.SCORE_ONLY,
            max_results=2
        )
        
        result = reranker_agent.rerank_documents(request)
        
        assert len(result.documents) == 2
        assert result.documents[0]["score"] >= result.documents[1]["score"]
        assert result.strategy_used == RerankingStrategy.SCORE_ONLY
    
    def test_keyword_match_rerank(self, reranker_agent, sample_documents):
        """Test keyword match reranking."""
        from src.portfolio_agent.agents import RerankingRequest
        
        request = RerankingRequest(
            documents=sample_documents,
            query="machine learning",
            strategy=RerankingStrategy.KEYWORD_MATCH,
            max_results=2
        )
        
        result = reranker_agent.rerank_documents(request)
        
        assert len(result.documents) == 2
        assert "keyword_score" in result.documents[0]
        assert result.strategy_used == RerankingStrategy.KEYWORD_MATCH


class TestPersonaAgent:
    """Test Persona Agent."""
    
    @pytest.fixture
    def persona_agent(self):
        """Create persona agent for testing."""
        return PersonaAgent()
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "id": "doc1",
                "content": "I have experience with Python programming and machine learning",
                "score": 0.9,
                "rank": 1,
                "metadata": {"source": "resume.txt"}
            }
        ]
    
    def test_generate_professional_response(self, persona_agent, sample_documents):
        """Test professional response generation."""
        from src.portfolio_agent.agents import PersonaRequest
        
        request = PersonaRequest(
            query="What programming languages do you know?",
            documents=sample_documents,
            persona_type=PersonaType.PROFESSIONAL,
            max_response_length=200
        )
        
        result = persona_agent.generate_response(request)
        
        assert len(result.response) > 0
        assert result.persona_used == PersonaType.PROFESSIONAL
        assert len(result.sources) == 1
        assert result.sources[0]["id"] == "doc1"
    
    def test_generate_friendly_response(self, persona_agent, sample_documents):
        """Test friendly response generation."""
        from src.portfolio_agent.agents import PersonaRequest
        
        request = PersonaRequest(
            query="Tell me about your skills",
            documents=sample_documents,
            persona_type=PersonaType.FRIENDLY,
            max_response_length=200
        )
        
        result = persona_agent.generate_response(request)
        
        assert len(result.response) > 0
        assert result.persona_used == PersonaType.FRIENDLY
        assert "Hi there" in result.response or "Great question" in result.response


class TestMemoryManager:
    """Test Memory Manager."""
    
    @pytest.fixture
    def memory_manager(self):
        """Create memory manager for testing."""
        return MemoryManager(max_turns=5)
    
    def test_start_conversation(self, memory_manager):
        """Test starting a new conversation."""
        session_id = "test_session"
        context = memory_manager.start_conversation(session_id)
        
        assert context.session_id == session_id
        assert len(context.turns) == 0
        assert session_id in memory_manager.conversations
    
    def test_add_turn(self, memory_manager):
        """Test adding a turn to conversation."""
        session_id = "test_session"
        memory_manager.start_conversation(session_id)
        
        turn = memory_manager.add_turn(
            session_id=session_id,
            user_query="Hello",
            agent_response="Hi there!",
            metadata={"test": "data"}
        )
        
        assert turn.user_query == "Hello"
        assert turn.agent_response == "Hi there!"
        assert turn.metadata["test"] == "data"
        
        # Check conversation context
        context = memory_manager.get_conversation_context(session_id)
        assert len(context.turns) == 1
        assert context.turns[0].user_query == "Hello"
    
    def test_get_recent_turns(self, memory_manager):
        """Test getting recent turns."""
        session_id = "test_session"
        memory_manager.start_conversation(session_id)
        
        # Add multiple turns
        for i in range(3):
            memory_manager.add_turn(
                session_id=session_id,
                user_query=f"Query {i}",
                agent_response=f"Response {i}"
            )
        
        recent_turns = memory_manager.get_recent_turns(session_id, num_turns=2)
        assert len(recent_turns) == 2
        assert recent_turns[0].user_query == "Query 1"
        assert recent_turns[1].user_query == "Query 2"
    
    def test_conversation_summary(self, memory_manager):
        """Test getting conversation summary."""
        session_id = "test_session"
        memory_manager.start_conversation(session_id)
        
        memory_manager.add_turn(
            session_id=session_id,
            user_query="What is machine learning?",
            agent_response="Machine learning is a subset of AI."
        )
        
        summary = memory_manager.get_conversation_summary(session_id)
        assert summary["total_turns"] == 1
        assert summary["session_id"] == session_id
        assert "machine" in summary["topics"]


class TestRAGPipeline:
    """Test RAG Pipeline."""
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing."""
        router = Mock(spec=RouterAgent)
        retriever = Mock(spec=RetrieverAgent)
        reranker = Mock(spec=RerankerAgent)
        persona = Mock(spec=PersonaAgent)
        memory = Mock(spec=MemoryManager)
        
        return router, retriever, reranker, persona, memory
    
    @pytest.fixture
    def rag_pipeline(self, mock_agents):
        """Create RAG pipeline for testing."""
        router, retriever, reranker, persona, memory = mock_agents
        return RAGPipeline(router, retriever, reranker, persona, memory)
    
    def test_pipeline_initialization(self, mock_agents):
        """Test pipeline initialization."""
        router, retriever, reranker, persona, memory = mock_agents
        pipeline = RAGPipeline(router, retriever, reranker, persona, memory)
        
        assert pipeline.router_agent == router
        assert pipeline.retriever_agent == retriever
        assert pipeline.reranker_agent == reranker
        assert pipeline.persona_agent == persona
        assert pipeline.memory_manager == memory
    
    def test_process_query(self, rag_pipeline, mock_agents):
        """Test query processing through pipeline."""
        router, retriever, reranker, persona, memory = mock_agents
        
        # Mock the agents' methods
        router.route_query.return_value = Mock(
            query_type=Mock(value="technical"),
            confidence=0.8,
            reasoning="Test reasoning",
            suggested_agents=["retriever", "persona"],
            metadata={}
        )
        
        retriever.retrieve_documents.return_value = Mock(
            documents=[{"id": "doc1", "content": "Test content", "score": 0.9}],
            query="test query",
            total_found=1,
            retrieval_time=0.1,
            metadata={}
        )
        
        reranker.rerank_documents.return_value = Mock(
            documents=[{"id": "doc1", "content": "Test content", "score": 0.9}],
            original_count=1,
            reranked_count=1,
            reranking_time=0.1,
            strategy_used=Mock(value="hybrid"),
            metadata={}
        )
        
        persona.generate_response.return_value = Mock(
            response="Test response",
            sources=[{"id": "doc1", "score": 0.9}],
            persona_used=Mock(value="professional"),
            response_time=0.1,
            metadata={}
        )
        
        memory.get_conversation_context.return_value = None
        
        # Create request
        request = RAGRequest(
            query="What is machine learning?",
            session_id="test_session"
        )
        
        # Process query
        response = rag_pipeline.process_query(request)
        
        assert response.response == "Test response"
        assert response.session_id == "test_session"
        assert len(response.sources) == 1
        assert response.processing_time > 0
    
    def test_pipeline_stats(self, rag_pipeline, mock_agents):
        """Test getting pipeline statistics."""
        router, retriever, reranker, persona, memory = mock_agents
        
        # Mock stats methods
        router.get_routing_stats.return_value = {"total_patterns": 6}
        retriever.get_retrieval_stats.return_value = {"total_documents": 100}
        reranker.get_reranking_stats.return_value = {"available_strategies": 5}
        persona.get_persona_stats.return_value = {"available_personas": 3}
        memory.get_memory_stats.return_value = {"active_sessions": 1}
        
        stats = rag_pipeline.get_pipeline_stats()
        
        assert "router_stats" in stats
        assert "retriever_stats" in stats
        assert "reranker_stats" in stats
        assert "persona_stats" in stats
        assert "memory_stats" in stats
