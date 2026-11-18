import json
from typing import Dict, Any, List
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.search.duckduckgo import DuckDuckGoSearchTool
from sales_agent.search.rag_engine import RAGEngine
from sales_agent.db import Database

class ResearchAgent:
    """
    Per-lead research agent:
    Runs DuckDuckGo web searches, performs RAG context ranking,
    and extracts real public facts with clickable source URLs.
    If nothing is found, records 'NOT FOUND' and a search warning.
    """

    def __init__(self, ollama: OllamaClient, db: Database):
        self.ollama = ollama
        self.db = db
        self.search_tool = DuckDuckGoSearchTool()
        self.rag = RAGEngine()

    def research_lead(self, lead_id: int) -> Dict[str, Any]:
        lead = self.db.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead with id {lead_id} not found.")

        name = lead["name"]
        company = lead["company"]
        role = lead.get("role", "")
        industry = lead.get("industry", "")

        # 1. Search web context via DuckDuckGo
        raw_results = self.search_tool.search_lead_context(name, company, role)

        # 2. Score and rank chunks with RAG engine (enforcing company/lead name presence)
        ranked_chunks = self.rag.process_and_rank(raw_results, name, company, role)

        # 3. Check if search succeeded or returned 0 verified results
        if not ranked_chunks:
            dossier = {
                "company_overview": "NOT FOUND",
                "search_status": "NO_RESULTS",
                "search_warning": "Warning: DuckDuckGo search returned 0 verified public results for this lead/company.",
                "facts": [
                    {
                        "fact": "NOT FOUND",
                        "source_url": "",
                        "source_title": "NOT FOUND"
                    }
                ],
                "recent_events": ["NOT FOUND"],
                "role_priorities": [f"Priorities for {role or 'Executive'} at {company}"],
                "potential_pain_points": ["General business scaling and operations"],
                "tailored_hooks": ["Direct introductory inquiry regarding operational priorities"],
                "confidence_score": 0.0,
                "sources": []
            }
            self.db.save_research_dossier(lead_id, dossier)
            self.db.log_decision(
                lead_id=lead_id,
                stage="RESEARCH",
                decision="SEARCH_EMPTY",
                reasoning="DuckDuckGo returned 0 verified results mentioning lead/company. Dossier marked as NOT FOUND to avoid hallucinations.",
                metadata={"confidence": 0.0, "source_count": 0}
            )
            return dossier

        # 4. Context block from verified ranked chunks
        context_block = self.rag.build_context_prompt(ranked_chunks, max_sources=5)

        # 4. LLM synthesis prompt with strict anti-hallucination rules
        system_prompt = (
            "You are a factual sales intelligence and research agent. "
            "CRITICAL RULES: "
            "1. Extract ONLY 3-4 verifiable bullet facts from the provided web search context. "
            "2. Each fact MUST include the exact source URL and Title from the context. "
            "3. If a fact is not in the context, do NOT invent or assume it. "
            "4. Never invent statistics, awards, or fake company milestones."
        )

        user_prompt = f"""
Analyze the verified web context below for {name} ({role}) at {company}:

{context_block}

Synthesize a factual Lead Dossier in valid JSON with these exact keys:
{{
  "company_overview": "1-2 factual sentences on what {company} does based strictly on search context",
  "facts": [
    {{
      "fact": "Specific verified event, news, partnership, product launch, or funding announcement",
      "source_url": "URL from context",
      "source_title": "Title from context"
    }}
  ],
  "role_priorities": [
    "Factual strategic focus or responsibility for this role based on the context"
  ],
  "potential_pain_points": [
    "Realistic friction point or challenge implied by the context"
  ],
  "tailored_hooks": [
    "Conversational opening hook referencing one of the verified facts above"
  ],
  "confidence_score": 0.90
}}
"""

        # Direct extraction from real search results without generic fluff
        facts_extracted = []
        for chunk in ranked_chunks[:4]:
            facts_extracted.append({
                "fact": chunk["text"],
                "source_url": chunk["url"],
                "source_title": chunk["title"]
            })

        fallback_dossier = {
            "company_overview": f"{company} is mentioned in recent web results.",
            "search_status": "OK",
            "search_warning": None,
            "facts": facts_extracted,
            "recent_events": [f["fact"] for f in facts_extracted],
            "role_priorities": [f"Driving operational growth as {role or 'Leader'}"],
            "potential_pain_points": ["Balancing outreach efficiency with personalized relationship building"],
            "tailored_hooks": [f"Noticed {facts_extracted[0]['source_title'] if facts_extracted else company}"],
            "confidence_score": 0.85
        }

        try:
            dossier = self.ollama.generate_json(user_prompt, system_prompt=system_prompt, fallback_dict=fallback_dossier)
            dossier["search_status"] = "OK"
            dossier["search_warning"] = None
            if not dossier.get("facts"):
                dossier["facts"] = facts_extracted
        except Exception:
            dossier = fallback_dossier

        # Attach sources list
        dossier["sources"] = [
            {"id": c["source_id"], "title": c["title"], "url": c["url"]}
            for c in ranked_chunks[:5]
        ]

        # Save to database
        self.db.save_research_dossier(lead_id, dossier)
        self.db.log_decision(
            lead_id=lead_id,
            stage="RESEARCH",
            decision="DOSSIER_COMPILED",
            reasoning=f"Compiled research dossier with {len(dossier.get('facts', []))} verified facts from real DuckDuckGo search.",
            metadata={"confidence": dossier.get("confidence_score", 0.85), "source_count": len(dossier.get("sources", []))}
        )

        return dossier
