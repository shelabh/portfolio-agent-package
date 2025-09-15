"""
GitHub ingestor for portfolio-agent.

This module provides functionality to ingest content from GitHub repositories.
"""

import re
import requests
import base64
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import logging
from datetime import datetime

from .pii_redactor import pii_redactor
from .chunker import text_chunker

logger = logging.getLogger(__name__)


class GitHubIngestor:
    """Ingestor for GitHub repository content."""
    
    def __init__(self, api_token: Optional[str] = None, max_files: int = 50):
        """Initialize GitHub ingestor.
        
        Args:
            api_token: GitHub API token for authentication
            max_files: Maximum number of files to process
        """
        self.api_token = api_token
        self.base_url = "https://api.github.com"
        self.max_files = max_files
        self.session = requests.Session()
        
        if self.api_token:
            self.session.headers.update({
                'Authorization': f'token {self.api_token}',
                'Accept': 'application/vnd.github.v3+json'
            })
    
    def ingest(self, repo_url: str, redact_pii: bool = True) -> List[Dict[str, Any]]:
        """Ingest content from a GitHub repository.
        
        Args:
            repo_url: URL of the GitHub repository
            redact_pii: Whether to redact PII from content
            
        Returns:
            List of document chunks with metadata
        """
        logger.info(f"Ingesting GitHub repository: {repo_url}")
        
        try:
            # Parse repository URL
            repo_info = self._parse_repo_url(repo_url)
            if not repo_info:
                raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
            
            # Fetch repository information
            repo_data = self._fetch_repository_info(repo_info['owner'], repo_info['repo'])
            if not repo_data:
                raise ValueError(f"Could not fetch repository data for {repo_url}")
            
            all_chunks = []
            
            # Fetch and process README
            readme_content = self._fetch_readme(repo_info['owner'], repo_info['repo'])
            if readme_content:
                readme_chunks = self._process_content(
                    readme_content, 
                    f"{repo_url}/README.md",
                    "readme",
                    repo_data,
                    redact_pii
                )
                all_chunks.extend(readme_chunks)
            
            # Fetch and process code files
            code_files = self._fetch_code_files(repo_info['owner'], repo_info['repo'])
            for file_info in code_files[:self.max_files]:
                file_content = self._fetch_file_content(file_info['download_url'])
                if file_content:
                    file_chunks = self._process_content(
                        file_content,
                        file_info['html_url'],
                        "code",
                        repo_data,
                        redact_pii,
                        file_info
                    )
                    all_chunks.extend(file_chunks)
            
            logger.info(f"Successfully ingested {len(all_chunks)} chunks from {repo_url}")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Error ingesting GitHub repository {repo_url}: {e}")
            return []
    
    def _parse_repo_url(self, repo_url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub repository URL to extract owner and repo name."""
        patterns = [
            r'https://github\.com/([^/]+)/([^/]+)',
            r'git@github\.com:([^/]+)/([^/]+)\.git',
            r'github\.com/([^/]+)/([^/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, repo_url)
            if match:
                return {
                    'owner': match.group(1),
                    'repo': match.group(2).replace('.git', '')
                }
        
        return None
    
    def _fetch_repository_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch repository information from GitHub API."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching repository info: {e}")
            return None
    
    def _fetch_readme(self, owner: str, repo: str) -> str:
        """Fetch README content from repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                readme_data = response.json()
                if readme_data.get('content'):
                    # Decode base64 content
                    content = base64.b64decode(readme_data['content']).decode('utf-8')
                    return content
        except requests.RequestException as e:
            logger.error(f"Error fetching README: {e}")
        
        return ""
    
    def _fetch_code_files(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Fetch list of code files from repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            contents = response.json()
            
            # Filter for code files
            code_files = []
            for item in contents:
                if item['type'] == 'file' and self._is_code_file(item['name']):
                    code_files.append(item)
                elif item['type'] == 'dir' and not item['name'].startswith('.'):
                    # Recursively fetch files from subdirectories
                    sub_files = self._fetch_directory_files(owner, repo, item['path'])
                    code_files.extend(sub_files)
            
            return code_files[:self.max_files]
            
        except requests.RequestException as e:
            logger.error(f"Error fetching code files: {e}")
            return []
    
    def _fetch_directory_files(self, owner: str, repo: str, path: str) -> List[Dict[str, Any]]:
        """Recursively fetch files from a directory."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            contents = response.json()
            
            files = []
            for item in contents:
                if item['type'] == 'file' and self._is_code_file(item['name']):
                    files.append(item)
                elif item['type'] == 'dir' and not item['name'].startswith('.'):
                    sub_files = self._fetch_directory_files(owner, repo, item['path'])
                    files.extend(sub_files)
            
            return files
            
        except requests.RequestException as e:
            logger.error(f"Error fetching directory files: {e}")
            return []
    
    def _fetch_file_content(self, download_url: str) -> str:
        """Fetch content of a specific file."""
        try:
            response = self.session.get(download_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching file content: {e}")
            return ""
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if a file is a code file based on extension."""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
            '.sql', '.sh', '.bash', '.yaml', '.yml', '.json', '.xml', '.html', '.css',
            '.scss', '.sass', '.less', '.md', '.txt', '.rst', '.tex'
        }
        
        return any(filename.lower().endswith(ext) for ext in code_extensions)
    
    def _process_content(self, content: str, source_url: str, content_type: str,
                        repo_data: Dict[str, Any], redact_pii: bool,
                        file_info: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process content into chunks with metadata."""
        # Redact PII if requested
        if redact_pii:
            content, redaction_stats = pii_redactor.redact_pii(content)
            if redaction_stats:
                logger.info(f"Redacted PII from {source_url}: {redaction_stats}")
        
        # Create base metadata
        metadata = {
            'source': source_url,
            'source_type': 'github',
            'content_type': content_type,
            'fetched_at': datetime.now().isoformat(),
            'repository': {
                'name': repo_data.get('name'),
                'full_name': repo_data.get('full_name'),
                'description': repo_data.get('description'),
                'language': repo_data.get('language'),
                'stars': repo_data.get('stargazers_count'),
                'forks': repo_data.get('forks_count'),
                'created_at': repo_data.get('created_at'),
                'updated_at': repo_data.get('updated_at')
            }
        }
        
        # Add file-specific metadata
        if file_info:
            metadata['file'] = {
                'name': file_info.get('name'),
                'path': file_info.get('path'),
                'size': file_info.get('size'),
                'sha': file_info.get('sha')
            }
        
        # Chunk the content
        chunks = text_chunker.chunk_text(content, metadata)
        
        return chunks
