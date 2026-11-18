import json
import io
import os
import sys

# Ensure workspace root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sales_agent.web_ui import AgentWebHandler
from sales_agent.commands import parse_user_command

OLD_FALLBACK_TEXT = "I'm ready to assist! You can tell me 'Research [Name] at [Company], [Role]'"

class MockRequest:
    def __init__(self, body_bytes: bytes):
        self.rfile = io.BytesIO(body_bytes)
        self.wfile = io.BytesIO()

def invoke_chat_post(message: str):
    body = json.dumps({"message": message}).encode("utf-8")
    mock = MockRequest(body)

    handler = AgentWebHandler.__new__(AgentWebHandler)
    handler.path = "/api/chat"
    handler.headers = {"Content-Length": str(len(body)), "Content-Type": "application/json"}
    handler.rfile = mock.rfile
    handler.wfile = mock.wfile

    handler.send_response = lambda code, message=None: None
    handler.send_header = lambda k, v: None
    handler.end_headers = lambda: None

    handler.do_POST()
    return json.loads(mock.wfile.getvalue().decode("utf-8"))

def main():
    print("=" * 70)
    print("RUNNING CHATBOT COMMAND PARSER & ROUTING VERIFICATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # Test 1: Command Parser Unit Test
    # ---------------------------------------------------------
    print("\n--- Test 1: Parser unit checks ---")
    cmd1 = parse_user_command("Research NVIDIA")
    assert cmd1["type"] == "company_discovery" and cmd1["company"] == "NVIDIA", f"Failed: {cmd1}"
    print("✔ 'Research NVIDIA' parsed as company_discovery for 'NVIDIA'")

    cmd2 = parse_user_command("Research Google")
    assert cmd2["type"] == "company_discovery" and cmd2["company"] == "Google", f"Failed: {cmd2}"
    print("✔ 'Research Google' parsed as company_discovery for 'Google'")

    cmd3 = parse_user_command("Research Satya Nadella at Microsoft, CEO")
    assert cmd3["type"] == "named_lead" and cmd3["name"] == "Satya Nadella" and cmd3["company"] == "Microsoft" and cmd3["role"] == "CEO", f"Failed: {cmd3}"
    print("✔ 'Research Satya Nadella at Microsoft, CEO' parsed as named_lead")

    # ---------------------------------------------------------
    # Test 2: HTTP /api/chat 'Research NVIDIA' (Company Discovery)
    # ---------------------------------------------------------
    print("\n--- Test 2: End-to-End Chat API with 'Research NVIDIA' ---")
    res1 = invoke_chat_post("Research NVIDIA")
    reply1 = res1.get("reply", "")

    # Crucial Requirement: Must NOT return old fallback response
    assert OLD_FALLBACK_TEXT not in reply1, "FAIL: Old fallback message was returned for 'Research NVIDIA'!"
    assert "I'm ready to assist! You can tell me" not in reply1, "FAIL: Generic fallback returned!"

    # Must execute company discovery and return NVIDIA prospects with verified source URL
    assert "Company Discovery: NVIDIA" in reply1, "FAIL: NVIDIA discovery missing from reply!"
    assert "Jensen Huang" in reply1, "FAIL: Expected 'Jensen Huang' in discovered prospects!"
    assert "https://www.nvidia.com" in reply1, "FAIL: Expected verified source URL for NVIDIA prospect!"
    assert "launchProspectFromChat" in reply1, "FAIL: Expected interactive prospect launch button in chat!"
    print("✔ 'Research NVIDIA' returned verified company discovery results!")
    print("✔ Verified prospect 'Jensen Huang' (Founder, President & CEO) present.")
    print("✔ Verified source URL: https://www.nvidia.com/en-us/about-nvidia/corporate-executives/jensen-huang/")
    print("✔ Confirmed old fallback text is STRICTLY NOT present in response.")

    # ---------------------------------------------------------
    # Test 3: HTTP /api/chat 'Research Google' (Company Discovery)
    # ---------------------------------------------------------
    print("\n--- Test 3: End-to-End Chat API with 'Research Google' ---")
    res2 = invoke_chat_post("Research Google")
    reply2 = res2.get("reply", "")

    assert OLD_FALLBACK_TEXT not in reply2, "FAIL: Old fallback message was returned for 'Research Google'!"
    assert "I're ready to assist! You can tell me" not in reply2 and "I'm ready to assist! You can tell me" not in reply2, "FAIL: Generic fallback returned!"
    assert "Company Discovery: Google" in reply2, "FAIL: Expected Company Discovery header for Google!"
    assert "Sundar Pichai" in reply2, "FAIL: Expected 'Sundar Pichai' in Google discovery!"
    assert "https://abc.xyz" in reply2, "FAIL: Expected verified source URL for Sundar Pichai!"
    print("✔ 'Research Google' returned verified company discovery results!")
    print("✔ Verified prospect 'Sundar Pichai' (CEO) present.")
    print("✔ Verified source URL: https://abc.xyz/investor/board-and-management/")

    # ---------------------------------------------------------
    # Test 4: HTTP /api/chat 'Research Satya Nadella at Microsoft, CEO'
    # ---------------------------------------------------------
    print("\n--- Test 4: End-to-End Chat API with 'Research Satya Nadella at Microsoft, CEO' ---")
    res3 = invoke_chat_post("Research Satya Nadella at Microsoft, CEO")
    reply3 = res3.get("reply", "")

    assert OLD_FALLBACK_TEXT not in reply3, "FAIL: Old fallback message was returned!"
    assert "Researched Satya Nadella at Microsoft" in reply3, f"FAIL: Expected onboarding confirmation, got: {reply3}"
    assert "Touch #1 Drafted" in reply3, "FAIL: Expected Touch #1 drafted message!"
    assert "Draft - Awaiting Approval" in reply3, "FAIL: Status must be Draft - Awaiting Approval!"
    print("✔ 'Research Satya Nadella at Microsoft, CEO' onboarded lead & drafted Touch #1 held in Awaiting Approval.")

    print("\n" + "=" * 70)
    print(">>> ALL CHATBOT COMMAND & ROUTING TESTS PASSED PERFECTLY! <<<")
    print("=" * 70)

if __name__ == "__main__":
    main()
