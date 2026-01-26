"""
Web Search Tool - DuckDuckGo search with content extraction.

This module provides web search functionality using DuckDuckGo (no API key required)
and extracts clean text content from HTML pages.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Web search with content extraction.
    
    Features:
    - DuckDuckGo search (no API key required)
    - HTML content extraction
    - Rate limiting
    - Error handling
    """
    
    def __init__(
        self,
        timeout: int = 10,
        max_content_length: int = 5000,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ):
        """
        Initialize web search tool.
        
        Args:
            timeout: Request timeout in seconds
            max_content_length: Maximum content length to extract
            user_agent: User agent string for requests
        """
        self.ddg = DDGS()
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.user_agent = user_agent
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        region: str = 'wt-wt',  # Worldwide
        safesearch: str = 'moderate'
    ) -> List[Dict[str, Any]]:
        """
        Search web and return results with extracted content.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            region: Region code (default: worldwide)
            safesearch: SafeSearch level (on, moderate, off)
        
        Returns:
            List of result dictionaries with url, title, snippet, content
        """
        logger.info(f"Searching DuckDuckGo for: {query} (max_results={max_results})")
        
        results = []
        
        try:
            # Get search results
            search_results = self.ddg.text(
                keywords=query,
                region=region,
                safesearch=safesearch,
                max_results=max_results
            )
            
            # Process each result
            for idx, result in enumerate(search_results, 1):
                try:
                    url = result.get('href') or result.get('link')
                    title = result.get('title', 'No title')
                    snippet = result.get('body', '')
                    
                    if not url:
                        logger.warning(f"Result {idx} has no URL, skipping")
                        continue
                    
                    logger.debug(f"Processing result {idx}: {url}")
                    
                    # Fetch and extract content
                    content = self._extract_content(url)
                    
                    if content:
                        results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet,
                            'content': content[:self.max_content_length],
                            'timestamp': datetime.now().isoformat(),
                            'source': 'duckduckgo'
                        })
                        logger.debug(f"Successfully extracted {len(content)} chars from {url}")
                    else:
                        # Include result even without content
                        results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet,
                            'content': snippet,  # Fallback to snippet
                            'timestamp': datetime.now().isoformat(),
                            'source': 'duckduckgo',
                            'extraction_failed': True
                        })
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error processing result {idx}: {e}")
                    continue
            
            logger.info(f"Successfully retrieved {len(results)} results")
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
        
        return results
    
    def _extract_content(self, url: str) -> Optional[str]:
        """
        Extract clean text content from a URL.
        
        Args:
            url: URL to fetch
        
        Returns:
            Extracted text content or None
        """
        try:
            # Fetch page
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                script.decompose()
            
            # Try to find main content area
            main_content = (
                soup.find('main') or
                soup.find('article') or
                soup.find(class_=lambda x: x and 'content' in x.lower()) or
                soup.find('body')
            )
            
            if main_content:
                # Extract text
                text = main_content.get_text(separator='\n', strip=True)
                
                # Clean up whitespace
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text = '\n'.join(lines)
                
                return text
            
            return None
            
        except requests.Timeout:
            logger.warning(f"Timeout fetching {url}")
            return None
        except requests.RequestException as e:
            logger.warning(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Content extraction error for {url}: {e}")
            return None
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is accessible.
        
        Args:
            url: URL to validate
        
        Returns:
            True if accessible, False otherwise
        """
        try:
            response = self.session.head(
                url,
                timeout=5,
                allow_redirects=True
            )
            return response.status_code < 400
        except Exception:
            return False
    
    def get_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to parse
        
        Returns:
            Domain name
        """
        parsed = urlparse(url)
        return parsed.netloc
    
    def __repr__(self) -> str:
        return f"WebSearchTool(timeout={self.timeout}s, max_content={self.max_content_length})"


class CachedWebSearch(WebSearchTool):
    """
    Web search with persistent caching to avoid redundant requests.
    """
    
    def __init__(
        self,
        cache_dir: str = "./cache/searches",
        cache_ttl_days: int = 7,
        **kwargs
    ):
        """
        Initialize cached web search.
        
        Args:
            cache_dir: Directory for cache files
            cache_ttl_days: Cache time-to-live in days
            **kwargs: Additional arguments for WebSearchTool
        """
        super().__init__(**kwargs)
        
        from pathlib import Path
        import pickle
        import hashlib
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_days = cache_ttl_days
        self.pickle = pickle
        self.hashlib = hashlib
    
    def search(self, query: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search with caching.
        
        Args:
            query: Search query
            max_results: Maximum results
            **kwargs: Additional search parameters
        
        Returns:
            List of search results (from cache or fresh)
        """
        # Generate cache key
        cache_key = self.hashlib.md5(
            f"{query}_{max_results}".encode()
        ).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # Check cache
        if cache_file.exists():
            # Check if cache is fresh
            age_days = (time.time() - cache_file.stat().st_mtime) / 86400
            
            if age_days < self.cache_ttl_days:
                logger.info(f"Using cached results for: {query} (age: {age_days:.1f} days)")
                with open(cache_file, 'rb') as f:
                    return self.pickle.load(f)
        
        # Fetch fresh results
        results = super().search(query, max_results, **kwargs)
        
        # Save to cache
        with open(cache_file, 'wb') as f:
            self.pickle.dump(results, f)
        
        logger.info(f"Cached {len(results)} results for: {query}")
        
        return results
