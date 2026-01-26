# Research-Grade Output Implementation Plan
## Transforming ZenKnowledgeForge from Outline Generator to Research System

**Date:** January 26, 2026  
**Goal:** Produce research documents matching academic/industry standards (4,500-8,000 words with evidence, citations, data)

---

## 📊 Current State Analysis

### What We Have Now
| Component | Status | Quality |
|-----------|--------|---------|
| Multi-agent architecture | ✅ Working | Good |
| Sequential execution | ✅ Working | Good |
| Model management | ✅ Optimized | Good |
| Progress tracking | ✅ Working | Good |
| **Evidence retrieval** | ❌ **MISSING** | **None** |
| **Knowledge base** | ❌ **MISSING** | **None** |
| **Web search** | ❌ **MISSING** | **None** |
| **Citation tracking** | ❌ **MISSING** | **None** |
| **Data collection** | ❌ **MISSING** | **None** |
| Output length | ❌ **500 words** | **Poor** |
| Output depth | ❌ **Outlines only** | **Poor** |
| Evidence support | ❌ **Hallucinations** | **None** |

### Current Output vs. Required Output

| Aspect | Current | Required | Gap |
|--------|---------|----------|-----|
| **Total length** | 500 words | 4,500-8,000 words | **9-16x too short** |
| **Section length** | 1-2 sentences | 300-1,200 words | **150-600x too short** |
| **Evidence** | None | Citations + data | **100% missing** |
| **Tables/Figures** | None | 5-10 items | **100% missing** |
| **References** | None | 20-50 sources | **100% missing** |
| **Statistical rigor** | None | Mean ± std, p-values | **100% missing** |
| **Reproducibility** | None | Full method + code | **100% missing** |

### Root Cause
**The system does NOT retrieve or access external knowledge.**
- Grounder has NO tools (no web search, no vector DB, no documents)
- It just prompts LLMs to "write about X" from memory
- LLMs hallucinate plausible-sounding generic text
- Judge compiles hallucinations into empty sections

---

## 🎯 Implementation Plan Overview

### Phase 1: Foundation (Week 1-2)
Build core RAG infrastructure and basic retrieval

### Phase 2: Evidence & Citations (Week 3-4)
Add web search, citation tracking, and source verification

### Phase 3: Data & Analysis (Week 5-6)
Implement data collection, tables, statistical analysis

### Phase 4: Quality & Polish (Week 7-8)
Add validation, reproducibility, and final refinements

---

## 📋 PHASE 1: Foundation Infrastructure (Week 1-2)

### 1.1 Set Up Vector Database (Day 1-3)

**Objective:** Create persistent knowledge base for evidence retrieval

**Tasks:**
```python
# Files to create/modify:
- src/tools/vector_store.py          # NEW: ChromaDB wrapper
- src/tools/embeddings.py            # NEW: Embedding generation
- config/vector_db.yaml              # NEW: VectorDB configuration
- pyproject.toml                     # UPDATE: Ensure chromadb installed
```

**Implementation:**
```python
# src/tools/vector_store.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class VectorStore:
    """Manage document embeddings and retrieval."""
    
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_documents(self, texts: list[str], metadata: list[dict], ids: list[str]):
        """Add documents to vector store."""
        embeddings = self.encoder.encode(texts).tolist()
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadata,
            ids=ids
        )
    
    def search(self, query: str, n_results: int = 10) -> dict:
        """Semantic search for relevant documents."""
        query_embedding = self.encoder.encode([query])[0].tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
    
    def get_statistics(self) -> dict:
        """Get vector DB statistics."""
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name
        }
```

**Success Criteria:**
- ✅ ChromaDB persists documents across sessions
- ✅ Semantic search returns relevant results
- ✅ Can add/retrieve 1000+ documents efficiently

---

### 1.2 Web Search Integration (Day 4-6)

**Objective:** Enable real-time web search for current information

**Tasks:**
```python
# Files to create:
- src/tools/web_search.py            # NEW: Web search API wrapper
- src/tools/content_extractor.py     # NEW: Clean HTML to text
- config/search.yaml                 # NEW: Search API config
```

**Implementation Options:**

**Option A: DuckDuckGo (Free, No API Key)**
```python
# src/tools/web_search.py
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

class WebSearchTool:
    """Web search with content extraction."""
    
    def __init__(self):
        self.ddg = DDGS()
        
    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search web and return results with content."""
        results = []
        
        # Get search results
        search_results = self.ddg.text(query, max_results=max_results)
        
        for result in search_results:
            try:
                # Fetch and extract content
                response = requests.get(result['href'], timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract main text
                for script in soup(['script', 'style']):
                    script.decompose()
                text = soup.get_text(separator='\n', strip=True)
                
                results.append({
                    'url': result['href'],
                    'title': result['title'],
                    'snippet': result['body'],
                    'content': text[:5000],  # First 5K chars
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to fetch {result['href']}: {e}")
                continue
        
        return results
```

**Option B: Tavily API (Paid, Better Quality)**
```python
from tavily import TavilyClient

class TavilySearchTool:
    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)
    
    def search(self, query: str, max_results: int = 10):
        response = self.client.search(
            query=query,
            max_results=max_results,
            include_raw_content=True
        )
        return response['results']
```

