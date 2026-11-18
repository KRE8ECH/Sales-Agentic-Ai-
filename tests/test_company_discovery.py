import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from sales_agent.db import Database
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.agents.orchestrator import OutreachOrchestrator

def test_company_discovery_suite():
    test_db_path = "test_discovery.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = Database(db_path=test_db_path)
    ollama = OllamaClient()
    orchestrator = OutreachOrchestrator(db=db, ollama=ollama)

    # Configure custom My Product Settings
    db.save_product_settings({
        "product_name": "SalesPilot AI",
        "what_it_does": "Automates account research and drafts verified multi-touch sales sequences",
        "sender_name": "Aryan Mehta",
        "company_name": "GrowthStack Tech",
        "calendly_link": "https://cal.com/aryan/15min"
    })

    print("\n=== Test 1: Research NVIDIA without employee name (Company-Only Discovery) ===")
    disc_nvidia = orchestrator.discover_company("NVIDIA", mode="demo")
    assert disc_nvidia["status"] == "OK"
    assert "NVIDIA" in disc_nvidia["company_name"]
    assert len(disc_nvidia["company_overview"]) > 20
    print(f"✔ Company Overview: {disc_nvidia['company_overview'][:100]}...")
    print(f"✔ Data Source: {disc_nvidia.get('data_source')}")

    print("\n=== Test 2: Discover Relevant Decision-Makers (Up to 3) ===")
    prospects = disc_nvidia.get("prospects", [])
    assert 1 <= len(prospects) <= 3, f"Expected 1 to 3 prospects, got {len(prospects)}"
    print(f"✔ Identified {len(prospects)} decision-makers:")
    for p in prospects:
        print(f"   - {p['name']} ({p['designation']}) at {p['company']}")
        assert len(p["name"]) > 2
        assert len(p["designation"]) > 2
        assert len(p["professional_relevance"]) > 5

    print("\n=== Test 3: Verify Source Links for Each Discovered Prospect ===")
    for p in prospects:
        source_url = p.get("source_url", "")
        print(f"   - {p['name']}: {source_url}")
        assert source_url.startswith("http"), f"Source URL must be valid HTTP URL for {p['name']}"

    print("\n=== Test 4: Select a Prospect (Jensen Huang) ===")
    selected_p = prospects[0]
    res_launch = orchestrator.select_and_launch_prospect(
        company=disc_nvidia["company_name"],
        prospect_name=selected_p["name"],
        designation=selected_p["designation"],
        context_dossier=disc_nvidia
    )
    lead_id = res_launch["lead_id"]
    lead = db.get_lead(lead_id)
    assert lead["name"] == selected_p["name"]
    assert lead["company"] == "NVIDIA"
    assert lead["role"] == selected_p["designation"]
    print(f"✔ Lead #{lead_id} created for {lead['name']} ({lead['role']})")

    print("\n=== Test 5: Generate Personalized Email with Zero Invented Stats ===")
    t1 = res_launch["first_touch"]
    email_body = t1["content"]
    assert "Aryan Mehta" in email_body, "Configured sender name MUST be in email"
    assert "GrowthStack Tech" in email_body, "Configured company name MUST be in email"
    assert "SalesPilot AI" in email_body, "Configured product name MUST be in email"
    assert "3x" not in email_body, "Invented claims like 3x MUST NOT be present"
    assert "Alex Morgan" not in email_body
    assert "GrowthScale AI" not in email_body
    print(f"✔ Email Subject: {t1.get('subject')}")
    print(f"✔ Email Preview:\n{email_body[:200]}...")

    print("\n=== Test 6: Confirm Email Remains Pending Human Approval (DRAFT - AWAITING APPROVAL) ===")
    assert t1["status"] == "AWAITING_APPROVAL", "Touch #1 must have status AWAITING_APPROVAL"
    assert lead["status"] == "AWAITING_APPROVAL", "Lead status must be AWAITING_APPROVAL"
    # Verify not sent yet
    touches = db.get_touches_for_lead(lead_id)
    assert touches[0]["status"] == "AWAITING_APPROVAL"
    assert touches[0]["sent_at"] is None, "Touch sent_at must be None until approved"
    print("✔ Touch #1 is confirmed held in DRAFT - AWAITING APPROVAL. Not sent automatically.")

    print("\n=== Test 7: Test Behavior When Company / Leadership Info Cannot Be Found ===")
    disc_unknown = orchestrator.discover_company("Nonexistent Unknown Fake Corp 987654321", mode="demo")
    assert disc_unknown["status"] == "NOT_FOUND"
    assert disc_unknown["company_overview"] == "NOT FOUND"
    assert len(disc_unknown["prospects"]) == 0
    assert disc_unknown.get("search_warning") is not None and len(disc_unknown.get("search_warning")) > 5
    print(f"✔ Nonexistent company correctly returned NOT FOUND with warning: {disc_unknown.get('search_warning')}")
    print("✔ Zero employee names were invented.")

    # Clean up test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("\n>>> ALL 7 COMPANY & PROSPECT DISCOVERY TESTS PASSED PERFECTLY! <<<")

if __name__ == "__main__":
    test_company_discovery_suite()
