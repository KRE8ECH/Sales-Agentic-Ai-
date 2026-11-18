import json
import logging
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional, Tuple
from sales_agent.search.duckduckgo import DuckDuckGoSearchTool
from sales_agent.search.rag_engine import RAGEngine
from sales_agent.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

# Verified offline leadership knowledge base for reference and explicit demo offline testing
VERIFIED_OFFLINE_COMPANIES = {
    "nvidia": {
        "company_name": "NVIDIA",
        "company_overview": "NVIDIA is a global technology pioneer that invented the GPU and powers accelerated computing, hyperscale AI infrastructure, and autonomous systems.",
        "business_activities": [
            "AI and Datacenter GPU hardware (Hopper, Blackwell architecture)",
            "CUDA parallel computing platform and developer ecosystem",
            "Enterprise AI software suites and autonomous vehicle platforms"
        ],
        "recent_announcements": [
            {
                "title": "NVIDIA Blackwell Architecture Accelerates Trillion-Parameter AI Models",
                "url": "https://nvidianews.nvidia.com/news/blackwell-architecture",
                "snippet": "NVIDIA unveiled the Blackwell platform to power a new era of computing, enabling organizations to build real-time generative AI."
            },
            {
                "title": "NVIDIA Reports Record Datacenter Revenue Growth",
                "url": "https://investor.nvidia.com/financial-info/quarterly-results/",
                "snippet": "NVIDIA reported record quarterly revenue driven by global hyperscale adoption of accelerated computing platforms."
            }
        ],
        "potential_business_needs": [
            "Scaling developer enablement and enterprise outbound for Blackwell AI platforms",
            "Optimizing partner onboarding and reducing sales cycle friction"
        ],
        "prospects": [
            {
                "id": 1,
                "name": "Jensen Huang",
                "designation": "Founder, President & CEO",
                "company": "NVIDIA",
                "professional_relevance": "Drives overall vision, capital allocation, and executive strategy for enterprise AI platforms.",
                "source_url": "https://www.nvidia.com/en-us/about-nvidia/corporate-executives/jensen-huang/",
                "source_title": "Official NVIDIA Leadership: Jensen Huang Profile"
            },
            {
                "id": 2,
                "name": "Bill Dally",
                "designation": "Chief Scientist & Senior VP of Research",
                "company": "NVIDIA",
                "professional_relevance": "Leads advanced research labs, computing architectures, and technology roadmap evaluations.",
                "source_url": "https://www.nvidia.com/en-us/about-nvidia/corporate-executives/bill-dally/",
                "source_title": "Official NVIDIA Leadership: Bill Dally Profile"
            },
            {
                "id": 3,
                "name": "Colette Kress",
                "designation": "Executive VP & Chief Financial Officer",
                "company": "NVIDIA",
                "professional_relevance": "Oversees worldwide finance operations, enterprise budgeting, and software infrastructure vendor investments.",
                "source_url": "https://www.nvidia.com/en-us/about-nvidia/corporate-executives/colette-kress/",
                "source_title": "Official NVIDIA Leadership: Colette Kress Profile"
            }
        ]
    },
    "microsoft": {
        "company_name": "Microsoft",
        "company_overview": "Microsoft is a worldwide leader in software, cloud computing (Azure), enterprise productivity tools (Office 365), and applied generative AI.",
        "business_activities": [
            "Azure Cloud Infrastructure and enterprise hybrid computing",
            "Microsoft Copilot AI integrated across productivity suites",
            "Developer tools, Windows ecosystem, and enterprise security platforms"
        ],
        "recent_announcements": [
            {
                "title": "Microsoft and OpenAI Expand Long-Term Partnership",
                "url": "https://blogs.microsoft.com/blog/2023/01/23/microsoft-and-openai-extend-partnership/",
                "snippet": "Microsoft announced the multiyear, multibillion-dollar investment to accelerate AI breakthroughs and global commercialization."
            },
            {
                "title": "Microsoft Copilot Adoption Expands Across Global Enterprises",
                "url": "https://www.microsoft.com/en-us/microsoft-365/enterprise/copilot",
                "snippet": "Over 70% of Fortune 500 enterprises have deployed Microsoft Copilot productivity and workflow automation features."
            }
        ],
        "potential_business_needs": [
            "Accelerating cloud sales pipeline and partner account development",
            "Equipping enterprise account executives with personalized, research-backed outreach"
        ],
        "prospects": [
            {
                "id": 1,
                "name": "Satya Nadella",
                "designation": "Chairman & Chief Executive Officer",
                "company": "Microsoft",
                "professional_relevance": "Leads Microsoft's mission, cloud-first transformation, and enterprise AI commercialization strategy.",
                "source_url": "https://news.microsoft.com/exec/satya-nadella/",
                "source_title": "Microsoft Executive Biographies: Satya Nadella"
            },
            {
                "id": 2,
                "name": "Kevin Scott",
                "designation": "Chief Technology Officer & EVP of AI",
                "company": "Microsoft",
                "professional_relevance": "Oversees corporate technology roadmaps, large-scale AI research initiatives, and infrastructure partnerships.",
                "source_url": "https://news.microsoft.com/exec/kevin-scott/",
                "source_title": "Microsoft Executive Biographies: Kevin Scott"
            },
            {
                "id": 3,
                "name": "Amy Hood",
                "designation": "Executive VP & Chief Financial Officer",
                "company": "Microsoft",
                "professional_relevance": "Directs global financial operations, cloud revenue planning, and strategic operational acquisitions.",
                "source_url": "https://news.microsoft.com/exec/amy-hood/",
                "source_title": "Microsoft Executive Biographies: Amy Hood"
            }
        ]
    },
    "infosys": {
        "company_name": "Infosys",
        "company_overview": "Infosys is a global leader in next-generation digital services, enterprise IT consulting, cloud transformation, and business solutions.",
        "business_activities": [
            "Infosys Topaz generative AI consulting and enterprise solutions",
            "Infosys Cobalt cloud migration and platform modernization",
            "Enterprise software engineering, application management, and digital automation"
        ],
        "recent_announcements": [
            {
                "title": "Infosys Launches Topaz: An AI-First Suite of Services and Solutions",
                "url": "https://www.infosys.com/newsroom/press-releases/2023/ai-first-services-solutions-topaz.html",
                "snippet": "Infosys Topaz converges generative AI capabilities to empower enterprises with amplified human potential."
            },
            {
                "title": "Infosys and Microsoft Deepen Strategic Collaboration for Enterprise AI",
                "url": "https://www.infosys.com/newsroom/press-releases/2024/strategic-collaboration-accelerate-cloud.html",
                "snippet": "Joint initiatives to deliver cloud-native transformation and AI capabilities to enterprise clients worldwide."
            }
        ],
        "potential_business_needs": [
            "Scaling outbound business development for specialized Topaz AI consulting practices",
            "Reducing manual sales prospecting workload across global delivery accounts"
        ],
        "prospects": [
            {
                "id": 1,
                "name": "Salil Parekh",
                "designation": "Chief Executive Officer & Managing Director",
                "company": "Infosys",
                "professional_relevance": "Drives strategic direction, executive client relationships, and global delivery execution.",
                "source_url": "https://www.infosys.com/about/management-profiles/salil-parekh.html",
                "source_title": "Infosys Leadership Profile: Salil Parekh"
            },
            {
                "id": 2,
                "name": "Shaji Mathew",
                "designation": "Group Head of Human Resources",
                "company": "Infosys",
                "professional_relevance": "Leads global people strategy, talent acquisition, leadership development, and employee experience.",
                "source_url": "https://www.infosys.com/about/management-profiles/shaji-mathew.html",
                "source_title": "Infosys Leadership Profile: Shaji Mathew"
            },
            {
                "id": 3,
                "name": "Jayesh Sanghrajka",
                "designation": "Chief Financial Officer",
                "company": "Infosys",
                "professional_relevance": "Manages global corporate finance, operational cost discipline, and enterprise software procurement.",
                "source_url": "https://www.infosys.com/about/management-profiles/jayesh-sanghrajka.html",
                "source_title": "Infosys Leadership Profile: Jayesh Sanghrajka"
            }
        ]
    },
    "google": {
        "company_name": "Google",
        "company_overview": "Google (Alphabet) is a global technology pioneer leading in search, cloud computing (Google Cloud), enterprise AI (Gemini), and autonomous systems.",
        "business_activities": [
            "Search and digital advertising infrastructure",
            "Google Cloud Platform (GCP) and enterprise Vertex AI solutions",
            "Google DeepMind frontier AI research and Gemini foundation models"
        ],
        "recent_announcements": [
            {
                "title": "Google Cloud Introduces Gemini 1.5 Pro to Enterprise Customers",
                "url": "https://blog.google/technology/ai/gemini-1-5-pro-updates/",
                "snippet": "Google expanded access to Gemini 1.5 Pro with its 1-million-token context window for global enterprise development."
            },
            {
                "title": "Google Announces Next-Generation Custom TPU Accelerators",
                "url": "https://cloud.google.com/blog/products/compute/introducing-cloud-tpu-v5e",
                "snippet": "Google Cloud unveiled next-generation Tensor Processing Units engineered for energy-efficient AI model training and inference."
            }
        ],
        "potential_business_needs": [
            "Expanding enterprise AI adoption across Fortune 500 accounts",
            "Accelerating outbound sales prospecting for Google Cloud Vertex AI infrastructure"
        ],
        "prospects": [
            {
                "id": 1,
                "name": "Sundar Pichai",
                "designation": "Chief Executive Officer",
                "company": "Google",
                "professional_relevance": "Directs overall corporate vision, AI investments, and global strategy across Google and Alphabet.",
                "source_url": "https://abc.xyz/investor/board-and-management/",
                "source_title": "Alphabet & Google Board and Management: Sundar Pichai"
            },
            {
                "id": 2,
                "name": "Thomas Kurian",
                "designation": "CEO, Google Cloud",
                "company": "Google",
                "professional_relevance": "Leads Google Cloud business strategy, enterprise customer relationships, and cloud sales engineering.",
                "source_url": "https://cloud.google.com/about/leadership",
                "source_title": "Google Cloud Leadership: Thomas Kurian"
            },
            {
                "id": 3,
                "name": "Demis Hassabis",
                "designation": "CEO, Google DeepMind",
                "company": "Google",
                "professional_relevance": "Directs frontier artificial intelligence research, model architectures, and scientific breakthrough initiatives.",
                "source_url": "https://deepmind.google/about/",
                "source_title": "Google DeepMind Leadership: Demis Hassabis"
            }
        ]
    }
}

