import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sales_agent.search.discovery import CompanyDiscoveryEngine
from sales_agent.search.duckduckgo import DuckDuckGoSearchTool
from sales_agent.commands import parse_user_command

class MockSearchTool(DuckDuckGoSearchTool):
    """Mock search tool capable of simulating live success, failed search, and partial role contexts."""
    def __init__(self, mode="success"):
        super().__init__()
        self.mock_mode = mode

    def search_with_status(self, query: str, max_results=None) -> Dict[str, Any]:
        if self.mock_mode == "failed":
            return {
                "status": "FAILED",
                "results": [],
                "error": "Connection timed out to DuckDuckGo backend (rate limit / network down)"
            }
        elif self.mock_mode == "no_results":
            return {
                "status": "NO_RESULTS",
                "results": [],
                "error": None
            }
        elif self.mock_mode == "unverified_role":
            # Snippet mentions person but does NOT mention their role
            return {
                "status": "SUCCESS",
                "results": [
                    {
                        "title": "Starlight Robotics Industry Overview",
                        "url": "https://starlight.example.com/about",
                        "snippet": "Starlight Robotics builds advanced robotic arms. Sarah Connor attended the conference in Boston."
                    }
                ],
                "error": None
            }
        else: # success
            return {
                "status": "SUCCESS",
                "results": [
                    {
                        "title": "QuantumFlow Systems Overview & Leadership",
                        "url": "https://quantumflow.example.com/leadership",
                        "snippet": "QuantumFlow Systems is an enterprise quantum software firm. Elena Vance serves as Chief Technology Officer and leads computing architecture."
                    },
                    {
                        "title": "QuantumFlow Announces Series B",
                        "url": "https://quantumflow.example.com/news/series-b",
                        "snippet": "QuantumFlow announced $30M in Series B funding to scale commercial quantum developer tooling."
                    }
                ],
                "error": None
            }

