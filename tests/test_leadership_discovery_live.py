import os
import sys
from typing import Dict, Any, List, Optional

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sales_agent.search.discovery import (
    CompanyDiscoveryEngine,
    deduplicate_prospects,
    LeadershipHTMLParser,
    clean_person_name,
    extract_role_from_text,
    score_source_authority
)
from sales_agent.search.duckduckgo import DuckDuckGoSearchTool

NVIDIA_HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head><title>Corporate Executives | NVIDIA</title></head>
<body>
  <h1>Corporate Executives</h1>
  <div class="leadership-grid">
    <div class="leader-card">
      <a href="/en-us/about-nvidia/corporate-executives/jensen-huang/">
        <h3>Jensen Huang</h3>
      </a>
      <p>Founder, President and Chief Executive Officer</p>
    </div>
    <div class="leader-card">
      <a href="/en-us/about-nvidia/corporate-executives/colette-kress/">
        <h3>Colette Kress</h3>
      </a>
      <p>Executive Vice President and Chief Financial Officer</p>
    </div>
    <div class="leader-card">
      <a href="/en-us/about-nvidia/corporate-executives/bill-dally/">
        <h3>Bill Dally</h3>
      </a>
      <p>Chief Scientist and Senior Vice President of Research</p>
    </div>
  </div>
</body>
</html>
"""

INFOSYS_HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head><title>Management Profiles | Infosys</title></head>
<body>
  <h2>Management Profiles</h2>
  <div class="management-profiles">
    <div class="profile-card">
      <a href="salil-parekh.html">
        <h4>Salil Parekh</h4>
      </a>
      <p class="role">Chief Executive Officer & Managing Director</p>
    </div>
    <div class="profile-card">
      <a href="jayesh-sanghrajka.html">
        <h4>Jayesh Sanghrajka</h4>
      </a>
      <p class="role">Chief Financial Officer</p>
    </div>
    <div class="profile-card">
      <a href="shaji-mathew.html">
        <h4>Shaji Mathew</h4>
      </a>
      <p class="role">Group Head of Human Resources</p>
    </div>
  </div>
</body>
</html>
"""

class MockSearchTool(DuckDuckGoSearchTool):
    """Configurable mock search tool tracking query invocations and returning realistic results."""
    def __init__(self, query_map: Optional[Dict[str, List[Dict[str, str]]]] = None, default_results: Optional[List[Dict[str, str]]] = None):
        super().__init__()
        self.query_map = query_map or {}
        self.default_results = default_results or []
        self.recorded_queries: List[str] = []

    def search_with_status(self, query: str, max_results=None) -> Dict[str, Any]:
        self.recorded_queries.append(query)
        for pattern, res in self.query_map.items():
            if pattern.lower() in query.lower():
                return {"status": "SUCCESS", "results": res, "error": None}
        return {"status": "SUCCESS", "results": self.default_results, "error": None}


def test_nvidia_live_discovery_with_page_fetching():
    print("\n=== Test 1: NVIDIA Discovery from Official Leadership Page Content ===")
    
    mock_search = MockSearchTool(
        default_results=[
            {
                "title": "NVIDIA Corporation - Accelerated Computing & Enterprise AI",
                "url": "https://www.nvidia.com/en-us/about-nvidia/",
                "snippet": "NVIDIA pioneered GPU-accelerated computing to solve some of the world's most complex computational challenges."
            },
            {
                "title": "Official Corporate Executives | NVIDIA",
                "url": "https://www.nvidia.com/en-us/about-nvidia/corporate-executives/",
                "snippet": "Meet the executive committee and corporate officers leading NVIDIA."
            }
        ]
    )

    def mock_fetcher(url: str) -> Optional[str]:
        if "nvidia.com" in url and "corporate-executives" in url:
            return NVIDIA_HTML_CONTENT
        return None

    engine = CompanyDiscoveryEngine(search_tool=mock_search, page_fetcher=mock_fetcher)
    result = engine.discover("NVIDIA", mode="live")

    assert result["status"] == "OK", f"Expected status 'OK', got {result['status']}"
    assert result["data_source"] == "LIVE_SEARCH", f"Expected LIVE_SEARCH, got {result['data_source']}"
    assert result["is_demo_mode"] is False
    assert len(result["prospects"]) == 3, f"Expected 3 prospects, got {len(result['prospects'])}"

    p_map = {p["name"]: p for p in result["prospects"]}
    assert "Jensen Huang" in p_map
    assert "Colette Kress" in p_map
    assert "Bill Dally" in p_map

    # Verification checks on designations
    assert p_map["Jensen Huang"]["designation"] == "Founder, President & CEO"
    assert p_map["Jensen Huang"]["verification_status"] == "VERIFIED"
    assert "jensen-huang" in p_map["Jensen Huang"]["source_url"]

    assert p_map["Colette Kress"]["designation"] == "Executive VP & Chief Financial Officer"
    assert p_map["Colette Kress"]["verification_status"] == "VERIFIED"
    assert "colette-kress" in p_map["Colette Kress"]["source_url"]

    assert p_map["Bill Dally"]["designation"] == "Chief Scientist & Senior VP of Research"
    assert p_map["Bill Dally"]["verification_status"] == "VERIFIED"
    assert "bill-dally" in p_map["Bill Dally"]["source_url"]

    print("✔ Discovered 3 verified NVIDIA executives with individual official profile links:")
    for p in result["prospects"]:
        print(f"   • {p['name']} — {p['designation']} [{p['verification_status']}]")
        print(f"     URL: {p['source_url']}")


