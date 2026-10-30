import logging
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
from backend.models.report import SourceMetadata, ResearchReport
from backend.models.tool_result import SearchCandidate, ScrapedDocument

logger = logging.getLogger("agent.verifier")

class CitationVerifier:
    """
    Automated Critic & Grounding Verifier.
    Performs deterministic post-synthesis checks:
    1. Validates that cited URLs originate from retrieved context (anti-hallucination).
    2. Calculates factual grounding score.
    3. Derives confidence rating ('High', 'Medium', 'Low') from concrete empirical metrics.
    """

    def verify_and_score(
        self,
        raw_report: Dict[str, Any],
        candidates: List[SearchCandidate],
        documents: List[ScrapedDocument],
        query: str
    ) -> Tuple[List[SourceMetadata], float, str, List[str]]:
        """
        Validates sources, computes dynamic confidence score and level.
        Returns: (verified_sources, confidence_score, confidence_level, limitations)
        """
        retrieved_urls = {c.url.rstrip("/") for c in candidates}
        retrieved_urls.update({d.url.rstrip("/") for d in documents if d.status == "success"})
        
        raw_sources = raw_report.get("sources_used", [])
        verified_sources: List[SourceMetadata] = []
        hallucinated_citations = 0

        for s in raw_sources:
            url = s.get("url", "").rstrip("/")
            title = s.get("title", "")
            snippet = s.get("snippet", "")
            domain = s.get("domain", "")
            
            if not domain and url:
                try:
                    domain = urlparse(url).netloc.replace("www.", "")
                except Exception:
                    domain = "unknown"

            # Check if this URL was actually retrieved
            is_valid = any(url == r_url or url in r_url or r_url in url for r_url in retrieved_urls)
            
            if is_valid:
                verified_sources.append(SourceMetadata(
                    title=title or domain,
                    url=url,
                    snippet=snippet or "Verified source citation",
                    domain=domain,
                    relevance_score=s.get("relevance_score", 0.9)
                ))
            else:
                hallucinated_citations += 1

        # If model hallucinated all citations or omitted them, backfill with top valid candidates
        if not verified_sources and candidates:
            for c in candidates[:3]:
                verified_sources.append(SourceMetadata(
                    title=c.title,
                    url=c.url,
                    snippet=c.snippet,
                    domain=c.domain,
                    relevance_score=0.85
                ))

        # --- DYNAMIC CONFIDENCE SCORING ALGORITHM ---
        # 1. Coverage weight (up to 0.40): Number of high-quality verified sources
        source_count = len(verified_sources)
        coverage_score = min(source_count / 3.0, 1.0) * 0.40
        
        # 2. Scrape Depth weight (up to 0.30): Did we successfully scrape full pages?
        successful_scrapes = sum(1 for d in documents if d.status == "success" and d.char_count > 500)
        depth_score = min(successful_scrapes / 2.0, 1.0) * 0.30

        # 3. Citation Authenticity weight (up to 0.30): Ratio of non-hallucinated citations
        total_citations = source_count + hallucinated_citations
        citation_ratio = (source_count / total_citations) if total_citations > 0 else 0.5
        authenticity_score = citation_ratio * 0.30

        confidence_score = round(coverage_score + depth_score + authenticity_score, 2)
        confidence_score = max(0.10, min(0.99, confidence_score))

        # Determine level
        if confidence_score >= 0.80:
            confidence_level = "High"
        elif confidence_score >= 0.55:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"

        # Update limitations if penalties applied
        limitations = list(raw_report.get("limitations_or_assumptions", []))
        if hallucinated_citations > 0:
            limitations.append(f"Filtered {hallucinated_citations} uncited or unverified references from synthesis.")
        if source_count < 2:
            limitations.append("Limited source diversity: findings based on sparse web search results.")
        if successful_scrapes == 0:
            limitations.append("Full page scraping was blocked or timed out; synthesis relied on search snippets.")

        return verified_sources, confidence_score, confidence_level, limitations

verifier = CitationVerifier()
