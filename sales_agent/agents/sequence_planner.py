from typing import List, Dict, Any
from sales_agent.config import config, SequenceTouchRule
from sales_agent.db import Database

class SequencePlannerAgent:
    """
    Plans the multi-touch outreach sequence with defined cadence
    and escalating intent per touchpoint.
    """

    def __init__(self, db: Database):
        self.db = db

    def plan_sequence(self, lead_id: int) -> List[Dict[str, Any]]:
        lead = self.db.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found.")

        rules: List[SequenceTouchRule] = config.sequence_rules
        planned_touches = []

        for rule in rules:
            planned_touches.append({
                "touch_number": rule.touch_number,
                "channel": rule.channel,
                "delay_days": rule.delay_days,
                "intent": rule.intent,
                "description": rule.description
            })

        self.db.log_decision(
            lead_id=lead_id,
            stage="PLANNING",
            decision="SEQUENCE_PLANNED",
            reasoning=f"Initialized standard {len(planned_touches)}-touch cadence spanning 12 days with escalating intent (Hook -> Insight -> Social Proof -> Polite Breakup).",
            metadata={"touches_count": len(planned_touches), "channels": list(set(r.channel for r in rules))}
        )

        return planned_touches