**Dependencies to Add:**
```toml
# pyproject.toml
dependencies = [
    # ... existing ...
    "duckduckgo-search>=4.0.0",  # Free web search
    "beautifulsoup4>=4.12.0",    # HTML parsing
    "requests>=2.31.0",          # HTTP client
    "tavily-python>=0.3.0",      # Optional: better search
]
```

**Success Criteria:**
- ✅ Can search and retrieve 10+ web results per query
- ✅ Extracts clean text from HTML pages
- ✅ Returns title, URL, snippet, and full content
- ✅ Handles timeouts and errors gracefully

---

### 1.3 Integrate Retrieval into Grounder (Day 7-10)

**Objective:** Make Grounder actually retrieve evidence instead of hallucinating

**Tasks:**
```python
# Files to modify:
- src/agents/grounder.py             # MAJOR UPDATE
- src/orchestration/state.py         # Add evidence tracking
```

**Implementation:**

```python
# src/agents/grounder.py (NEW VERSION)
class GrounderAgent(BaseAgent):
    """Evidence retrieval and citation agent."""
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b-instruct-q4_K_M",
        vram_mb: int = 4500,
        temperature: float = 0.2,
        max_sources: int = 10
    ):
        super().__init__(name="Grounder", model_name=model_name, 
                        vram_mb=vram_mb, temperature=temperature)
        
        # NEW: Initialize retrieval tools
        self.vector_store = VectorStore()
        self.web_search = WebSearchTool()
        self.max_sources = max_sources
        
        self.prompt_template = self.load_prompt_template(...)
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """NEW: Retrieve evidence BEFORE prompting."""
        research_questions = state.plan.get("research_questions", [])
        
        # Collect evidence for all questions
        all_evidence = {}
        for rq in research_questions:
            question = rq['question']
            
            # 1. Search vector DB (existing knowledge)
            vector_results = self.vector_store.search(question, n_results=5)
            
            # 2. Search web (current information)
            web_results = self.web_search.search(question, max_results=5)
            
            # 3. Combine and rank evidence
            combined_evidence = self._combine_evidence(
                vector_results, 
                web_results
            )
            
            all_evidence[rq['id']] = combined_evidence
        
        # Now create prompt WITH actual evidence
        input_json = {
            "user_brief": state.user_brief,
            "research_questions": research_questions,
            "retrieved_evidence": all_evidence,  # NEW: Real evidence!
            "instructions": """
You now have ACTUAL EVIDENCE from web search and knowledge base.

For EACH research question:
1. Analyze the retrieved evidence (sources provided below)
2. Synthesize findings into 300-500 word answer
3. Cite specific sources using [Source X] notation
4. Identify gaps where evidence is lacking
5. Provide confidence scores based on evidence quality

DO NOT make up information. ONLY use the provided evidence.
If evidence is insufficient, explicitly state limitations.
"""
        }
        
        prompt = f"{self.prompt_template}\n\n"
        prompt += f"## Retrieved Evidence\n\n"
        
        # Include evidence in prompt
        for rq_id, evidence in all_evidence.items():
            prompt += f"### Evidence for {rq_id}\n\n"
            for i, source in enumerate(evidence, 1):
                prompt += f"**[Source {i}]** {source['title']}\n"
                prompt += f"URL: {source['url']}\n"
                prompt += f"Content: {source['content'][:1000]}...\n\n"
        
        prompt += f"## Your Task\n\n"
        prompt += f"Analyze the evidence above and provide detailed answers.\n"
        prompt += f"```json\n{json.dumps(input_json, indent=2)}\n```\n"
        
        return prompt
    
    def _combine_evidence(self, vector_results: dict, web_results: list) -> list:
        """Combine and rank evidence from multiple sources."""
        combined = []
        
        # Add vector DB results
        for i, doc in enumerate(vector_results.get('documents', [[]])[0]):
            combined.append({
                'source': 'vector_db',
                'content': doc,
                'metadata': vector_results['metadatas'][0][i],
                'score': vector_results['distances'][0][i]
            })
        
        # Add web search results
        for result in web_results:
            combined.append({
                'source': 'web',
                'title': result['title'],
                'url': result['url'],
                'content': result['content'],
                'score': 1.0  # All web results equally weighted initially
            })
        
        # Sort by relevance score
        combined.sort(key=lambda x: x.get('score', 1.0))
        
        return combined[:self.max_sources]
```

**Success Criteria:**
- ✅ Grounder retrieves 10+ sources per question
- ✅ Evidence included in LLM prompt
- ✅ Output includes actual citations with URLs
- ✅ Answers grounded in retrieved content

---

### 1.4 Citation Tracking (Day 11-14)

**Objective:** Track and validate all citations

**Tasks:**
```python
# Files to create:
- src/tools/citation_manager.py      # NEW: Citation tracking
- src/renderers/citation_formatter.py # NEW: Format references
```

**Implementation:**

