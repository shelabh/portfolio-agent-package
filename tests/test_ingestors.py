"""
Tests for ingestion modules.

This module tests all ingestion functionality including:
- GitHub ingestor
- Resume ingestor  
- Website ingestor
- Generic ingestor
- PII redaction
- Text chunking
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from portfolio_agent.ingestion import (
    GitHubIngestor, ResumeIngestor, WebsiteIngestor, GenericIngestor,
    PIIRedactor, TextChunker, pii_redactor, text_chunker
)


class TestPIIRedactor:
    """Test PII redaction functionality."""
    
    def test_init(self):
        """Test PII redactor initialization."""
        redactor = PIIRedactor()
        assert len(redactor.patterns) > 0
        assert 'email' in redactor.patterns
        assert 'phone' in redactor.patterns
    
    def test_redact_email(self):
        """Test email redaction."""
        text = "Contact me at john.doe@example.com for more info."
        redacted, stats = pii_redactor.redact_pii(text)
        
        assert "[REDACTED]" in redacted
        assert "john.doe@example.com" not in redacted
        assert stats['email'] == 1
    
    def test_redact_phone(self):
        """Test phone number redaction."""
        text = "Call me at (555) 123-4567 or 555-123-4567"
        redacted, stats = pii_redactor.redact_pii(text)
        
        assert "[REDACTED]" in redacted
        assert "(555) 123-4567" not in redacted
        assert "555-123-4567" not in redacted
        assert stats['phone'] >= 1
    
    def test_redact_ssn(self):
        """Test SSN redaction."""
        text = "My SSN is 123-45-6789"
        redacted, stats = pii_redactor.redact_pii(text)
        
        assert "[REDACTED]" in redacted
        assert "123-45-6789" not in redacted
        assert stats['ssn'] == 1
    
    def test_redact_credit_card(self):
        """Test credit card redaction."""
        text = "Card number: 1234-5678-9012-3456"
        redacted, stats = pii_redactor.redact_pii(text)
        
        assert "[REDACTED]" in redacted
        assert "1234-5678-9012-3456" not in redacted
        assert stats['credit_card'] == 1
    
    def test_redact_api_keys(self):
        """Test API key redaction."""
        text = "API key: sk-1234567890abcdef1234567890abcdef1234567890abcdef"
        redacted, stats = pii_redactor.redact_pii(text)
        
        assert "[REDACTED]" in redacted
        assert "sk-1234567890abcdef1234567890abcdef1234567890abcdef" not in redacted
        # Check if any API key pattern matched
        assert sum(stats.values()) > 0
    
    def test_no_pii_found(self):
        """Test text with no PII."""
        text = "This is just regular text with no sensitive information."
        redacted, stats = pii_redactor.redact_pii(text)
        
        assert redacted == text
        assert sum(stats.values()) == 0
    
    def test_custom_pattern(self):
        """Test custom PII pattern."""
        redactor = PIIRedactor()
        redactor.add_custom_pattern('custom_id', r'ID:\s*(\d{6})')
        
        text = "User ID: 123456"
        redacted, stats = redactor.redact_pii(text)
        
        assert "[REDACTED]" in redacted
        assert "123456" not in redacted
        assert stats['custom_id'] == 1
    
    def test_validate_text(self):
        """Test PII validation without redaction."""
        text = "Email: test@example.com, Phone: 555-123-4567"
        validation = pii_redactor.validate_text(text)
        
        assert validation['email'] is True
        assert validation['phone'] is True
        assert validation['ssn'] is False


class TestTextChunker:
    """Test text chunking functionality."""
    
    def test_init(self):
        """Test chunker initialization."""
        chunker = TextChunker(chunk_size=500, chunk_overlap=100)
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 100
        assert chunker.preserve_sentences is True
    
    def test_small_text(self):
        """Test chunking small text."""
        text = "This is a short text."
        metadata = {'source': 'test.txt', 'source_type': 'file'}
        
        chunks = text_chunker.chunk_text(text, metadata)
        
        assert len(chunks) == 1
        assert chunks[0]['content'] == text
        assert chunks[0]['metadata']['source'] == 'test.txt'
        assert chunks[0]['metadata']['chunk_index'] == 0
    
    def test_large_text(self):
        """Test chunking large text."""
        # Create text longer than default chunk size
        text = "This is a sentence. " * 100  # ~2000 characters
        metadata = {'source': 'test.txt', 'source_type': 'file'}
        
        chunks = text_chunker.chunk_text(text, metadata)
        
        assert len(chunks) > 1
        assert all(chunk['metadata']['chunk_size'] <= text_chunker.chunk_size for chunk in chunks)
        assert all(chunk['metadata']['chunk_index'] == i for i, chunk in enumerate(chunks))
    
    def test_chunk_overlap(self):
        """Test chunk overlap functionality."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a longer text that should be split into multiple chunks with overlap."
        metadata = {'source': 'test.txt', 'source_type': 'file'}
        
        chunks = chunker.chunk_text(text, metadata)
        
        assert len(chunks) > 1
        # Check that chunks have proper start/end positions
        for i, chunk in enumerate(chunks):
            assert chunk['metadata']['chunk_start'] >= 0
            assert chunk['metadata']['chunk_end'] <= len(text)
    
    def test_sentence_boundary_preservation(self):
        """Test sentence boundary preservation."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20, preserve_sentences=True)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        metadata = {'source': 'test.txt', 'source_type': 'file'}
        
        chunks = chunker.chunk_text(text, metadata)
        
        # Check that chunks end at sentence boundaries when possible
        for chunk in chunks:
            content = chunk['content']
            if not content.endswith('.'):
                # If it doesn't end with period, it should be the last chunk or very short
                assert len(content) < chunker.chunk_size * 0.5 or chunk == chunks[-1]
    
    def test_paragraph_chunking(self):
        """Test paragraph-based chunking."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        metadata = {'source': 'test.txt', 'source_type': 'file'}
        
        chunks = text_chunker.chunk_by_paragraphs(text, metadata)
        
        assert len(chunks) == 3
        assert "First paragraph." in chunks[0]['content']
        assert "Second paragraph." in chunks[1]['content']
        assert "Third paragraph." in chunks[2]['content']
    
    def test_section_chunking(self):
        """Test section-based chunking."""
        text = "# Header 1\nContent 1\n\n## Header 2\nContent 2"
        metadata = {'source': 'test.txt', 'source_type': 'file'}
        
        chunks = text_chunker.chunk_by_sections(text, metadata)
        
        assert len(chunks) >= 1
        # Should have at least one chunk with header content
        assert any('Header' in chunk['content'] for chunk in chunks)


