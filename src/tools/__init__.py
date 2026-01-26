"""
Tools package - External integrations and utilities.

This package provides tools for:
- Vector database operations (ChromaDB)
- Web search and content retrieval (DuckDuckGo)
- Citation management and bibliography generation
- Future: Browser automation, API clients, etc.
"""

from .vector_store import VectorStore
from .web_search import WebSearchTool, CachedWebSearch
from .citation_manager import CitationManager, Citation

__all__ = [
    'VectorStore',
    'WebSearchTool',
    'CachedWebSearch',
    'CitationManager',
    'Citation',
]