```python
# src/tools/citation_manager.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Citation:
    """Structured citation data."""
    id: str
    title: str
    url: str
    accessed_date: str
    authors: list[str] = None
    publication_date: str = None
    source_type: str = "web"  # web, paper, book, etc.
    
class CitationManager:
    """Manage citations and generate bibliographies."""
    
    def __init__(self):
        self.citations = {}
        self.citation_counter = 1
    
    def add_citation(self, title: str, url: str, **kwargs) -> str:
        """Add citation and return citation ID."""
        citation_id = f"cite{self.citation_counter}"
        self.citation_counter += 1
        
        self.citations[citation_id] = Citation(
            id=citation_id,
            title=title,
            url=url,
            accessed_date=datetime.now().strftime("%Y-%m-%d"),
            **kwargs
        )
        
        return citation_id
    
    def format_bibliography(self, style: str = "apa") -> list[str]:
        """Generate formatted bibliography."""
        if style == "apa":
            return self._format_apa()
        elif style == "ieee":
            return self._format_ieee()
        else:
            return self._format_plain()
    
    def _format_apa(self) -> list[str]:
        """APA style citations."""
        bibliography = []
        for cite in sorted(self.citations.values(), key=lambda x: x.title):
            entry = f"{cite.title}. "
            if cite.url:
                entry += f"Retrieved {cite.accessed_date} from {cite.url}"
            bibliography.append(entry)
        return bibliography
    
    def get_citation_stats(self) -> dict:
        """Get citation statistics."""
        return {
            "total_citations": len(self.citations),
            "source_types": self._count_by_type(),
            "citation_ids": list(self.citations.keys())
        }
```

**Success Criteria:**
- ✅ All sources tracked with unique IDs
- ✅ Bibliography auto-generated
- ✅ Citations linked to specific claims
- ✅ APA/IEEE formatting support

---

## 📋 PHASE 2: Evidence & Citations (Week 3-4)

### 2.1 Enhanced Evidence Synthesis (Day 15-17)

**Objective:** Generate detailed, evidence-backed sections

**Tasks:**
```python
# Files to modify:
- src/agents/judge.py                # MAJOR UPDATE: Evidence synthesis
- config/prompts/judge.md            # UPDATE: New requirements
```

**Implementation:**

```python
# src/agents/judge.py (Enhanced synthesis)
class JudgeAgent(BaseAgent):
    """Final synthesis with evidence integration."""
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """Enhanced prompt with evidence requirements."""
        
        # Count total evidence available
        total_sources = 0
        for finding in state.research_findings:
            if 'sources' in finding:
                total_sources += len(finding['sources'])
        
        input_json = {
            "user_brief": state.user_brief,
            "research_findings": state.research_findings,
            "available_sources": total_sources,
            "synthesis_requirements": {
                "total_length": "4500-8000 words",
                "sections": "15-25 distinct sections",
                "section_length": {
                    "core": "800-1200 words (15-20 paragraphs)",
                    "important": "500-800 words (10-15 paragraphs)",
                    "supporting": "300-500 words (6-10 paragraphs)"
                },
                "evidence_requirements": {
                    "citations_per_section": "minimum 5 citations",
                    "data_points": "specific numbers/statistics",
                    "examples": "2-3 concrete examples per claim"
                },
                "structural_requirements": {
                    "tables": "3-5 data tables",
                    "methodology": "explicit research approach",
                    "limitations": "detailed section on gaps",
                    "references": "20-50 cited sources"
                }
            }
        }
        
        prompt = f"""
# CRITICAL SYNTHESIS REQUIREMENTS

You must produce a RESEARCH-GRADE document (4500-8000 words total).

## Structure Requirements

Generate 15-25 sections organized as:

1. **Executive Summary** (300-500 words)
   - Clear problem statement
   - Key findings with quantitative results
   - Main implications

2. **Introduction** (600-1000 words)
   - Context and importance
   - Research gap
   - 3-5 explicit contributions
   - Document roadmap

3. **Core Topic Sections** (800-1200 words each, 5-8 sections)
   - Deep technical explanations
   - Historical context
   - Multiple perspectives
   - Concrete examples with data
   - Implementation details

4. **Supporting Sections** (300-500 words each, 5-8 sections)
   - Comparisons and alternatives
   - Use cases and applications
   - Challenges and solutions
   - Performance analysis

5. **Methodology** (500-800 words)
   - Exact research approach used
   - Data sources with URLs
   - Evidence collection method
   - Quality assessment criteria

6. **Data & Analysis** (600-1000 words)
   - Tables summarizing key findings
   - Statistical summaries
   - Comparative analysis

7. **Limitations** (400-600 words)
   - Explicit gaps in evidence
   - Constraints of approach
   - What questions remain unanswered

8. **Conclusion** (200-400 words)
   - Summary of findings
   - Implications
   - Future directions

9. **References** (20-50 citations)
   - All cited sources
   - URLs and access dates

## Evidence Requirements

EVERY claim must be supported by:
- Specific citation: [Source X]
- Data point or statistic where applicable
- Concrete example demonstrating the concept

Example of proper evidence:
"Neural networks achieve 95% accuracy on ImageNet [Source 12], 
compared to 75% for traditional methods [Source 3]. For instance,
ResNet-50 processes 1000 images/second on a V100 GPU [Source 12],
making it suitable for real-time applications like autonomous driving
where latency must be under 100ms [Source 18]."

## Your Input

```json
{input_json}
```

## Output Format

Provide FULL DETAILED SECTIONS in your JSON response, not outlines.
"""
        
        return prompt
```

