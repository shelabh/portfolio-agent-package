"""
Router Agent for portfolio-agent.

This module provides query classification and routing functionality to determine
which agents should handle specific queries.
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries that can be routed."""
    GENERAL = "general"
    TECHNICAL = "technical"
    PERSONAL = "personal"
    PROJECT = "project"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CONTACT = "contact"
    UNKNOWN = "unknown"

@dataclass
class RoutingDecision:
    """Decision made by the router agent."""
    query_type: QueryType
    confidence: float
    reasoning: str
    suggested_agents: List[str]
    metadata: Dict[str, Any]

class RouterAgent:
    """Router agent for query classification and routing."""
    
    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize router agent.
        
        Args:
            confidence_threshold: Minimum confidence for routing decisions
        """
        self.confidence_threshold = confidence_threshold
        
        # Define routing patterns and keywords
        self.routing_patterns = {
            QueryType.TECHNICAL: {
                "keywords": [
                    "programming", "code", "algorithm", "software", "development",
                    "python", "javascript", "react", "node", "api", "database",
                    "machine learning", "ai", "data science", "backend", "frontend",
                    "architecture", "design pattern", "testing", "deployment"
                ],
                "agents": ["retriever", "persona"]
            },
            QueryType.PROJECT: {
                "keywords": [
                    "project", "portfolio", "work", "built", "developed", "created",
                    "implemented", "designed", "launched", "deployed", "github",
                    "repository", "demo", "showcase", "case study"
                ],
                "agents": ["retriever", "persona"]
            },
            QueryType.EXPERIENCE: {
                "keywords": [
                    "experience", "background", "career", "work history", "job",
                    "position", "role", "responsibilities", "achievements", "skills",
                    "expertise", "years", "professional", "industry"
                ],
                "agents": ["retriever", "persona"]
            },
            QueryType.EDUCATION: {
                "keywords": [
                    "education", "degree", "university", "college", "school",
                    "graduated", "major", "minor", "certification", "course",
                    "learning", "studied", "academic", "qualification"
                ],
                "agents": ["retriever", "persona"]
            },
            QueryType.CONTACT: {
                "keywords": [
                    "contact", "email", "phone", "linkedin", "github", "website",
                    "reach", "connect", "get in touch", "hire", "collaborate",
                    "available", "location", "timezone"
                ],
                "agents": ["persona"]
            },
            QueryType.PERSONAL: {
                "keywords": [
                    "about", "who", "personal", "interests", "hobbies", "passion",
                    "motivation", "goals", "values", "philosophy", "story",
                    "background", "journey", "inspiration"
                ],
                "agents": ["persona"]
            }
        }
        
        # Default routing for unknown queries
        self.default_agents = ["retriever", "persona"]
        
        logger.info("Router agent initialized")
    
    def route_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """Route a query to appropriate agents.
        
        Args:
            query: The user query to route
            context: Optional context information
            
        Returns:
            RoutingDecision with routing information
        """
        logger.info(f"Routing query: {query[:100]}...")
        
        # Analyze the query
        query_lower = query.lower().strip()
        
        # Calculate scores for each query type
        type_scores = {}
        for query_type, pattern_info in self.routing_patterns.items():
            score = self._calculate_type_score(query_lower, pattern_info["keywords"])
            type_scores[query_type] = score
        
        # Find the best match
        best_type = max(type_scores.items(), key=lambda x: x[1])
        query_type, confidence = best_type
        
        # Determine suggested agents
        if confidence >= self.confidence_threshold:
            suggested_agents = self.routing_patterns[query_type]["agents"]
            reasoning = f"Query classified as {query_type.value} with {confidence:.2f} confidence"
        else:
            query_type = QueryType.UNKNOWN
            suggested_agents = self.default_agents
            reasoning = f"Low confidence ({confidence:.2f}), using default routing"
        
        # Create routing decision
        decision = RoutingDecision(
            query_type=query_type,
            confidence=confidence,
            reasoning=reasoning,
            suggested_agents=suggested_agents,
            metadata={
                "all_scores": {k.value: v for k, v in type_scores.items()},
                "query_length": len(query),
                "context_provided": context is not None
            }
        )
        
        logger.info(f"Routing decision: {query_type.value} -> {suggested_agents}")
        return decision
    
    def _calculate_type_score(self, query: str, keywords: List[str]) -> float:
        """Calculate score for a query type based on keyword matching.
        
        Args:
            query: The query text
            keywords: List of keywords for the type
            
        Returns:
            Score between 0 and 1
        """
        if not query or not keywords:
            return 0.0
        
        # Count keyword matches
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword in query:
                matches += 1
        
        # Calculate base score
        base_score = matches / total_keywords if total_keywords > 0 else 0.0
        
        # Boost score for exact phrase matches
        phrase_boost = 0.0
        for keyword in keywords:
            if keyword in query:
                # Check if it's a phrase (multiple words)
                if len(keyword.split()) > 1:
                    phrase_boost += 0.1
        
        # Combine scores
        final_score = min(1.0, base_score + phrase_boost)
        
        return final_score
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agents.
        
        Returns:
            List of agent names
        """
        return ["retriever", "reranker", "persona", "memory"]
    
    def validate_routing_decision(self, decision: RoutingDecision) -> bool:
        """Validate a routing decision.
        
        Args:
            decision: The routing decision to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not decision.suggested_agents:
            return False
        
        available_agents = self.get_available_agents()
        for agent in decision.suggested_agents:
            if agent not in available_agents:
                logger.warning(f"Invalid agent in routing decision: {agent}")
                return False
        
        if decision.confidence < 0.0 or decision.confidence > 1.0:
            logger.warning(f"Invalid confidence score: {decision.confidence}")
            return False
        
        return True
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics.
        
        Returns:
            Dictionary with routing statistics
        """
        return {
            "total_patterns": len(self.routing_patterns),
            "confidence_threshold": self.confidence_threshold,
            "available_agents": self.get_available_agents(),
            "query_types": [qt.value for qt in QueryType]
        }

# Convenience function for easy access
def create_router_agent(**kwargs) -> RouterAgent:
    """Create a router agent with default settings.
    
    Args:
        **kwargs: Arguments to pass to RouterAgent
        
    Returns:
        Configured RouterAgent instance
    """
    return RouterAgent(**kwargs)