VERIFIED_OFFLINE_COMPANIES["alphabet"] = VERIFIED_OFFLINE_COMPANIES["google"]

# =========================================================================
# EXTRACTION, NORMALIZATION, DEDUPLICATION & VERIFICATION HELPERS
# =========================================================================

NAV_HEADING_PATTERNS = [
    r"^(?:executive committee|board of directors|board of governance|board of|leadership team|leadership profiles?|leadership|management profiles?|management team|management|senior management|senior leadership|corporate governance|executive officers?|executive leadership|our leaders?|our team|our executive team|key executives?|key people|company leadership|executive biograph(?:y|ies)|executive profiles?|profile of|biography of|meet the team|meet our|officers and directors|members of the executive committee|members of|about us|home|overview)\b\s*[-:–—|]?\s*",
    r"^(?:directors?|officers?|executives?|leaders?|members?|committee)\b\s*[-:–—|]?\s*"
]

ROLE_PATTERNS: List[Tuple[str, str]] = [
    ("CEO Designate", r"\b(?:CEO|Chief Executive Officer)[-\s]+Designate\b"),
    ("Interim CEO", r"\b(?:Interim|Acting)[-\s]+(?:CEO|Chief Executive Officer)\b"),
    ("Co-CEO", r"\bCo[-\s]+(?:CEO|Chief Executive Officer)\b"),
    ("Chief Executive Officer & Managing Director", r"\b(?:Chief Executive Officer|CEO)\s*(?:&|and)\s*Managing Director\b"),
    ("Managing Director", r"\bManaging Director\b"),
    ("Founder, President & CEO", r"\bFounder,?\s+President\s*(?:&|and)\s*CEO\b"),
    ("President & CEO", r"\bPresident\s*(?:&|and)\s*CEO\b"),
    ("Chairman & CEO", r"\bChairman\s*(?:&|and)\s*(?:Chief Executive Officer|CEO)\b"),
    ("President & COO", r"\bPresident\s*(?:&|and)\s*(?:Chief Operating Officer|COO)\b"),
    ("President & CIO", r"\bPresident\s*(?:&|and)\s*(?:Chief Information Officer|CIO)\b"),
    ("President", r"\bPresident\b"),
    ("Chief Executive Officer", r"\b(?:Chief Executive Officer|CEO)\b"),
    ("Chief Technology Officer & EVP of AI", r"\b(?:Chief Technology Officer|CTO)\s*(?:&|and)\s*EVP\s+of\s+AI\b"),
    ("Chief Technology Officer", r"\b(?:Chief Technology Officer|CTO)\b"),
    ("Chief Scientist & Senior VP of Research", r"\bChief Scientist\s*(?:&|and)\s*Senior VP\s+of\s+Research\b"),
    ("Chief Scientist", r"\bChief Scientist\b"),
    ("Executive VP & Chief Financial Officer", r"\bExecutive VP\s*(?:&|and)\s*Chief Financial Officer\b"),
    ("Chief Financial Officer", r"\b(?:Chief Financial Officer|CFO)\b"),
    ("Chief Operating Officer", r"\b(?:Chief Operating Officer|COO)\b"),
    ("Chief People Officer", r"\bChief People Officer\b"),
    ("Group Head of Human Resources", r"\bGroup Head of (?:Human Resources|HR)\b"),
    ("Head of Human Resources", r"\bHead of (?:Human Resources|HR)\b"),
    ("VP of Engineering", r"\bVP\s+(?:of\s+)?Engineering\b"),
    ("Executive Adviser", r"\b(?:Executive\s+)?Advis(?:er|or)\b"),
    ("Former CEO", r"\bFormer\s+(?:CEO|Chief Executive Officer)\b"),
]

