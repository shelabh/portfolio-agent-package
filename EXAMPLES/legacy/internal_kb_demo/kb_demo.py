#!/usr/bin/env python3
"""
Internal Knowledge Base Demo - Portfolio Agent for Team Knowledge Management

This demo showcases how the Portfolio Agent can be used to build and manage
internal knowledge bases for teams and organizations.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add the parent directory to the path to import portfolio_agent
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from portfolio_agent.rag_pipeline import RAGPipeline
from portfolio_agent.config import settings
from portfolio_agent.ingestion.generic_ingestor import GenericIngestor
from portfolio_agent.ingestion.website_ingestor import WebsiteIngestor
from portfolio_agent.vector_stores.faiss_store import FAISSVectorStore
from portfolio_agent.embeddings.openai_embedder import OpenAIEmbedder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeBaseDemo:
    """Knowledge base demo application for team knowledge management."""
    
    def __init__(self):
        self.rag_pipeline = None
        self.workspaces = {}
        self.documents = {}
        self.users = {}
        self.search_history = []
        
    async def initialize(self):
        """Initialize the RAG pipeline and demo data."""
        logger.info("Initializing Knowledge Base Demo...")
        
        try:
            # Initialize RAG pipeline
            self.rag_pipeline = RAGPipeline()
            await self.rag_pipeline.initialize()
            
            # Load demo data
            await self.load_demo_data()
            
            logger.info("Knowledge Base Demo initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize demo: {e}")
            raise
    
    async def load_demo_data(self):
        """Load demo workspaces, documents, and users."""
        logger.info("Loading demo data...")
        
        # Demo users
        self.users = {
            "user_001": {
                "name": "Alice Johnson",
                "role": "Engineering Manager",
                "department": "Engineering",
                "email": "alice.johnson@company.com",
                "permissions": ["read", "write", "admin"]
            },
            "user_002": {
                "name": "Bob Smith",
                "role": "Senior Developer",
                "department": "Engineering",
                "email": "bob.smith@company.com",
                "permissions": ["read", "write"]
            },
            "user_003": {
                "name": "Carol Davis",
                "role": "Product Manager",
                "department": "Product",
                "email": "carol.davis@company.com",
                "permissions": ["read", "write"]
            },
            "user_004": {
                "name": "David Wilson",
                "role": "DevOps Engineer",
                "department": "Engineering",
                "email": "david.wilson@company.com",
                "permissions": ["read", "write"]
            }
        }
        
        # Demo workspaces
        self.workspaces = {
            "workspace_001": {
                "name": "Engineering Documentation",
                "description": "Technical documentation, processes, and best practices for the engineering team",
                "owner": "user_001",
                "members": ["user_001", "user_002", "user_004"],
                "created_at": "2024-01-15T10:00:00Z",
                "tags": ["engineering", "documentation", "processes"]
            },
            "workspace_002": {
                "name": "Product Requirements",
                "description": "Product specifications, user stories, and feature documentation",
                "owner": "user_003",
                "members": ["user_003", "user_001"],
                "created_at": "2024-01-20T14:30:00Z",
                "tags": ["product", "requirements", "features"]
            },
            "workspace_003": {
                "name": "Company Policies",
                "description": "HR policies, company procedures, and compliance documentation",
                "owner": "user_001",
                "members": ["user_001", "user_002", "user_003", "user_004"],
                "created_at": "2024-01-10T09:00:00Z",
                "tags": ["policies", "hr", "compliance"]
            }
        }
        
        # Demo documents
        self.documents = {
            "doc_001": {
                "title": "API Development Guidelines",
                "content": """
                # API Development Guidelines
                
                ## Overview
                This document outlines the standards and best practices for API development at our company.
                
                ## REST API Standards
                - Use HTTP methods appropriately (GET, POST, PUT, DELETE)
                - Follow RESTful URL patterns
                - Use proper HTTP status codes
                - Implement consistent error handling
                
                ## Authentication
                - Use JWT tokens for authentication
                - Implement proper token expiration
                - Use HTTPS for all API endpoints
                
                ## Documentation
                - Document all endpoints using OpenAPI/Swagger
                - Include request/response examples
                - Maintain up-to-date documentation
                
                ## Testing
                - Write unit tests for all endpoints
                - Implement integration tests
                - Use automated testing in CI/CD pipeline
                """,
                "workspace_id": "workspace_001",
                "author": "user_002",
                "created_at": "2024-01-16T11:00:00Z",
                "updated_at": "2024-01-16T11:00:00Z",
                "tags": ["api", "development", "guidelines"],
                "category": "technical"
            },
            "doc_002": {
                "title": "Code Review Process",
                "content": """
                # Code Review Process
                
                ## Purpose
                Code reviews ensure code quality, knowledge sharing, and maintainability.
                
                ## Process
                1. Create feature branch from main
                2. Implement changes with tests
                3. Create pull request with description
                4. Request review from team members
                5. Address feedback and make changes
                6. Merge after approval
                
                ## Review Guidelines
                - Check for code quality and standards
                - Verify test coverage
                - Ensure security best practices
                - Review for performance implications
                - Check documentation updates
                
                ## Approval Requirements
                - At least one senior developer approval
                - All CI/CD checks must pass
                - No outstanding security issues
                """,
                "workspace_id": "workspace_001",
                "author": "user_001",
                "created_at": "2024-01-18T15:30:00Z",
                "updated_at": "2024-01-18T15:30:00Z",
                "tags": ["code-review", "process", "quality"],
                "category": "process"
            },
            "doc_003": {
                "title": "User Authentication Feature Requirements",
                "content": """
                # User Authentication Feature Requirements
                
                ## Overview
                Implement secure user authentication system for our application.
                
                ## Functional Requirements
                - User registration with email verification
                - Secure login with password
                - Password reset functionality
                - Two-factor authentication (2FA)
                - Session management
                
                ## Security Requirements
                - Password hashing using bcrypt
                - Rate limiting on login attempts
                - Account lockout after failed attempts
                - Secure session tokens
                - HTTPS enforcement
                
                ## User Experience
                - Simple registration flow
                - Clear error messages
                - Remember me functionality
                - Social login options (Google, GitHub)
                
                ## Technical Requirements
                - JWT token-based authentication
                - Refresh token mechanism
                - Database schema for user data
                - API endpoints for auth operations
                """,
                "workspace_id": "workspace_002",
                "author": "user_003",
                "created_at": "2024-01-22T09:15:00Z",
                "updated_at": "2024-01-22T09:15:00Z",
                "tags": ["authentication", "security", "features"],
                "category": "requirements"
            },
            "doc_004": {
                "title": "Remote Work Policy",
                "content": """
                # Remote Work Policy
                
                ## Policy Statement
                Our company supports flexible remote work arrangements to promote work-life balance and productivity.
                
                ## Eligibility
                - All employees are eligible for remote work
                - Manager approval required for full remote
                - Performance and productivity standards apply
                
                ## Guidelines
                - Maintain regular communication with team
                - Use company-approved tools and platforms
                - Ensure secure internet connection
                - Follow data security protocols
                
                ## Equipment and Setup
                - Company provides laptop and necessary equipment
                - Home office setup requirements
                - IT support available for remote workers
                
                ## Communication
                - Daily standup meetings required
                - Use Slack for team communication
                - Video calls for important meetings
                - Regular check-ins with manager
                """,
                "workspace_id": "workspace_003",
                "author": "user_001",
                "created_at": "2024-01-12T16:45:00Z",
                "updated_at": "2024-01-12T16:45:00Z",
                "tags": ["remote-work", "policy", "hr"],
                "category": "policy"
            }
        }
        
        logger.info(f"Loaded {len(self.users)} users, {len(self.workspaces)} workspaces, and {len(self.documents)} documents")
    
    async def search_knowledge(self, query: str, user_id: str, workspace_id: Optional[str] = None, 
                             max_results: int = 10) -> Dict[str, Any]:
        """Search the knowledge base."""
        logger.info(f"Searching knowledge base for: {query}")
        
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        
        # Build search context
        context = {
            "user": user,
            "workspace_id": workspace_id,
            "max_results": max_results
        }
        
        # Add workspace filter if specified
        if workspace_id:
            if workspace_id not in self.workspaces:
                raise ValueError(f"Workspace {workspace_id} not found")
            
            workspace = self.workspaces[workspace_id]
            if user_id not in workspace["members"]:
                raise ValueError(f"User {user_id} not authorized to access workspace {workspace_id}")
            
            context["workspace"] = workspace
        
        try:
            # Run search through RAG pipeline
            result = await self.rag_pipeline.run(
                query=query,
                user_id=user_id,
                session_id=f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                context=context
            )
            
            # Store search in history
            search_record = {
                "query": query,
                "user_id": user_id,
                "workspace_id": workspace_id,
                "timestamp": datetime.now().isoformat(),
                "results_count": len(result.get('citations', [])),
                "user": user
            }
            self.search_history.append(search_record)
            
            # Add relevant documents from our demo data
            relevant_docs = self._find_relevant_documents(query, workspace_id)
            
            return {
                "query": query,
                "response": result.get('response', ''),
                "citations": result.get('citations', []),
                "metadata": result.get('metadata', {}),
                "relevant_documents": relevant_docs,
                "search_context": context
            }
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            raise
    
    def _find_relevant_documents(self, query: str, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find relevant documents from demo data based on query."""
        relevant_docs = []
        query_lower = query.lower()
        
        for doc_id, doc in self.documents.items():
            # Filter by workspace if specified
            if workspace_id and doc["workspace_id"] != workspace_id:
                continue
            
            # Simple relevance scoring based on keyword matching
            score = 0
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            
            # Check title matches
            if any(word in title_lower for word in query_lower.split()):
                score += 3
            
            # Check content matches
            for word in query_lower.split():
                if word in content_lower:
                    score += 1
            
            # Check tag matches
            for tag in doc["tags"]:
                if tag.lower() in query_lower:
                    score += 2
            
            if score > 0:
                relevant_docs.append({
                    "document_id": doc_id,
                    "title": doc["title"],
                    "workspace_id": doc["workspace_id"],
                    "author": doc["author"],
                    "created_at": doc["created_at"],
                    "tags": doc["tags"],
                    "category": doc["category"],
                    "relevance_score": score,
                    "content_snippet": doc["content"][:200] + "..."
                })
        
        # Sort by relevance score
        relevant_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_docs[:5]  # Return top 5
    
    async def add_document(self, title: str, content: str, workspace_id: str, 
                          author_id: str, tags: List[str] = None) -> str:
        """Add a new document to the knowledge base."""
        logger.info(f"Adding document '{title}' to workspace {workspace_id}")
        
        if author_id not in self.users:
            raise ValueError(f"User {author_id} not found")
        
        if workspace_id not in self.workspaces:
            raise ValueError(f"Workspace {workspace_id} not found")
        
        workspace = self.workspaces[workspace_id]
        if author_id not in workspace["members"]:
            raise ValueError(f"User {author_id} not authorized to add documents to workspace {workspace_id}")
        
        # Generate document ID
        doc_id = f"doc_{len(self.documents) + 1:03d}"
        
        # Create document
        document = {
            "title": title,
            "content": content,
            "workspace_id": workspace_id,
            "author": author_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tags": tags or [],
            "category": "general"
        }
        
        self.documents[doc_id] = document
        
        # Add to RAG pipeline (simplified)
        try:
            # In a real implementation, you would add the document to the vector store
            logger.info(f"Document {doc_id} added successfully")
        except Exception as e:
            logger.error(f"Error adding document to RAG pipeline: {e}")
            # Remove from local storage if RAG pipeline fails
            del self.documents[doc_id]
            raise
        
        return doc_id
    
    async def create_workspace(self, name: str, description: str, owner_id: str, 
                              members: List[str] = None) -> str:
        """Create a new workspace."""
        logger.info(f"Creating workspace '{name}' for user {owner_id}")
        
        if owner_id not in self.users:
            raise ValueError(f"User {owner_id} not found")
        
        # Generate workspace ID
        workspace_id = f"workspace_{len(self.workspaces) + 1:03d}"
        
        # Create workspace
        workspace = {
            "name": name,
            "description": description,
            "owner": owner_id,
            "members": [owner_id] + (members or []),
            "created_at": datetime.now().isoformat(),
            "tags": []
        }
        
        self.workspaces[workspace_id] = workspace
        
        logger.info(f"Workspace {workspace_id} created successfully")
        return workspace_id
    
    def get_workspace_documents(self, workspace_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents in a workspace."""
        if workspace_id not in self.workspaces:
            raise ValueError(f"Workspace {workspace_id} not found")
        
        workspace = self.workspaces[workspace_id]
        if user_id not in workspace["members"]:
            raise ValueError(f"User {user_id} not authorized to access workspace {workspace_id}")
        
        workspace_docs = []
        for doc_id, doc in self.documents.items():
            if doc["workspace_id"] == workspace_id:
                workspace_docs.append({
                    "document_id": doc_id,
                    "title": doc["title"],
                    "author": doc["author"],
                    "created_at": doc["created_at"],
                    "updated_at": doc["updated_at"],
                    "tags": doc["tags"],
                    "category": doc["category"]
                })
        
        return sorted(workspace_docs, key=lambda x: x["updated_at"], reverse=True)
    
    def display_users(self):
        """Display available users."""
        print("\n👥 Available Users:")
        print("=" * 50)
        
        for user_id, user in self.users.items():
            print(f"\n{user_id}: {user['name']}")
            print(f"  Role: {user['role']}")
            print(f"  Department: {user['department']}")
            print(f"  Permissions: {', '.join(user['permissions'])}")
    
    def display_workspaces(self):
        """Display available workspaces."""
        print("\n📁 Available Workspaces:")
        print("=" * 50)
        
        for workspace_id, workspace in self.workspaces.items():
            print(f"\n{workspace_id}: {workspace['name']}")
            print(f"  Description: {workspace['description']}")
            print(f"  Owner: {workspace['owner']}")
            print(f"  Members: {len(workspace['members'])}")
            print(f"  Created: {workspace['created_at']}")
    
    def display_documents(self, workspace_id: Optional[str] = None):
        """Display documents."""
        print(f"\n📄 Documents{' in ' + workspace_id if workspace_id else ''}:")
        print("=" * 50)
        
        for doc_id, doc in self.documents.items():
            if workspace_id and doc["workspace_id"] != workspace_id:
                continue
            
            print(f"\n{doc_id}: {doc['title']}")
            print(f"  Workspace: {doc['workspace_id']}")
            print(f"  Author: {doc['author']}")
            print(f"  Created: {doc['created_at']}")
            print(f"  Tags: {', '.join(doc['tags'])}")
    
    async def interactive_demo(self):
        """Run interactive demo session."""
        print("\n🧠 Knowledge Base Demo - Interactive Session")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. List users")
            print("2. List workspaces")
            print("3. List documents")
            print("4. Search knowledge base")
            print("5. Add document")
            print("6. Create workspace")
            print("7. View workspace documents")
            print("8. View search history")
            print("9. Exit")
            
            choice = input("\nEnter your choice (1-9): ").strip()
            
            try:
                if choice == "1":
                    self.display_users()
                
                elif choice == "2":
                    self.display_workspaces()
                
                elif choice == "3":
                    self.display_documents()
                
                elif choice == "4":
                    self.display_users()
                    user_id = input("\nEnter user ID: ").strip()
                    self.display_workspaces()
                    workspace_id = input("Enter workspace ID (or press Enter for global search): ").strip() or None
                    query = input("Enter search query: ").strip()
                    max_results = int(input("Max results (default 10): ").strip() or "10")
                    
                    print(f"\n🔍 Searching knowledge base...")
                    results = await self.search_knowledge(query, user_id, workspace_id, max_results)
                    
                    print(f"\n📊 Search Results:")
                    print("=" * 50)
                    print(f"Query: {results['query']}")
                    print(f"\nResponse: {results['response']}")
                    
                    if results['relevant_documents']:
                        print(f"\n📄 Relevant Documents:")
                        for i, doc in enumerate(results['relevant_documents'], 1):
                            print(f"\n{i}. {doc['title']} (Score: {doc['relevance_score']})")
                            print(f"   Workspace: {doc['workspace_id']}")
                            print(f"   Author: {doc['author']}")
                            print(f"   Tags: {', '.join(doc['tags'])}")
                            print(f"   Snippet: {doc['content_snippet']}")
                
                elif choice == "5":
                    self.display_users()
                    author_id = input("\nEnter author user ID: ").strip()
                    self.display_workspaces()
                    workspace_id = input("Enter workspace ID: ").strip()
                    title = input("Enter document title: ").strip()
                    content = input("Enter document content: ").strip()
                    tags_input = input("Enter tags (comma-separated): ").strip()
                    tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
                    
                    print(f"\n📝 Adding document...")
                    doc_id = await self.add_document(title, content, workspace_id, author_id, tags)
                    print(f"✅ Document {doc_id} added successfully")
                
                elif choice == "6":
                    self.display_users()
                    owner_id = input("\nEnter owner user ID: ").strip()
                    name = input("Enter workspace name: ").strip()
                    description = input("Enter workspace description: ").strip()
                    members_input = input("Enter member user IDs (comma-separated): ").strip()
                    members = [member.strip() for member in members_input.split(",")] if members_input else []
                    
                    print(f"\n📁 Creating workspace...")
                    workspace_id = await self.create_workspace(name, description, owner_id, members)
                    print(f"✅ Workspace {workspace_id} created successfully")
                
                elif choice == "7":
                    self.display_workspaces()
                    workspace_id = input("\nEnter workspace ID: ").strip()
                    self.display_users()
                    user_id = input("Enter user ID: ").strip()
                    
                    print(f"\n📄 Documents in workspace {workspace_id}:")
                    documents = self.get_workspace_documents(workspace_id, user_id)
                    
                    if documents:
                        for i, doc in enumerate(documents, 1):
                            print(f"\n{i}. {doc['title']}")
                            print(f"   Author: {doc['author']}")
                            print(f"   Created: {doc['created_at']}")
                            print(f"   Tags: {', '.join(doc['tags'])}")
                    else:
                        print("No documents found in this workspace")
                
                elif choice == "8":
                    print(f"\n📚 Search History ({len(self.search_history)} searches):")
                    print("=" * 50)
                    for i, search in enumerate(self.search_history[-10:], 1):  # Show last 10
                        print(f"\n{i}. Query: {search['query']}")
                        print(f"   User: {search['user']['name']}")
                        print(f"   Workspace: {search['workspace_id'] or 'Global'}")
                        print(f"   Results: {search['results_count']}")
                        print(f"   Time: {search['timestamp']}")
                
                elif choice == "9":
                    print("\n👋 Thank you for using the Knowledge Base Demo!")
                    break
                
                else:
                    print("❌ Invalid choice. Please try again.")
            
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"Demo error: {e}")

async def main():
    """Main function to run the knowledge base demo."""
    print("🚀 Portfolio Agent - Knowledge Base Demo")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize and run demo
        demo = KnowledgeBaseDemo()
        await demo.initialize()
        await demo.interactive_demo()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
