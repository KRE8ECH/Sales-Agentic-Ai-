import re
from typing import List, Dict, Any

class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) processor that chunks, scores,
    and formats web search results into an evidence-backed context window.
    """

    KEY_INTENT_TERMS = [
        "growth", "launch", "hiring", "funding", "ai", "expansion", "revenue",
        "partnership", "challenge", "customer", "strategy", "acquisition", "product"
    ]

    def process_and_rank(self, search_results: List[Dict[str, str]], lead_name: str, company: str, role: str = "") -> List[Dict[str, Any]]:
        scored_chunks = []
        name_lower = lead_name.lower()
        company_lower = company.lower()
        role_tokens = set(role.lower().split()) if role else set()

        for idx, item in enumerate(search_results):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("url", "")
            text = f"{title}. {snippet}".strip()

            if not text:
                continue

            # Calculate heuristic relevance score
            score = 1.0
            text_lower = text.lower()

            if company_lower in text_lower:
                score += 3.0
            if name_lower in text_lower:
                score += 4.0
            for token in role_tokens:
                if len(token) > 2 and token in text_lower:
                    score += 1.5
            for term in self.KEY_INTENT_TERMS:
                if term in text_lower:
                    score += 0.8

            scored_chunks.append({
                "source_id": idx + 1,
                "title": title,
                "url": url,
                "text": text,
                "score": score
            })

        # Sort by highest relevance score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks

    def build_context_prompt(self, ranked_chunks: List[Dict[str, Any]], max_sources: int = 5) -> str:
        """Format ranked chunks into an evidence block with citations."""
        if not ranked_chunks:
            return "No recent public context found via web search."

        lines = ["=== VERIFIED PUBLIC CONTEXT (DuckDuckGo RAG Sources) ==="]
        for chunk in ranked_chunks[:max_sources]:
            lines.append(f"[{chunk['source_id']}] Title: {chunk['title']}")
            lines.append(f"    URL: {chunk['url']}")
            lines.append(f"    Evidence: {chunk['text']}")
            lines.append("")
        return "\n".join(lines)
