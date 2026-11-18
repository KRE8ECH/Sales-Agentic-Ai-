import json
from typing import Dict, Any, Optional
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.config import config
from sales_agent.db import Database

class DraftingAgent:
    """
    Personalized message-drafting agent:
    Uses the user's configured 'My Product' settings and verified research facts.
    Strictly forbids invented statistics or claims (e.g., '3x higher response rates').
    Drafts are created with status 'AWAITING_APPROVAL'.
    """

    def __init__(self, ollama: OllamaClient, db: Database):
        self.ollama = ollama
        self.db = db

    def draft_touch(self, lead_id: int, touch_number: int) -> Dict[str, Any]:
        lead = self.db.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found.")

        dossier = lead.get("research_dossier") or {}
        settings = self.db.get_product_settings()

        sender_name = settings.get("sender_name", "Our Team")
        company_name = settings.get("company_name", "Our Company")
        product_name = settings.get("product_name", "Our Product")
        what_it_does = settings.get("what_it_does", "helps businesses improve their sales operations")
        calendly_link = settings.get("calendly_link", "")

        # Match touch rule
        touch_rule = next((r for r in config.sequence_rules if r.touch_number == touch_number), None)
        channel = touch_rule.channel if touch_rule else "email"
        intent = touch_rule.intent if touch_rule else f"Touch {touch_number}"
        touch_desc = touch_rule.description if touch_rule else ""

        # Extract verified facts
        raw_facts = dossier.get("facts", [])
        formatted_facts = []
        for f in raw_facts:
            if isinstance(f, dict):
                formatted_facts.append(f"{f.get('fact', '')} (Source: {f.get('source_title', '')})")
            elif isinstance(f, str):
                formatted_facts.append(f)

        has_real_facts = bool(formatted_facts and formatted_facts[0] != "NOT FOUND")

        system_prompt = (
            "You are a professional, transparent B2B sales copywriter. "
            "STRICT INTEGRITY RULES: "
            "1. You must use ONLY the user's configured product and sender details: "
            f"Sender: {sender_name}, Company: {company_name}, Product: {product_name}. "
            "2. ABSOLUTELY FORBIDDEN: Do NOT invent statistics, metrics, percentages, or ROI claims "
            "(e.g., NEVER say '3x higher response rates', '99% uptime', 'save 10 hours', etc.). "
            "3. You may ONLY reference facts present in the RESEARCH FACTS, or capabilities stated in MY PRODUCT DESCRIPTION. "
            "4. If RESEARCH FACTS is 'NOT FOUND', do NOT make up any company news; write a brief, polite role-based inquiry. "
            "5. Keep emails concise (under 100 words), human, and conversational."
        )

        user_prompt = f"""
Draft Touch #{touch_number} for this lead:

LEAD:
- Name: {lead['name']}
- Title / Role: {lead.get('role', 'Leader')}
- Company: {lead['company']}
- Industry: {lead.get('industry', 'Business')}

VERIFIED RESEARCH FACTS (DuckDuckGo):
{json.dumps(formatted_facts if has_real_facts else ['NOT FOUND'], indent=2)}

MY PRODUCT & SENDER DETAILS (Use ONLY these):
- Sender Name: {sender_name}
- Company: {company_name}
- Product Name: {product_name}
- What It Does: {what_it_does}
{f'- Calendar Link: {calendly_link}' if calendly_link else ''}

TOUCH REQUIREMENTS:
- Channel: {channel.upper()}
- Sequence Intent: {intent}
- Goal: {touch_desc}

Provide your response as a valid JSON object with these exact keys:
{{
  "subject": "Concise subject line under 6 words (empty string if LinkedIn)",
  "content": "The actual message text to send",
  "researched_evidence_used": "Explain specifically which real fact or product capability was referenced (or 'Role-based inquiry (research NOT FOUND)')",
  "call_to_action": "Specific low-friction question or CTA"
}}
"""

        # Grounded fallback draft without invented statistics
        if has_real_facts:
            first_fact = raw_facts[0].get("fact", "") if isinstance(raw_facts[0], dict) else raw_facts[0]
            evidence_used = f"Referenced verified public news: '{first_fact[:100]}...'"
            opening = f"Noticed {lead['company']}'s recent announcement regarding {first_fact[:90]}."
        else:
            evidence_used = "Role-based inquiry (public news NOT FOUND)"
            opening = f"Reaching out to you as {lead.get('role', 'leader')} at {lead['company']}."

        fallback_draft = {
            "subject": f"Thought regarding {lead['company']}" if channel == "email" else "",
            "content": (
                f"Hi {lead['name']},\n\n"
                f"{opening}\n\n"
                f"At {company_name}, we built {product_name} to {what_it_does.rstrip('.')}.\n\n"
                f"Would you be open to a brief 10-minute introductory conversation this week?\n\n"
                f"Best regards,\n{sender_name}\n{company_name}"
            ),
            "researched_evidence_used": evidence_used,
            "call_to_action": "10-minute introductory conversation this week"
        }

        try:
            draft_res = self.ollama.generate_json(user_prompt, system_prompt=system_prompt, fallback_dict=fallback_draft)
            # Extra safety check: sanitize any accidental hallucinated stats
            content = draft_res.get("content", "")
            if "3x" in content or "300%" in content or "higher response rates" in content:
                content = content.replace("3x higher response rates", "higher relevance")
                content = content.replace("3x", "significant")
                draft_res["content"] = content
        except Exception:
            draft_res = fallback_draft

        # Save touch into database with status AWAITING_APPROVAL
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
            decision=f"DRAFTED_TOUCH_{touch_number}_AWAITING_APPROVAL",
            reasoning=f"Generated {channel.upper()} draft for Touch #{touch_number}. Grounded in: {draft_res.get('researched_evidence_used', '')}. Status set to Awaiting Human Approval.",
            metadata={"touch_id": touch_id, "channel": channel, "touch_number": touch_number}
        )

        draft_res["touch_id"] = touch_id
        draft_res["status"] = "AWAITING_APPROVAL"
        return draft_res
