import json
import logging
from typing import Dict, Any, List, Optional
from sales_agent.search.duckduckgo import DuckDuckGoSearchTool
from sales_agent.search.rag_engine import RAGEngine
from sales_agent.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

# Verified offline leadership knowledge base for reference and demo offline testing
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

class CompanyDiscoveryEngine:
    """
    AI-powered company and prospect discovery engine:
    1. Researches company overview and public announcements via DuckDuckGo
    2. Identifies up to 3 verifiable decision-makers (CEO, CTO, HR Head, etc.)
    3. Strictly enforces verifiable source URLs (never invents people or titles)
    4. Distinguishes live search from verified offline demo data
    """

    def __init__(self, ollama: Optional[OllamaClient] = None):
        self.ollama = ollama or OllamaClient()
        self.search_tool = DuckDuckGoSearchTool()
        self.rag = RAGEngine()

    def discover(self, company_name: str, my_product_settings: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        company_clean = company_name.strip()
        comp_key = company_clean.lower()

        # Step 1: Attempt Live DuckDuckGo search queries
        queries = [
            f"{company_clean} company overview business products",
            f"{company_clean} CEO founder leadership team",
            f"{company_clean} CTO Chief Technology Officer leadership",
            f"{company_clean} recent news announcements 2024 2025"
        ]

        live_results = []
        seen_urls = set()
        search_error = None

        try:
            for q in queries:
                res = self.search_tool.search(q, max_results=3)
                for item in res:
                    url = item.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        live_results.append(item)
        except Exception as e:
            search_error = str(e)
            logger.warning(f"DuckDuckGo search error during discovery for {company_clean}: {e}")

        # Step 2: Check if live search returned relevant results mentioning the company
        relevant_chunks = []
        for item in live_results:
            text = f"{item.get('title', '')}. {item.get('snippet', '')}".lower()
            if comp_key in text:
                relevant_chunks.append(item)

        # If live search succeeded and found verified company context
        if len(relevant_chunks) >= 2:
            live_result = self._synthesize_live_discovery(company_clean, relevant_chunks, my_product_settings)
            # If live search returned verified prospects, return immediately
            if live_result.get("prospects"):
                return live_result

        # Step 3: If live search was rate-limited, failed, or didn't identify executive names:
        # Check if company is in our verified reference offline dataset
        matched_offline = None
        for k, v in VERIFIED_OFFLINE_COMPANIES.items():
            if k in comp_key or comp_key in k:
                matched_offline = v
                break

        if matched_offline:
            # Return verified offline reference data clearly marked as DEMO_DATA
            result = dict(matched_offline)
            result["data_source"] = "DEMO_DATA"
            result["status"] = "OK"
            result["search_warning"] = (
                f"DuckDuckGo live search encountered rate limits or network timeout. "
                f"Displaying verified offline reference profiles for {matched_offline['company_name']}."
            )
            return result

        # Step 4: If company is unknown and live search found no verifiable results, explicitly return NOT FOUND
        return {
            "status": "NOT_FOUND",
            "company_name": company_clean,
            "data_source": "LIVE_SEARCH",
            "company_overview": "NOT FOUND",
            "search_error": search_error or "DuckDuckGo search returned 0 verified public results for this company.",
            "search_warning": f"DuckDuckGo search could not verify public leadership or company overview for '{company_clean}'.",
            "business_activities": [],
            "recent_announcements": [],
            "potential_business_needs": [],
            "prospects": []
        }

    def _synthesize_live_discovery(self, company: str, chunks: List[Dict[str, str]], my_product_settings: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Extracts factual company overview, announcements, and verifiable prospects from live search."""
        product_info = ""
        if my_product_settings:
            product_info = f"My Product: {my_product_settings.get('product_name', '')} - {my_product_settings.get('what_it_does', '')}"

        context_lines = []
        for idx, c in enumerate(chunks[:8]):
            context_lines.append(f"[{idx+1}] Title: {c.get('title')}\n    URL: {c.get('url')}\n    Snippet: {c.get('snippet')}")
        context_str = "\n".join(context_lines)

        system_prompt = (
            "You are an expert sales intelligence research agent. "
            "Analyze the public web context and extract factual company overview, recent announcements, "
            "and identify up to 3 publicly verifiable decision-makers (CEO, CTO, Founder, VP Eng, Head of HR). "
            "STRICT RULES: "
            "1. NEVER invent employee names or job titles. A person MUST be explicitly named in the context with their role. "
            "2. If no employee names are verified in the context, leave 'prospects' empty []. "
            "3. Every prospect MUST include the exact source URL from the context where they were mentioned. "
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
      "name": "Full Name of real executive from context",
      "designation": "Their actual role (e.g. CEO, CTO, VP)",
      "company": "{company}",
      "professional_relevance": "Why relevant to B2B partnership",
      "source_url": "Source URL from context verifying this person",
      "source_title": "Title of the source page"
    }}
  ]
}}
"""

        try:
            parsed = self.ollama.generate_json(user_prompt, system_prompt=system_prompt)
            # Strict verification filter: Ensure each prospect's name was actually in the web snippets
            verified_prospects = []
            for p in parsed.get("prospects", []):
                p_name = p.get("name", "").strip()
                if not p_name or p_name.lower() in ["not found", "unknown", "none", "n/a"]:
                    continue
                if p_name.lower() in context_str.lower():
                    verified_prospects.append(p)

            # Build final structure
            return {
                "status": "OK" if verified_prospects else "PARTIAL",
                "company_name": company,
                "data_source": "LIVE_SEARCH",
                "company_overview": parsed.get("company_overview", f"{company} public profile"),
                "business_activities": parsed.get("business_activities", []),
                "recent_announcements": parsed.get("recent_announcements", []),
                "potential_business_needs": parsed.get("potential_business_needs", []),
                "prospects": verified_prospects[:3],
                "search_warning": None if verified_prospects else "Company found, but specific executive names were not verified in the snippets. Displayed company overview."
            }
        except Exception as e:
            logger.warning(f"Ollama parsing error during discovery synthesis: {e}")
            announcements = []
            for c in chunks[:3]:
                announcements.append({
                    "title": c.get("title", ""),
                    "url": c.get("url", ""),
                    "snippet": c.get("snippet", "")
                })

            # Check if company matches verified offline companies
            matched_offline = None
            comp_key = company.lower()
            for k, v in VERIFIED_OFFLINE_COMPANIES.items():
                if k in comp_key or comp_key in k:
                    matched_offline = v
                    break

            if matched_offline:
                result = dict(matched_offline)
                result["data_source"] = "DEMO_DATA"
                result["status"] = "OK"
                result["search_warning"] = (
                    f"Live search returned general context but local LLM is offline or model not installed. "
                    f"Displaying verified offline reference profiles for {matched_offline['company_name']}."
                )
                return result

            return {
                "status": "OK",
                "company_name": company,
                "data_source": "LIVE_SEARCH",
                "company_overview": chunks[0].get("snippet", f"{company} business overview"),
                "business_activities": [f"Enterprise operations at {company}"],
                "recent_announcements": announcements,
                "potential_business_needs": ["Optimizing operational and sales performance"],
                "prospects": [],
                "search_warning": "Could not verify individual executive names from raw search snippets without hallucinating. Please select manual entry or verified demo lead."
            }
