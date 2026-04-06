"""
Text chunking module for portfolio-agent.

This module provides functionality to split text into chunks with configurable
size, overlap, and metadata extraction.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TextChunker:
    """Text chunking utility with configurable parameters."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                 preserve_sentences: bool = True):
        """Initialize text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks in characters
            preserve_sentences: Whether to preserve sentence boundaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_sentences = preserve_sentences
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata.
        
        Args:
            text: Input text to chunk
            metadata: Base metadata for all chunks
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        if len(text) <= self.chunk_size:
            # Text is small enough to be a single chunk
            return [self._create_chunk(text, 0, len(text), metadata, 0)]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Adjust end to preserve sentence boundaries if enabled
            if self.preserve_sentences and end < len(text):
                end = self._find_sentence_boundary(text, start, end)
            
            # Guard against non-progress when boundary detection or overlap
            # would otherwise revisit the same slice indefinitely.
            if end <= start:
                end = min(start + self.chunk_size, len(text))
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk = self._create_chunk(chunk_text, start, end, metadata, chunk_index)
                chunks.append(chunk)
                chunk_index += 1
            
            if end >= len(text):
                break

            # Move start position with overlap while guaranteeing forward progress.
            start = end - self.chunk_overlap
            if start <= chunks[-1]['metadata']['chunk_start']:
                start = chunks[-1]['metadata']['chunk_end']
        
        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """Find the best sentence boundary within the chunk size limit."""
        # Look for sentence endings within the last 200 characters
        search_start = max(start, end - 200)
        search_text = text[search_start:end]
        
        # Find the last sentence boundary
        sentence_endings = ['.', '!', '?', '\n\n']
        best_end = end
        
        for ending in sentence_endings:
            last_ending = search_text.rfind(ending)
            if last_ending != -1:
                candidate_end = search_start + last_ending + 1
                if candidate_end > start + self.chunk_size * 0.5:  # Don't make chunks too small
                    best_end = candidate_end
                    break
        
        return best_end
    
    def _create_chunk(self, content: str, start: int, end: int, 
                     base_metadata: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """Create a chunk dictionary with metadata."""
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            'chunk_index': chunk_index,
            'chunk_start': start,
            'chunk_end': end,
            'chunk_size': len(content),
            'processed_at': datetime.now().isoformat()
        })
        
        return {
            'id': f"{base_metadata.get('source_id', 'unknown')}_chunk_{chunk_index}",
            'content': content,
            'metadata': chunk_metadata
        }
    
    def chunk_by_paragraphs(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text by paragraphs instead of fixed size."""
        paragraphs = text.split('\n\n')
        chunks = []
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if paragraph:
                chunk = self._create_chunk(paragraph, 0, len(paragraph), metadata, i)
                chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} paragraph-based chunks")
        return chunks
    
    def chunk_by_sections(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text by sections (headers)."""
        # Split by common header patterns
        section_pattern = r'\n(#{1,6}\s+.*|\n[A-Z][A-Z\s]+\n)'
        sections = re.split(section_pattern, text)
        
        chunks = []
        current_section = ""
        
        for i, section in enumerate(sections):
            section = section.strip()
            if section:
                if section.startswith('#') or section.isupper():
                    # This is a header, start new section
                    if current_section:
                        chunk = self._create_chunk(current_section, 0, len(current_section), metadata, len(chunks))
                        chunks.append(chunk)
                    current_section = section + "\n"
                else:
                    # This is content, add to current section
                    current_section += section + "\n"
        
        # Add the last section
        if current_section:
            chunk = self._create_chunk(current_section, 0, len(current_section), metadata, len(chunks))
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} section-based chunks")
        return chunks


# Global chunker instance
text_chunker = TextChunker()
