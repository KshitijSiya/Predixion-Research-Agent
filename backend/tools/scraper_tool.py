import asyncio
import logging
from typing import List, Optional
import trafilatura
from backend.config import settings
from backend.models.tool_result import ScrapedDocument
from backend.tools.cache import scraper_cache
from backend.core.sanitization import sanitizer

logger = logging.getLogger("agent.tools.scraper")

class WebScraperTool:
    """
    Production web scraper that extracts clean, readable text from HTML pages
    using Trafilatura. Includes strict timeouts, token capping, and prompt-injection sanitization.
    """
    def __init__(self):
        self.timeout = settings.SCRAPE_TIMEOUT_SECONDS
        self.max_chars = settings.MAX_CONTENT_TOKENS_PER_PAGE * 4  # approx 4 chars per token

    async def scrape(self, url: str, simulate_failure: str = "none") -> ScrapedDocument:
        """
        Scrapes a single URL and returns clean markdown text.
        """
        if simulate_failure == "bad_scrape":
            logger.info(f"[SIMULATION] Returning malformed HTML/scrape error for {url}")
            return ScrapedDocument(
                url=url,
                title="Malformed Page",
                content="403 Forbidden - Access Denied by Captcha Challenge.",
                char_count=50,
                status="blocked",
                error_message="Simulated 403 Forbidden Captcha Challenge."
            )

        if simulate_failure == "timeout":
            logger.info(f"[SIMULATION] Simulating scraper timeout for {url}")
            await asyncio.sleep(0.3)
            return ScrapedDocument(
                url=url,
                content="",
                status="timeout",
                error_message="Simulated connection timeout after 8 seconds."
            )

        cached = scraper_cache.get(url)
        if cached is not None:
            logger.info(f"Cache hit for URL: {url}")
            return cached

        try:
            loop = asyncio.get_running_loop()
            
            # Use trafilatura's robust fetch_url inside executor
            html = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: trafilatura.fetch_url(url)),
                timeout=float(self.timeout)
            )

            if not html:
                return ScrapedDocument(
                    url=url,
                    content="",
                    status="parse_error",
                    error_message="Failed to fetch webpage content."
                )

            # Extract clean body text
            text = await loop.run_in_executor(
                None, 
                lambda: trafilatura.extract(
                    html, 
                    include_links=False, 
                    include_images=False,
                    favor_precision=True
                )
            )

            if not text or len(text.strip()) < 50:
                # Fallback baseline extraction
                text = await loop.run_in_executor(None, lambda: trafilatura.baseline(html)[1])

            text = text or ""
            # Sanitize and truncate to prevent context explosion
            cleaned = sanitizer.sanitize_text(text)
            if len(cleaned) > self.max_chars:
                cleaned = cleaned[:self.max_chars] + "\n...[Content truncated for length bound]..."

            # Extract title if present
            title = ""
            metadata = await loop.run_in_executor(None, lambda: trafilatura.extract_metadata(html))
            if metadata and metadata.title:
                title = metadata.title

            doc = ScrapedDocument(
                url=url,
                title=title or url,
                content=cleaned,
                char_count=len(cleaned),
                status="success" if cleaned else "parse_error"
            )
            scraper_cache.set(url, doc)
            return doc

        except asyncio.TimeoutError:
            logger.warning(f"Scrape timeout for {url}")
            return ScrapedDocument(
                url=url,
                content="",
                status="timeout",
                error_message=f"Request timed out after {self.timeout}s."
            )
        except Exception as e:
            logger.warning(f"Scrape error for {url}: {e}")
            return ScrapedDocument(
                url=url,
                content="",
                status="parse_error",
                error_message=str(e)
            )

    async def scrape_multi(
        self, 
        urls: List[str], 
        max_concurrent: int = 4,
        simulate_failure: str = "none"
    ) -> List[ScrapedDocument]:
        """
        Scrapes multiple URLs concurrently with concurrency limit.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _bounded_scrape(u: str):
            async with semaphore:
                return await self.scrape(u, simulate_failure=simulate_failure)

        tasks = [_bounded_scrape(u) for u in urls]
        return await asyncio.gather(*tasks)

# Singleton
scraper_tool = WebScraperTool()
