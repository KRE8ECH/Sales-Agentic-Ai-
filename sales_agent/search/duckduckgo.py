import sys
import json
import time
import logging
import subprocess
import warnings
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class DuckDuckGoSearchTool:
    """Wrapper around DuckDuckGo search (ddgs / duckduckgo_search) for gathering public web context."""

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _search_ddgs_isolated(self, query: str, limit: int, backend_opt: str = "lite") -> Tuple[List[Dict[str, str]], Optional[str]]:
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
    sys.stderr.write(str(e))
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
                return json.loads(proc.stdout.strip()), None
            err = proc.stderr.strip() or f"DDGS subprocess exited with code {proc.returncode}"
            return [], err
        except Exception as e:
            logger.debug(f"Isolated DDGS search execution error: {e}")
            return [], str(e)

    def search_with_status(self, query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
        """Runs search and returns explicit status ('SUCCESS', 'FAILED', 'NO_RESULTS') and error details."""
        limit = max_results or self.max_results
        last_error = None

        for backend_opt in ["lite", "auto", "html"]:
            res, err = self._search_ddgs_isolated(query, limit, backend_opt)
            if res:
                return {
                    "status": "SUCCESS",
                    "results": res,
                    "error": None,
                    "backend": backend_opt
                }
            if err:
                last_error = err
            time.sleep(0.1)

        return {
            "status": "FAILED" if last_error else "NO_RESULTS",
            "results": [],
            "error": last_error or "Search returned 0 results"
        }

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        res_obj = self.search_with_status(query, max_results)
        return res_obj.get("results", [])

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