class TestGitHubIngestor:
    """Test GitHub ingestor functionality."""
    
    def test_init(self):
        """Test GitHub ingestor initialization."""
        ingestor = GitHubIngestor(api_token="test_token", max_files=10)
        assert ingestor.api_token == "test_token"
        assert ingestor.max_files == 10
        assert ingestor.base_url == "https://api.github.com"
    
    def test_parse_repo_url(self):
        """Test repository URL parsing."""
        ingestor = GitHubIngestor()
        
        # Test HTTPS URL
        result = ingestor._parse_repo_url("https://github.com/user/repo")
        assert result == {'owner': 'user', 'repo': 'repo'}
        
        # Test SSH URL
        result = ingestor._parse_repo_url("git@github.com:user/repo.git")
        assert result == {'owner': 'user', 'repo': 'repo'}
        
        # Test invalid URL
        result = ingestor._parse_repo_url("https://example.com/user/repo")
        assert result is None
    
    def test_is_code_file(self):
        """Test code file detection."""
        ingestor = GitHubIngestor()
        
        assert ingestor._is_code_file("script.py") is True
        assert ingestor._is_code_file("app.js") is True
        assert ingestor._is_code_file("README.md") is True
        assert ingestor._is_code_file("image.png") is False
        assert ingestor._is_code_file("data.csv") is False
    
    @patch('portfolio_agent.ingestion.github_ingestor.requests.Session.get')
    def test_fetch_repository_info(self, mock_get):
        """Test repository info fetching."""
        ingestor = GitHubIngestor()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            'name': 'test-repo',
            'full_name': 'user/test-repo',
            'description': 'Test repository',
            'language': 'Python',
            'stargazers_count': 42
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = ingestor._fetch_repository_info('user', 'test-repo')
        
        assert result['name'] == 'test-repo'
        assert result['full_name'] == 'user/test-repo'
        mock_get.assert_called_once()
    
    @patch('portfolio_agent.ingestion.github_ingestor.requests.Session.get')
    def test_fetch_readme(self, mock_get):
        """Test README fetching."""
        ingestor = GitHubIngestor()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': 'IyBUZXN0IFJFQURNRSBGaWxl'  # Base64 encoded "# Test README File"
        }
        mock_get.return_value = mock_response
        
        result = ingestor._fetch_readme('user', 'test-repo')
        
        assert "# Test README File" in result
        mock_get.assert_called_once()
    
    @patch('portfolio_agent.ingestion.github_ingestor.GitHubIngestor._fetch_repository_info')
    @patch('portfolio_agent.ingestion.github_ingestor.GitHubIngestor._fetch_readme')
    @patch('portfolio_agent.ingestion.github_ingestor.GitHubIngestor._fetch_code_files')
    def test_ingest_success(self, mock_code_files, mock_readme, mock_repo_info):
        """Test successful ingestion."""
        ingestor = GitHubIngestor()
        
        # Mock responses
        mock_repo_info.return_value = {'name': 'test-repo', 'full_name': 'user/test-repo'}
        mock_readme.return_value = "# Test README"
        mock_code_files.return_value = []
        
        result = ingestor.ingest("https://github.com/user/test-repo")
        
        assert len(result) > 0
        assert result[0]['metadata']['source_type'] == 'github'
        assert result[0]['metadata']['repository']['name'] == 'test-repo'


