import sys
import json
import time
import logging
import subprocess
import urllib.request
import urllib.parse
from html.parser import HTMLParser
import warnings
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class _DDGHtmlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.in_title = False
        self.in_snippet = False
        self.curr = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == "a" and ("result__snippet" in cls or "result-snippet" in cls):
            self.in_snippet = True
        elif tag == "a" and ("result__a" in cls or "result__title" in cls or "result-link" in cls):
            self.in_title = True
            href = attrs_dict.get("href", "")
            if "uddg=" in href:
                try:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    href = qs.get("uddg", [href])[0]
                except Exception:
                    pass
            self.curr = {"title": "", "url": href, "snippet": ""}

    def handle_endtag(self, tag):
        if self.in_title and tag == "a":
            self.in_title = False
        elif self.in_snippet and (tag in ["a", "td", "div", "span"]):
            self.in_snippet = False
            if self.curr.get("title") and self.curr.get("url"):
                self.results.append(self.curr)
                self.curr = {}

    def handle_data(self, data):
        if self.in_title and "title" in self.curr:
            self.curr["title"] += data
        elif self.in_snippet and "snippet" in self.curr:
            self.curr["snippet"] += data

class DuckDuckGoSearchTool:
    """Wrapper around DuckDuckGo search for gathering public web context with zero Rust dependencies."""

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _search_urllib(self, query: str, limit: int) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """Pure-Python direct DuckDuckGo HTML scraper with no Rust system-configuration dependencies."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        endpoints = [
            f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}",
            f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
        ]
        for url in endpoints:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=7) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    parser = _DDGHtmlParser()
                    parser.feed(html)
                    if parser.results:
                        clean_results = []
                        for r in parser.results[:limit]:
                            clean_results.append({
                                "title": r.get("title", "").strip(),
                                "url": r.get("url", "").strip(),
                                "snippet": r.get("snippet", "").strip()
                            })
                        if clean_results:
                            return clean_results, None
            except Exception as e:
                logger.debug(f"Urllib DDG query error ({url}): {e}")
        return [], "Urllib DDG fetch returned 0 results"

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

        # 1. Try pure-Python urllib scraper first (immune to Rust DynamicStore crashes)
        res_u, err_u = self._search_urllib(query, limit)
        if res_u:
            return {
                "status": "SUCCESS",
                "results": res_u,
                "error": None,
                "backend": "urllib_html"
            }

        # 2. Try isolated DDGS backends as fallback
        last_error = err_u
        for backend_opt in ["lite", "html", "auto"]:
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
            time.sleep(0.05)

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