**Updated config/prompts/judge.md:**
```markdown
# Judge Agent Prompt - Research Synthesis

## CRITICAL REQUIREMENTS

You MUST produce research-grade output (4500-8000 words).

### Section Length Requirements

**UNACCEPTABLE:**
- "Neural networks learn through backpropagation." [1 sentence]

**REQUIRED:**
Neural networks learn through a multi-stage process called backpropagation,
which adjusts connection weights based on error gradients [Source 1]. 
The algorithm, first formalized by Rumelhart et al. in 1986 [Source 2], 
operates in two phases: forward propagation where inputs are processed 
through layers to produce outputs, and backward propagation where errors 
are propagated back to update weights [Source 1, 3].

Mathematically, the weight update follows the gradient descent rule:
w_new = w_old - learning_rate * ∂Loss/∂w [Source 4]

In practice, implementations use mini-batch gradient descent with batch 
sizes of 32-256 samples [Source 5], achieving convergence in 10-100 epochs 
depending on dataset complexity [Source 6]. Modern optimizers like Adam 
combine momentum and adaptive learning rates, improving training speed 
by 2-3x compared to vanilla SGD [Source 7, 8].

Real-world example: Training ResNet-50 on ImageNet (1.3M images) takes 
approximately 12 hours on 8x V100 GPUs, consuming roughly 15 kWh of energy 
[Source 9]. This highlights both the computational intensity and environmental 
considerations of deep learning [Source 10].

[300-500 words per section minimum]

### Evidence Density

Every paragraph must contain:
- 2-3 citations minimum
- At least one specific number/statistic
- One concrete example or use case

### Table Requirements

Include 3-5 tables such as:

**Table 1: Dataset Comparison**
| Dataset | Size | Task | Source |
|---------|------|------|--------|
| ImageNet | 1.3M images | Classification | [1] |
| COCO | 330K images | Detection | [2] |

**Table 2: Model Performance**
| Model | Accuracy | Params | Speed | Source |
|-------|----------|--------|-------|--------|
| ResNet-50 | 76.2% | 25M | 100 img/s | [3] |
| ViT-B | 77.9% | 86M | 45 img/s | [4] |
```

**Success Criteria:**
- ✅ Sections contain 300-1200 words (not 1-2 sentences)
- ✅ Every claim has citation: [Source X]
- ✅ Includes 3-5 data tables
- ✅ Total output: 4500-8000 words

---

### 2.2 Data Collection & Presentation (Day 18-21)

**Objective:** Generate tables, figures, and data summaries

**Tasks:**
```python
# Files to create:
- src/tools/data_formatter.py        # NEW: Table generation
- src/renderers/table_renderer.py    # NEW: Markdown tables
```

**Implementation:**

```python
# src/tools/data_formatter.py
class DataFormatter:
    """Format data into tables and figures."""
    
    @staticmethod
    def create_comparison_table(
        data: list[dict],
        columns: list[str],
        title: str = ""
    ) -> str:
        """Generate markdown comparison table."""
        
        # Header
        table = f"\n**{title}**\n\n" if title else "\n"
        table += "| " + " | ".join(columns) + " |\n"
        table += "|" + "|".join(["---"] * len(columns)) + "|\n"
        
        # Rows
        for row in data:
            values = [str(row.get(col, "N/A")) for col in columns]
            table += "| " + " | ".join(values) + " |\n"
        
        return table
    
    @staticmethod
    def create_summary_stats(data: dict) -> str:
        """Generate statistical summary."""
        summary = "\n**Summary Statistics**\n\n"
        for metric, value in data.items():
            if isinstance(value, (int, float)):
                summary += f"- **{metric}**: {value:.2f}\n"
            else:
                summary += f"- **{metric}**: {value}\n"
        return summary
    
    @staticmethod
    def extract_quantitative_data(text: str) -> list[dict]:
        """Extract numbers and statistics from text."""
        import re
        
        patterns = [
            r'(\d+\.?\d*)\s*%',  # Percentages
            r'(\d+\.?\d*)\s*(million|billion|thousand)',  # Large numbers
            r'(\d+\.?\d*)\s*(GB|MB|seconds?|hours?)',  # Units
        ]
        
        findings = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            findings.extend(matches)
        
        return findings
```

**Success Criteria:**
- ✅ Auto-generate 3-5 tables per document
- ✅ Extract quantitative data from evidence
- ✅ Format statistical summaries
- ✅ Tables are properly formatted markdown

---

### 2.3 Source Verification & Quality Scoring (Day 22-24)

**Objective:** Assess and report source quality

**Tasks:**
```python
# Files to create:
- src/tools/source_validator.py      # NEW: Validate sources
- src/tools/quality_scorer.py        # NEW: Score evidence quality
```

**Implementation:**

