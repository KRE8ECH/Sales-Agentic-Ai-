import sys
import json
import time
import logging
import subprocess
import warnings
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DuckDuckGoSearchTool:
    """Wrapper around DuckDuckGo search (ddgs / duckduckgo_search) for gathering public web context."""

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _search_ddgs_isolated(self, query: str, limit: int, backend_opt: str = "lite") -> List[Dict[str, str]]:
        """Run DDGS in an isolated worker to prevent rust/system-configuration crashes on macOS."""
        worker_code = f"""
import sys, json, warnings
warnings.simplefilter('ignore')
try:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS

    with DDGS(timeout=8) as ddgs:
        raw = list(ddgs.text({repr(query)}, backend={repr(backend_opt)}, max_results={limit}))
        items = []
        for item in raw:
            items.append({{
                "title": item.get("title", ""),
                "url": item.get("href", "") or item.get("link", ""),
                "snippet": item.get("body", "") or item.get("snippet", "")
            }})
        print(json.dumps(items))
except Exception as e:
    sys.exit(1)
"""
        try:
            proc = subprocess.run(
                [sys.executable, "-c", worker_code],
                capture_output=True,
                text=True,
                timeout=12
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return json.loads(proc.stdout.strip())
        except Exception as e:
            logger.debug(f"Isolated DDGS search execution error: {e}")
        return []

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        limit = max_results or self.max_results

        # Try backend="lite" then "auto" then "html"
        for backend_opt in ["lite", "auto", "html"]:
            res = self._search_ddgs_isolated(query, limit, backend_opt)
            if res:
                return res
            time.sleep(0.1)

        return []

    def search_lead_context(self, name: str, company: str, role: str = "") -> List[Dict[str, str]]:
        """Run targeted multi-angle queries for a specific lead."""
        queries = [
            f"{company} news announcements 2024 2025 2026",
            f"{name} {company} {role}",
            f"{company} growth funding product launch"
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
            time.sleep(0.1)

        return aggregated
