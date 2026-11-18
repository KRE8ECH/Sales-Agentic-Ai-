import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sales_agent.search.discovery import (
    CompanyDiscoveryEngine,
    clean_person_name,
    normalize_person_name,
    extract_role_from_text,
    are_designations_conflicting,
    deduplicate_prospects,
    LeadershipHTMLParser,
    extract_structured_candidates
)
from sales_agent.search.duckduckgo import DuckDuckGoSearchTool

class MockSearchTool(DuckDuckGoSearchTool):
    def __init__(self, results: List[Dict[str, str]]):
        super().__init__()
        self.mock_results = results

    def search_with_status(self, query: str, max_results=None) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "results": self.mock_results,
            "error": None
        }

def test_heading_and_name_merging():
    print("\n--- Test 1: Heading and Name Merging ---")
    
    # 1. Direct unit checks for clean_person_name
    c1 = clean_person_name("Executive Committee Salil Parekh", company="Infosys")
    assert c1 == "Salil Parekh", f"Expected 'Salil Parekh', got '{c1}'"
    print("✔ 'Executive Committee Salil Parekh' stripped to 'Salil Parekh'")

    c2 = clean_person_name("Board of Directors Jensen Huang", company="NVIDIA")
    assert c2 == "Jensen Huang", f"Expected 'Jensen Huang', got '{c2}'"
    print("✔ 'Board of Directors Jensen Huang' stripped to 'Jensen Huang'")

    c3 = clean_person_name("About Us Leadership Team Satya Nadella", company="Microsoft")
    assert c3 == "Satya Nadella", f"Expected 'Satya Nadella', got '{c3}'"
    print("✔ 'About Us Leadership Team Satya Nadella' stripped to 'Satya Nadella'")

    c4 = clean_person_name("Management Profiles Jayesh Sanghrajka", company="Infosys")
    assert c4 == "Jayesh Sanghrajka", f"Expected 'Jayesh Sanghrajka', got '{c4}'"
    print("✔ 'Management Profiles Jayesh Sanghrajka' stripped to 'Jayesh Sanghrajka'")

    # 2. End-to-end extraction from HTML chunk with merged heading
    html_chunk = [{
        "title": "Infosys Leadership | Executive Committee Salil Parekh",
        "url": "https://www.infosys.com/about/management-profiles/salil-parekh.html",
        "snippet": "<h3>Executive Committee Salil Parekh</h3><p>Chief Executive Officer & Managing Director</p>"
    }]
    engine = CompanyDiscoveryEngine(search_tool=MockSearchTool(html_chunk))
    res = engine.discover("Infosys", mode="live")
    assert res["status"] == "OK"
    assert len(res["prospects"]) > 0
    extracted_name = res["prospects"][0]["name"]
    assert extracted_name == "Salil Parekh", f"Heading was not stripped! Got '{extracted_name}'"
    assert "Executive Committee" not in extracted_name
    print(f"✔ Live discovery extraction correctly separated heading: '{extracted_name}'")

def test_duplicate_people():
    print("\n--- Test 2: Duplicate People Normalization & Deduplication ---")

    # 1. Normalization checks
    n1 = normalize_person_name("Salil Parekh")
    n2 = normalize_person_name("Executive Committee Salil Parekh")
    n3 = normalize_person_name("Salil S. Parekh")
    n4 = normalize_person_name("Mr. Salil Parekh")
    assert n1 == n2 == n3 == n4 == "salil parekh", f"Normalization failed: {n1}, {n2}, {n3}, {n4}"
    print(f"✔ Names normalized identically across heading & honorific variations: '{n1}'")

    # 2. Deduplication function check
    prospects = [
        {
            "name": "Executive Committee Salil Parekh",
            "designation": "Chief Executive Officer & Managing Director",
            "verification_status": "VERIFIED",
            "source_url": "https://www.infosys.com/profile1",
            "source_title": "Infosys Leadership"
        },
        {
            "name": "Salil S. Parekh",
            "designation": "CEO & Managing Director",
            "verification_status": "VERIFIED",
            "source_url": "https://www.infosys.com/profile2",
            "source_title": "Infosys Executive Profile"
        },
        {
            "name": "Salil Parekh",
            "designation": "Chief Executive Officer & Managing Director",
            "verification_status": "VERIFIED",
            "source_url": "https://www.infosys.com/about/management-profiles/salil-parekh.html",
            "source_title": "Infosys Leadership Profile: Salil Parekh"
        }
    ]
    deduped = deduplicate_prospects(prospects, company="Infosys")
    assert len(deduped) == 1, f"Expected exactly 1 prospect after deduplication, got {len(deduped)}"
    assert deduped[0]["name"] == "Salil Parekh"
    print("✔ Successfully deduplicated 3 variants of Salil Parekh to exactly 1 prospect.")

