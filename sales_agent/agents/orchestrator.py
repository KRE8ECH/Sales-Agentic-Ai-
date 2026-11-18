from typing import Dict, Any, List, Optional
from sales_agent.db import Database, DEMO_LEADS_DATA
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.agents.research_agent import ResearchAgent
from sales_agent.agents.sequence_planner import SequencePlannerAgent
from sales_agent.agents.drafting_agent import DraftingAgent
from sales_agent.agents.reply_classifier import ReplyClassifierAgent
from sales_agent.agents.decision_agent import DecisionAgent
from sales_agent.search.discovery import CompanyDiscoveryEngine

class OutreachOrchestrator:
    """
    Coordinates the multi-agent pipeline with Human-in-the-Loop approval:
    Company Discovery -> Decision-Maker Identification -> Research -> Sequence Planning -> Drafting (Awaiting Approval) -> User Approval & Send -> Reply Classification -> Decision Engine
    All state is stored and persisted in SQLite.
    """

    def __init__(self, db: Optional[Database] = None, ollama: Optional[OllamaClient] = None):
        self.db = db or Database()
        self.ollama = ollama or OllamaClient()
        self.researcher = ResearchAgent(self.ollama, self.db)
        self.planner = SequencePlannerAgent(self.db)
        self.drafter = DraftingAgent(self.ollama, self.db)
        self.classifier = ReplyClassifierAgent(self.ollama, self.db)
        self.decision_engine = DecisionAgent(self.db)
        self.discovery_engine = CompanyDiscoveryEngine(self.ollama)

    def discover_company(self, company_name: str) -> Dict[str, Any]:
        """Discovers company overview, business activities, and up to 3 verified decision-makers."""
        settings = self.db.get_product_settings()
        discovery_result = self.discovery_engine.discover(company_name, my_product_settings=settings)

        # Log decision into audit table
        prospects = discovery_result.get("prospects", [])
        status = discovery_result.get("status", "OK")
        reasoning = (
            f"Company discovery executed for '{company_name}'. "
            f"Identified {len(prospects)} verified decision-makers via {discovery_result.get('data_source', 'LIVE_SEARCH')}. "
            f"{discovery_result.get('search_warning', '')}"
        )
        self.db.log_decision(
            lead_id=0,
            stage="COMPANY_DISCOVERY",
            decision="DISCOVERY_COMPLETED" if prospects else "DISCOVERY_NO_PROSPECTS",
            reasoning=reasoning.strip(),
            metadata={
                "company": company_name,
                "data_source": discovery_result.get("data_source"),
                "prospects_count": len(prospects),
                "status": status
            }
        )

        return discovery_result

    def select_and_launch_prospect(
        self,
        company: str,
        prospect_name: str,
        designation: str,
        industry: str = "",
        context_dossier: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Onboards a prospect selected from Company Discovery and drafts Touch 1 awaiting approval."""
        email = f"{prospect_name.lower().replace(' ', '.')}@{company.lower().replace(' ', '')}.com"

        # 1. Create lead record
        lead_id = self.db.create_lead(
            name=prospect_name,
            company=company,
            role=designation,
            email=email,
            industry=industry or "Technology"
        )

        # 2. Compile research dossier
        if context_dossier and context_dossier.get("company_overview"):
            # Format facts from discovery
            facts = []
            for ann in context_dossier.get("recent_announcements", []):
                facts.append({
                    "fact": ann.get("title", "") + ": " + ann.get("snippet", ""),
                    "source_url": ann.get("url", ""),
                    "source_title": ann.get("title", "")
                })

            lead_dossier = {
                "company_overview": context_dossier.get("company_overview", ""),
                "search_status": "OK",
                "search_warning": context_dossier.get("search_warning"),
                "facts": facts or [
                    {
                        "fact": f"{prospect_name} serves as {designation} at {company}.",
                        "source_url": context_dossier.get("prospects", [{}])[0].get("source_url", ""),
                        "source_title": f"{company} Leadership"
                    }
                ],
                "recent_events": [f["fact"] for f in facts] if facts else [f"{prospect_name} leads operations as {designation}"],
                "role_priorities": [
                    f"Driving high-impact initiatives and operations as {designation} at {company}",
                    "Evaluating enterprise solutions aligned with strategic roadmap"
                ],
                "potential_pain_points": context_dossier.get("potential_business_needs", [
                    "Balancing aggressive growth priorities with efficient execution"
                ]),
                "tailored_hooks": [
                    f"Noticed {company}'s strategic momentum and public announcements.",
                    f"Reaching out to {designation} leadership regarding operational enablement."
                ],
                "confidence_score": 0.90,
                "sources": [
                    {"id": idx + 1, "title": ann.get("title", ""), "url": ann.get("url", "")}
                    for idx, ann in enumerate(context_dossier.get("recent_announcements", []))
                ]
            }
            self.db.save_research_dossier(lead_id, lead_dossier)
            dossier = lead_dossier
        else:
            # Run fresh research agent
            dossier = self.researcher.research_lead(lead_id)

        # 3. Sequence Planner establishes 4-touch schedule
        plan = self.planner.plan_sequence(lead_id)

        # 4. Drafting Agent crafts Touch 1 (Saved as AWAITING_APPROVAL)
        touch1 = self.drafter.draft_touch(lead_id, touch_number=1)

        # 5. Lead is placed in AWAITING_APPROVAL state (NOT sent automatically)
        self.db.update_lead_status(lead_id, status="AWAITING_APPROVAL", current_touch=0)

        self.db.log_decision(
            lead_id=lead_id,
            stage="PROSPECT_SELECTED",
            decision="TOUCH_1_READY_FOR_APPROVAL",
            reasoning=f"Selected prospect '{prospect_name}' ({designation} at {company}) from Company Discovery. Touch #1 drafted and held for human review.",
            metadata={"lead_id": lead_id, "touch_id": touch1["touch_id"], "subject": touch1.get("subject", "")}
        )

        return {
            "lead_id": lead_id,
            "dossier": dossier,
            "plan": plan,
            "first_touch": touch1
        }

    def onboard_and_launch_lead(
        self,
        name: str,
        company: str,
        role: str = "",
        email: str = "",
        linkedin_url: str = "",
        industry: str = ""
    ) -> Dict[str, Any]:
        """Runs research, sequence planning, and drafts Touch 1 awaiting human approval."""
        # 1. Create lead record
        lead_id = self.db.create_lead(
            name=name,
            company=company,
            role=role,
            email=email,
            linkedin_url=linkedin_url,
            industry=industry
        )

        # 2. Research Agent gathers real web intelligence & synthesizes dossier
        dossier = self.researcher.research_lead(lead_id)

        # 3. Sequence Planner establishes 4-touch schedule
        plan = self.planner.plan_sequence(lead_id)

        # 4. Drafting Agent crafts Touch 1 (Saved as AWAITING_APPROVAL)
        touch1 = self.drafter.draft_touch(lead_id, touch_number=1)

        # 5. Lead is placed in AWAITING_APPROVAL state (NOT sent automatically)
        self.db.update_lead_status(lead_id, status="AWAITING_APPROVAL", current_touch=0)

        self.db.log_decision(
            lead_id=lead_id,
            stage="DRAFT_REVIEW",
            decision="TOUCH_1_READY_FOR_APPROVAL",
            reasoning=f"Drafted Touch #1 ({touch1.get('channel', 'email').upper()}) for {name} at {company}. Awaiting human review & approval before sending.",
            metadata={"touch_id": touch1["touch_id"], "subject": touch1.get("subject", "")}
        )

        return {
            "lead_id": lead_id,
            "dossier": dossier,
            "plan": plan,
            "first_touch": touch1
        }

    def load_demo_lead(self, demo_type: str = "founder") -> Dict[str, Any]:
        """Loads a realistic pre-configured demo lead (founder, hr, cto) with real public facts."""
        lead_id = self.db.create_demo_lead(demo_type)
        lead = self.db.get_lead(lead_id)
        plan = self.planner.plan_sequence(lead_id)
        touch1 = self.drafter.draft_touch(lead_id, touch_number=1)
        self.db.update_lead_status(lead_id, status="AWAITING_APPROVAL", current_touch=0)

        self.db.log_decision(
            lead_id=lead_id,
            stage="DEMO_SEED",
            decision="DEMO_LEAD_LOADED",
            reasoning=f"Loaded realistic offline demo lead '{lead['name']}' ({lead.get('role')} at {lead['company']}) with verified facts and drafted Touch #1.",
            metadata={"demo_type": demo_type, "lead_id": lead_id}
        )

        return {
            "lead_id": lead_id,
            "lead": lead,
            "dossier": lead.get("research_dossier", {}),
            "plan": plan,
            "first_touch": touch1
        }

    def approve_and_send(self, touch_id: int) -> Dict[str, Any]:
        """Explicit human approval action: approves touch and simulates dispatch."""
        return self.db.approve_and_send_touch(touch_id)

    def handle_inbound_reply(self, lead_id: int, reply_text: str) -> Dict[str, Any]:
        """Processes an incoming reply from a lead and triggers the adaptive decision agent."""
        lead = self.db.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found.")

        current_touch = max(1, lead.get("current_touch", 1))

        # 1. Classify the reply
        classification = self.classifier.classify_reply(
            lead_id=lead_id,
            reply_text=reply_text,
            in_response_to_touch=current_touch
        )

        # 2. Make adaptive decision
        decision = self.decision_engine.evaluate_next_step(lead_id, latest_classification=classification)

        next_touch_draft = None
        # 3. If decision is CONTINUE_SEQUENCE, draft next touch (requires approval)
        if decision["decision"] == "CONTINUE_SEQUENCE":
            next_touch_num = lead.get("current_touch", 1) + 1
            next_touch_draft = self.drafter.draft_touch(lead_id, touch_number=next_touch_num)

        return {
            "classification": classification,
            "decision": decision,
            "next_touch_draft": next_touch_draft
        }

    def advance_cadence_no_reply(self, lead_id: int) -> Dict[str, Any]:
        """Simulates a cadence timeout where the lead did not respond to the last touch."""
        lead = self.db.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found.")

        current_touch = lead.get("current_touch", 1)

        no_reply_classification = {
            "classification": "NO_REPLY",
            "confidence": 1.0,
            "sentiment": "NEUTRAL",
            "extracted_intent": f"No response received after scheduled delay for Touch #{current_touch}.",
            "return_date": None
        }

        decision = self.decision_engine.evaluate_next_step(lead_id, latest_classification=no_reply_classification)

        next_touch_draft = None
        if decision["decision"] == "CONTINUE_SEQUENCE":
            next_touch_num = current_touch + 1
            next_touch_draft = self.drafter.draft_touch(lead_id, touch_number=next_touch_num)

        return {
            "decision": decision,
            "next_touch_draft": next_touch_draft
        }
