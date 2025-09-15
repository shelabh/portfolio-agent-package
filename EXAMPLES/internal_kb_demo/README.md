# Internal Knowledge Base Demo

This demo showcases the Portfolio Agent's capabilities for building and managing internal knowledge bases for teams and organizations. It demonstrates how the RAG system can be used to create a collaborative knowledge management platform.

## Features

### Knowledge Management
- **Document Ingestion**: Support for various document formats (PDF, Word, Markdown, etc.)
- **Content Organization**: Automatic categorization and tagging of content
- **Version Control**: Track changes and maintain document versions
- **Search and Discovery**: Powerful semantic search across all knowledge

### Team Collaboration
- **Shared Workspaces**: Team-specific knowledge spaces
- **Content Sharing**: Easy sharing of knowledge across teams
- **Collaborative Editing**: Multiple users can contribute to knowledge
- **Access Control**: Role-based permissions and content visibility

### Knowledge Discovery
- **Semantic Search**: Find relevant information using natural language
- **Related Content**: Discover related documents and topics
- **Knowledge Graphs**: Visualize relationships between concepts
- **Trending Topics**: Identify popular and emerging topics

### Content Intelligence
- **Auto-Summarization**: Generate summaries of long documents
- **Key Phrase Extraction**: Identify important concepts and terms
- **Content Recommendations**: Suggest relevant content to users
- **Duplicate Detection**: Identify and merge duplicate content

## Quick Start

1. **Setup Environment**:
   ```bash
   cd EXAMPLES/internal_kb_demo
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
   python kb_demo.py
   ```

## Usage Examples

### Basic Knowledge Search
```python
from portfolio_agent.rag_pipeline import RAGPipeline

# Initialize the RAG pipeline
rag = RAGPipeline()

# Search for information
result = await rag.run(
    query="How do we handle customer onboarding?",
    user_id="employee_123",
    context={"team": "customer_success", "department": "operations"}
)
```

### Document Ingestion
```python
from portfolio_agent.ingestion.generic_ingestor import GenericIngestor

# Ingest a document
ingestor = GenericIngestor()
document = await ingestor.ingest_file("path/to/document.pdf")

# Add to knowledge base
await rag.add_document(document)
```

### Team Workspace Management
```python
# Create a team workspace
workspace = await rag.create_workspace(
    name="Engineering Team",
    description="Technical documentation and processes",
    members=["engineer1", "engineer2", "tech_lead"]
)

# Add documents to workspace
await rag.add_document_to_workspace(
    document_id="doc_123",
    workspace_id=workspace.id
)
```

## Configuration

The knowledge base demo can be configured through environment variables or a config file:

```yaml
# kb_config.yaml
knowledge_base:
  workspaces:
    default_workspace: "general"
    max_workspaces_per_user: 10
    max_documents_per_workspace: 1000
  
  content:
    supported_formats: ["pdf", "docx", "txt", "md", "html"]
    max_file_size: "10MB"
    auto_categorization: true
    duplicate_detection: true
  
  search:
    default_results: 10
    max_results: 100
    enable_semantic_search: true
    enable_keyword_search: true
  
  collaboration:
    enable_sharing: true
    enable_comments: true
    enable_version_control: true
    max_versions_per_document: 50
```

## API Endpoints

The knowledge base demo exposes several specialized endpoints:

- `POST /api/v1/kb/search` - Search knowledge base
- `POST /api/v1/kb/upload` - Upload documents
- `GET /api/v1/kb/workspaces` - List workspaces
- `POST /api/v1/kb/workspaces` - Create workspace
- `GET /api/v1/kb/documents` - List documents
- `POST /api/v1/kb/documents` - Add document
- `GET /api/v1/kb/suggestions` - Get content suggestions

## Data Sources

The knowledge base demo can ingest data from various sources:

- **Documents**: PDF, Word, Markdown, HTML, plain text
- **Web Pages**: Company websites, documentation sites
- **Confluence**: Atlassian Confluence pages
- **Notion**: Notion databases and pages
- **GitHub**: Repository documentation and README files
- **Slack**: Channel messages and shared files
- **Email**: Important email threads and attachments

## Security and Privacy

- **Access Control**: Role-based permissions for workspaces and documents
- **Data Encryption**: All content encrypted at rest and in transit
- **Audit Logging**: Complete audit trail of all knowledge activities
- **Compliance**: GDPR and SOC2 compliant data handling
- **Data Retention**: Configurable retention policies

## Integration

The knowledge base demo can be integrated with:

- **Confluence**: Import existing Confluence spaces
- **Notion**: Sync Notion databases and pages
- **Slack**: Index Slack messages and files
- **GitHub**: Import repository documentation
- **SharePoint**: Sync SharePoint document libraries
- **Google Drive**: Import Google Drive documents

## Customization

### Custom Document Processors
```python
# Define custom document processor
class CustomDocumentProcessor:
    def process(self, document):
        # Custom processing logic
        processed_doc = {
            "content": document.content,
            "metadata": self.extract_metadata(document),
            "categories": self.categorize(document),
            "tags": self.extract_tags(document)
        }
        return processed_doc
    
    def extract_metadata(self, document):
        # Extract custom metadata
        pass
    
    def categorize(self, document):
        # Custom categorization logic
        pass
    
    def extract_tags(self, document):
        # Custom tag extraction
        pass
```

### Custom Search Algorithms
```python
# Implement custom search logic
def custom_search(query, documents, user_context):
    # Custom search algorithm
    semantic_results = semantic_search(query, documents)
    keyword_results = keyword_search(query, documents)
    collaborative_results = collaborative_filtering(query, user_context)
    
    # Combine and rank results
    combined_results = combine_results(
        semantic_results, 
        keyword_results, 
        collaborative_results
    )
    
    return rank_results(combined_results, user_context)
```

## Monitoring and Analytics

The knowledge base demo includes comprehensive monitoring:

- **Usage Metrics**: Track search queries and document access
- **Content Metrics**: Monitor document creation and updates
- **User Engagement**: Track user activity and engagement
- **Performance Metrics**: Monitor search performance and response times

## Troubleshooting

### Common Issues

1. **Document Upload Failures**: Check file format and size limits
2. **Search Performance**: Optimize vector indexes and caching
3. **Access Control Issues**: Verify user permissions and workspace settings
4. **Content Duplication**: Review duplicate detection settings

### Support

For technical support or questions about the knowledge base demo:
- Check the main documentation
- Review the API documentation
- Contact the development team

## Future Enhancements

Planned features for future releases:

- **AI-Powered Content Generation**: Generate documentation and summaries
- **Advanced Analytics**: Content usage and engagement analytics
- **Mobile App**: Mobile application for knowledge access
- **Voice Search**: Voice-activated knowledge search
- **Integration Hub**: Pre-built integrations with popular tools