def main():
    print("=" * 75)
    print("TESTING COMPANY DISCOVERY DATA-SOURCE TRANSPARENCY & VERIFICATION")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # Test 1: Live Search Success with Sources, Timestamp & Designation Verification
    # -------------------------------------------------------------------------
    print("\n--- Test 1: Live Search Success (Transparent Metadata & Verified Role) ---")
    mock_success = MockSearchTool(mode="success")
    engine = CompanyDiscoveryEngine(search_tool=mock_success)

    live_res = engine.discover("QuantumFlow", mode="live")
    assert live_res["data_source"] == "LIVE_SEARCH", f"Expected LIVE_SEARCH, got {live_res['data_source']}"
    assert live_res["is_demo_mode"] is False, "is_demo_mode must be False for live search"
    assert live_res["search_status"] == "SUCCESS", f"Expected SUCCESS search_status, got {live_res['search_status']}"
    assert live_res["retrieval_timestamp"] is not None and "UTC" in live_res["retrieval_timestamp"], "Missing retrieval timestamp"
    assert len(live_res["sources_retrieved"]) > 0, "Expected sources_retrieved to be populated"
    print(f"✔ Live Search Status: {live_res['search_status']}")
    print(f"✔ Retrieval Timestamp: {live_res['retrieval_timestamp']}")
    print(f"✔ Data Source: {live_res['data_source']} (is_demo_mode={live_res['is_demo_mode']})")

    # Verify prospect designation verification
    assert len(live_res["prospects"]) > 0, "Expected at least 1 discovered prospect"
    prospect = live_res["prospects"][0]
    assert prospect["name"] == "Elena Vance"
    assert "Chief Technology Officer" in prospect["designation"] or "CTO" in prospect["designation"]
    assert prospect["verification_status"] == "VERIFIED", f"Expected VERIFIED, got {prospect['verification_status']}"
    assert prospect["source_url"] == "https://quantumflow.example.com/leadership"
    assert prospect["source_title"] == "QuantumFlow Systems Overview & Leadership"
    assert prospect["retrieval_timestamp"] is not None
    print(f"✔ Verified Prospect: {prospect['name']} • {prospect['designation']} [{prospect['verification_status']}]")
    print(f"✔ Verified Source Link: {prospect['source_url']}")

    # -------------------------------------------------------------------------
    # Test 2: Unverified Designation -> Shows 'Role not verified' (Requirement 4 & 5)
    # -------------------------------------------------------------------------
    print("\n--- Test 2: Unverified Designation ('Role not verified' & ROLE_NOT_VERIFIED) ---")
    mock_unverified = MockSearchTool(mode="unverified_role")
    engine_unverified = CompanyDiscoveryEngine(search_tool=mock_unverified)

    # Candidate extracted from context where role is absent
    role_check = engine_unverified._verify_person_and_role(
        candidate_name="Sarah Connor",
        candidate_role="Chief Executive Officer",
        sources=mock_unverified.search_with_status("Starlight Robotics")["results"],
        retrieval_timestamp="2026-11-19 00:00:00 UTC"
    )
    assert role_check is not None
    assert role_check["designation"] == "Role not verified", f"Expected 'Role not verified', got: {role_check['designation']}"
    assert role_check["verification_status"] == "ROLE_NOT_VERIFIED", f"Expected ROLE_NOT_VERIFIED, got: {role_check['verification_status']}"
    assert role_check["source_url"] == "https://starlight.example.com/about"
    print(f"✔ Candidate Sarah Connor: Designation evaluated to '{role_check['designation']}'")
    print(f"✔ Verification status correctly set to: {role_check['verification_status']}")

    # -------------------------------------------------------------------------
    # Test 3: DuckDuckGo Search Failure for Non-Catalog Company
    # -------------------------------------------------------------------------
    print("\n--- Test 3: Search Failure Handling for Uncataloged Company ---")
    mock_fail = MockSearchTool(mode="failed")
    engine_fail = CompanyDiscoveryEngine(search_tool=mock_fail)

    fail_res = engine_fail.discover("StarlightUnknownCorp", mode="live")
    assert fail_res["status"] == "SEARCH_FAILED", f"Expected SEARCH_FAILED, got: {fail_res['status']}"
    assert fail_res["search_status"] == "FAILED", f"Expected FAILED, got: {fail_res['search_status']}"
    assert fail_res["data_source"] == "LIVE_SEARCH", "data_source must be LIVE_SEARCH"
    assert len(fail_res["prospects"]) == 0, f"Prospects must be empty on search failure, got {len(fail_res['prospects'])}"
    assert "DuckDuckGo search failed" in fail_res["search_error"]
    print("✔ DuckDuckGo search failure correctly returned status=SEARCH_FAILED with explicit error.")
    print("✔ Verified zero employee names were invented.")

    # -------------------------------------------------------------------------
    # Test 4: Verified Reference Dataset (Clean Badging, Zero Offline Wording)
    # -------------------------------------------------------------------------
    print("\n--- Test 4: Verified Reference Dataset ---")
    demo_res = engine.discover("NVIDIA", mode="reference")
    assert demo_res["status"] == "OK"
    assert demo_res["data_source"] == "VERIFIED_RESEARCH", f"Expected VERIFIED_RESEARCH, got {demo_res['data_source']}"
    assert demo_res["search_status"] == "SUCCESS"
    assert "OFFLINE" not in demo_res["search_status"]
    assert len(demo_res["prospects"]) == 3
    for p in demo_res["prospects"]:
        assert p["verification_status"] == "VERIFIED"
        assert "OFFLINE" not in p["verification_status"]
    print("✔ Verified Reference Dataset correctly activated for 'NVIDIA'.")
    print(f"✔ Data Source: {demo_res['data_source']}")
    print("✔ Verified prospects clearly labeled with VERIFIED with official URLs.")

    # -------------------------------------------------------------------------
    # Test 5: Command Parser 'demo' vs 'live' routing
    # -------------------------------------------------------------------------
    print("\n--- Test 5: Command Parser Live vs Demo Detection ---")
    cmd_live = parse_user_command("Research NVIDIA")
    assert cmd_live["type"] == "company_discovery" and cmd_live["mode"] == "live"
    print("✔ 'Research NVIDIA' parsed as mode='live'")

    cmd_demo = parse_user_command("Demo NVIDIA")
    assert cmd_demo["type"] == "company_discovery" and cmd_demo["mode"] == "demo"
    print("✔ 'Demo NVIDIA' parsed as mode='demo'")

    cmd_demo2 = parse_user_command("Research Google (demo)")
    assert cmd_demo2["type"] == "company_discovery" and cmd_demo2["mode"] == "demo" and cmd_demo2["company"] == "Google"
    print("✔ 'Research Google (demo)' parsed as company='Google', mode='demo'")

    print("\n" + "=" * 75)
    print(">>> ALL 5 DATA-SOURCE TRANSPARENCY & VERIFICATION TESTS PASSED! <<<")
    print("=" * 75)

if __name__ == "__main__":
    main()