def test_infosys_management_profiles_and_exact_designations():
    print("\n=== Test 2: Infosys Discovery & Exact Designation Distinction ===")

    mock_search = MockSearchTool(
        default_results=[
            {
                "title": "Infosys - Digital Services & Consulting",
                "url": "https://www.infosys.com/about.html",
                "snippet": "Infosys is a global leader in next-generation digital services and consulting."
            },
            {
                "title": "Infosys Leadership | Management Profiles",
                "url": "https://www.infosys.com/about/management-profiles.html",
                "snippet": "Profiles of Infosys executive leadership and management committee."
            }
        ]
    )

    def mock_fetcher(url: str) -> Optional[str]:
        if "infosys.com" in url and "management-profiles" in url:
            return INFOSYS_HTML_CONTENT
        return None

    engine = CompanyDiscoveryEngine(search_tool=mock_search, page_fetcher=mock_fetcher)
    result = engine.discover("Infosys", mode="live")

    assert result["status"] == "OK"
    assert result["data_source"] == "LIVE_SEARCH"
    assert len(result["prospects"]) == 3

    p_map = {p["name"]: p for p in result["prospects"]}
    assert "Salil Parekh" in p_map
    # Crucial distinction: never downgrade or strip Chief Executive Officer & Managing Director
    assert p_map["Salil Parekh"]["designation"] == "Chief Executive Officer & Managing Director"
    assert p_map["Salil Parekh"]["verification_status"] == "VERIFIED"
    assert "salil-parekh.html" in p_map["Salil Parekh"]["source_url"]

    assert "Jayesh Sanghrajka" in p_map
    assert p_map["Jayesh Sanghrajka"]["designation"] == "Chief Financial Officer"
    assert "jayesh-sanghrajka.html" in p_map["Jayesh Sanghrajka"]["source_url"]

    assert "Shaji Mathew" in p_map
    assert p_map["Shaji Mathew"]["designation"] == "Group Head of Human Resources"
    assert "shaji-mathew.html" in p_map["Shaji Mathew"]["source_url"]

    print("✔ Verified exact designations preserved without downgrade:")
    for p in result["prospects"]:
        print(f"   • {p['name']} — {p['designation']} ({p['source_url']})")


def test_cross_referencing_separate_snippets():
    print("\n=== Test 3: Multi-Snippet Cross-Referencing (Requirement 6) ===")
    # Snippet A mentions the person without designation
    # Snippet B establishes the official relationship on an official profile page
    mock_search = MockSearchTool(
        default_results=[
            {
                "title": "Jensen Huang Keynote at AI Conference",
                "url": "https://technews.example.com/gtc-summary",
                "snippet": "Jensen Huang delivered the keynote on modern computing at GTC in San Jose."
            },
            {
                "title": "Official NVIDIA Leadership: Jensen Huang Profile",
                "url": "https://www.nvidia.com/en-us/about-nvidia/corporate-executives/jensen-huang/",
                "snippet": "Jensen Huang is the Founder, President & CEO of NVIDIA Corporation."
            }
        ]
    )

    engine = CompanyDiscoveryEngine(search_tool=mock_search)
    result = engine.discover("NVIDIA", mode="live")

    assert result["status"] == "OK"
    assert len(result["prospects"]) > 0
    p = result["prospects"][0]
    assert p["name"] == "Jensen Huang"
    assert p["designation"] == "Founder, President & CEO"
    assert p["verification_status"] == "VERIFIED"
    assert "nvidia.com" in p["source_url"]
    print(f"✔ Cross-referencing verified {p['name']} across multiple snippets without requiring name and designation in same initial snippet.")