```python
# src/tools/source_validator.py
class SourceValidator:
    """Validate and score source quality."""
    
    TRUSTED_DOMAINS = {
        'arxiv.org': 0.95,
        'ieee.org': 0.95,
        'acm.org': 0.95,
        'nature.com': 0.98,
        'science.org': 0.98,
        '.edu': 0.85,
        '.gov': 0.90,
        'wikipedia.org': 0.70,
    }
    
    def validate_url(self, url: str) -> dict:
        """Validate source URL and assess credibility."""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check against trusted domains
        trust_score = 0.5  # Default
        for trusted_domain, score in self.TRUSTED_DOMAINS.items():
            if trusted_domain in domain:
                trust_score = score
                break
        
        # Additional checks
        has_https = parsed.scheme == 'https'
        is_academic = any(x in domain for x in ['.edu', 'arxiv', 'ieee', 'acm'])
        
        return {
            'url': url,
            'domain': domain,
            'trust_score': trust_score,
            'is_secure': has_https,
            'is_academic': is_academic,
            'validation_status': 'valid' if trust_score >= 0.6 else 'low_quality'
        }
    
    def assess_evidence_quality(self, sources: list[dict]) -> dict:
        """Assess overall evidence quality."""
        total_sources = len(sources)
        academic_count = sum(1 for s in sources if s.get('is_academic', False))
        avg_trust = sum(s.get('trust_score', 0.5) for s in sources) / max(total_sources, 1)
        
        return {
            'total_sources': total_sources,
            'academic_sources': academic_count,
            'average_trust_score': avg_trust,
            'quality_grade': self._grade_quality(avg_trust, academic_count, total_sources)
        }
    
    def _grade_quality(self, avg_trust: float, academic: int, total: int) -> str:
        """Assign quality grade."""
        academic_ratio = academic / max(total, 1)
        
        if avg_trust >= 0.85 and academic_ratio >= 0.5:
            return "Excellent"
        elif avg_trust >= 0.75 and academic_ratio >= 0.3:
            return "Good"
        elif avg_trust >= 0.65:
            return "Satisfactory"
        else:
            return "Needs Improvement"
```

**Success Criteria:**
- ✅ Each source scored for credibility
- ✅ Academic sources prioritized
- ✅ Quality report included in output
- ✅ Low-quality sources flagged

---

## 📋 PHASE 3: Data & Analysis (Week 5-6)

### 3.1 Statistical Analysis Integration (Day 25-28)

**Objective:** Add statistical rigor to findings

**Tasks:**
```python
# Files to create:
- src/tools/statistics.py            # NEW: Statistical analysis
```

**Implementation:**

```python
# src/tools/statistics.py
import numpy as np
from scipy import stats

class StatisticalAnalyzer:
    """Perform statistical analysis on data."""
    
    @staticmethod
    def compute_summary_stats(data: list[float]) -> dict:
        """Compute mean, std, median, etc."""
        arr = np.array(data)
        return {
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'median': float(np.median(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'n': len(data)
        }
    
    @staticmethod
    def compare_groups(group_a: list[float], group_b: list[float]) -> dict:
        """Compare two groups with t-test."""
        t_stat, p_value = stats.ttest_ind(group_a, group_b)
        
        return {
            'test': 't-test',
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': p_value < 0.05,
            'interpretation': 'significantly different' if p_value < 0.05 else 'not significantly different'
        }
    
    @staticmethod
    def format_statistical_result(mean: float, std: float, n: int) -> str:
        """Format as Mean ± SD (n=X)."""
        return f"{mean:.2f} ± {std:.2f} (n={n})"
```

**Success Criteria:**
- ✅ Statistical summaries included
- ✅ Mean ± std reported where applicable
- ✅ Significance tests performed
- ✅ Results formatted professionally

---

### 3.2 Reproducibility Documentation (Day 29-32)

**Objective:** Document methodology for reproducibility

**Tasks:**
```python
# Files to modify:
- src/renderers/markdown.py          # Add methodology section
- config/templates/research_report.md.j2  # Update template
```

**Updated Template:**

```jinja2
<!-- config/templates/research_report.md.j2 -->

## Methodology

**Research Approach:** {{ methodology.approach }}

**Data Collection:**
- **Search Queries Used:** {{ methodology.search_queries|length }} distinct queries
- **Sources Retrieved:** {{ methodology.total_sources }} sources
  - Academic papers: {{ methodology.academic_sources }}
  - Web articles: {{ methodology.web_sources }}
  - Documentation: {{ methodology.doc_sources }}
- **Retrieval Period:** {{ methodology.start_time }} to {{ methodology.end_time }}

**Evidence Synthesis:**
- **Vector Database:** {{ methodology.vector_db_size }} documents indexed
- **Embedding Model:** {{ methodology.embedding_model }}
- **Search Method:** Cosine similarity with threshold {{ methodology.similarity_threshold }}

**Quality Assurance:**
- **Source Validation:** All sources verified for accessibility
- **Citation Tracking:** {{ methodology.total_citations }} unique citations
- **Evidence Grading:** Average source trust score: {{ methodology.avg_trust_score }}

**Agents Used:**
{% for agent in methodology.agents %}
- **{{ agent.name }}**: {{ agent.role }} ({{ agent.model }})
{% endfor %}

**Reproducibility:**
- **System Version:** ZenKnowledgeForge v{{ version }}
- **Execution Time:** {{ execution_time }}
- **Random Seed:** {{ random_seed }}
- **Configuration:** Available in session log

## Data Sources

### Retrieved Documents

{{ sources_table }}

### Citation Statistics

- Total unique sources: {{ citation_stats.total }}
- Academic sources: {{ citation_stats.academic }}
- Average publication date: {{ citation_stats.avg_date }}
- Average trust score: {{ citation_stats.avg_trust }}
```

