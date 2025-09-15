"""
Website ingestor for portfolio-agent.

This module provides functionality to ingest content from websites.
"""

import re
import requests
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List, Dict, Any, Optional, Set
import logging
from datetime import datetime
import time

from .pii_redactor import pii_redactor
from .chunker import text_chunker

logger = logging.getLogger(__name__)

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WebsiteIngestor:
    """Ingestor for website content."""
    
    def __init__(self, max_depth: int = 2, respect_robots: bool = True, 
                 max_pages: int = 20, delay: float = 1.0):
        """Initialize website ingestor.
        
        Args:
            max_depth: Maximum crawl depth
            respect_robots: Whether to respect robots.txt
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
        """
        self.max_depth = max_depth
        self.respect_robots = respect_robots
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; PortfolioAgent/1.0; +https://github.com/shelabhtyagi/portfolio-agent)'
        })
        
        if not BS4_AVAILABLE:
            logger.warning("BeautifulSoup not available. Install beautifulsoup4 for HTML parsing.")
    
    def ingest(self, url: str, redact_pii: bool = True) -> List[Dict[str, Any]]:
        """Ingest content from a website.
        
        Args:
            url: URL of the website to ingest
            redact_pii: Whether to redact PII from content
            
        Returns:
            List of document chunks with metadata
        """
        logger.info(f"Ingesting website: {url}")
        
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL: {url}")
            
            # Check robots.txt if requested
            if self.respect_robots and not self._check_robots_txt(url):
                logger.warning(f"Robots.txt disallows crawling: {url}")
                return []
            
            # Crawl website and collect URLs
            urls_to_crawl = self._crawl_website(url)
            
            all_chunks = []
            crawled_count = 0
            
            for page_url in urls_to_crawl:
                if crawled_count >= self.max_pages:
                    break
                
                try:
                    # Fetch page content
                    page_content = self._fetch_page_content(page_url)
                    if page_content:
                        # Process content
                        chunks = self._process_content(
                            page_content, 
                            page_url, 
                            redact_pii
                        )
                        all_chunks.extend(chunks)
                        crawled_count += 1
                        
                        # Respect delay between requests
                        if self.delay > 0:
                            time.sleep(self.delay)
                            
                except Exception as e:
                    logger.error(f"Error processing page {page_url}: {e}")
                    continue
            
            logger.info(f"Successfully ingested {len(all_chunks)} chunks from {crawled_count} pages")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Error ingesting website {url}: {e}")
            return []
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check robots.txt to see if crawling is allowed."""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                robots_content = response.text
                # Simple robots.txt parsing - check for Disallow: /
                if 'Disallow: /' in robots_content:
                    return False
            return True
            
        except Exception as e:
            logger.debug(f"Could not check robots.txt: {e}")
            return True  # Allow crawling if robots.txt is not accessible
    
    def _crawl_website(self, start_url: str) -> List[str]:
        """Crawl website and collect URLs to process."""
        parsed_start = urlparse(start_url)
        base_domain = parsed_start.netloc
        
        urls_to_visit = [start_url]
        visited_urls: Set[str] = set()
        urls_to_crawl = []
        
        depth = 0
        while urls_to_visit and depth < self.max_depth:
            current_depth_urls = urls_to_visit.copy()
            urls_to_visit.clear()
            
            for url in current_depth_urls:
                if url in visited_urls:
                    continue
                
                visited_urls.add(url)
                urls_to_crawl.append(url)
                
                if depth < self.max_depth - 1:  # Don't crawl links on the last depth
                    try:
                        # Fetch page to extract links
                        response = self.session.get(url, timeout=10)
                        if response.status_code == 200 and BS4_AVAILABLE:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            links = self._extract_links(soup, url, base_domain)
                            urls_to_visit.extend(links)
                    except Exception as e:
                        logger.debug(f"Error crawling {url}: {e}")
            
            depth += 1
        
        return urls_to_crawl[:self.max_pages]
    
    def _extract_links(self, soup: BeautifulSoup, current_url: str, base_domain: str) -> List[str]:
        """Extract relevant links from a page."""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(current_url, href)
            parsed_url = urlparse(absolute_url)
            
            # Only include links from the same domain
            if parsed_url.netloc == base_domain:
                # Clean URL (remove fragments)
                clean_url = urlunparse((
                    parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                    parsed_url.params, parsed_url.query, ''
                ))
                
                # Filter out common non-content URLs
                if not self._is_content_url(clean_url):
                    continue
                
                links.append(clean_url)
        
        return list(set(links))  # Remove duplicates
    
    def _is_content_url(self, url: str) -> bool:
        """Check if URL likely contains content worth crawling."""
        # Skip common non-content paths
        skip_patterns = [
            r'/admin', r'/login', r'/register', r'/logout', r'/api/',
            r'/static/', r'/assets/', r'/css/', r'/js/', r'/images/',
            r'/downloads/', r'/files/', r'/media/', r'\.(css|js|png|jpg|jpeg|gif|svg|ico|pdf|zip)$'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    def _fetch_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch content from a single page."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Check if content is HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.debug(f"Skipping non-HTML content: {url}")
                return None
            
            return {
                'url': url,
                'html': response.text,
                'status_code': response.status_code,
                'content_type': content_type,
                'title': self._extract_title(response.text),
                'fetched_at': datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None
    
    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML."""
        if not BS4_AVAILABLE:
            # Simple regex fallback
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            return title_match.group(1).strip() if title_match else ""
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            title_tag = soup.find('title')
            return title_tag.get_text().strip() if title_tag else ""
        except Exception:
            return ""
    
    def _extract_text_from_html(self, html: str, url: str) -> str:
        """Extract clean text content from HTML."""
        if not BS4_AVAILABLE:
            # Simple fallback - remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return ""
    
    def _process_content(self, page_data: Dict[str, Any], url: str, redact_pii: bool) -> List[Dict[str, Any]]:
        """Process page content into chunks."""
        # Extract text from HTML
        text_content = self._extract_text_from_html(page_data['html'], url)
        
        if not text_content.strip():
            return []
        
        # Redact PII if requested
        if redact_pii:
            text_content, redaction_stats = pii_redactor.redact_pii(text_content)
            if redaction_stats:
                logger.info(f"Redacted PII from {url}: {redaction_stats}")
        
        # Create metadata
        metadata = {
            'source': url,
            'source_type': 'website',
            'content_type': 'html',
            'fetched_at': page_data['fetched_at'],
            'title': page_data['title'],
            'status_code': page_data['status_code'],
            'content_type': page_data['content_type'],
            'pii_redacted': redact_pii
        }
        
        # Chunk the content
        chunks = text_chunker.chunk_text(text_content, metadata)
        
        return chunks
