import re
from typing import Dict, Any

def parse_user_command(raw_input: str) -> Dict[str, Any]:
    """
    Parses user inputs from web chat or CLI into structured commands:
    1. Named lead outreach:
       - 'Research [Name] at [Company], [Role]'
       - 'Research [Name] at [Company]'
       - 'Prospect [Name] at [Company], [Role]'
    2. Company discovery:
       - 'Research [Company]' (e.g. 'Research NVIDIA', 'Research Google')
       - 'Discover [Company]'
       - 'Explore [Company]'
       - 'Find leads in [Company]'
       - 'Company: [Company]'
    3. Conversational query:
       - General assistant queries
    """
    if not raw_input:
        return {"type": "empty"}

    text = raw_input.strip().rstrip(".!?;:")
    # Remove interior quotes or surrounding markdown formatting
    cleaned = re.sub(r'[\'"`\*_]', '', text).strip()

    # Pattern 1: Named Lead Outreach: contains " at "
    # e.g., "Research Satya Nadella at Microsoft, CEO", "Research Jensen Huang at NVIDIA"
    named_match = re.search(
        r"^(?:please\s+|can\s+you\s+)?(?:research|prospect|add\s+lead|lookup|find)?\s*(.+?)\s+at\s+([A-Za-z0-9\s\.\&\-]+?)(?:,\s*([A-Za-z0-9\s\.\&\-\/]+))?$",
        cleaned,
        re.IGNORECASE
    )
    if named_match and " at " in cleaned.lower():
        name = named_match.group(1).strip()
        company = named_match.group(2).strip()
        role = named_match.group(3).strip() if named_match.group(3) else "Executive"
        if len(name) >= 2 and len(company) >= 2:
            return {
                "type": "named_lead",
                "name": name,
                "company": company,
                "role": role,
                "original": raw_input
            }

    # Pattern 2: Company-Only Discovery
    # e.g., "Research NVIDIA", "Research Google", "Discover Microsoft", "Find leads in Infosys"
    comp_match = re.search(
        r"^(?:please\s+|can\s+you\s+)?(?:research|discover|explore|find\s+leads\s+in|lookup|search|company[:\s]+)\s+([A-Za-z0-9\s\.\&\-]+)$",
        cleaned,
        re.IGNORECASE
    )
    if comp_match:
        company = comp_match.group(1).strip()
        # Exclude reserved assistant navigation keywords
        if company.lower() not in ["help", "hello", "hi", "hey", "demo", "status", "settings", "leads", "touches", "logs"]:
            return {
                "type": "company_discovery",
                "company": company,
                "original": raw_input
            }

    return {
        "type": "conversational",
        "query": text,
        "original": raw_input
    }
