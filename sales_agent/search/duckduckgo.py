import time
import logging
import warnings
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DuckDuckGoSearchTool:
    """Wrapper around DuckDuckGo search (ddgs / duckduckgo_search) for gathering public web context."""

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _get_ddgs_class(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from ddgs import DDGS
                return DDGS
        except ImportError:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from duckduckgo_search import DDGS
                return DDGS

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        limit = max_results or self.max_results
        results = []
        try:
            DDGS = self._get_ddgs_class()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query, max_results=limit))
                    for item in raw_results:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("href", "") or item.get("link", ""),
                            "snippet": item.get("body", "") or item.get("snippet", "")
                        })
        except Exception as e:
            logger.warning(f"DuckDuckGo search error for query '{query}': {e}")
            try:
                DDGS = self._get_ddgs_class()
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ddgs = DDGS()
                    res = ddgs.text(keywords=query, max_results=limit)
                    for item in res:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("href", "") or item.get("link", ""),
                            "snippet": item.get("body", "") or item.get("snippet", "")
                        })
            except Exception as e2:
                logger.error(f"Fallback DDGS also failed: {e2}")

        return results

    def search_lead_context(self, name: str, company: str, role: str = "") -> List[Dict[str, str]]:
        """Run targeted multi-angle queries for a specific lead."""
        queries = [
            f'"{company}" news announcements 2024 2025 2026',
            f'"{name}" "{company}" {role}',
            f'"{company}" challenges growth funding product launch'
        ]
        
        aggregated = []
        seen_urls = set()

        for q in queries:
            items = self.search(q, max_results=3)
            for item in items:
                url = item.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    aggregated.append(item)
            time.sleep(0.3)

        return aggregated
