# Recruiter Demo

This demo showcases the Portfolio Agent's capabilities for recruiters and hiring managers. It demonstrates how the RAG system can be used to evaluate candidates, match skills to job requirements, and streamline the recruitment process.

## Features

### Candidate Evaluation
- **Skill Assessment**: Automatically extract and evaluate technical skills from resumes and portfolios
- **Experience Analysis**: Analyze work experience and project history
- **Cultural Fit**: Assess alignment with company values and team dynamics
- **Gap Analysis**: Identify skill gaps and training needs

### Job Matching
- **Requirement Matching**: Match candidate skills against job requirements
- **Scoring System**: Provide quantitative scores for candidate fit
- **Ranking**: Rank candidates based on multiple criteria
- **Recommendations**: Suggest interview questions and focus areas

### Interview Support
- **Question Generation**: Generate relevant interview questions based on candidate profile
- **Technical Assessments**: Create coding challenges and technical tests
- **Behavioral Questions**: Suggest behavioral questions based on experience
- **Follow-up Questions**: Generate follow-up questions for deeper evaluation

## Quick Start

1. **Setup Environment**:
   ```bash
   cd EXAMPLES/recruiter_demo
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ../..
   ```

2. **Configure API Keys**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

3. **Run the Demo**:
   ```bash
   python recruiter_demo.py
   ```

## Usage Examples

### Basic Candidate Evaluation
```python
from portfolio_agent.rag_pipeline import RAGPipeline

# Initialize the RAG pipeline
rag = RAGPipeline()

# Evaluate a candidate
result = await rag.run(
    query="Evaluate this candidate's Python skills and machine learning experience",
    user_id="recruiter_123",
    context={"candidate_id": "candidate_456", "job_role": "ML Engineer"}
)
```

### Job Requirement Matching
```python
# Match candidate against job requirements
result = await rag.run(
    query="How well does this candidate match our Senior Python Developer role?",
    user_id="recruiter_123",
    context={
        "job_requirements": [
            "5+ years Python experience",
            "Django/FastAPI frameworks",
            "PostgreSQL database experience",
            "AWS cloud services",
            "Team leadership experience"
        ],
        "candidate_id": "candidate_456"
    }
)
```

### Interview Question Generation
```python
# Generate interview questions
result = await rag.run(
    query="Generate 5 technical interview questions for this Python developer candidate",
    user_id="recruiter_123",
    context={
        "candidate_id": "candidate_456",
        "job_role": "Senior Python Developer",
        "focus_areas": ["Python", "Django", "AWS", "Leadership"]
    }
)
```

## Configuration

The recruiter demo can be configured through environment variables or a config file:

```yaml
# recruiter_config.yaml
recruiter:
  evaluation:
    skill_weight: 0.4
    experience_weight: 0.3
    cultural_fit_weight: 0.2
    education_weight: 0.1
  
  matching:
    min_score_threshold: 0.7
    max_candidates: 10
    include_reasoning: true
  
  interview:
    question_count: 5
    difficulty_level: "intermediate"
    include_follow_ups: true
```

## API Endpoints

The recruiter demo exposes several specialized endpoints:

- `POST /api/v1/recruiter/evaluate` - Evaluate a candidate
- `POST /api/v1/recruiter/match` - Match candidates to job requirements
- `POST /api/v1/recruiter/questions` - Generate interview questions
- `GET /api/v1/recruiter/candidates` - List evaluated candidates
- `GET /api/v1/recruiter/jobs` - List job postings

## Data Sources

The recruiter demo can ingest data from various sources:

- **Resumes**: PDF, Word, or text format resumes
- **LinkedIn Profiles**: Public LinkedIn profile data
- **GitHub Profiles**: Code repositories and contributions
- **Portfolio Websites**: Personal websites and project showcases
- **Interview Notes**: Previous interview feedback and notes
- **Reference Letters**: Professional references and recommendations

## Security and Privacy

- **PII Protection**: Automatic detection and redaction of sensitive information
- **Data Encryption**: All candidate data is encrypted at rest and in transit
- **Access Control**: Role-based access control for different user types
- **Audit Logging**: Complete audit trail of all evaluation activities
- **Compliance**: GDPR and CCPA compliant data handling

## Integration

The recruiter demo can be integrated with:

- **ATS Systems**: Applicant Tracking Systems like Greenhouse, Lever, Workday
- **HR Platforms**: Human Resources platforms and databases
- **Interview Tools**: Video interview platforms and scheduling tools
- **Assessment Platforms**: Technical assessment and coding challenge platforms

## Customization

### Custom Evaluation Criteria
```python
# Define custom evaluation criteria
custom_criteria = {
    "technical_skills": {
        "weight": 0.4,
        "subcategories": ["programming", "frameworks", "tools", "cloud"]
    },
    "soft_skills": {
        "weight": 0.3,
        "subcategories": ["communication", "leadership", "teamwork", "problem_solving"]
    },
    "experience": {
        "weight": 0.3,
        "subcategories": ["years_experience", "relevant_projects", "industry_experience"]
    }
}
```

### Custom Scoring Algorithms
```python
# Implement custom scoring logic
def custom_scoring_algorithm(candidate_data, job_requirements):
    # Your custom scoring logic here
    technical_score = evaluate_technical_skills(candidate_data, job_requirements)
    experience_score = evaluate_experience(candidate_data, job_requirements)
    cultural_score = evaluate_cultural_fit(candidate_data, job_requirements)
    
    return {
        "overall_score": (technical_score * 0.5 + experience_score * 0.3 + cultural_score * 0.2),
        "technical_score": technical_score,
        "experience_score": experience_score,
        "cultural_score": cultural_score
    }
```

## Monitoring and Analytics

The recruiter demo includes comprehensive monitoring:

- **Evaluation Metrics**: Track evaluation accuracy and consistency
- **Performance Metrics**: Monitor system performance and response times
- **Usage Analytics**: Track feature usage and user engagement
- **Quality Metrics**: Monitor evaluation quality and user satisfaction

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your OpenAI API key is correctly set
2. **Data Loading Issues**: Check that candidate data is properly formatted
3. **Performance Issues**: Monitor system resources and optimize queries
4. **Evaluation Inconsistencies**: Review evaluation criteria and scoring algorithms

### Support

For technical support or questions about the recruiter demo:
- Check the main documentation
- Review the API documentation
- Contact the development team

## Future Enhancements

Planned features for future releases:

- **Video Interview Analysis**: Analyze video interview responses
- **Predictive Analytics**: Predict candidate success and retention
- **Bias Detection**: Detect and mitigate evaluation bias
- **Multi-language Support**: Support for multiple languages
- **Advanced Matching**: Machine learning-based candidate matching