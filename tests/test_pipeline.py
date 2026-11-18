import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from sales_agent.db import Database
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.agents.orchestrator import OutreachOrchestrator

def test_full_pipeline():
    test_db_path = "test_outreach.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = Database(db_path=test_db_path)
    ollama = OllamaClient()
    orchestrator = OutreachOrchestrator(db=db, ollama=ollama)

    print("=== Step 1: Onboard and Launch Lead (Research + Sequence Plan + Touch 1) ===")
    res = orchestrator.onboard_and_launch_lead(
        name="Satya Nadella",
        company="Microsoft",
        role="CEO",
        email="satya.nadella@microsoft.com",
        industry="Enterprise Software & Cloud AI"
    )
    lead_id = res["lead_id"]
    print(f"Lead Created: ID #{lead_id}")
    print(f"Sources gathered: {len(res['dossier'].get('sources', []))}")
    print(f"Touch #1 Subject: {res['first_touch'].get('subject')}")
    print(f"Touch #1 Content Preview: {res['first_touch'].get('content')[:120]}...")

    lead = db.get_lead(lead_id)
    assert lead["status"] == "IN_SEQUENCE"
    assert lead["current_touch"] == 1

    print("\n=== Step 2: Inbound Reply Simulation - Scenario: INTERESTED ===")
    rep1 = orchestrator.handle_inbound_reply(
        lead_id=lead_id,
        reply_text="Hi Alex, thanks for reaching out. We are actually exploring this right now. Can we jump on a call next Tuesday?"
    )
    cls1 = rep1["classification"]
    dec1 = rep1["decision"]
    print(f"Classified: {cls1['classification']} (Confidence: {cls1.get('confidence')})")
    print(f"Decision: {dec1['decision']} (Status: {dec1['status']})")
    print(f"Reasoning: {dec1['reasoning']}")
    assert dec1["decision"] == "ESCALATE_TO_HUMAN"
    assert dec1["status"] == "ESCALATED"

    print("\n=== Step 3: Test Scenario: OUT_OF_OFFICE ===")
    lead_id_2 = db.create_lead(name="Sarah Connor", company="Cyberdyne", role="VP Engineering")
    orchestrator.planner.plan_sequence(lead_id_2)
    orchestrator.drafter.draft_touch(lead_id_2, 1)
    db.update_lead_status(lead_id_2, "IN_SEQUENCE", 1)

    rep2 = orchestrator.handle_inbound_reply(
        lead_id=lead_id_2,
        reply_text="Thank you for your message. I am currently out of the office on annual leave until November 25th with no access to email."
    )
    print(f"Classified: {rep2['classification']['classification']}")
    print(f"Decision: {rep2['decision']['decision']} (Status: {rep2['decision']['status']})")
    assert rep2['decision']['decision'] == "PAUSE"
    assert rep2['decision']['status'] == "PAUSED"

    print("\n=== Step 4: Test Scenario: NOT_INTERESTED / STOP ===")
    lead_id_3 = db.create_lead(name="Bob Smith", company="Acme Corp", role="Director")
    orchestrator.planner.plan_sequence(lead_id_3)
    orchestrator.drafter.draft_touch(lead_id_3, 1)
    db.update_lead_status(lead_id_3, "IN_SEQUENCE", 1)

    rep3 = orchestrator.handle_inbound_reply(
        lead_id=lead_id_3,
        reply_text="Please stop emailing me and unsubscribe our domain."
    )
    print(f"Classified: {rep3['classification']['classification']}")
    print(f"Decision: {rep3['decision']['decision']} (Status: {rep3['decision']['status']})")
    assert rep3['decision']['decision'] == "STOP"
    assert rep3['decision']['status'] == "STOPPED"

    print("\n=== Step 5: Test Decision Logs Audit Trail ===")
    logs = db.get_decision_logs(lead_id=lead_id)
    print(f"Recorded {len(logs)} audit decision logs for Lead #{lead_id}:")
    for l in logs:
        print(f" - [{l['stage']}] {l['decision']}: {l['reasoning'][:90]}...")

    # Clean up test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("\n>>> ALL AGENT PIPELINE TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_full_pipeline()
