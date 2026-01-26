"""
Citation Manager - Track and format citations for research documents.

This module manages citations, generates bibliographies, and validates sources.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Structured citation data."""
    id: str
    title: str
    url: str
    accessed_date: str
    authors: Optional[List[str]] = None
    publication_date: Optional[str] = None
    source_type: str = "web"  # web, paper, book, documentation
    publisher: Optional[str] = None
    doi: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CitationManager:
    """
    Manage citations and generate bibliographies.
    
    Features:
    - Citation tracking with unique IDs
    - Multiple citation styles (APA, IEEE, MLA)
    - Bibliography generation
    - Source validation
    - Citation statistics
    """
    
    def __init__(self):
        """Initialize citation manager."""
        self.citations: Dict[str, Citation] = {}
        self.citation_counter = 1
        logger.info("CitationManager initialized")
    
    def add_citation(
        self,
        title: str,
        url: str,
        **kwargs
    ) -> str:
        """
        Add a citation and return its ID.
        
        Args:
            title: Source title
            url: Source URL
            **kwargs: Additional citation fields
        
        Returns:
            Citation ID (e.g., "cite1", "cite2")
        """
        # Generate unique ID
        citation_id = f"cite{self.citation_counter}"
        self.citation_counter += 1
        
        # Create citation
        citation = Citation(
            id=citation_id,
            title=title,
            url=url,
            accessed_date=datetime.now().strftime("%Y-%m-%d"),
            **kwargs
        )
        
        self.citations[citation_id] = citation
        logger.debug(f"Added citation {citation_id}: {title}")
        
        return citation_id
    
    def add_from_search_result(self, result: Dict[str, Any]) -> str:
        """
        Add citation from web search result.
        
        Args:
            result: Search result dictionary
        
        Returns:
            Citation ID
        """
        return self.add_citation(
            title=result.get('title', 'Untitled'),
            url=result.get('url', ''),
            source_type='web',
            publisher=self._extract_publisher(result.get('url', ''))
        )
    
    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """
        Get citation by ID.
        
        Args:
            citation_id: Citation ID
        
        Returns:
            Citation object or None
        """
        return self.citations.get(citation_id)
    
    def format_bibliography(self, style: str = "apa") -> List[str]:
        """
        Generate formatted bibliography.
        
        Args:
            style: Citation style (apa, ieee, mla, plain)
        
        Returns:
            List of formatted citation strings
        """
        logger.info(f"Generating bibliography in {style.upper()} style")
        
        if style.lower() == "apa":
            return self._format_apa()
        elif style.lower() == "ieee":
            return self._format_ieee()
        elif style.lower() == "mla":
            return self._format_mla()
        else:
            return self._format_plain()
    
    def _format_apa(self) -> List[str]:
        """
        Format citations in APA style.
        
        Returns:
            List of APA-formatted citations
        """
        bibliography = []
        
        for cite in sorted(self.citations.values(), key=lambda x: x.title.lower()):
            entry = f"{cite.title}. "
            
            if cite.authors:
                authors = ", ".join(cite.authors)
                entry = f"{authors}. {entry}"
            
            if cite.publication_date:
                entry += f"({cite.publication_date}). "
            
            if cite.publisher:
                entry += f"{cite.publisher}. "
            
            entry += f"Retrieved {cite.accessed_date} from {cite.url}"
            
            bibliography.append(entry)
        
        return bibliography
    
    def _format_ieee(self) -> List[str]:
        """
        Format citations in IEEE style.
        
        Returns:
            List of IEEE-formatted citations
        """
        bibliography = []
        
        for idx, cite in enumerate(sorted(self.citations.values(), key=lambda x: x.title.lower()), 1):
            entry = f"[{idx}] "
            
            if cite.authors:
                authors = ", ".join(cite.authors)
                entry += f"{authors}, "
            
            entry += f'"{cite.title}"'
            
            if cite.publisher:
                entry += f", {cite.publisher}"
            
            if cite.publication_date:
                entry += f", {cite.publication_date}"
            
            entry += f". Available: {cite.url}"
            entry += f" [Accessed: {cite.accessed_date}]"
            
            bibliography.append(entry)
        
        return bibliography
    
    def _format_mla(self) -> List[str]:
        """
        Format citations in MLA style.
        
        Returns:
            List of MLA-formatted citations
        """
        bibliography = []
        
        for cite in sorted(self.citations.values(), key=lambda x: x.title.lower()):
            entry = f'"{cite.title}." '
            
            if cite.publisher:
                entry += f"{cite.publisher}, "
            
            if cite.publication_date:
                entry += f"{cite.publication_date}. "
            
            entry += f"Web. {cite.accessed_date}. <{cite.url}>"
            
            bibliography.append(entry)
        
        return bibliography
    
    def _format_plain(self) -> List[str]:
        """
        Format citations in plain style (simple list).
        
        Returns:
            List of plain-formatted citations
        """
        bibliography = []
        
        for cite in sorted(self.citations.values(), key=lambda x: x.title.lower()):
            entry = f"{cite.title} - {cite.url} (accessed {cite.accessed_date})"
            bibliography.append(entry)
        
        return bibliography
    
    def get_citation_stats(self) -> Dict[str, Any]:
        """
        Get citation statistics.
        
        Returns:
            Dictionary with statistics
        """
        source_types = {}
        publishers = {}
        
        for cite in self.citations.values():
            # Count source types
            source_types[cite.source_type] = source_types.get(cite.source_type, 0) + 1
            
            # Count publishers
            if cite.publisher:
                publishers[cite.publisher] = publishers.get(cite.publisher, 0) + 1
        
        return {
            'total_citations': len(self.citations),
            'source_types': source_types,
            'top_publishers': sorted(
                publishers.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'citation_ids': list(self.citations.keys())
        }
    
    def export_to_json(self) -> Dict[str, Any]:
        """
        Export all citations to JSON-serializable format.
        
        Returns:
            Dictionary with all citations
        """
        return {
            'citations': [cite.to_dict() for cite in self.citations.values()],
            'count': len(self.citations),
            'generated_at': datetime.now().isoformat()
        }
    
    def _extract_publisher(self, url: str) -> str:
        """
        Extract publisher/domain from URL.
        
        Args:
            url: URL to parse
        
        Returns:
            Publisher name
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Extract main domain name
            parts = domain.split('.')
            if len(parts) > 1:
                return parts[0].title()
            
            return domain
        except Exception:
            return "Unknown"
    
    def validate_citations(self) -> List[Dict[str, Any]]:
        """
        Validate all citations for completeness.
        
        Returns:
            List of validation issues
        """
        issues = []
        
        for cite_id, cite in self.citations.items():
            # Check for required fields
            if not cite.title or cite.title == "Untitled":
                issues.append({
                    'citation_id': cite_id,
                    'issue': 'Missing or generic title',
                    'severity': 'warning'
                })
            
            if not cite.url:
                issues.append({
                    'citation_id': cite_id,
                    'issue': 'Missing URL',
                    'severity': 'error'
                })
            
            # Check URL format
            if cite.url and not cite.url.startswith('http'):
                issues.append({
                    'citation_id': cite_id,
                    'issue': f'Invalid URL format: {cite.url}',
                    'severity': 'error'
                })
        
        logger.info(f"Citation validation: {len(issues)} issues found")
        return issues
    
    def generate_inline_citation(self, citation_id: str) -> str:
        """
        Generate inline citation marker.
        
        Args:
            citation_id: Citation ID
        
        Returns:
            Inline citation string (e.g., "[Source 1]")
        """
        if citation_id in self.citations:
            # Extract number from citation ID (e.g., "cite1" -> 1)
            num = citation_id.replace("cite", "")
            return f"[Source {num}]"
        return f"[{citation_id}]"
    
    def __len__(self) -> int:
        """Return number of citations."""
        return len(self.citations)
    
    def __repr__(self) -> str:
        return f"CitationManager(citations={len(self.citations)})"