**Success Criteria:**
- ✅ Complete methodology section (500-800 words)
- ✅ All data sources listed with URLs
- ✅ Reproducibility information included
- ✅ Execution metadata captured

---

### 3.3 Enhanced Output Formatting (Day 33-35)

**Objective:** Professional document formatting

**Tasks:**
```python
# Files to modify:
- config/templates/research_report.md.j2  # Major redesign
```

**Enhanced Template Structure:**

```jinja2
# {{ title }}

{% if subtitle %}
## {{ subtitle }}
{% endif %}

> **Research Report**  
> Generated by ZenKnowledgeForge Multi-Agent Research System  
> Date: {{ generation_date }}  
> Session ID: {{ session_id }}

---

## Document Information

| Field | Value |
|-------|-------|
| **Topic** | {{ topic }} |
| **Research Mode** | {{ mode }} |
| **Total Sources** | {{ total_sources }} |
| **Word Count** | {{ word_count }} |
| **Consensus Score** | {{ consensus_score }}/100 |
| **Quality Grade** | {{ quality_grade }} |

---

## Executive Summary

{{ executive_summary }}

**Key Findings:**
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

**Main Implications:**
{{ implications }}

---

## Table of Contents

{% for section in sections %}
{{ loop.index }}. [{{ section.title }}](#{{ section.anchor }})
{% endfor %}

---

{% for section in sections %}
## {{ section.title }}

{{ section.content }}

{% if section.tables %}
{% for table in section.tables %}
{{ table }}
{% endfor %}
{% endif %}

{% if section.citations %}
**References for this section:** {{ section.citations|join(', ') }}
{% endif %}

*Section Quality: {{ section.confidence }}% | Word Count: {{ section.word_count }}*

---

{% endfor %}

## Limitations & Gaps

This research has the following limitations:

{% for limitation in limitations %}
- **{{ limitation.category }}**: {{ limitation.description }}
{% endfor %}

**Evidence Gaps:**
{% for gap in evidence_gaps %}
- {{ gap }}
{% endfor %}

---

## References

{% for citation in citations %}
[{{ loop.index }}] {{ citation.title }}. {% if citation.authors %}{{ citation.authors|join(', ') }}. {% endif %}Retrieved {{ citation.accessed_date }} from {{ citation.url }}
{% endfor %}

---

## Appendix: Methodology Details

### Search Queries Used

{% for query in search_queries %}
{{ loop.index }}. `{{ query }}`
{% endfor %}

### Agent Execution Log

{% for log in agent_logs %}
- **{{ log.timestamp }}** - {{ log.agent }}: {{ log.action }}
{% endfor %}

### Quality Metrics

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Groundedness | {{ metrics.groundedness }}% | {{ metrics.groundedness_interpretation }} |
| Coherence | {{ metrics.coherence }}% | {{ metrics.coherence_interpretation }} |
| Completeness | {{ metrics.completeness }}% | {{ metrics.completeness_interpretation }} |
| Source Quality | {{ metrics.source_quality }}% | {{ metrics.source_quality_interpretation }} |
| **Overall** | **{{ metrics.overall }}%** | **{{ metrics.overall_interpretation }}** |

---

*This research report was generated through a deliberative multi-agent process. All findings are grounded in retrieved evidence with full source attribution for verification.*
```

---

## 📋 PHASE 4: Quality & Polish (Week 7-8)

### 4.1 Content Validation (Day 36-38)

**Objective:** Validate output meets research standards

**Tasks:**
```python
# Files to create:
- src/validators/research_validator.py  # NEW: Validate research quality
```

**Implementation:**

