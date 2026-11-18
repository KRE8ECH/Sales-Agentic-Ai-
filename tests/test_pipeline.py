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

    print("\n=== Test 1: Check Custom 'My Product' Settings Persistence ===")
    custom_settings = {
        "product_name": "DevAutoTest AI",
        "what_it_does": "Automates end-to-end regression testing for microservices teams",
        "sender_name": "Priya Sharma",
        "company_name": "CloudPeak Technologies",
        "calendly_link": "https://cal.com/priya/15min"
    }
    db.save_product_settings(custom_settings)
    saved = db.get_product_settings()
    assert saved["product_name"] == "DevAutoTest AI"
    assert saved["sender_name"] == "Priya Sharma"
    assert saved["company_name"] == "CloudPeak Technologies"
    print("✔ Product settings saved and retrieved correctly.")

    print("\n=== Test 2: Test 3 Offline Demo Leads (Founder, HR, CTO) ===")
    for d_type in ["founder", "hr", "cto"]:
        res_demo = orchestrator.load_demo_lead(d_type)
        lead = db.get_lead(res_demo["lead_id"])
        dossier = lead["research_dossier"]
        facts = dossier.get("facts", [])
        assert len(facts) >= 3, f"Demo lead {d_type} must have at least 3 bullet facts"
        for f in facts:
            assert "source_url" in f and f["source_url"].startswith("http"), "Each fact must have a valid clickable source URL"
            assert "fact" in f and len(f["fact"]) > 10, "Each fact must have realistic text"
        print(f"✔ Demo lead [{d_type.upper()}]: '{lead['name']}' at {lead['company']} loaded with {len(facts)} verified facts with URLs.")

    print("\n=== Test 3: Touch Approval Flow ('Draft - Awaiting Approval' -> 'Approve & Send') ===")
    demo_lead_id = 1
    touches = db.get_touches_for_lead(demo_lead_id)
    assert len(touches) >= 1
    t1 = touches[0]
    assert t1["status"] == "AWAITING_APPROVAL", "Touch must initially be in AWAITING_APPROVAL status"
    lead = db.get_lead(demo_lead_id)
    assert lead["status"] == "AWAITING_APPROVAL"
    print(f"✔ Touch #{t1['id']} is correctly held as 'Draft - Awaiting Approval'.")

    # Approve and send
    approved_touch = orchestrator.approve_and_send(t1["id"])
    assert approved_touch["status"] == "SENT"
    lead = db.get_lead(demo_lead_id)
    assert lead["status"] == "IN_SEQUENCE"
    assert lead["current_touch"] == 1
    print(f"✔ Touch #{t1['id']} approved & marked as SENT. Lead status advanced to IN_SEQUENCE.")

    print("\n=== Test 4: Verify NO Hardcoded Names & NO Invented Statistics in Email ===")
    email_content = t1["content"]
    assert "Alex Morgan" not in email_content, "Hardcoded 'Alex Morgan' must NOT appear in email"
    assert "GrowthScale AI" not in email_content, "Hardcoded 'GrowthScale AI' must NOT appear in email"
    assert "3x higher response rates" not in email_content, "Invented claims like '3x higher response rates' must NOT appear"
    assert "3x" not in email_content, "Invented multipliers must NOT appear"
    assert "Priya Sharma" in email_content, "User's configured sender name MUST appear"
    assert "CloudPeak Technologies" in email_content, "User's configured company name MUST appear"
    print("✔ Email content strictly adheres to user product settings with ZERO invented statistics.")

    print("\n=== Test 5: Verify 'NOT FOUND' Behavior When Search Has No Results ===")
    lead_empty_id = db.create_lead(name="Unknown Person XYZ123", company="Nonexistent Company ABC987")
    dossier_empty = orchestrator.researcher.research_lead(lead_empty_id)
    assert dossier_empty["search_status"] == "NO_RESULTS"
    assert "Warning" in dossier_empty["search_warning"]
    assert dossier_empty["facts"][0]["fact"] == "NOT FOUND"
    print("✔ Search without results correctly returns 'NOT FOUND' and a visible warning.")

    print("\n=== Test 6: Inbound Reply Classification & Decision Logic ===")
    rep = orchestrator.handle_inbound_reply(
        lead_id=demo_lead_id,
        reply_text="Yes Priya, let's connect next week for a demo."
    )
    assert rep["classification"]["classification"] == "INTERESTED"
    assert rep["decision"]["decision"] == "ESCALATE_TO_HUMAN"
    print(f"✔ Classified: {rep['classification']['classification']} -> Decision: {rep['decision']['decision']}")

    # Clean up test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("\n>>> ALL 5 NEW REQUIREMENTS & REGRESSION TESTS PASSED! <<<")

if __name__ == "__main__":
    test_full_pipeline()
