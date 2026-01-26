"""
Grounder Agent - RAG retrieval, evidence citation, confidence scoring.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import json

from .base_agent import BaseAgent, PromptEngine
from ..orchestration.state import SharedState
from ..tools import VectorStore, CachedWebSearch, CitationManager


logger = logging.getLogger(__name__)


class GrounderAgent(BaseAgent):
    """
    The Grounder agent retrieves evidence, cites sources,
    and provides confidence scores for claims.
    
    Model: Qwen 2.5 7B
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b-instruct-q4_K_M",
        vram_mb: int = 4500,
        temperature: float = 0.2,
        max_sources: int = 10
    ):
        """
        Initialize the Grounder agent.
        
        Args:
            model_name: Ollama model name
            vram_mb: Expected VRAM usage
            temperature: Sampling temperature
            max_sources: Maximum sources to cite
        """
        super().__init__(
            name="Grounder",
            model_name=model_name,
            vram_mb=vram_mb,
            temperature=temperature
        )
        
        self.max_sources = max_sources
        
        # NEW: Initialize retrieval tools
        logger.info("Initializing Grounder retrieval tools...")
        try:
            self.vector_store = VectorStore(persist_dir="./chroma_db")
            logger.info(f"Vector store initialized: {self.vector_store.get_statistics()}")
        except Exception as e:
            logger.warning(f"Vector store initialization failed: {e}. Proceeding without vector search.")
            self.vector_store = None
        
        self.web_search = CachedWebSearch(cache_ttl_days=7)
        self.citation_manager = CitationManager()
        logger.info("Web search and citation manager initialized")
        
        # Load prompt template
        config_dir = Path(__file__).parent.parent.parent / "config"
        template_path = config_dir / "prompts" / "grounder.md"
        self.prompt_template = self.load_prompt_template(str(template_path))
    
    def _retrieve_evidence(
        self,
        research_questions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve evidence for all research questions.
        
        Args:
            research_questions: List of research question dictionaries
        
        Returns:
            Dictionary mapping question IDs to evidence lists
        """
        all_evidence = {}
        
        for rq in research_questions:
            question = rq.get('question', '')
            rq_id = rq.get('id', 'RQ_unknown')
            
            logger.info(f"Retrieving evidence for {rq_id}: {question}")
            evidence_sources = []
            
            # 1. Search vector database (if available)
            if self.vector_store is not None:
                try:
                    vector_results = self.vector_store.search(question, n_results=5)
                    
                    # Process vector DB results
                    for i, (doc, metadata, distance) in enumerate(zip(
                        vector_results.get('documents', []),
                        vector_results.get('metadatas', []),
                        vector_results.get('distances', [])
                    )):
                        evidence_sources.append({
                            'source': 'vector_db',
                            'content': doc[:1000],  # First 1K chars
                            'metadata': metadata,
                            'relevance_score': 1.0 - distance,  # Convert distance to similarity
                            'title': metadata.get('title', 'Knowledge Base Document')
                        })
                    
                    logger.info(f"Found {len(vector_results.get('documents', []))} vector DB results for {rq_id}")
                except Exception as e:
                    logger.warning(f"Vector search failed for {rq_id}: {e}")
            
            # 2. Search web
            try:
                web_results = self.web_search.search(question, max_results=5)
                
                # Process web search results
                for result in web_results:
                    # Add citation
                    cite_id = self.citation_manager.add_citation(
                        title=result.get('title', 'Untitled'),
                        url=result.get('url', ''),
                        source_type='web'
                    )
                    
                    evidence_sources.append({
                        'source': 'web',
                        'title': result.get('title', 'Untitled'),
                        'url': result.get('url', ''),
                        'content': result.get('content', result.get('snippet', ''))[:1000],
                        'snippet': result.get('snippet', ''),
                        'citation_id': cite_id,
                        'relevance_score': 1.0  # Default relevance
                    })
                
                logger.info(f"Found {len(web_results)} web results for {rq_id}")
            except Exception as e:
                logger.error(f"Web search failed for {rq_id}: {e}")
            
            # 3. Combine and rank evidence
            # Sort by relevance score (descending)
            evidence_sources.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Limit to max_sources
            all_evidence[rq_id] = evidence_sources[:self.max_sources]
            
            logger.info(f"Total evidence for {rq_id}: {len(all_evidence[rq_id])} sources")
        
        return all_evidence
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """
        Prepare the prompt for the Grounder.
        
        Args:
            state: Current shared state
        
        Returns:
            Formatted prompt with evidence sources
        """
        # Get ALL research questions from the plan
        all_research_questions = []
        if state.plan and "research_questions" in state.plan:
            all_research_questions = state.plan["research_questions"]
        
        # If no plan, create from user brief
        if not all_research_questions:
            all_research_questions = [
                {
                    "id": "RQ1",
                    "question": state.user_brief,
                    "type": "exploratory"
                }
            ]
        
        # *** NEW: Retrieve evidence for all questions ***
        logger.info(f"Retrieving evidence for {len(all_research_questions)} research questions...")
        all_evidence = self._retrieve_evidence(all_research_questions)
        
        # Log retrieval summary
        total_sources = sum(len(sources) for sources in all_evidence.values())
        logger.info(f"Retrieved total of {total_sources} evidence sources across all questions")
        
        # Store evidence in state for later use
        if not hasattr(state, 'evidence'):
            state.evidence = {}
        state.evidence.update(all_evidence)
        
        # Build evidence sections for prompt
        evidence_sections = []
        for rq_id, sources in all_evidence.items():
            if sources:
                evidence_text = f"\n### Evidence for {rq_id}\n\n"
                for idx, source in enumerate(sources, 1):
                    source_marker = f"[Source {idx}]"
                    evidence_text += f"{source_marker} **{source.get('title', 'Untitled')}**\n"
                    
                    if source.get('url'):
                        evidence_text += f"URL: {source['url']}\n"
                    
                    evidence_text += f"Content: {source.get('content', source.get('snippet', 'No content available'))[:500]}...\n\n"
                
                evidence_sections.append(evidence_text)
        
        # Prepare comprehensive input JSON with all questions AND evidence
        input_json = {
            "user_brief": state.user_brief,
            "research_questions": all_research_questions,
            "evidence_available": len(evidence_sections) > 0,
            "instructions": """
CRITICAL DIRECTIVE: Provide comprehensive, evidence-backed answers for each research question.

For EACH research question, provide:
1. A clear, detailed answer (3-5 paragraphs, 300-500 words per question)
2. Technical analysis explaining key principles and mechanisms
3. Real-world examples (2-3) with specific use cases
4. Key findings with supporting evidence from retrieved sources
5. Related concepts and interconnections
6. Implementation guidance and best practices
7. Common challenges and solutions
8. Future trends and directions

**CITATION REQUIREMENTS**:
- Reference sources using [Source N] markers (e.g., "According to [Source 1]...")
- Integrate evidence naturally into your narrative
- Prioritize information from provided sources
- Cite sources for all factual claims when available

Focus on depth, accuracy, and evidence-based reasoning.
Target: 2000-4000 words total for all questions combined.
Every claim should be substantiated with citations or reasoning.
"""
        }
        
        # Build the full prompt
        prompt = f"{self.prompt_template}\n\n"
        prompt += f"## Input\n\n"
        prompt += f"```json\n{self.prompt_engine.inject_variables('{input}', {'input': input_json})}\n```\n\n"
        
        # *** NEW: Include retrieved evidence ***
        if evidence_sections:
            prompt += f"\n## Retrieved Evidence\n"
            prompt += "\n".join(evidence_sections)
            prompt += "\n"
            logger.info(f"Prompt includes {len(evidence_sections)} evidence sections with {total_sources} total sources")
        else:
            logger.warning("No evidence retrieved - output may lack citations")
        
        prompt += f"""## Content Requirements

**CRITICAL DIRECTIVE**: Provide comprehensive, evidence-backed answers. Each research question requires:
- Clear explanation (3-5 paragraphs, 300-500 words)
- Technical analysis explaining key concepts and mechanisms
- Real-world examples (2-3) with specific use cases from sources
- Implementation guidance: practical patterns and best practices
- Common challenges with solutions
- Future directions and emerging trends
- **CITE all factual claims using [Source N] markers**

TARGET: 2000-4000 words total for all questions combined.
Focus on clarity, accuracy, and practical value.
Every claim must be substantiated with evidence from sources or reasoning.
Provide actionable insights that users can apply.

## Your Response

Provide your response as valid JSON only:"""
        
        return prompt
    
    def _parse_response(
        self,
        response: str,
        state: SharedState
    ) -> Optional[Dict[str, Any]]:
        """
        Parse the Grounder's JSON response.
        
        Args:
            response: Raw LLM response
            state: Current shared state
        
        Returns:
            Parsed output dictionary or None
        """
        parsed = self.prompt_engine.extract_json_from_response(response)
        
        if parsed is None:
            logger.warning("Failed to extract JSON from Grounder response")
            return None
        
        # Validate required fields
        required_fields = ["answer", "key_findings", "overall_confidence"]
        
        for field in required_fields:
            if field not in parsed:
                logger.warning(f"Missing required field in Grounder output: {field}")
                return None
        
        return parsed
    
    def _graceful_degradation(self, state: SharedState) -> Dict[str, Any]:
        """
        Provide fallback when Grounder fails.
        
        Args:
            state: Current shared state
        
        Returns:
            Minimal valid output
        """
        return {
            "answer": "Unable to retrieve sufficient evidence",
            "key_findings": [],
            "contradictions": [],
            "knowledge_gaps": ["Insufficient data available"],
            "overall_confidence": 0.3,
            "degraded": True
        }
