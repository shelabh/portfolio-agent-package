"""
RAG Pipeline for portfolio-agent.

This module provides a LangGraph-based orchestration pipeline that coordinates
all agents to provide intelligent, contextual responses.
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None
    add_messages = None

from .agents import (
    RouterAgent, RetrieverAgent, RerankerAgent, PersonaAgent, MemoryManager,
    QueryType, PersonaType, RerankingStrategy
)

logger = logging.getLogger(__name__)

class RAGState(TypedDict):
    """State for the RAG pipeline."""
    query: str
    session_id: str
    routing_decision: Optional[Dict[str, Any]]
    retrieved_documents: List[Dict[str, Any]]
    reranked_documents: List[Dict[str, Any]]
    response: str
    sources: List[Dict[str, Any]]
    response_metadata: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str]
    max_documents: int
    persona_type: str
    include_sources: bool

@dataclass
class RAGRequest:
    """Request for RAG pipeline."""
    query: str
    session_id: str
    persona_type: PersonaType = PersonaType.PROFESSIONAL
    max_documents: int = 5
    reranking_strategy: RerankingStrategy = RerankingStrategy.HYBRID
    include_sources: bool = True
    context: Optional[Dict[str, Any]] = None

@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    response: str
    sources: List[Dict[str, Any]]
    session_id: str
    processing_time: float
    metadata: Dict[str, Any]

class RAGPipeline:
    """RAG pipeline orchestrating all agents."""
    
    def __init__(
        self,
        router_agent: RouterAgent,
        retriever_agent: RetrieverAgent,
        reranker_agent: RerankerAgent,
        persona_agent: PersonaAgent,
        memory_manager: MemoryManager,
        checkpointer=None,
    ):
        """Initialize RAG pipeline.
        
        Args:
            router_agent: Router agent for query classification
            retriever_agent: Retriever agent for document retrieval
            reranker_agent: Reranker agent for result ranking
            persona_agent: Persona agent for response generation
            memory_manager: Memory manager for conversation context
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph not available. Install with: pip install langgraph"
            )
        
        self.router_agent = router_agent
        self.retriever_agent = retriever_agent
        self.reranker_agent = reranker_agent
        self.persona_agent = persona_agent
        self.memory_manager = memory_manager
        
        # Build the graph
        self.graph = self._build_graph(checkpointer=checkpointer)
        
        logger.info("RAG pipeline initialized")
    
    def _build_graph(self, checkpointer=None) -> StateGraph:
        """Build the LangGraph state graph.
        
        Returns:
            Configured StateGraph
        """
        # Create the graph
        graph = StateGraph(RAGState)
        
        # Add nodes
        graph.add_node("router", self._router_node)
        graph.add_node("retriever", self._retriever_node)
        graph.add_node("reranker", self._reranker_node)
        graph.add_node("persona", self._persona_node)
        graph.add_node("memory", self._memory_node)
        
        # Define the flow
        graph.set_entry_point("router")
        
        # Router can go to retriever or directly to persona
        graph.add_conditional_edges(
            "router",
            self._should_retrieve,
            {
                "retrieve": "retriever",
                "persona_only": "persona"
            }
        )
        
        # Retriever goes to reranker
        graph.add_edge("retriever", "reranker")
        
        # Reranker goes to persona
        graph.add_edge("reranker", "persona")
        
        # Persona goes to memory
        graph.add_edge("persona", "memory")
        
        # Memory is the end
        graph.add_edge("memory", END)
        
        return graph.compile(checkpointer=checkpointer)
    
    def _router_node(self, state: RAGState) -> RAGState:
        """Router node for query classification."""
        logger.info("Executing router node")
        
        try:
            # Get conversation context
            context = self.memory_manager.get_conversation_context(state["session_id"])
            
            # Route the query
            routing_decision = self.router_agent.route_query(
                query=state["query"],
                context=context.metadata if context else None
            )
            
            state["routing_decision"] = {
                "query_type": routing_decision.query_type.value,
                "confidence": routing_decision.confidence,
                "reasoning": routing_decision.reasoning,
                "suggested_agents": routing_decision.suggested_agents,
                "metadata": routing_decision.metadata
            }
            
            logger.info(f"Routing decision: {routing_decision.query_type.value}")
            
        except Exception as e:
            logger.error(f"Error in router node: {e}")
            state["error"] = str(e)
        
        return state
    
    def _should_retrieve(self, state: RAGState) -> str:
        """Determine if retrieval is needed."""
        routing_decision = state.get("routing_decision")
        
        if not routing_decision:
            return "retrieve"  # Default to retrieval
        
        suggested_agents = routing_decision.get("suggested_agents", [])
        
        if "retriever" in suggested_agents:
            return "retrieve"
        else:
            return "persona_only"
    
    def _retriever_node(self, state: RAGState) -> RAGState:
        """Retriever node for document retrieval."""
        logger.info("Executing retriever node")
        
        try:
            from .agents import RetrievalRequest
            
            # Create retrieval request
            request = RetrievalRequest(
                query=state["query"],
                k=state.get("max_documents", 5),
                include_metadata=True
            )
            
            # Retrieve documents
            result = self.retriever_agent.retrieve_documents(request)
            
            state["retrieved_documents"] = result.documents
            
            logger.info(f"Retrieved {len(result.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error in retriever node: {e}")
            state["error"] = str(e)
            state["retrieved_documents"] = []
        
        return state
    
    def _reranker_node(self, state: RAGState) -> RAGState:
        """Reranker node for result ranking."""
        logger.info("Executing reranker node")
        
        try:
            from .agents import RerankingRequest, RerankingStrategy
            
            documents = state.get("retrieved_documents", [])
            
            if not documents:
                state["reranked_documents"] = []
                return state
            
            # Create reranking request
            request = RerankingRequest(
                documents=documents,
                query=state["query"],
                strategy=RerankingStrategy.HYBRID,
                max_results=state.get("max_documents", 5)
            )
            
            # Rerank documents
            result = self.reranker_agent.rerank_documents(request)
            
            state["reranked_documents"] = result.documents
            
            logger.info(f"Reranked {len(result.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error in reranker node: {e}")
            state["error"] = str(e)
            state["reranked_documents"] = state.get("retrieved_documents", [])
        
        return state
    
    def _persona_node(self, state: RAGState) -> RAGState:
        """Persona node for response generation."""
        logger.info("Executing persona node")
        
        try:
            from .agents import PersonaRequest, PersonaType
            
            # Get documents (reranked if available, otherwise retrieved)
            documents = state.get("reranked_documents", state.get("retrieved_documents", []))
            
            # Create persona request
            persona_type = PersonaType(state.get("persona_type", PersonaType.PROFESSIONAL.value))
            request = PersonaRequest(
                query=state["query"],
                documents=documents,
                persona_type=persona_type,
                max_response_length=500,
                include_sources=state.get("include_sources", True),
                context=state.get("metadata"),
            )
            
            # Generate response
            result = self.persona_agent.generate_response(request)
            
            state["response"] = result.response
            state["sources"] = result.sources
            state["response_metadata"] = result.metadata
            
            logger.info("Generated persona response")
            
        except Exception as e:
            logger.error(f"Error in persona node: {e}")
            state["error"] = str(e)
            state["response"] = "I apologize, but I'm having trouble generating a response right now."
            state["sources"] = []
            state["response_metadata"] = {"error": str(e), "evidence_strength": "none"}
        
        return state
    
    def _memory_node(self, state: RAGState) -> RAGState:
        """Memory node for conversation management."""
        logger.info("Executing memory node")
        
        try:
            # Add turn to conversation
            self.memory_manager.add_turn(
                session_id=state["session_id"],
                user_query=state["query"],
                agent_response=state["response"],
                metadata={
                    "routing_decision": state.get("routing_decision"),
                    "documents_used": len(state.get("retrieved_documents", [])),
                    "sources": state.get("sources", [])
                }
            )
            
            logger.info("Added turn to memory")
            
        except Exception as e:
            logger.error(f"Error in memory node: {e}")
            # Don't fail the pipeline for memory errors
        
        return state
    
    def process_query(
        self,
        request: RAGRequest,
        context: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """Process a query through the RAG pipeline.
        
        Args:
            request: RAG request with query and parameters
            context: Optional context information
            
        Returns:
            RAGResponse with generated response
        """
        import time
        start_time = time.time()
        
        logger.info(f"Processing query: {request.query[:100]}...")
        
        try:
            # Initialize state
            initial_state = RAGState(
                query=request.query,
                session_id=request.session_id,
                routing_decision=None,
                retrieved_documents=[],
                reranked_documents=[],
                response="",
                sources=[],
                response_metadata={},
                metadata=request.context or {},
                error=None,
                max_documents=request.max_documents,
                persona_type=request.persona_type.value,
                include_sources=request.include_sources,
            )
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            processing_time = time.time() - start_time
            
            # Create response
            response = RAGResponse(
                response=final_state["response"],
                sources=final_state["sources"],
                session_id=request.session_id,
                processing_time=processing_time,
                metadata={
                    "routing_decision": final_state.get("routing_decision"),
                    "documents_retrieved": len(final_state.get("retrieved_documents", [])),
                    "documents_reranked": len(final_state.get("reranked_documents", [])),
                    "retrieved_sources": self._source_labels(final_state.get("retrieved_documents", [])),
                    "reranked_sources": self._source_labels(final_state.get("reranked_documents", [])),
                    "response_metadata": final_state.get("response_metadata", {}),
                    "error": final_state.get("error")
                }
            )
            
            logger.info(f"Processed query in {processing_time:.3f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return RAGResponse(
                response="I apologize, but I encountered an error processing your request. Please try again.",
                sources=[],
                session_id=request.session_id,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics.
        
        Returns:
            Dictionary with pipeline statistics
        """
        return {
            "router_stats": self.router_agent.get_routing_stats(),
            "retriever_stats": self.retriever_agent.get_retrieval_stats(),
            "reranker_stats": self.reranker_agent.get_reranking_stats(),
            "persona_stats": self.persona_agent.get_persona_stats(),
            "memory_stats": self.memory_manager.get_memory_stats()
        }

    def _source_labels(self, documents: List[Dict[str, Any]]) -> List[str]:
        labels: List[str] = []
        for document in documents:
            metadata = document.get("metadata", {})
            label = metadata.get("source") or document.get("id", "")
            if label and label not in labels:
                labels.append(label)
        return labels

# Convenience function for easy access
def create_rag_pipeline(
    router_agent: RouterAgent,
    retriever_agent: RetrieverAgent,
    reranker_agent: RerankerAgent,
    persona_agent: PersonaAgent,
    memory_manager: MemoryManager
) -> RAGPipeline:
    """Create a RAG pipeline with the provided agents.
    
    Args:
        router_agent: Router agent
        retriever_agent: Retriever agent
        reranker_agent: Reranker agent
        persona_agent: Persona agent
        memory_manager: Memory manager
        
    Returns:
        Configured RAGPipeline instance
    """
    return RAGPipeline(
        router_agent=router_agent,
        retriever_agent=retriever_agent,
        reranker_agent=reranker_agent,
        persona_agent=persona_agent,
        memory_manager=memory_manager
    )