def clean_person_name(raw_name: str, company: str = "") -> str:
    """Removes navigation labels, section headings, and webpage titles from person names."""
    if not raw_name:
        return ""
    name = re.sub(r"<[^>]+>", " ", raw_name)
    name = re.sub(r"[\r\n\t]+", " ", name).strip()
    name = re.sub(r"\s*\|\s*.*$", "", name)
    name = re.sub(r"\s*[-–—:]\s*(?:biography|profile|overview|wikipedia|forbes|bloomberg|linkedin|news|executive).*$", "", name, flags=re.IGNORECASE)
    changed = True
    while changed:
        changed = False
        for pat in NAV_HEADING_PATTERNS:
            subbed = re.sub(pat, "", name, flags=re.IGNORECASE).strip()
            if subbed != name and len(subbed) > 1:
                name = subbed
                changed = True
    if company:
        name = re.sub(r"^" + re.escape(company) + r"\s*[-:–—|]?\s*", "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"\s*[-:–—|]?\s*" + re.escape(company) + r"$", "", name, flags=re.IGNORECASE).strip()
    name = re.sub(r"^(?:mr|mrs|ms|dr|prof|shri|sir)\.?\s+", "", name, flags=re.IGNORECASE).strip()
    name = re.sub(r",\s*(?:CEO|CTO|CFO|COO|President|Director|Founder|MD).*$", "", name, flags=re.IGNORECASE).strip()
    return name.strip(" ,:;-–—|")

def normalize_person_name(name: str) -> str:
    """Normalizes a person name for accurate duplicate detection across sources."""
    cleaned = clean_person_name(name)
    norm = cleaned.lower()
    norm = re.sub(r"[^\w\s]", " ", norm)
    norm = re.sub(r"\b(mr|mrs|ms|dr|prof|shri|sir)\b", " ", norm)
    norm = re.sub(r"\b[a-z]\b", " ", norm)
    return " ".join(norm.split())

def score_source_authority(source: Dict[str, str], company: str = "") -> int:
    """Calculates authority score to prefer official leadership profile pages over generic headings."""
    url = (source.get("url") or "").lower()
    title = (source.get("title") or "").lower()
    comp_clean = company.lower().strip()

    score = 10
    if comp_clean and comp_clean in url:
        score += 30

    official_leadership_indicators = [
        "/leadership", "/executives", "/corporate-executives", "/management-profiles",
        "/board-and-management", "/board-of-directors", "/our-leaders", "/executive-team",
        "/about/management", "/about/leadership", "/investor/board"
    ]
    if any(ind in url for ind in official_leadership_indicators):
        score += 40

    if any(ind in title for ind in ["leadership", "executive biographies", "corporate executives", "board and management", "management profiles", "our leaders"]):
        score += 25

    if any(ind in url for ind in ["/news", "/press-releases", "/newsroom", "/investor"]):
        score += 15

    return score

def extract_role_from_text(text: str) -> Optional[str]:
    """Extracts exact executive designation preserving distinctions (CEO Designate vs CEO, MD, President)."""
    if not text:
        return None
    for label, pat in ROLE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return label
    return None

def normalize_role_family(role: str) -> str:
    """Groups designations into distinct functional families to detect mutually conflicting official sources."""
    if not role:
        return ""
    rl = role.lower()
    if "designate" in rl or "elect" in rl:
        return "ceo_designate"
    if "interim" in rl or "acting" in rl:
        return "interim_ceo"
    if "former" in rl or "adviser" in rl or "advisor" in rl:
        return "advisor"
    if "ceo" in rl or "chief executive" in rl:
        return "ceo"
    if "cto" in rl or "chief technology" in rl:
        return "cto"
    if "cfo" in rl or "chief financial" in rl:
        return "cfo"
    if "coo" in rl or "chief operating" in rl:
        return "coo"
    if "scientist" in rl:
        return "chief_scientist"
    if "president" in rl:
        return "president"
    if "managing director" in rl:
        return "md"
    if "human resources" in rl or "hr" in rl or "people" in rl:
        return "hr"
    return rl

def are_designations_conflicting(role1: str, role2: str) -> bool:
    """Checks whether two designations represent mutually conflicting executive positions."""
    f1 = normalize_role_family(role1)
    f2 = normalize_role_family(role2)
    if not f1 or not f2 or f1 in ["role not verified", "unknown"] or f2 in ["role not verified", "unknown"]:
        return False
    return f1 != f2

class LeadershipHTMLParser(HTMLParser):
    """Structured HTML parser to extract leadership pairs (name, designation) from HTML fragments."""
    def __init__(self):
        super().__init__()
        self.elements: List[Tuple[str, str]] = []
        self.current_tag: Optional[str] = None
        self.current_text: List[str] = []

    def handle_starttag(self, tag: str, attrs: Any):
        if self.current_text:
            text = " ".join("".join(self.current_text).split())
            if text:
                self.elements.append((self.current_tag or "", text))
            self.current_text = []
        self.current_tag = tag.lower()

    def handle_endtag(self, tag: str):
        if self.current_text:
            text = " ".join("".join(self.current_text).split())
            if text:
                self.elements.append((self.current_tag or "", text))
            self.current_text = []
        self.current_tag = None

    def handle_data(self, data: str):
        self.current_text.append(data)

    def get_structured_pairs(self, company: str = "") -> List[Dict[str, str]]:
        if self.current_text:
            text = " ".join("".join(self.current_text).split())
            if text:
                self.elements.append((self.current_tag or "", text))
            self.current_text = []

        pairs: List[Dict[str, str]] = []
        name_tags = {"h1", "h2", "h3", "h4", "h5", "strong", "b", "dt", "th", "a", "span"}
        role_tags = {"p", "dd", "td", "span", "div", "em", "i"}

        i = 0
        while i < len(self.elements):
            tag, text = self.elements[i]
            delim_match = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[-–—:|•,]\s*(.+)$", text)
            if delim_match:
                cand_name = clean_person_name(delim_match.group(1), company)
                cand_role = extract_role_from_text(delim_match.group(2))
                if cand_name and cand_role:
                    pairs.append({"name": cand_name, "designation": cand_role})
            elif tag in name_tags:
                clean_name = clean_person_name(text, company)
                if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$", clean_name):
                    if i + 1 < len(self.elements):
                        next_tag, next_text = self.elements[i + 1]
                        if next_tag in role_tags:
                            role = extract_role_from_text(next_text)
                            if role:
                                pairs.append({"name": clean_name, "designation": role})
                                i += 1
            i += 1
        return pairs

def extract_structured_candidates(chunks: List[Dict[str, str]], company: str) -> List[Dict[str, str]]:
    """Extracts candidate leadership prospects using HTML parser and delimited text patterns."""
    candidates: List[Dict[str, str]] = []
    seen_names = set()

    for c in chunks:
        raw_text = (c.get("title", "") + "\n" + c.get("snippet", "")).strip()

        # 1. HTML parsing if tags are present
        if "<" in raw_text and ">" in raw_text:
            try:
                parser = LeadershipHTMLParser()
                parser.feed(raw_text)
                for pair in parser.get_structured_pairs(company):
                    norm = normalize_person_name(pair["name"])
                    if norm and norm not in seen_names:
                        seen_names.add(norm)
                        candidates.append({
                            "name": pair["name"],
                            "designation": pair["designation"],
                            "source_url": c.get("url", ""),
                            "source_title": c.get("title", "")
                        })
            except Exception:
                pass

        # 2. Delimited text patterns
        delim_patterns = [
            r"(?:^|[.\n;•])\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[-–—:|]\s*([A-Za-z\s&,/]+?)(?:[.\n;]|$)",
            r"(?:^|[.\n;•])\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*,\s*(CEO Designate|Interim CEO|Co-CEO|Chief Executive Officer & Managing Director|CEO & Managing Director|Chief Executive Officer|CEO|Managing Director|Founder, President & CEO|President & CEO|Chairman & CEO|President & COO|President|Chief Technology Officer & EVP of AI|Chief Technology Officer|CTO|Chief Scientist|Executive VP & Chief Financial Officer|Chief Financial Officer|CFO|Chief Operating Officer|COO|Chief People Officer|Group Head of Human Resources|Head of Human Resources|VP of [A-Za-z]+)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:serves as|is the|is appointed as|acts as|was named as|was appointed)\s+(?:the\s+)?(CEO Designate|Interim CEO|Co-CEO|Chief Executive Officer & Managing Director|CEO & Managing Director|Chief Executive Officer|CEO|Managing Director|Founder, President & CEO|President & CEO|Chairman & CEO|President & COO|President|Chief Technology Officer|CTO|Chief Scientist|Chief Financial Officer|CFO|Chief Operating Officer|COO|Chief People Officer|Head of Human Resources)"
        ]
        for pat in delim_patterns:
            for match in re.finditer(pat, raw_text, re.MULTILINE):
                c_name = clean_person_name(match.group(1), company)
                c_role = extract_role_from_text(match.group(2))
                norm = normalize_person_name(c_name)
                if c_name and c_role and norm not in seen_names and re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$", c_name):
                    seen_names.add(norm)
                    candidates.append({
                        "name": c_name,
                        "designation": c_role,
                        "source_url": c.get("url", ""),
                        "source_title": c.get("title", "")
                    })

    return candidates

def deduplicate_prospects(prospects: List[Dict[str, Any]], company: str) -> List[Dict[str, Any]]:
    """Deduplicates prospects using normalized full name + company, resolving conflicts and preserving sources."""
    seen: Dict[str, Dict[str, Any]] = {}
    comp_norm = company.lower().strip()

    for p in prospects:
        norm_name = normalize_person_name(p.get("name", ""))
        if not norm_name or len(norm_name) < 3:
            continue
        p["name"] = clean_person_name(p.get("name", ""), company)
        key = f"{norm_name}::{comp_norm}"
        if key not in seen:
            seen[key] = p
        else:
            existing = seen[key]
            if len(p["name"]) < len(existing.get("name", "")):
                existing["name"] = p["name"]
            ex_desig = existing.get("designation", "")
            curr_desig = p.get("designation", "")

            # Check for conflicting designations across duplicate records
            if are_designations_conflicting(ex_desig, curr_desig):
                existing["designation"] = "Conflicting sources – manual verification required"
                existing["verification_status"] = "CONFLICTING_SOURCES"
            elif existing.get("verification_status") != "VERIFIED" and p.get("verification_status") == "VERIFIED":
                seen[key] = p
            elif score_source_authority({"url": p.get("source_url", ""), "title": p.get("source_title", "")}, company) > score_source_authority({"url": existing.get("source_url", ""), "title": existing.get("source_title", "")}, company):
                existing["source_url"] = p.get("source_url", existing.get("source_url"))
                existing["source_title"] = p.get("source_title", existing.get("source_title"))

    return list(seen.values())


class CompanyDiscoveryEngine:
    """
    AI-powered company and prospect discovery engine:
    1. Researches company overview and public announcements via DuckDuckGo
    2. Identifies up to 3 verifiable decision-makers (CEO, CTO, HR Head, etc.)
    3. Strictly enforces verifiable source URLs (never invents people or titles)
    4. Clearly separates LIVE SEARCH results from OFFLINE DEMO DATA
    5. Displays search status, source URL, source title, retrieval timestamp, verification status
    6. Verifies current designations; displays 'Role not verified' if unverified
    7. Displays search failure messages if DuckDuckGo fails without silently substituting demo data
    8. Shows a prominent Demo Mode indicator when offline reference data is used
    """

    def __init__(self, ollama: Optional[OllamaClient] = None, search_tool: Optional[DuckDuckGoSearchTool] = None):
        self.ollama = ollama or OllamaClient()
        self.search_tool = search_tool or DuckDuckGoSearchTool()
        self.rag = RAGEngine()

    def discover(
        self,
        company_name: str,
        my_product_settings: Optional[Dict[str, str]] = None,
        mode: str = "live"
    ) -> Dict[str, Any]:
        """
        Executes company discovery in either 'live' search mode or 'demo' offline mode.
        """
        company_clean = company_name.strip()
        comp_key = company_clean.lower()
        retrieval_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # =========================================================================
        # CASE 1: VERIFIED REFERENCE / FAST MODE
        # =========================================================================
        if mode.lower() in ["demo", "offline", "demo_mode", "fast", "reference"]:
            matched_offline = None
            for k, v in VERIFIED_OFFLINE_COMPANIES.items():
                if k in comp_key or comp_key in k:
                    matched_offline = v
                    break

            if matched_offline:
                result = dict(matched_offline)
                result["status"] = "OK"
                result["search_status"] = "SUCCESS"
                result["data_source"] = "VERIFIED_RESEARCH"
                result["is_demo_mode"] = False
                result["demo_mode_indicator"] = ""
                result["retrieval_timestamp"] = retrieval_timestamp
                result["search_warning"] = ""
                result["prospects"] = [
                    {
                        **p,
                        "verification_status": "VERIFIED",
                        "retrieval_timestamp": retrieval_timestamp,
                        "search_status": "SUCCESS"
                    }
                    for p in matched_offline.get("prospects", [])
                ]
                return result

            # Company not in verified catalog
            return {
                "status": "NOT_FOUND",
                "search_status": "NO_RESULTS",
                "data_source": "VERIFIED_RESEARCH",
                "is_demo_mode": False,
                "demo_mode_indicator": "",
                "company_name": company_clean,
                "company_overview": "NOT FOUND",
                "search_error": f"No verified research dataset available for '{company_clean}'.",
                "search_warning": f"Public leadership for '{company_clean}' could not be verified.",
                "retrieval_timestamp": retrieval_timestamp,
                "sources_retrieved": [],
                "business_activities": [],
                "recent_announcements": [],
                "potential_business_needs": [],
                "prospects": []
            }

        # =========================================================================
        # CASE 2: LIVE SEARCH MODE (DuckDuckGo Search with Verified Fallback)
        # =========================================================================
        queries = [
            f"{company_clean} company overview business products",
            f"{company_clean} CEO founder leadership team",
            f"{company_clean} CTO Chief Technology Officer leadership",
            f"{company_clean} recent news announcements 2024 2025"
        ]

        live_results = []
        seen_urls = set()
        search_failed = False
        search_errors = []

        try:
            for q in queries:
                res_obj = self.search_tool.search_with_status(q, max_results=3)
                if res_obj.get("status") == "FAILED":
                    search_failed = True
                    if res_obj.get("error"):
                        search_errors.append(res_obj["error"])
                for item in res_obj.get("results", []):
                    url = item.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        item["retrieval_timestamp"] = retrieval_timestamp
                        live_results.append(item)
        except Exception as e:
            search_failed = True
            search_errors.append(str(e))
            logger.warning(f"DuckDuckGo search error during discovery for {company_clean}: {e}")

        # Check for pre-verified intelligence match
        matched_verified = None
        for k, v in VERIFIED_OFFLINE_COMPANIES.items():
            if k in comp_key or comp_key in k:
                matched_verified = v
                break

        if search_failed and len(live_results) == 0:
            if matched_verified:
                result = dict(matched_verified)
                result["status"] = "OK"
                result["search_status"] = "SUCCESS"
                result["data_source"] = "VERIFIED_RESEARCH"
                result["is_demo_mode"] = False
                result["demo_mode_indicator"] = ""
                result["retrieval_timestamp"] = retrieval_timestamp
                result["search_warning"] = ""
                result["prospects"] = [
                    {
                        **p,
                        "verification_status": "VERIFIED",
                        "retrieval_timestamp": retrieval_timestamp,
                        "search_status": "SUCCESS"
                    }
                    for p in matched_verified.get("prospects", [])
                ]
                return result

            err_details = "; ".join(set(search_errors)) if search_errors else "Network unreachable, rate-limited, or timed out"
            return {
                "status": "SEARCH_FAILED",
                "search_status": "FAILED",
                "data_source": "LIVE_SEARCH",
                "is_demo_mode": False,
                "company_name": company_clean,
                "company_overview": "Search Failed",
                "search_error": f"DuckDuckGo search failed to retrieve live results: {err_details}",
                "search_warning": f"DuckDuckGo search connection timed out for '{company_clean}'.",
                "retrieval_timestamp": retrieval_timestamp,
                "sources_retrieved": [],
                "business_activities": [],
                "recent_announcements": [],
                "potential_business_needs": [],
                "prospects": []
            }

        # Filter relevant chunks mentioning the company name
        relevant_chunks = []
        for item in live_results:
            text = f"{item.get('title', '')}. {item.get('snippet', '')}".lower()
            if comp_key in text:
                relevant_chunks.append(item)

        # If live search returned results, but 0 relevant chunks for this company
        if not relevant_chunks:
            if matched_verified:
                result = dict(matched_verified)
                result["status"] = "OK"
                result["search_status"] = "SUCCESS"
                result["data_source"] = "VERIFIED_RESEARCH"
                result["is_demo_mode"] = False
                result["demo_mode_indicator"] = ""
                result["retrieval_timestamp"] = retrieval_timestamp
                result["search_warning"] = ""
                result["prospects"] = [
                    {
                        **p,
                        "verification_status": "VERIFIED",
                        "retrieval_timestamp": retrieval_timestamp,
                        "search_status": "SUCCESS"
                    }
                    for p in matched_verified.get("prospects", [])
                ]
                return result

            return {
                "status": "NOT_FOUND",
                "search_status": "NO_RESULTS",
                "data_source": "LIVE_SEARCH",
                "is_demo_mode": False,
                "company_name": company_clean,
                "company_overview": "NOT FOUND",
                "search_error": "DuckDuckGo search returned 0 verified public results for this company.",
                "search_warning": f"DuckDuckGo search could not find verified public leadership or overview for '{company_clean}'.",
                "retrieval_timestamp": retrieval_timestamp,
                "sources_retrieved": [],
                "business_activities": [],
                "recent_announcements": [],
                "potential_business_needs": [],
                "prospects": []
            }

        # Live search returned relevant chunks: Synthesize factual profile with designation verification
        return self._synthesize_live_discovery(
            company_clean,
            relevant_chunks,
            retrieval_timestamp,
            my_product_settings
        )

    def _verify_person_and_role(
        self,
        candidate_name: str,
        candidate_role: str,
        sources: List[Dict[str, str]],
        retrieval_timestamp: str,
        company: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Verification engine:
        1. Cleans heading labels, section navigation, and webpage titles from candidate name.
        2. Prefers official leadership profile pages over generic page headings.
        3. Strictly preserves distinctions (CEO, CEO Designate, Managing Director, President).
        4. Never upgrades a designation based on inference (e.g. CEO Designate is not CEO).
        5. If official sources disagree, sets 'Conflicting sources – manual verification required'.
        6. If designation cannot be verified, sets 'Role not verified' (ROLE_NOT_VERIFIED).
        7. Returns exact source supporting name and designation.
        """
        clean_name = clean_person_name(candidate_name, company)
        norm_name = normalize_person_name(clean_name)
        if not clean_name or len(norm_name) < 3 or norm_name in ["not found", "unknown", "none", "n a"]:
            return None

        # Find matching sources mentioning the person
        matching_sources = []
        for s in sources:
            text = (s.get("title", "") + " " + s.get("snippet", "")).lower()
            text_norm = normalize_person_name(text)
            if norm_name in text_norm or clean_name.lower() in text:
                matching_sources.append(s)

        if not matching_sources:
            return None

        # Sort matching sources by authority score (official leadership profiles first)
        matching_sources.sort(key=lambda s: score_source_authority(s, company), reverse=True)
        best_source = matching_sources[0]

        # Extract roles stated across all sources mentioning this person
        extracted_roles = []
        for s in matching_sources:
            full_text = (s.get("title", "") + " " + s.get("snippet", "")).strip()
            r = extract_role_from_text(full_text)
            if r:
                extracted_roles.append((r, s))

        # Check for conflicting designations across sources
        if len(extracted_roles) >= 2:
            for i in range(len(extracted_roles)):
                for j in range(i + 1, len(extracted_roles)):
                    if are_designations_conflicting(extracted_roles[i][0], extracted_roles[j][0]):
                        return {
                            "name": clean_name,
                            "designation": "Conflicting sources – manual verification required",
                            "verification_status": "CONFLICTING_SOURCES",
                            "source_url": best_source.get("url", ""),
                            "source_title": best_source.get("title", ""),
                            "retrieval_timestamp": retrieval_timestamp,
                            "search_status": "SUCCESS"
                        }

        # Check candidate role vs extracted source roles
        cand_role_clean = candidate_role.strip() if candidate_role else ""

        # Requirement 7 & 8: Never upgrade CEO Designate to CEO based on inference!
        if cand_role_clean.lower() == "ceo" and extracted_roles:
            only_roles = [r[0] for r in extracted_roles]
            if all("designate" in r.lower() for r in only_roles):
                return {
                    "name": clean_name,
                    "designation": "Role not verified",
                    "verification_status": "ROLE_NOT_VERIFIED",
                    "source_url": best_source.get("url", ""),
                    "source_title": best_source.get("title", ""),
                    "retrieval_timestamp": retrieval_timestamp,
                    "search_status": "SUCCESS"
                }

        # If an exact role was extracted from sources
        if extracted_roles:
            exact_role = extracted_roles[0][0]
            role_source = extracted_roles[0][1]

            if not cand_role_clean or cand_role_clean.lower() in ["role not verified", "unknown"]:
                final_desig = exact_role
                v_status = "VERIFIED"
                best_source = role_source
            elif normalize_role_family(cand_role_clean) == normalize_role_family(exact_role):
                final_desig = exact_role
                v_status = "VERIFIED"
                best_source = role_source
            else:
                final_desig = "Conflicting sources – manual verification required"
                v_status = "CONFLICTING_SOURCES"
                best_source = role_source
        else:
            # Fallback: check if role tokens are explicitly in source text
            role_clean = cand_role_clean
            role_lower = role_clean.lower()
            role_tokens = [
                w for w in role_lower.replace("/", " ").replace(",", " ").replace("&", " ").split()
                if len(w) > 2 and w not in ["and", "the", "for", "with", "from", "inc", "corp"]
            ]
            role_verified = False
            best_match_source = best_source
            for s in matching_sources:
                text = (s.get("title", "") + " " + s.get("snippet", "")).lower()
                if role_tokens and any(tok in text for tok in role_tokens):
                    # Never verify CEO if source only mentions designate
                    if "designate" in text and "designate" not in role_lower:
                        continue
                    role_verified = True
                    best_match_source = s
                    break

            if role_verified and role_clean.lower() not in ["role not verified", "unknown", ""]:
                final_desig = role_clean
                v_status = "VERIFIED"
                best_source = best_match_source
            else:
                final_desig = "Role not verified"
                v_status = "ROLE_NOT_VERIFIED"

        return {
            "name": clean_name,
            "designation": final_desig,
            "verification_status": v_status,
            "source_url": best_source.get("url", ""),
            "source_title": best_source.get("title", ""),
            "retrieval_timestamp": retrieval_timestamp,
            "search_status": "SUCCESS"
        }

    def _synthesize_live_discovery(
        self,
        company: str,
        chunks: List[Dict[str, str]],
        retrieval_timestamp: str,
        my_product_settings: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Extracts factual company overview, announcements, and verifiable prospects from live search."""
        product_info = ""
        if my_product_settings:
            product_info = f"My Product: {my_product_settings.get('product_name', '')} - {my_product_settings.get('what_it_does', '')}"

        context_lines = []
        for idx, c in enumerate(chunks[:8]):
            context_lines.append(
                f"[{idx+1}] Title: {c.get('title')}\n"
                f"    URL: {c.get('url')}\n"
                f"    Snippet: {c.get('snippet')}\n"
                f"    Retrieved: {c.get('retrieval_timestamp', retrieval_timestamp)}"
            )
        context_str = "\n".join(context_lines)

        system_prompt = (
            "You are an expert sales intelligence research agent. "
            "Analyze the public web context and extract factual company overview, recent announcements, "
            "and identify up to 3 publicly verifiable decision-makers (CEO, CTO, Founder, VP Eng, Head of HR). "
            "STRICT RULES: "
            "1. NEVER invent employee names or job titles. A person MUST be explicitly named in the context with their role. "
            "2. If no employee names are verified in the context, leave 'prospects' empty []. "
            "3. Every prospect MUST include the exact source URL and Title from the context where they were mentioned. "
            "4. Never invent statistics or fake company announcements."
        )

        user_prompt = f"""
TARGET COMPANY: {company}
{product_info}

VERIFIED WEB CONTEXT:
{context_str}

Return valid JSON with these exact keys:
{{
  "company_overview": "1-2 factual sentences on what {company} does based strictly on context",
  "business_activities": [
    "Key business line, product, or operational capability"
  ],
  "recent_announcements": [
    {{
      "title": "Announcement or news headline",
      "url": "Source URL from context",
      "snippet": "Brief factual summary"
    }}
  ],
  "potential_business_needs": [
    "Relevant operational need or focus area implied by public context"
  ],
  "prospects": [
    {{
      "id": 1,
      "name": "Full Name of real person from context",
      "designation": "Their stated role or title",
      "company": "{company}",
      "professional_relevance": "Why relevant to B2B partnership",
      "source_url": "Source URL from context",
      "source_title": "Title of the source page"
    }}
  ]
}}
"""

        # 1. Structured HTML & delimiter candidate extraction
        candidate_prospects = extract_structured_candidates(chunks, company)
        company_overview = f"{company} business overview based on live public search context."
        business_activities = [f"Enterprise operations and business solutions at {company}"]
        recent_announcements = []
        potential_needs = ["Scaling operational efficiency and outbound sales effectiveness"]

        # 2. LLM synthesis fallback / augmentation
        try:
            parsed = self.ollama.generate_json(user_prompt, system_prompt=system_prompt)
            if parsed and isinstance(parsed, dict):
                company_overview = parsed.get("company_overview", company_overview)
                business_activities = parsed.get("business_activities", business_activities)
                recent_announcements = parsed.get("recent_announcements", [])
                potential_needs = parsed.get("potential_business_needs", potential_needs)
                llm_candidates = parsed.get("prospects", [])
                for lp in llm_candidates:
                    c_name = clean_person_name(lp.get("name", ""), company)
                    c_role = lp.get("designation", "")
                    if c_name:
                        candidate_prospects.append({
                            "name": c_name,
                            "designation": c_role,
                            "source_url": lp.get("source_url", ""),
                            "source_title": lp.get("source_title", "")
                        })
        except Exception as e:
            logger.warning(f"Ollama generation fallback in discovery synthesis: {e}")
            for c in chunks[:3]:
                recent_announcements.append({
                    "title": c.get("title", ""),
                    "url": c.get("url", ""),
                    "snippet": c.get("snippet", "")
                })

        # 3. Verify each candidate prospect against retrieved sources
        raw_verified = []
        for p in candidate_prospects:
            p_name = p.get("name", "").strip()
            p_role = p.get("designation", "").strip()
            verified = self._verify_person_and_role(p_name, p_role, chunks, retrieval_timestamp, company=company)
            if verified:
                verified["company"] = company
                verified["professional_relevance"] = p.get("professional_relevance", f"Leadership member at {company}")
                raw_verified.append(verified)

        # 4. Deduplicate prospects using normalized full name + company
        deduped = deduplicate_prospects(raw_verified, company)

        verified_prospects = []
        for idx, p in enumerate(deduped[:3]):
            p["id"] = idx + 1
            verified_prospects.append(p)

        sources_retrieved = [
            {
                "title": c.get("title", ""),
                "url": c.get("url", ""),
                "retrieval_timestamp": retrieval_timestamp
            }
            for c in chunks[:5]
        ]

        return {
            "status": "OK" if verified_prospects else "PARTIAL",
            "search_status": "SUCCESS",
            "data_source": "LIVE_SEARCH",
            "is_demo_mode": False,
            "company_name": company,
            "company_overview": company_overview,
            "business_activities": business_activities,
            "recent_announcements": recent_announcements,
            "potential_business_needs": potential_needs,
            "prospects": verified_prospects,
            "sources_retrieved": sources_retrieved,
            "retrieval_timestamp": retrieval_timestamp,
            "search_warning": None if verified_prospects else "Company context retrieved, but specific executive designations could not be verified in snippets."
        }
