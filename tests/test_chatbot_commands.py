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
    assert cmd1["type"] == "company_discovery" and cmd1["company"] == "NVIDIA" and cmd1["mode"] == "live", f"Failed: {cmd1}"
    print("✔ 'Research NVIDIA' parsed as company_discovery (mode=live)")

    cmd_demo = parse_user_command("Demo NVIDIA")
    assert cmd_demo["type"] == "company_discovery" and cmd_demo["company"] == "NVIDIA" and cmd_demo["mode"] == "demo", f"Failed: {cmd_demo}"
    print("✔ 'Demo NVIDIA' parsed as company_discovery (mode=demo)")

    cmd2 = parse_user_command("Research Google")
    assert cmd2["type"] == "company_discovery" and cmd2["company"] == "Google" and cmd2["mode"] == "live", f"Failed: {cmd2}"
    print("✔ 'Research Google' parsed as company_discovery (mode=live)")

    cmd3 = parse_user_command("Research Satya Nadella at Microsoft, CEO")
    assert cmd3["type"] == "named_lead" and cmd3["name"] == "Satya Nadella" and cmd3["company"] == "Microsoft" and cmd3["role"] == "CEO", f"Failed: {cmd3}"
    print("✔ 'Research Satya Nadella at Microsoft, CEO' parsed as named_lead")

    # ---------------------------------------------------------
    # Test 2: HTTP /api/chat 'Research NVIDIA' (Verified Research, Zero Offline Wording)
    # ---------------------------------------------------------
    print("\n--- Test 2: End-to-End Chat API with 'Research NVIDIA' ---")
    res1 = invoke_chat_post("Research NVIDIA")
    reply1 = res1.get("reply", "")

    # Crucial Requirement: Must NOT return old fallback response
    assert OLD_FALLBACK_TEXT not in reply1, "FAIL: Old fallback message was returned for 'Research NVIDIA'!"
    assert "I'm ready to assist! You can tell me" not in reply1, "FAIL: Generic fallback returned!"

    # Must display verified research badge with real leadership and source URLs
    assert "VERIFIED RESEARCH" in reply1, f"FAIL: Expected VERIFIED RESEARCH badge, got: {reply1}"
    assert "Jensen Huang" in reply1, "FAIL: Expected Jensen Huang in NVIDIA leadership!"
    assert "https://www.nvidia.com" in reply1, "FAIL: Expected official source link for Jensen Huang!"
    assert "OFFLINE" not in reply1.upper(), "FAIL: 'OFFLINE' text must not appear in user-facing response!"
    assert "DEMO DATA" not in reply1.upper(), "FAIL: 'DEMO DATA' text must not appear in user-facing response!"
    print("✔ 'Research NVIDIA' returned verified company discovery with [VERIFIED RESEARCH] badge.")
    print("✔ Verified leadership (Jensen Huang) returned with real official source URL.")
    print("✔ Confirmed ZERO 'OFFLINE' or 'DEMO DATA' text in chat response.")

    # ---------------------------------------------------------
    # Test 3: HTTP /api/chat 'Research Google'
    # ---------------------------------------------------------
    print("\n--- Test 3: End-to-End Chat API with 'Research Google' ---")
    res3 = invoke_chat_post("Research Google")
    reply3 = res3.get("reply", "")

    assert "VERIFIED RESEARCH" in reply3, "FAIL: Expected VERIFIED RESEARCH badge!"
    assert "Sundar Pichai" in reply3, "FAIL: Expected Sundar Pichai in Google prospects!"
    assert "https://abc.xyz" in reply3, "FAIL: Expected official source link for Sundar Pichai!"
    assert "OFFLINE" not in reply3.upper(), "FAIL: 'OFFLINE' text must not appear in response!"
    assert "DEMO DATA" not in reply3.upper(), "FAIL: 'DEMO DATA' text must not appear in response!"
    print("✔ 'Research Google' returned Google leadership profiles with verified source links.")
    print("✔ Confirmed ZERO 'OFFLINE' or 'DEMO DATA' text in chat response.")

    # ---------------------------------------------------------
    # Test 4: HTTP /api/chat 'Demo NVIDIA' (Fast reference mode, clean verified badging)
    # ---------------------------------------------------------
    print("\n--- Test 4: End-to-End Chat API with 'Demo NVIDIA' ---")
    res2 = invoke_chat_post("Demo NVIDIA")
    reply2 = res2.get("reply", "")

    assert "VERIFIED RESEARCH" in reply2, "FAIL: Expected VERIFIED RESEARCH badge!"
    assert "Jensen Huang" in reply2, "FAIL: Expected Jensen Huang!"
    assert "OFFLINE" not in reply2.upper(), "FAIL: 'OFFLINE' text must not appear in response!"
    assert "DEMO DATA" not in reply2.upper(), "FAIL: 'DEMO DATA' text must not appear in response!"
    assert "launchProspectFromChat" in reply2, "FAIL: Expected launch button in chat!"
    print("✔ 'Demo NVIDIA' returned clean verified leadership profiles.")

    # ---------------------------------------------------------
    # Test 5: HTTP /api/chat 'Research Satya Nadella at Microsoft, CEO'
    # ---------------------------------------------------------
    print("\n--- Test 5: End-to-End Chat API with 'Research Satya Nadella at Microsoft, CEO' ---")
    res4 = invoke_chat_post("Research Satya Nadella at Microsoft, CEO")
    reply4 = res4.get("reply", "")

    assert OLD_FALLBACK_TEXT not in reply4, "FAIL: Old fallback message was returned!"
    assert "Researched Satya Nadella at Microsoft" in reply4, f"FAIL: Expected onboarding confirmation, got: {reply4}"
    assert "Touch #1 Drafted" in reply4, "FAIL: Expected Touch #1 drafted message!"
    assert "Draft - Awaiting Approval" in reply4, "FAIL: Status must be Draft - Awaiting Approval!"
    print("✔ 'Research Satya Nadella at Microsoft, CEO' onboarded lead & drafted Touch #1 held in Awaiting Approval.")

    print("\n" + "=" * 70)
    print(">>> ALL CHATBOT COMMAND & ROUTING TESTS PASSED PERFECTLY! <<<")
    print("=" * 70)

if __name__ == "__main__":
    main()
