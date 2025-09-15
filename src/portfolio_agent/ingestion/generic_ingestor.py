"""
Generic ingestor for portfolio-agent.

This module provides functionality to ingest various file formats.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .pii_redactor import pii_redactor
from .chunker import text_chunker

logger = logging.getLogger(__name__)

# Try to import optional libraries
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class GenericIngestor:
    """Generic ingestor for various file formats."""
    
    def __init__(self, supported_formats: Optional[List[str]] = None, 
                 max_file_size_mb: int = 10):
        """Initialize generic ingestor.
        
        Args:
            supported_formats: List of supported file extensions
            max_file_size_mb: Maximum file size in MB
        """
        self.supported_formats = supported_formats or [
            ".txt", ".md", ".html", ".json", ".xml", ".csv", ".docx"
        ]
        self.max_file_size_mb = max_file_size_mb
    
    def ingest(self, file_path: str, redact_pii: bool = True) -> List[Dict[str, Any]]:
        """Ingest content from a file.
        
        Args:
            file_path: Path to the file to ingest
            redact_pii: Whether to redact PII from content
            
        Returns:
            List of document chunks with metadata
        """
        logger.info(f"Ingesting file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported: {self.supported_formats}")
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB")
        
        try:
            # Read file content based on format
            content = self._read_file_content(file_path, file_ext)
            if not content.strip():
                logger.warning(f"No content extracted from {file_path}")
                return []
            
            # Redact PII if requested
            if redact_pii:
                content, redaction_stats = pii_redactor.redact_pii(content)
                if redaction_stats:
                    logger.info(f"Redacted PII from {file_path}: {redaction_stats}")
            
            # Create metadata
            file_stats = os.stat(file_path)
            metadata = {
                'source': file_path,
                'source_type': 'file',
                'content_type': file_ext[1:],  # Remove the dot
                'fetched_at': datetime.now().isoformat(),
                'file_size': file_stats.st_size,
                'file_size_mb': file_size_mb,
                'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'pii_redacted': redact_pii
            }
            
            # Chunk the content
            chunks = text_chunker.chunk_text(content, metadata)
            
            logger.info(f"Successfully processed {file_path}: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return []
    
    def _read_file_content(self, file_path: str, file_ext: str) -> str:
        """Read content from file based on extension."""
        if file_ext == '.txt':
            return self._read_text_file(file_path)
        elif file_ext == '.md':
            return self._read_markdown_file(file_path)
        elif file_ext == '.html':
            return self._read_html_file(file_path)
        elif file_ext == '.json':
            return self._read_json_file(file_path)
        elif file_ext == '.xml':
            return self._read_xml_file(file_path)
        elif file_ext == '.csv':
            return self._read_csv_file(file_path)
        elif file_ext == '.docx':
            return self._read_docx_file(file_path)
        else:
            # Fallback to text reading
            return self._read_text_file(file_path)
    
    def _read_text_file(self, file_path: str) -> str:
        """Read content from a text file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, read as binary and decode with errors='replace'
            with open(file_path, 'rb') as file:
                return file.read().decode('utf-8', errors='replace')
                
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return ""
    
    def _read_markdown_file(self, file_path: str) -> str:
        """Read content from a markdown file."""
        try:
            content = self._read_text_file(file_path)
            
            if MARKDOWN_AVAILABLE:
                # Convert markdown to HTML then extract text
                html = markdown.markdown(content)
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(html, 'html.parser')
                    return soup.get_text()
                else:
                    # Simple HTML tag removal
                    import re
                    return re.sub(r'<[^>]+>', '', html)
            else:
                # Return raw markdown content
                return content
                
        except Exception as e:
            logger.error(f"Error reading markdown file {file_path}: {e}")
            return ""
    
    def _read_html_file(self, file_path: str) -> str:
        """Read content from an HTML file."""
        try:
            content = self._read_text_file(file_path)
            
            if BS4_AVAILABLE:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                return soup.get_text()
            else:
                # Simple HTML tag removal
                import re
                return re.sub(r'<[^>]+>', ' ', content)
                
        except Exception as e:
            logger.error(f"Error reading HTML file {file_path}: {e}")
            return ""
    
    def _read_json_file(self, file_path: str) -> str:
        """Read content from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Convert JSON to readable text
            if isinstance(data, dict):
                return self._json_to_text(data)
            elif isinstance(data, list):
                return '\n'.join(str(item) for item in data)
            else:
                return str(data)
                
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return ""
    
    def _json_to_text(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Convert JSON data to readable text."""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{'  ' * indent}{key}:")
                lines.append(self._json_to_text(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{'  ' * indent}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._json_to_text(item, indent + 1))
                    else:
                        lines.append(f"{'  ' * (indent + 1)}{item}")
            else:
                lines.append(f"{'  ' * indent}{key}: {value}")
        
        return '\n'.join(lines)
    
    def _read_xml_file(self, file_path: str) -> str:
        """Read content from an XML file."""
        try:
            content = self._read_text_file(file_path)
            
            if BS4_AVAILABLE:
                soup = BeautifulSoup(content, 'xml')
                return soup.get_text()
            else:
                # Simple XML tag removal
                import re
                return re.sub(r'<[^>]+>', ' ', content)
                
        except Exception as e:
            logger.error(f"Error reading XML file {file_path}: {e}")
            return ""
    
    def _read_csv_file(self, file_path: str) -> str:
        """Read content from a CSV file."""
        try:
            content = self._read_text_file(file_path)
            
            # Convert CSV to readable text
            lines = content.strip().split('\n')
            if not lines:
                return ""
            
            # Parse CSV (simple approach)
            csv_lines = []
            for line in lines:
                # Simple CSV parsing - split by comma
                fields = line.split(',')
                csv_lines.append(' | '.join(field.strip() for field in fields))
            
            return '\n'.join(csv_lines)
            
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            return ""
    
    def _read_docx_file(self, file_path: str) -> str:
        """Read content from a DOCX file."""
        try:
            if not DOCX_AVAILABLE:
                logger.warning("python-docx not available. Install it to read DOCX files.")
                return ""
            
            doc = Document(file_path)
            paragraphs = []
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    paragraphs.append(text)
            
            return '\n'.join(paragraphs)
            
        except Exception as e:
            logger.error(f"Error reading DOCX file {file_path}: {e}")
            return ""
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file."""
        if not os.path.exists(file_path):
            return {}
        
        file_stats = os.stat(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        return {
            'filename': os.path.basename(file_path),
            'file_extension': file_ext,
            'file_size': file_stats.st_size,
            'file_size_mb': file_stats.st_size / (1024 * 1024),
            'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            'is_supported': file_ext in self.supported_formats,
            'supported_formats': self.supported_formats
        }