```python
# src/validators/research_validator.py
class ResearchValidator:
    """Validate research document quality."""
    
    REQUIREMENTS = {
        'total_words': (4500, 8000),
        'sections_count': (15, 25),
        'core_section_words': (800, 1200),
        'citations_count': (20, 50),
        'tables_count': (3, 5),
        'executive_summary_words': (300, 500),
        'methodology_words': (500, 800),
    }
    
    def validate(self, document: dict) -> dict:
        """Validate document against requirements."""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        # Check total word count
        total_words = self._count_words(document)
        results['metrics']['total_words'] = total_words
        
        min_words, max_words = self.REQUIREMENTS['total_words']
        if total_words < min_words:
            results['valid'] = False
            results['errors'].append(
                f"Document too short: {total_words} words (minimum: {min_words})"
            )
        elif total_words > max_words:
            results['warnings'].append(
                f"Document very long: {total_words} words (maximum: {max_words})"
            )
        
        # Check section count
        section_count = len(document.get('sections', []))
        results['metrics']['sections'] = section_count
        
        min_sections, max_sections = self.REQUIREMENTS['sections_count']
        if section_count < min_sections:
            results['valid'] = False
            results['errors'].append(
                f"Too few sections: {section_count} (minimum: {min_sections})"
            )
        
        # Check citations
        citations = len(document.get('citations', []))
        results['metrics']['citations'] = citations
        
        min_cites, max_cites = self.REQUIREMENTS['citations_count']
        if citations < min_cites:
            results['valid'] = False
            results['errors'].append(
                f"Insufficient citations: {citations} (minimum: {min_cites})"
            )
        
        # Check for required sections
        required_sections = [
            'Executive Summary',
            'Introduction',
            'Methodology',
            'Limitations',
            'Conclusion',
            'References'
        ]
        
        section_titles = [s['title'] for s in document.get('sections', [])]
        for req_section in required_sections:
            if not any(req_section.lower() in title.lower() for title in section_titles):
                results['errors'].append(f"Missing required section: {req_section}")
                results['valid'] = False
        
        # Check evidence density
        for section in document.get('sections', []):
            content = section.get('content', '')
            citations_in_section = content.count('[Source ')
            words_in_section = len(content.split())
            
            if words_in_section > 200 and citations_in_section == 0:
                results['warnings'].append(
                    f"Section '{section['title']}' has no citations ({words_in_section} words)"
                )
        
        return results
    
    def _count_words(self, document: dict) -> int:
        """Count total words in document."""
        total = 0
        for section in document.get('sections', []):
            total += len(section.get('content', '').split())
        return total
    
    def generate_validation_report(self, results: dict) -> str:
        """Generate human-readable validation report."""
        report = "# Research Document Validation Report\n\n"
        
        report += f"**Status:** {'✅ PASS' if results['valid'] else '❌ FAIL'}\n\n"
        
        report += "## Metrics\n\n"
        for metric, value in results['metrics'].items():
            report += f"- **{metric.replace('_', ' ').title()}:** {value}\n"
        
        if results['errors']:
            report += "\n## ❌ Errors\n\n"
            for error in results['errors']:
                report += f"- {error}\n"
        
        if results['warnings']:
            report += "\n## ⚠️ Warnings\n\n"
            for warning in results['warnings']:
                report += f"- {warning}\n"
        
        return report
```

**Success Criteria:**
- ✅ Validation catches short documents
- ✅ Flags missing required sections
- ✅ Warns about uncited claims
- ✅ Generates actionable validation report

---

### 4.2 Automated Testing (Day 39-42)

**Objective:** Ensure system reliability

**Tasks:**
```python
# Files to create:
- tests/integration/test_full_pipeline.py     # Integration tests
- tests/unit/test_vector_store.py             # Unit tests
- tests/unit/test_web_search.py               # Unit tests
- tests/unit/test_citations.py                # Unit tests
```

**Example Test:**

```python
# tests/integration/test_full_pipeline.py
import pytest
from src.orchestration.engine import PipelineEngine
from src.validators.research_validator import ResearchValidator

def test_research_mode_produces_valid_output():
    """Test that research mode produces documents meeting requirements."""
    
    # Run pipeline
    engine = PipelineEngine()
    result = engine.execute_pipeline(
        user_brief="What is quantum computing?",
        mode="research"
    )
    
    # Validate output
    validator = ResearchValidator()
    validation = validator.validate(result['final_artifact'])
    
    # Assertions
    assert validation['valid'], f"Validation failed: {validation['errors']}"
    assert validation['metrics']['total_words'] >= 4500
    assert validation['metrics']['sections'] >= 15
    assert validation['metrics']['citations'] >= 20
    
def test_all_sections_have_content():
    """Ensure no empty sections."""
    
    engine = PipelineEngine()
    result = engine.execute_pipeline(
        user_brief="Explain neural networks",
        mode="research"
    )
    
    sections = result['final_artifact']['sections']
    
    for section in sections:
        word_count = len(section['content'].split())
        assert word_count >= 100, f"Section '{section['title']}' too short: {word_count} words"

def test_citations_are_valid_urls():
    """Validate all citations have valid URLs."""
    
    engine = PipelineEngine()
    result = engine.execute_pipeline(
        user_brief="Machine learning basics",
        mode="research"
    )
    
    citations = result['final_artifact']['citations']
    
    for citation in citations:
        assert 'url' in citation
        assert citation['url'].startswith('http'), f"Invalid URL: {citation['url']}"
        assert 'title' in citation
        assert len(citation['title']) > 5
```

---

### 4.3 Performance Optimization (Day 43-45)

**Objective:** Optimize for speed and resource usage

**Tasks:**
```python
# Files to modify:
- src/tools/web_search.py           # Add caching
- src/tools/vector_store.py         # Optimize queries
```

**Implementation:**

```python
# Caching layer for web search
from functools import lru_cache
import hashlib
import pickle
from pathlib import Path

class CachedWebSearch:
    """Web search with persistent caching."""
    
    def __init__(self, cache_dir: str = "./cache/searches"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.web_search = WebSearchTool()
    
    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search with caching."""
        
        # Generate cache key
        cache_key = hashlib.md5(
            f"{query}_{max_results}".encode()
        ).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # Check cache
        if cache_file.exists():
            # Check if cache is fresh (< 7 days)
            age_days = (time.time() - cache_file.stat().st_mtime) / 86400
            if age_days < 7:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        # Fetch fresh results
        results = self.web_search.search(query, max_results)
        
        # Save to cache
        with open(cache_file, 'wb') as f:
            pickle.dump(results, f)
        
        return results
```

**Optimization Goals:**
- ✅ Cache web searches for 7 days
- ✅ Batch vector DB queries
- ✅ Parallel evidence retrieval
- ✅ Reduce duplicate API calls