def test_secondary_search_when_only_company_context_found():
    print("\n=== Test 4: Secondary Official Leadership Search Triggered (Requirement 8) ===")
    
    # Query map: Initial queries return only general company context (0 leadership in initial snippets)
    # Secondary queries return leadership results!
    query_map = {
        "overview": [
            {
                "title": "NVIDIA Overview and Market Capitalization",
                "url": "https://www.nvidia.com/en-us/about-nvidia/",
                "snippet": "NVIDIA is a multinational technology company inventing accelerated computing."
            }
        ],
        "corporate executives": [
            {
                "title": "Official Corporate Executives | NVIDIA",
                "url": "https://www.nvidia.com/en-us/about-nvidia/corporate-executives/",
                "snippet": "Jensen Huang serves as Founder, President & CEO of NVIDIA."
            }
        ]
    }

    mock_search = MockSearchTool(query_map=query_map)
    engine = CompanyDiscoveryEngine(search_tool=mock_search)
    result = engine.discover("NVIDIA", mode="live")

    # Verify secondary queries were recorded
    has_secondary_query = any("corporate executives" in q.lower() or "chief executive officer" in q.lower() for q in mock_search.recorded_queries)
    assert has_secondary_query, "Expected secondary leadership search queries to be executed"

    assert result["status"] == "OK", f"Expected OK status after secondary search, got: {result['status']}"
    assert len(result["prospects"]) > 0
    assert result["prospects"][0]["name"] == "Jensen Huang"
    print(f"✔ Secondary search automatically triggered and successfully discovered {result['prospects'][0]['name']} without returning NOT FOUND.")


def test_genuine_failure_diagnostic_explanation():
    print("\n=== Test 5: Genuine Failure Diagnostic Message (Requirement 9) ===")

    # Company with real overview but genuinely absent leadership
    mock_search = MockSearchTool(
        default_results=[
            {
                "title": "Aurora Stealth AI Lab Overview",
                "url": "https://aurorastealth.example.com/about",
                "snippet": "Aurora Stealth AI Lab builds autonomous edge models under stealth operations."
            }
        ]
    )

    engine = CompanyDiscoveryEngine(search_tool=mock_search)
    result = engine.discover("Aurora Stealth", mode="live")

    assert result["status"] == "PARTIAL"
    assert len(result["prospects"]) == 0
    assert result["search_warning"] is not None
    assert "leadership designations" in result["search_warning"]
    assert "could not be verified" in result["search_warning"]
    print(f"✔ Genuine failure diagnosed accurately: '{result['search_warning']}'")
    print("✔ Confirmed zero employee names or designations were invented.")


def test_duplicate_and_conflict_handling():
    print("\n=== Test 6: Duplicate Deduplication & Designation Conflict Prevention ===")

    # 1. Duplicate deduplication
    dup_candidates = [
        {
            "name": "Jensen Huang",
            "designation": "Founder, President & CEO",
            "verification_status": "VERIFIED",
            "source_url": "https://news.example.com/jensen-general",
            "source_title": "News"
        },
        {
            "name": "Mr. Jensen Huang",
            "designation": "Founder, President & CEO",
            "verification_status": "VERIFIED",
            "source_url": "https://www.nvidia.com/en-us/about-nvidia/corporate-executives/jensen-huang/",
            "source_title": "Official Profile"
        }
    ]
    deduped = deduplicate_prospects(dup_candidates, "NVIDIA")
    assert len(deduped) == 1
    assert deduped[0]["name"] == "Jensen Huang"
    assert "nvidia.com" in deduped[0]["source_url"], "Expected highest authority official source URL to win"
    print("✔ Duplicate prospects normalized and deduplicated to single entry with official source.")

    # 2. Conflicting sources
    conflict_candidates = [
        {
            "name": "Jane Doe",
            "designation": "Chief Executive Officer",
            "verification_status": "VERIFIED",
            "source_url": "https://source1.example.com",
            "source_title": "Source 1"
        },
        {
            "name": "Jane Doe",
            "designation": "Chief Technology Officer",
            "verification_status": "VERIFIED",
            "source_url": "https://source2.example.com",
            "source_title": "Source 2"
        }
    ]
    conflict_deduped = deduplicate_prospects(conflict_candidates, "ExampleCorp")
    assert len(conflict_deduped) == 1
    assert conflict_deduped[0]["verification_status"] == "CONFLICTING_SOURCES"
    assert "Conflicting sources" in conflict_deduped[0]["designation"]
    print("✔ Conflicting executive designations correctly detected and flagged.")


def main():
    print("=" * 80)
    print("RUNNING LIVE LEADERSHIP DISCOVERY & VERIFICATION TEST SUITE")
    print("=" * 80)
    test_nvidia_live_discovery_with_page_fetching()
    test_infosys_management_profiles_and_exact_designations()
    test_cross_referencing_separate_snippets()
    test_secondary_search_when_only_company_context_found()
    test_genuine_failure_diagnostic_explanation()
    test_duplicate_and_conflict_handling()
    print("\n" + "=" * 80)
    print(">>> ALL 6 LIVE LEADERSHIP DISCOVERY & VERIFICATION TESTS PASSED! <<<")
    print("=" * 80)


if __name__ == "__main__":
    main()
