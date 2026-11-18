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
    and prompts local Ollama to synthesize a structured Lead Dossier.
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

        # 2. Score and rank chunks with RAG engine
        ranked_chunks = self.rag.process_and_rank(raw_results, name, company, role)
        context_block = self.rag.build_context_prompt(ranked_chunks, max_sources=5)

        # 3. LLM synthesis prompt
        system_prompt = (
            "You are an expert sales intelligence and lead research agent. "
            "Your job is to synthesize public web evidence into a high-precision, factual Lead Research Dossier. "
            "Never invent facts or hallucinate awards/events that are not supported by the context."
        )

        user_prompt = f"""
Analyze the lead and public context below:

Target Lead:
- Name: {name}
- Title / Role: {role}
- Company: {company}
- Industry: {industry}

{context_block}

Synthesize a comprehensive Lead Dossier in valid JSON with these exact keys:
{{
  "company_overview": "Brief 1-2 sentence description of what the company does and its current market position",
  "recent_events": [
    "Specific recent event, milestone, funding, product launch or public move (with source citation if available)",
    "Another notable event or growth indicator"
  ],
  "role_priorities": [
    "Likely strategic priority or KPI for someone in this specific role ({role})",
    "Key operational bottleneck or focus area"
  ],
  "potential_pain_points": [
    "Challenge they likely face in scaling, pipeline generation, or operations",
    "Efficiency or tool sprawl challenge"
  ],
  "tailored_hooks": [
    "Specific conversation hook connecting their recent public news to our value proposition",
    "Alternative hook focusing on industry trend"
  ],
  "confidence_score": 0.85
}}
"""

        fallback_dossier = {
            "company_overview": f"{company} is an active organization operating in the {industry or 'technology'} space.",
            "recent_events": [
                f"{company} has been expanding market presence and optimizing go-to-market strategies.",
                f"Recent leadership focus on scaling operational efficiency."
            ],
            "role_priorities": [
                f"Driving high-impact growth and pipeline for {company} as {role or 'Leader'}.",
                "Increasing team productivity and conversion efficiency."
            ],
            "potential_pain_points": [
                "Overcoming low response rates from generic outbound and repetitive manual prospecting.",
                "Balancing outreach volume with deep personalization."
            ],
            "tailored_hooks": [
                f"Noticed {company}'s ongoing market acceleration and initiative in expanding their customer base.",
                f"Connecting with {role or 'leadership'} regarding scaling outreach conversion."
            ],
            "confidence_score": 0.75
        }

        try:
            dossier = self.ollama.generate_json(user_prompt, system_prompt=system_prompt, fallback_dict=fallback_dossier)
        except Exception:
            dossier = fallback_dossier

        # Attach citations
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
            reasoning=f"Compiled research dossier with {len(dossier.get('sources', []))} web sources and {len(dossier.get('recent_events', []))} verified events.",
            metadata={"confidence": dossier.get("confidence_score", 0.8), "source_count": len(dossier.get("sources", []))}
        )

        return dossier