class TestResumeIngestor:
    """Test resume ingestor functionality."""
    
    def test_init(self):
        """Test resume ingestor initialization."""
        ingestor = ResumeIngestor(redact_pii=True, prefer_pymupdf=True)
        assert ingestor.redact_pii is True
        assert ingestor.prefer_pymupdf is True
    
    def test_validate_pdf(self):
        """Test PDF validation."""
        ingestor = ResumeIngestor()
        
        # Test with non-existent file
        assert ingestor.validate_pdf("nonexistent.pdf") is False
        
        # Test with non-PDF file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Not a PDF")
            temp_path = f.name
        
        try:
            assert ingestor.validate_pdf(temp_path) is False
        finally:
            os.unlink(temp_path)
    
    def test_get_extraction_method(self):
        """Test extraction method detection."""
        ingestor = ResumeIngestor()
        method = ingestor._get_extraction_method()
        
        # Should return one of the available methods
        assert method in ['pymupdf', 'pypdf', 'none']
    
    def test_extract_metadata(self):
        """Test PDF metadata extraction."""
        ingestor = ResumeIngestor()
        
        # Test with non-existent file
        metadata = ingestor.extract_metadata("nonexistent.pdf")
        assert metadata == {}
        
        # Test with existing file (even if not PDF)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"Not a real PDF")
            temp_path = f.name
        
        try:
            metadata = ingestor.extract_metadata(temp_path)
            assert 'filename' in metadata
            assert 'file_size' in metadata
            assert 'file_extension' in metadata
        finally:
            os.unlink(temp_path)


