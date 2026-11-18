import json
from typing import Dict, Any
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.db import Database

class ReplyClassifierAgent:
    """
    Classifies incoming prospect replies into:
    - INTERESTED
    - NOT_INTERESTED
    - OBJECTION
    - OUT_OF_OFFICE
    - NO_REPLY
    """

    CATEGORIES = ["INTERESTED", "NOT_INTERESTED", "OBJECTION", "OUT_OF_OFFICE", "NO_REPLY"]

    def __init__(self, ollama: OllamaClient, db: Database):
        self.ollama = ollama
        self.db = db

    def classify_reply(self, lead_id: int, reply_text: str, in_response_to_touch: int = 1) -> Dict[str, Any]:
        lead = self.db.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found.")

        system_prompt = (
            "You are an expert sales communications intelligence classifier. "
            "Your task is to accurately classify inbound sales email/message replies into exactly one category: "
            "1. INTERESTED: Asks for a call, demo, pricing, more details, or expresses positive interest. "
            "2. NOT_INTERESTED: Explicit rejection, unsubscribe, 'remove me', 'not interested'. "
            "3. OBJECTION: Mentions a specific blocker such as budget, timing ('reach out in Q4'), currently using a competitor, or refers to another decision maker. "
            "4. OUT_OF_OFFICE: Automated auto-responder indicating absence or vacation, usually containing a return date. "
            "5. NO_REPLY: Prospect has not replied within the scheduled window."
        )

        user_prompt = f"""
Prospect Reply:
\"\"\"{reply_text}\"\"\"

Analyze the reply above and return a valid JSON object with these exact keys:
{{
  "classification": "One of [INTERESTED, NOT_INTERESTED, OBJECTION, OUT_OF_OFFICE, NO_REPLY]",
  "confidence": 0.95,
  "sentiment": "POSITIVE, NEGATIVE, or NEUTRAL",
  "extracted_intent": "1 sentence summarizing the prospect's intent",
  "objection_subtype": "If OBJECTION, specify (TIMING, BUDGET, COMPETITOR, WRONG_PERSON, OTHER). Otherwise null",
  "return_date": "If OUT_OF_OFFICE, return date string if mentioned, else null",
  "suggested_action": "Recommended next step for the sales rep or agent"
}}
"""

        # Rule-based fast heuristics fallback
        reply_lower = reply_text.lower()
        if any(w in reply_lower for w in ["unsubscribe", "remove me", "not interested", "stop emailing", "take me off"]):
            heuristic_class = "NOT_INTERESTED"
            sentiment = "NEGATIVE"
        elif any(w in reply_lower for w in ["out of the office", "out of office", "on vacation", "annual leave", "autoreply", "automatic reply"]):
            heuristic_class = "OUT_OF_OFFICE"
            sentiment = "NEUTRAL"
        elif any(w in reply_lower for w in ["yes", "demo", "call", "schedule", "sounds interesting", "send over", "pricing", "chat next week"]):
            heuristic_class = "INTERESTED"
            sentiment = "POSITIVE"
        elif any(w in reply_lower for w in ["budget", "competitor", "bad timing", "q3", "q4", "not right now", "talk to", "already using"]):
            heuristic_class = "OBJECTION"
            sentiment = "NEUTRAL"
        else:
            heuristic_class = "OBJECTION"
            sentiment = "NEUTRAL"

        fallback_result = {
            "classification": heuristic_class,
            "confidence": 0.88,
            "sentiment": sentiment,
            "extracted_intent": f"Prospect provided reply classified as {heuristic_class}.",
            "objection_subtype": "TIMING" if "timing" in reply_lower else None,
            "return_date": None,
            "suggested_action": "Follow agent adaptive recommendation."
        }

        try:
            result = self.ollama.generate_json(user_prompt, system_prompt=system_prompt, fallback_dict=fallback_result)
            if result.get("classification") not in self.CATEGORIES:
                result["classification"] = heuristic_class
        except Exception:
            result = fallback_result

        # Save to database
        reply_id = self.db.record_reply(
            lead_id=lead_id,
            reply_text=reply_text,
            in_response_to=in_response_to_touch,
            classification=result.get("classification", "OBJECTION"),
            confidence=float(result.get("confidence", 0.85)),
            sentiment=result.get("sentiment", "NEUTRAL"),
            intent=result.get("extracted_intent", "")
        )

        self.db.log_decision(
            lead_id=lead_id,
            stage="CLASSIFICATION",
            decision=result["classification"],
            reasoning=f"Classified inbound message as {result['classification']} with confidence {result.get('confidence', 0.85)}. Intent: {result.get('extracted_intent', '')}",
            metadata={"reply_id": reply_id, "sentiment": result.get("sentiment"), "return_date": result.get("return_date")}
        )

        result["reply_id"] = reply_id
        return result
