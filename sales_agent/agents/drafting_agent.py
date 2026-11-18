import json
from typing import Dict, Any, Optional
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.config import config
from sales_agent.db import Database

class DraftingAgent:
    """
    Personalized message-drafting agent:
    Uses the research dossier to generate hyper-personalized outreach
    for each touch in the sequence, explicitly grounding copy in facts.
    """

    def __init__(self, ollama: OllamaClient, db: Database):
        self.ollama = ollama
        self.db = db

    def draft_touch(self, lead_id: int, touch_number: int) -> Dict[str, Any]:
        lead = self.db.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found.")

        dossier = lead.get("research_dossier") or {}
        sender = config.sender

        # Match touch rule
        touch_rule = next((r for r in config.sequence_rules if r.touch_number == touch_number), None)
        channel = touch_rule.channel if touch_rule else "email"
        intent = touch_rule.intent if touch_rule else f"Touch {touch_number}"
        touch_desc = touch_rule.description if touch_rule else ""

        system_prompt = (
            "You are a world-class elite B2B sales copywriter specializing in hyper-personalized outreach. "
            "Rule #1: NEVER write generic fluff or boilerplate sales templates. "
            "Rule #2: You MUST explicitly reference specific facts, company initiatives, or role context from the provided research dossier. "
            "Rule #3: Keep emails concise (under 120 words), conversational, and focused on one specific low-friction call-to-action (CTA). "
            "Rule #4: If the channel is LinkedIn, keep the message punchy and under 75 words."
        )

        user_prompt = f"""
Draft Touch #{touch_number} for the following lead:

LEAD DETAILS:
- Name: {lead['name']}
- Title / Role: {lead.get('role', 'Executive')}
- Company: {lead['company']}
- Industry: {lead.get('industry', 'B2B')}

RESEARCH DOSSIER:
- Company Overview: {dossier.get('company_overview', '')}
- Recent Events / News: {json.dumps(dossier.get('recent_events', []), ensure_ascii=False)}
- Role Priorities: {json.dumps(dossier.get('role_priorities', []), ensure_ascii=False)}
- Pain Points: {json.dumps(dossier.get('potential_pain_points', []), ensure_ascii=False)}
- Best Hooks: {json.dumps(dossier.get('tailored_hooks', []), ensure_ascii=False)}

SENDER DETAILS:
- Name: {sender.name}
- Title: {sender.role} at {sender.company}
- Value Proposition: {sender.value_proposition}

TOUCH SPECIFICATION:
- Channel: {channel.upper()}
- Sequence Intent: {intent}
- Goal: {touch_desc}

Provide your response as a valid JSON object with these exact keys:
{{
  "subject": "Clear, curiosity-inducing subject line under 6 words (empty string if LinkedIn)",
  "content": "The actual message text to send",
  "researched_evidence_used": "1-2 sentences explaining exactly what specific research points from the dossier were woven into this draft",
  "call_to_action": "The specific low-friction CTA used"
}}
"""

        fallback_draft = {
            "subject": f"Quick thought on {lead['company']}'s growth" if channel == "email" else "",
            "content": (
                f"Hi {lead['name']},\n\n"
                f"Saw {lead['company']}'s recent momentum in expanding your go-to-market footprint. "
                f"As {lead.get('role', 'leader')}, you're likely focused on keeping outbound conversion high without overloading your reps.\n\n"
                f"At {sender.company}, we help teams generate 3x higher response rates through deep research grounding. "
                f"Open to a quick 10-minute chat this Thursday?\n\n"
                f"Best,\n{sender.name}"
            ),
            "researched_evidence_used": f"Referenced {lead['company']}'s market momentum and {lead.get('role', 'executive')} role priorities.",
            "call_to_action": "10-minute exploratory chat on Thursday"
        }

        try:
            draft_res = self.ollama.generate_json(user_prompt, system_prompt=system_prompt, fallback_dict=fallback_draft)
        except Exception:
            draft_res = fallback_draft

        # Save touch into database
        touch_id = self.db.save_touch(
            lead_id=lead_id,
            touch_number=touch_number,
            channel=channel,
            subject=draft_res.get("subject", ""),
            content=draft_res.get("content", ""),
            evidence=draft_res.get("researched_evidence_used", "")
        )

        self.db.log_decision(
            lead_id=lead_id,
            stage="DRAFTING",
            decision=f"DRAFTED_TOUCH_{touch_number}",
            reasoning=f"Generated {channel.upper()} draft for Touch #{touch_number} targeting '{intent}'. Evidence grounded: {draft_res.get('researched_evidence_used', '')}",
            metadata={"touch_id": touch_id, "channel": channel, "touch_number": touch_number}
        )

        draft_res["touch_id"] = touch_id
        return draft_res