def test_ceo_vs_ceo_designate():
    print("\n--- Test 3: CEO vs CEO Designate Distinction & No Inference Upgrades ---")

    snippet = "Jane Doe was appointed CEO Designate of Horizon Cloud Systems."
    role = extract_role_from_text(snippet)
    assert role == "CEO Designate", f"Expected 'CEO Designate', got '{role}'"
    print(f"✔ Extracted distinct role: '{role}' (did not conflate with CEO)")

    engine = CompanyDiscoveryEngine()

    # Case A: Candidate claims "CEO", but the official source strictly states "CEO Designate"
    # Rule: NEVER upgrade a designation based on inference.
    mock_sources = [{
        "title": "Horizon Cloud Executive Appointment",
        "url": "https://horizoncloud.example.com/press/jane-doe",
        "snippet": "Horizon Cloud Systems today announced that Jane Doe was appointed CEO Designate."
    }]

    check_ceo = engine._verify_person_and_role(
        candidate_name="Jane Doe",
        candidate_role="CEO",
        sources=mock_sources,
        retrieval_timestamp="2026-11-19 00:00:00 UTC",
        company="Horizon Cloud"
    )
    assert check_ceo is not None
    assert check_ceo["verification_status"] == "ROLE_NOT_VERIFIED", f"Expected ROLE_NOT_VERIFIED, got {check_ceo['verification_status']}"
    assert check_ceo["designation"] == "Role not verified"
    print("✔ Verified: Candidate claiming 'CEO' when source states 'CEO Designate' is REJECTED (no inferred upgrade).")

    # Case B: Candidate claims "CEO Designate" and source confirms "CEO Designate"
    check_designate = engine._verify_person_and_role(
        candidate_name="Jane Doe",
        candidate_role="CEO Designate",
        sources=mock_sources,
        retrieval_timestamp="2026-11-19 00:00:00 UTC",
        company="Horizon Cloud"
    )
    assert check_designate is not None
    assert check_designate["verification_status"] == "VERIFIED"
    assert check_designate["designation"] == "CEO Designate"
    print("✔ Verified: Candidate claiming 'CEO Designate' is confirmed and preserved as 'CEO Designate'.")

def test_missing_designation():
    print("\n--- Test 4: Missing Designation Evaluation ---")

    engine = CompanyDiscoveryEngine()
    sources_no_role = [{
        "title": "Starlight Robotics Industry Overview",
        "url": "https://starlight.example.com/about",
        "snippet": "Starlight Robotics builds advanced robotic arms. Sarah Connor attended the conference in Boston."
    }]

    check_missing = engine._verify_person_and_role(
        candidate_name="Sarah Connor",
        candidate_role="Chief Executive Officer",
        sources=sources_no_role,
        retrieval_timestamp="2026-11-19 00:00:00 UTC",
        company="Starlight Robotics"
    )
    assert check_missing is not None
    assert check_missing["designation"] == "Role not verified", f"Expected 'Role not verified', got {check_missing['designation']}"
    assert check_missing["verification_status"] == "ROLE_NOT_VERIFIED"
    assert check_missing["source_url"] == "https://starlight.example.com/about"
    print(f"✔ Missing designation correctly evaluated to '{check_missing['designation']}' [{check_missing['verification_status']}]")

def test_conflicting_official_sources():
    print("\n--- Test 5: Conflicting Official Sources Detection ---")

    engine = CompanyDiscoveryEngine()
    conflicting_sources = [
        {
            "title": "QuantumScale Official Leadership",
            "url": "https://quantumscale.example.com/leadership",
            "snippet": "Jane Doe serves as Chief Executive Officer at QuantumScale."
        },
        {
            "title": "QuantumScale Press Release",
            "url": "https://quantumscale.example.com/news/board-update",
            "snippet": "Jane Doe has transitioned to Executive Adviser at QuantumScale."
        }
    ]

    check_conflict = engine._verify_person_and_role(
        candidate_name="Jane Doe",
        candidate_role="",
        sources=conflicting_sources,
        retrieval_timestamp="2026-11-19 00:00:00 UTC",
        company="QuantumScale"
    )
    assert check_conflict is not None
    assert check_conflict["verification_status"] == "CONFLICTING_SOURCES", f"Expected CONFLICTING_SOURCES, got {check_conflict['verification_status']}"
    assert check_conflict["designation"] == "Conflicting sources – manual verification required", f"Expected conflicting notice, got '{check_conflict['designation']}'"
    assert check_conflict["source_url"] == "https://quantumscale.example.com/leadership"
    print("✔ Conflicting sources correctly flagged as:")
    print(f"   Designation: '{check_conflict['designation']}' [{check_conflict['verification_status']}]")

def main():
    print("=" * 80)
    print("RUNNING COMPANY DISCOVERY EXTRACTION & VERIFICATION TEST SUITE")
    print("=" * 80)

    test_heading_and_name_merging()
    test_duplicate_people()
    test_ceo_vs_ceo_designate()
    test_missing_designation()
    test_conflicting_official_sources()

    print("\n" + "=" * 80)
    print(">>> ALL 5 EXTRACTION & VERIFICATION TESTS PASSED PERFECTLY! <<<")
    print("=" * 80)

if __name__ == "__main__":
    main()