class TestWebsiteIngestor:
    """Test website ingestor functionality."""
    
    def test_init(self):
        """Test website ingestor initialization."""
        ingestor = WebsiteIngestor(max_depth=3, respect_robots=False, max_pages=50)
        assert ingestor.max_depth == 3
        assert ingestor.respect_robots is False
        assert ingestor.max_pages == 50
        assert ingestor.delay == 1.0
    
    def test_is_content_url(self):
        """Test content URL detection."""
        ingestor = WebsiteIngestor()
        
        assert ingestor._is_content_url("https://example.com/page") is True
        assert ingestor._is_content_url("https://example.com/admin") is False
        assert ingestor._is_content_url("https://example.com/static/style.css") is False
        assert ingestor._is_content_url("https://example.com/api/data") is False
    
    def test_extract_title(self):
        """Test title extraction from HTML."""
        ingestor = WebsiteIngestor()
        
        html = "<html><head><title>Test Page</title></head><body>Content</body></html>"
        title = ingestor._extract_title(html)
        
        assert title == "Test Page"
    
    def test_extract_title_no_title(self):
        """Test title extraction with no title tag."""
        ingestor = WebsiteIngestor()
        
        html = "<html><head></head><body>Content</body></html>"
        title = ingestor._extract_title(html)
        
        assert title == ""
    
    @patch('portfolio_agent.ingestion.website_ingestor.requests.Session.get')
    def test_fetch_page_content(self, mock_get):
        """Test page content fetching."""
        ingestor = WebsiteIngestor()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><head><title>Test</title></head><body>Content</body></html>"
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = ingestor._fetch_page_content("https://example.com")
        
        assert result is not None
        assert result['url'] == "https://example.com"
        assert result['title'] == "Test"
        assert result['status_code'] == 200
        mock_get.assert_called_once()
    
    @patch('portfolio_agent.ingestion.website_ingestor.requests.Session.get')
    def test_fetch_page_content_non_html(self, mock_get):
        """Test page content fetching with non-HTML content."""
        ingestor = WebsiteIngestor()
        
        # Mock non-HTML response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = ingestor._fetch_page_content("https://example.com/api")
        
        assert result is None
        mock_get.assert_called_once()


class TestGenericIngestor:
    """Test generic ingestor functionality."""
    
    def test_init(self):
        """Test generic ingestor initialization."""
        ingestor = GenericIngestor(supported_formats=['.txt', '.md'], max_file_size_mb=5)
        assert '.txt' in ingestor.supported_formats
        assert '.md' in ingestor.supported_formats
        assert ingestor.max_file_size_mb == 5
    
    def test_get_file_info(self):
        """Test file info extraction."""
        ingestor = GenericIngestor()
        
        # Test with non-existent file
        info = ingestor.get_file_info("nonexistent.txt")
        assert info == {}
        
        # Test with existing file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            info = ingestor.get_file_info(temp_path)
            assert info['filename'] == os.path.basename(temp_path)
            assert info['file_extension'] == '.txt'
            assert info['file_size'] > 0
            assert info['is_supported'] is True
        finally:
            os.unlink(temp_path)
    
    def test_read_text_file(self):
        """Test text file reading."""
        ingestor = GenericIngestor()
        
        # Test with UTF-8 file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Test content with unicode: café")
            temp_path = f.name
        
        try:
            content = ingestor._read_text_file(temp_path)
            assert "Test content with unicode: café" in content
        finally:
            os.unlink(temp_path)
    
    def test_read_json_file(self):
        """Test JSON file reading."""
        ingestor = GenericIngestor()
        
        test_data = {"name": "John", "age": 30, "city": "New York"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            content = ingestor._read_json_file(temp_path)
            assert "name: John" in content
            assert "age: 30" in content
            assert "city: New York" in content
        finally:
            os.unlink(temp_path)
    
    def test_json_to_text(self):
        """Test JSON to text conversion."""
        ingestor = GenericIngestor()
        
        data = {
            "user": {
                "name": "John",
                "details": {
                    "age": 30,
                    "city": "New York"
                }
            },
            "items": ["item1", "item2"]
        }
        
        text = ingestor._json_to_text(data)
        
        assert "user:" in text
        assert "name: John" in text
        assert "age: 30" in text
        assert "items:" in text
        assert "item1" in text
    
    def test_ingest_unsupported_format(self):
        """Test ingestion with unsupported format."""
        ingestor = GenericIngestor(supported_formats=['.txt'])
        
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b"# Test")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                ingestor.ingest(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_ingest_file_too_large(self):
        """Test ingestion with file too large."""
        ingestor = GenericIngestor(max_file_size_mb=0.001)  # 1KB limit
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"x" * 2000)  # 2KB file
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="File too large"):
                ingestor.ingest(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_ingest_success(self):
        """Test successful file ingestion."""
        ingestor = GenericIngestor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("This is test content for ingestion.")
            temp_path = f.name
        
        try:
            chunks = ingestor.ingest(temp_path)
            
            assert len(chunks) > 0
            assert chunks[0]['metadata']['source_type'] == 'file'
            assert chunks[0]['metadata']['content_type'] == 'txt'
            assert "This is test content for ingestion." in chunks[0]['content']
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__])
