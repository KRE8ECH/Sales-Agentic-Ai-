from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sales_agent.db import Database
from sales_agent.config import config

class DecisionAgent:
    """
    Adaptive Next-Step Agent:
    Evaluates current conversation state, touches sent, and classified replies
    to make an autonomous, transparent next-step decision:
    - CONTINUE_SEQUENCE
    - PAUSE
    - ESCALATE_TO_HUMAN
    - STOP
    """

    def __init__(self, db: Database):
        self.db = db

    def evaluate_next_step(self, lead_id: int, latest_classification: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        lead = self.db.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found.")

        current_touch = lead.get("current_touch", 0)
        max_touches = len(config.sequence_rules)

        classification = latest_classification.get("classification") if latest_classification else "NO_REPLY"
        intent = latest_classification.get("extracted_intent", "") if latest_classification else "No response recorded"
        return_date = latest_classification.get("return_date") if latest_classification else None

        decision = ""
        new_status = ""
        reasoning = ""
        recommended_action = ""
        next_touch_date = None

        if classification == "INTERESTED":
            decision = "ESCALATE_TO_HUMAN"
            new_status = "ESCALATED"
            reasoning = (
                f"Prospect demonstrated positive buying intent ('{intent}'). "
                "Per outreach governance, automated touchpoints are immediately halted and conversation is handed to human sales rep to schedule demo/closing call."
            )
            recommended_action = f"Human rep should review lead dossier and send calendar link or personalized invite to {lead['name']} within 2 hours."

        elif classification == "NOT_INTERESTED":
            decision = "STOP"
            new_status = "STOPPED"
            reasoning = (
                f"Prospect explicitly signaled non-interest or requested unsubscribe ('{intent}'). "
                "Halting all future communications to honor prospect preference and ensure compliance."
            )
            recommended_action = "Mark lead as Opt-Out in CRM and blacklist from future cold sequences."

        elif classification == "OUT_OF_OFFICE":
            decision = "PAUSE"
            new_status = "PAUSED"
            if return_date:
                next_touch_date = return_date
                reasoning = f"Autoresponder detected. Prospect returns on {return_date}. Pausing sequence until return date."
            else:
                resume_time = datetime.utcnow() + timedelta(days=5)
                next_touch_date = resume_time.strftime("%Y-%m-%d")
                reasoning = f"Autoresponder detected without exact return date. Pausing sequence for 5 business days (resume {next_touch_date})."
            recommended_action = f"System will resume cadence automatically on {next_touch_date}."

        elif classification == "OBJECTION":
            subtype = latest_classification.get("objection_subtype", "GENERAL")
            if subtype in ["WRONG_PERSON", "COMPETITOR", "BUDGET"]:
                decision = "ESCALATE_TO_HUMAN"
                new_status = "ESCALATED"
                reasoning = (
                    f"Prospect raised a nuanced objection ({subtype}: '{intent}'). "
                    "Automated bot scripts risk damaging relationship; escalating to sales rep for strategic objection handling or re-routing."
                )
                recommended_action = f"Sales rep should address the {subtype} objection with custom proof point."
            else:
                decision = "CONTINUE_SEQUENCE"
                new_status = "IN_SEQUENCE"
                reasoning = f"Soft objection encountered ('{intent}'). Sequence will address this in the upcoming touchpoint with relevant case study evidence."
                recommended_action = "Draft next touch emphasizing ROI and overcoming friction."

        elif classification == "NO_REPLY":
            if current_touch < max_touches:
                next_touch_num = current_touch + 1
                rule = next((r for r in config.sequence_rules if r.touch_number == next_touch_num), None)
                delay_days = rule.delay_days if rule else 3
                resume_date = datetime.utcnow() + timedelta(days=delay_days)
                next_touch_date = resume_date.strftime("%Y-%m-%d")

                decision = "CONTINUE_SEQUENCE"
                new_status = "IN_SEQUENCE"
                reasoning = (
                    f"No response received for Touch #{current_touch}. Cadence rules specify advancing to Touch #{next_touch_num} "
                    f"({rule.channel.upper()} - {rule.intent}) with {delay_days} days delay."
                )
                recommended_action = f"Prepare and execute Touch #{next_touch_num} via {rule.channel.upper()}."
            else:
                decision = "STOP"
                new_status = "COMPLETED"
                reasoning = f"Lead completed all {max_touches} planned touches across 12-day cadence without engagement. Sequence completed."
                recommended_action = "Move to cold nurture pool; re-engage in 90 days."

        # Update Lead State in DB
        self.db.update_lead_status(lead_id, status=new_status, next_touch_date=next_touch_date)

        # Log decision with full audit trail
        self.db.log_decision(
            lead_id=lead_id,
            stage="NEXT_STEP",
            decision=decision,
            reasoning=reasoning,
            metadata={
                "previous_touch": current_touch,
                "classification": classification,
                "new_status": new_status,
                "recommended_action": recommended_action,
                "next_touch_date": next_touch_date
            }
        )

        return {
            "decision": decision,
            "status": new_status,
            "reasoning": reasoning,
            "recommended_action": recommended_action,
            "next_touch_date": next_touch_date
        }
