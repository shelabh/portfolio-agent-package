"""
Resume ingestor for portfolio-agent.

This module provides functionality to ingest and process resume PDFs.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .pii_redactor import pii_redactor
from .chunker import text_chunker

logger = logging.getLogger(__name__)

# Try to import PDF processing libraries
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class ResumeIngestor:
    """Ingestor for resume PDF documents."""
    
    def __init__(self, redact_pii: bool = True, prefer_pymupdf: bool = True):
        """Initialize resume ingestor.
        
        Args:
            redact_pii: Whether to automatically redact PII
            prefer_pymupdf: Whether to prefer PyMuPDF over pypdf
        """
        self.redact_pii = redact_pii
        self.prefer_pymupdf = prefer_pymupdf
        
        # Check available PDF libraries
        if not PYPDF_AVAILABLE and not PYMUPDF_AVAILABLE:
            logger.warning("No PDF processing libraries available. Install pypdf or pymupdf.")
    
    def ingest(self, file_path: str) -> List[Dict[str, Any]]:
        """Ingest content from a resume PDF.
        
        Args:
            file_path: Path to the resume PDF file
            
        Returns:
            List of document chunks with metadata
        """
        logger.info(f"Ingesting resume PDF: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        if not file_path.lower().endswith('.pdf'):
            raise ValueError(f"File must be a PDF: {file_path}")
        
        try:
            # Extract text from PDF
            text_content = self._extract_text_from_pdf(file_path)
            if not text_content.strip():
                logger.warning(f"No text content extracted from {file_path}")
                return []
            
            # Redact PII if requested
            if self.redact_pii:
                text_content, redaction_stats = pii_redactor.redact_pii(text_content)
                if redaction_stats:
                    logger.info(f"Redacted PII from resume: {redaction_stats}")
            
            # Create metadata
            file_stats = os.stat(file_path)
            metadata = {
                'source': file_path,
                'source_type': 'resume',
                'content_type': 'pdf',
                'fetched_at': datetime.now().isoformat(),
                'file_size': file_stats.st_size,
                'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'pii_redacted': self.redact_pii,
                'extraction_method': self._get_extraction_method()
            }
            
            # Chunk the content
            chunks = text_chunker.chunk_text(text_content, metadata)
            
            logger.info(f"Successfully processed resume: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing resume {file_path}: {e}")
            return []
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file using available libraries."""
        if self.prefer_pymupdf and PYMUPDF_AVAILABLE:
            return self._extract_with_pymupdf(file_path)
        elif PYPDF_AVAILABLE:
            return self._extract_with_pypdf(file_path)
        else:
            raise ImportError("No PDF processing library available. Install pypdf or pymupdf.")
    
    def _extract_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF (fitz)."""
        try:
            doc = fitz.open(file_path)
            text_content = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text_content += page.get_text() + "\n"
            
            doc.close()
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text with PyMuPDF: {e}")
            return ""
    
    def _extract_with_pypdf(self, file_path: str) -> str:
        """Extract text using pypdf."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text_content = ""
                
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                
                return text_content.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text with pypdf: {e}")
            return ""
    
    def _get_extraction_method(self) -> str:
        """Get the PDF extraction method being used."""
        if self.prefer_pymupdf and PYMUPDF_AVAILABLE:
            return "pymupdf"
        elif PYPDF_AVAILABLE:
            return "pypdf"
        else:
            return "none"
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file."""
        metadata = {
            'filename': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'file_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        }
        
        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(file_path)
                pdf_metadata = doc.metadata
                metadata.update({
                    'title': pdf_metadata.get('title', ''),
                    'author': pdf_metadata.get('author', ''),
                    'subject': pdf_metadata.get('subject', ''),
                    'creator': pdf_metadata.get('creator', ''),
                    'producer': pdf_metadata.get('producer', ''),
                    'creation_date': pdf_metadata.get('creationDate', ''),
                    'modification_date': pdf_metadata.get('modDate', ''),
                    'page_count': doc.page_count
                })
                doc.close()
            elif PYPDF_AVAILABLE:
                with open(file_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    pdf_metadata = pdf_reader.metadata
                    if pdf_metadata:
                        metadata.update({
                            'title': pdf_metadata.get('/Title', ''),
                            'author': pdf_metadata.get('/Author', ''),
                            'subject': pdf_metadata.get('/Subject', ''),
                            'creator': pdf_metadata.get('/Creator', ''),
                            'producer': pdf_metadata.get('/Producer', ''),
                            'creation_date': str(pdf_metadata.get('/CreationDate', '')),
                            'modification_date': str(pdf_metadata.get('/ModDate', ''))
                        })
                    metadata['page_count'] = len(pdf_reader.pages)
                    
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
        
        return metadata
    
    def validate_pdf(self, file_path: str) -> bool:
        """Validate that the file is a valid PDF."""
        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(file_path)
                is_valid = doc.page_count > 0
                doc.close()
                return is_valid
            elif PYPDF_AVAILABLE:
                with open(file_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    return len(pdf_reader.pages) > 0
            else:
                # Basic file extension check
                return file_path.lower().endswith('.pdf')
        except Exception:
            return False
