import asyncio
import logging
from typing import List, Optional
from urllib.parse import urlparse
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from backend.config import settings
from backend.models.tool_result import SearchCandidate
from backend.tools.cache import search_cache

logger = logging.getLogger("agent.tools.search")

class SearchTool:
    """
    Zero-config DuckDuckGo search tool with multi-query support,
    automatic URL deduplication, domain extraction, and TTL caching.
    """
    def __init__(self):
        self.max_results = settings.MAX_SEARCH_RESULTS

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    async def search(
        self, 
        query: str, 
        max_results: Optional[int] = None,
        simulate_failure: str = "none"
    ) -> List[SearchCandidate]:
        """
        Executes a single search query against DuckDuckGo.
        """
        if simulate_failure == "empty_results":
            logger.info("[SIMULATION] Returning 0 search results for testing fallback.")
            return []
            
        if simulate_failure == "timeout":
            logger.info("[SIMULATION] Simulating network timeout on search.")
            await asyncio.sleep(0.5)
            raise TimeoutError("Simulated network timeout during search execution.")

        limit = max_results or self.max_results
        cache_key = f"ddg:{query.strip().lower()}:{limit}"
        
        cached = search_cache.get(cache_key)
        if cached is not None:
            logger.info(f"Cache hit for search query: '{query}'")
            return cached

        # DDGS is synchronous; execute in threadpool to keep async loop non-blocking
        def _fetch_ddg():
            results = []
            try:
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query, max_results=limit))
                    for idx, r in enumerate(raw_results):
                        url = r.get("href", "")
                        title = r.get("title", "")
                        body = r.get("body", "")
                        domain = self._extract_domain(url)
                        results.append(SearchCandidate(
                            title=title,
                            url=url,
                            snippet=body,
                            rank=idx + 1,
                            domain=domain
                        ))
            except Exception as e:
                logger.error(f"DuckDuckGo search error for query '{query}': {e}")
            return results

        loop = asyncio.get_running_loop()
        candidates = await loop.run_in_executor(None, _fetch_ddg)
        
        # Cache successful results
        if candidates:
            search_cache.set(cache_key, candidates)
            
        return candidates

    async def search_multi(
        self, 
        queries: List[str], 
        max_results_per_query: int = 3,
        simulate_failure: str = "none"
    ) -> List[SearchCandidate]:
        """
        Executes multiple search queries concurrently and deduplicates results by URL.
        """
        tasks = [
            self.search(q, max_results=max_results_per_query, simulate_failure=simulate_failure) 
            for q in queries
        ]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        deduped: List[SearchCandidate] = []
        seen_urls = set()
        
        for res in results_lists:
            if isinstance(res, list):
                for candidate in res:
                    normalized_url = candidate.url.rstrip("/")
                    if normalized_url not in seen_urls:
                        seen_urls.add(normalized_url)
                        deduped.append(candidate)
                        
        return deduped

# Singleton
search_tool = SearchTool()
