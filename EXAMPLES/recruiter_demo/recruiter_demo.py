#!/usr/bin/env python3
"""
Recruiter Demo - Portfolio Agent for Recruitment

This demo showcases how the Portfolio Agent can be used by recruiters
and hiring managers to evaluate candidates, match skills to job requirements,
and streamline the recruitment process.
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
from portfolio_agent.ingestion.resume_ingestor import ResumeIngestor
from portfolio_agent.ingestion.github_ingestor import GitHubIngestor
from portfolio_agent.vector_stores.faiss_store import FAISSVectorStore
from portfolio_agent.embeddings.openai_embedder import OpenAIEmbedder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RecruiterDemo:
    """Recruiter demo application for candidate evaluation and job matching."""
    
    def __init__(self):
        self.rag_pipeline = None
        self.candidates = {}
        self.job_postings = {}
        self.evaluation_history = []
        
    async def initialize(self):
        """Initialize the RAG pipeline and demo data."""
        logger.info("Initializing Recruiter Demo...")
        
        try:
            # Initialize RAG pipeline
            self.rag_pipeline = RAGPipeline()
            await self.rag_pipeline.initialize()
            
            # Load demo data
            await self.load_demo_data()
            
            logger.info("Recruiter Demo initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize demo: {e}")
            raise
    
    async def load_demo_data(self):
        """Load demo candidates and job postings."""
        logger.info("Loading demo data...")
        
        # Demo candidates
        self.candidates = {
            "candidate_001": {
                "name": "Sarah Johnson",
                "role": "Senior Python Developer",
                "experience": "6 years",
                "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Docker"],
                "education": "BS Computer Science",
                "location": "San Francisco, CA",
                "resume_path": "data/candidates/sarah_johnson_resume.pdf",
                "github_url": "https://github.com/sarahjohnson",
                "portfolio_url": "https://sarahjohnson.dev"
            },
            "candidate_002": {
                "name": "Michael Chen",
                "role": "Full Stack Developer",
                "experience": "4 years",
                "skills": ["JavaScript", "React", "Node.js", "MongoDB", "AWS", "TypeScript"],
                "education": "BS Software Engineering",
                "location": "Seattle, WA",
                "resume_path": "data/candidates/michael_chen_resume.pdf",
                "github_url": "https://github.com/michaelchen",
                "portfolio_url": "https://michaelchen.dev"
            },
            "candidate_003": {
                "name": "Emily Rodriguez",
                "role": "Machine Learning Engineer",
                "experience": "5 years",
                "skills": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "AWS", "Kubernetes"],
                "education": "MS Data Science",
                "location": "Austin, TX",
                "resume_path": "data/candidates/emily_rodriguez_resume.pdf",
                "github_url": "https://github.com/emilyrodriguez",
                "portfolio_url": "https://emilyrodriguez.ai"
            }
        }
        
        # Demo job postings
        self.job_postings = {
            "job_001": {
                "title": "Senior Python Developer",
                "company": "TechCorp Inc.",
                "location": "San Francisco, CA",
                "type": "Full-time",
                "requirements": [
                    "5+ years Python development experience",
                    "Experience with Django or FastAPI frameworks",
                    "PostgreSQL database experience",
                    "AWS cloud services knowledge",
                    "Docker containerization experience",
                    "Team leadership and mentoring skills"
                ],
                "preferred": [
                    "Machine learning experience",
                    "Microservices architecture",
                    "CI/CD pipeline experience",
                    "Agile development methodology"
                ],
                "salary_range": "$120,000 - $160,000",
                "benefits": ["Health insurance", "401k matching", "Stock options", "Flexible PTO"]
            },
            "job_002": {
                "title": "Full Stack Developer",
                "company": "StartupXYZ",
                "location": "Remote",
                "type": "Full-time",
                "requirements": [
                    "3+ years full-stack development experience",
                    "JavaScript/TypeScript proficiency",
                    "React frontend development",
                    "Node.js backend development",
                    "MongoDB or PostgreSQL experience",
                    "Git version control"
                ],
                "preferred": [
                    "AWS or Google Cloud experience",
                    "GraphQL API development",
                    "Testing frameworks (Jest, Cypress)",
                    "Startup experience"
                ],
                "salary_range": "$90,000 - $130,000",
                "benefits": ["Health insurance", "Stock options", "Remote work", "Learning budget"]
            },
            "job_003": {
                "title": "Machine Learning Engineer",
                "company": "AI Solutions Ltd.",
                "location": "Austin, TX",
                "type": "Full-time",
                "requirements": [
                    "4+ years machine learning experience",
                    "Python programming proficiency",
                    "TensorFlow or PyTorch experience",
                    "Data preprocessing and feature engineering",
                    "Model deployment and MLOps",
                    "Cloud platform experience (AWS/GCP/Azure)"
                ],
                "preferred": [
                    "Deep learning specialization",
                    "NLP or computer vision experience",
                    "Kubernetes container orchestration",
                    "PhD in related field"
                ],
                "salary_range": "$130,000 - $180,000",
                "benefits": ["Health insurance", "401k matching", "Stock options", "Conference budget"]
            }
        }
        
        logger.info(f"Loaded {len(self.candidates)} candidates and {len(self.job_postings)} job postings")
    
    async def evaluate_candidate(self, candidate_id: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate a candidate against job requirements."""
        logger.info(f"Evaluating candidate {candidate_id} for job {job_id}")
        
        if candidate_id not in self.candidates:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        candidate = self.candidates[candidate_id]
        job = self.job_postings.get(job_id) if job_id else None
        
        # Build evaluation query
        if job:
            query = f"""
            Evaluate candidate {candidate['name']} for the {job['title']} position at {job['company']}.
            
            Candidate Profile:
            - Role: {candidate['role']}
            - Experience: {candidate['experience']}
            - Skills: {', '.join(candidate['skills'])}
            - Education: {candidate['education']}
            - Location: {candidate['location']}
            
            Job Requirements:
            {chr(10).join(f"- {req}" for req in job['requirements'])}
            
            Preferred Qualifications:
            {chr(10).join(f"- {pref}" for pref in job.get('preferred', []))}
            
            Please provide:
            1. Overall fit score (0-100)
            2. Technical skills assessment
            3. Experience evaluation
            4. Cultural fit assessment
            5. Strengths and weaknesses
            6. Interview recommendations
            7. Salary expectation analysis
            """
        else:
            query = f"""
            Provide a comprehensive evaluation of candidate {candidate['name']}.
            
            Candidate Profile:
            - Role: {candidate['role']}
            - Experience: {candidate['experience']}
            - Skills: {', '.join(candidate['skills'])}
            - Education: {candidate['education']}
            - Location: {candidate['location']}
            
            Please provide:
            1. Overall candidate assessment
            2. Technical skills analysis
            3. Experience evaluation
            4. Strengths and areas for improvement
            5. Recommended roles and companies
            6. Interview preparation suggestions
            """
        
        try:
            # Run evaluation through RAG pipeline
            result = await self.rag_pipeline.run(
                query=query,
                user_id="recruiter_demo",
                session_id=f"evaluation_{candidate_id}_{job_id or 'general'}"
            )
            
            # Store evaluation in history
            evaluation = {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "timestamp": datetime.now().isoformat(),
                "evaluation": result,
                "candidate": candidate,
                "job": job
            }
            self.evaluation_history.append(evaluation)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating candidate {candidate_id}: {e}")
            raise
    
    async def match_candidates_to_job(self, job_id: str, max_candidates: int = 5) -> List[Dict[str, Any]]:
        """Match candidates to a specific job posting."""
        logger.info(f"Matching candidates to job {job_id}")
        
        if job_id not in self.job_postings:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.job_postings[job_id]
        matches = []
        
        for candidate_id, candidate in self.candidates.items():
            try:
                # Quick match query
                query = f"""
                Rate the match between candidate {candidate['name']} and the {job['title']} position.
                
                Candidate Skills: {', '.join(candidate['skills'])}
                Job Requirements: {', '.join(job['requirements'])}
                
                Provide a match score (0-100) and brief reasoning.
                """
                
                result = await self.rag_pipeline.run(
                    query=query,
                    user_id="recruiter_demo",
                    session_id=f"match_{job_id}_{candidate_id}"
                )
                
                # Extract score from response (simplified)
                score = self._extract_score(result.get('response', ''))
                
                matches.append({
                    "candidate_id": candidate_id,
                    "candidate": candidate,
                    "match_score": score,
                    "reasoning": result.get('response', ''),
                    "job": job
                })
                
            except Exception as e:
                logger.error(f"Error matching candidate {candidate_id} to job {job_id}: {e}")
                continue
        
        # Sort by match score and return top candidates
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:max_candidates]
    
    async def generate_interview_questions(self, candidate_id: str, job_id: str, 
                                         question_type: str = "technical") -> List[str]:
        """Generate interview questions for a candidate."""
        logger.info(f"Generating {question_type} interview questions for candidate {candidate_id}")
        
        if candidate_id not in self.candidates:
            raise ValueError(f"Candidate {candidate_id} not found")
        if job_id not in self.job_postings:
            raise ValueError(f"Job {job_id} not found")
        
        candidate = self.candidates[candidate_id]
        job = self.job_postings[job_id]
        
        query = f"""
        Generate 5 {question_type} interview questions for candidate {candidate['name']} 
        applying for the {job['title']} position at {job['company']}.
        
        Candidate Background:
        - Skills: {', '.join(candidate['skills'])}
        - Experience: {candidate['experience']}
        - Education: {candidate['education']}
        
        Job Requirements:
        {chr(10).join(f"- {req}" for req in job['requirements'])}
        
        Please provide:
        1. 5 specific {question_type} questions
        2. Expected answers or key points
        3. Follow-up questions for each
        4. Difficulty level assessment
        """
        
        try:
            result = await self.rag_pipeline.run(
                query=query,
                user_id="recruiter_demo",
                session_id=f"questions_{candidate_id}_{job_id}"
            )
            
            # Parse questions from response (simplified)
            questions = self._extract_questions(result.get('response', ''))
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            raise
    
    def _extract_score(self, response: str) -> int:
        """Extract numerical score from response text."""
        import re
        
        # Look for score patterns like "Score: 85" or "85/100"
        score_patterns = [
            r'score[:\s]+(\d+)',
            r'(\d+)/100',
            r'(\d+)%',
            r'rating[:\s]+(\d+)'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, response.lower())
            if match:
                return int(match.group(1))
        
        # Default score if no pattern found
        return 50
    
    def _extract_questions(self, response: str) -> List[str]:
        """Extract questions from response text."""
        import re
        
        # Split by numbered questions
        questions = re.split(r'\n\s*\d+\.', response)
        questions = [q.strip() for q in questions if q.strip()]
        
        # Clean up questions
        cleaned_questions = []
        for q in questions:
            # Remove common prefixes
            q = re.sub(r'^(question|q)[:\s]*', '', q, flags=re.IGNORECASE)
            # Remove extra whitespace
            q = ' '.join(q.split())
            if q and len(q) > 10:  # Filter out very short fragments
                cleaned_questions.append(q)
        
        return cleaned_questions[:5]  # Return max 5 questions
    
    def display_candidates(self):
        """Display available candidates."""
        print("\n📋 Available Candidates:")
        print("=" * 50)
        
        for candidate_id, candidate in self.candidates.items():
            print(f"\n{candidate_id}: {candidate['name']}")
            print(f"  Role: {candidate['role']}")
            print(f"  Experience: {candidate['experience']}")
            print(f"  Skills: {', '.join(candidate['skills'])}")
            print(f"  Location: {candidate['location']}")
    
    def display_jobs(self):
        """Display available job postings."""
        print("\n💼 Available Job Postings:")
        print("=" * 50)
        
        for job_id, job in self.job_postings.items():
            print(f"\n{job_id}: {job['title']} at {job['company']}")
            print(f"  Location: {job['location']}")
            print(f"  Type: {job['type']}")
            print(f"  Salary: {job['salary_range']}")
            print(f"  Requirements: {len(job['requirements'])} items")
    
    async def interactive_demo(self):
        """Run interactive demo session."""
        print("\n🎯 Recruiter Demo - Interactive Session")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. List candidates")
            print("2. List job postings")
            print("3. Evaluate candidate")
            print("4. Match candidates to job")
            print("5. Generate interview questions")
            print("6. View evaluation history")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            try:
                if choice == "1":
                    self.display_candidates()
                
                elif choice == "2":
                    self.display_jobs()
                
                elif choice == "3":
                    self.display_candidates()
                    candidate_id = input("\nEnter candidate ID: ").strip()
                    self.display_jobs()
                    job_id = input("Enter job ID (or press Enter for general evaluation): ").strip() or None
                    
                    print(f"\n🔍 Evaluating candidate {candidate_id}...")
                    evaluation = await self.evaluate_candidate(candidate_id, job_id)
                    
                    print(f"\n📊 Evaluation Results:")
                    print("=" * 50)
                    print(evaluation['evaluation']['response'])
                
                elif choice == "4":
                    self.display_jobs()
                    job_id = input("\nEnter job ID: ").strip()
                    max_candidates = int(input("Max candidates to return (default 5): ").strip() or "5")
                    
                    print(f"\n🔍 Matching candidates to job {job_id}...")
                    matches = await self.match_candidates_to_job(job_id, max_candidates)
                    
                    print(f"\n📊 Top Matches:")
                    print("=" * 50)
                    for i, match in enumerate(matches, 1):
                        print(f"\n{i}. {match['candidate']['name']} - Score: {match['match_score']}/100")
                        print(f"   Role: {match['candidate']['role']}")
                        print(f"   Skills: {', '.join(match['candidate']['skills'])}")
                        print(f"   Reasoning: {match['reasoning'][:200]}...")
                
                elif choice == "5":
                    self.display_candidates()
                    candidate_id = input("\nEnter candidate ID: ").strip()
                    self.display_jobs()
                    job_id = input("Enter job ID: ").strip()
                    
                    question_types = ["technical", "behavioral", "situational"]
                    print(f"\nQuestion types: {', '.join(question_types)}")
                    question_type = input("Enter question type (default: technical): ").strip() or "technical"
                    
                    print(f"\n🔍 Generating {question_type} interview questions...")
                    questions = await self.generate_interview_questions(candidate_id, job_id, question_type)
                    
                    print(f"\n❓ Interview Questions:")
                    print("=" * 50)
                    for i, question in enumerate(questions, 1):
                        print(f"\n{i}. {question}")
                
                elif choice == "6":
                    print(f"\n📚 Evaluation History ({len(self.evaluation_history)} evaluations):")
                    print("=" * 50)
                    for i, eval_record in enumerate(self.evaluation_history[-5:], 1):  # Show last 5
                        print(f"\n{i}. {eval_record['candidate']['name']} - {eval_record['timestamp']}")
                        if eval_record['job']:
                            print(f"   Job: {eval_record['job']['title']} at {eval_record['job']['company']}")
                        else:
                            print("   Job: General evaluation")
                
                elif choice == "7":
                    print("\n👋 Thank you for using the Recruiter Demo!")
                    break
                
                else:
                    print("❌ Invalid choice. Please try again.")
            
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"Demo error: {e}")

async def main():
    """Main function to run the recruiter demo."""
    print("🚀 Portfolio Agent - Recruiter Demo")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize and run demo
        demo = RecruiterDemo()
        await demo.initialize()
        await demo.interactive_demo()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