---

### 4.4 Final Documentation (Day 46-49)

**Objective:** Complete user documentation

**Tasks:**
```python
# Files to create/update:
- RESEARCH_OUTPUT_GUIDE.md          # NEW: Guide to output quality
- README.md                         # UPDATE: New capabilities
- docs/RESEARCH_MODE.md             # NEW: Research mode details
```

**Content:**

```markdown
# Research Output Guide

## What to Expect

When you run ZenKnowledgeForge in research mode, you will receive a comprehensive research document (4,500-8,000 words) containing:

### Document Structure

1. **Executive Summary** (300-500 words)
   - Problem statement
   - Key findings
   - Main implications

2. **Introduction** (600-1,000 words)
   - Context and motivation
   - Research gap
   - Explicit contributions

3. **Core Topic Sections** (5-8 sections, 800-1,200 words each)
   - Deep technical explanations
   - Historical context
   - Concrete examples
   - Implementation details

4. **Supporting Sections** (5-8 sections, 300-500 words each)
   - Comparisons and alternatives
   - Use cases
   - Challenges and solutions

5. **Methodology** (500-800 words)
   - Research approach
   - Data sources (with URLs)
   - Quality assessment

6. **Limitations** (400-600 words)
   - Evidence gaps
   - Constraints
   - Future work needed

7. **References** (20-50 citations)
   - Full bibliography
   - All sources cited in text

### Evidence Quality

Every document includes:
- **20-50 cited sources** from web search and knowledge base
- **5+ citations per section** supporting claims
- **Source validation** - each source scored for credibility
- **Data tables** summarizing key findings
- **Concrete examples** demonstrating concepts

### Quality Metrics

Each document is validated for:
- ✅ Minimum 4,500 words total
- ✅ 15-25 distinct sections
- ✅ 20+ unique citations
- ✅ 3-5 data tables
- ✅ All required sections present
- ✅ Evidence density (citations per 100 words)

### Reproducibility

Every document includes:
- Complete methodology section
- All search queries used
- Source retrieval timestamps
- Agent execution log
- System version and configuration
```

---

## 📊 Implementation Summary

### Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1: Foundation** | Week 1-2 | Vector DB, Web search, RAG integration |
| **Phase 2: Evidence** | Week 3-4 | Citations, Enhanced synthesis, Data tables |
| **Phase 3: Data & Analysis** | Week 5-6 | Statistics, Reproducibility, Formatting |
| **Phase 4: Quality** | Week 7-8 | Validation, Testing, Documentation |

**Total Duration:** 8 weeks (2 months)

### Resource Requirements

**Development:**
- 1 senior developer (full-time, 8 weeks)
- OR 2 mid-level developers (full-time, 8 weeks)

**Infrastructure:**
- ChromaDB storage: ~10GB for knowledge base
- Web search API: Free (DuckDuckGo) or $50/month (Tavily)
- Increased compute: +20% for embedding generation

**Dependencies to Add:**
```toml
# New dependencies
"duckduckgo-search>=4.0.0",
"beautifulsoup4>=4.12.0",
"requests>=2.31.0",
"scipy>=1.11.0",
"numpy>=1.24.0",
```

### Expected Outcomes

**Before Implementation:**
- ❌ Output: 500 words
- ❌ Evidence: None (hallucinations)
- ❌ Citations: None
- ❌ Quality: 20% (outlines only)

**After Implementation:**
- ✅ Output: 4,500-8,000 words
- ✅ Evidence: 20-50 real sources
- ✅ Citations: Full bibliography
- ✅ Quality: 80%+ (research-grade)

---

## 🚀 Quick Start Implementation (Minimum Viable)

If 8 weeks is too long, here's a **2-week MVP**:

### Week 1: Core Retrieval
1. Add web search (DuckDuckGo) - Day 1-2
2. Integrate into Grounder - Day 3-4
3. Citation tracking - Day 5

### Week 2: Enhanced Output
1. Update Judge prompts for longer sections - Day 1-2
2. Add data tables - Day 3-4
3. Validation & testing - Day 5

**MVP Outcome:** 2,000-3,000 words with real citations (not perfect, but 6x better than current)

---

## ✅ Success Criteria

The implementation will be considered successful when:

1. ✅ **Documents are 4,500-8,000 words** (not 500)
2. ✅ **20-50 real sources cited** with URLs
3. ✅ **All claims supported by evidence** (no hallucinations)
4. ✅ **3-5 data tables** included
5. ✅ **Methodology section** explains research process
6. ✅ **Validation passes** 95%+ of test cases
7. ✅ **Execution time** < 30 minutes per document
8. ✅ **User satisfaction** with output quality

---

## 📝 Next Steps

To begin implementation:

1. **Review & Approve Plan** - Stakeholder sign-off
2. **Set Up Development Environment** - Install dependencies
3. **Create Feature Branch** - `feature/research-grade-output`
4. **Begin Phase 1, Day 1** - Vector store implementation
5. **Weekly Progress Reviews** - Track against timeline

---

*This plan transforms ZenKnowledgeForge from an outline generator into a true research system capable of producing publication-quality documents with evidence, citations, and rigorous analysis.*
