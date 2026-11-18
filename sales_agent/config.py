import os
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class SenderProfile:
    name: str = "My Name"
    role: str = "Founder"
    company: str = "My Company"
    product_name: str = "My Product"
    what_it_does: str = "Automates B2B sales research and crafts personalized multi-touch outreach."
    calendly_link: str = ""

@dataclass
class SequenceTouchRule:
    touch_number: int
    channel: str  # "email" or "linkedin"
    delay_days: int
    intent: str
    description: str

DEFAULT_SEQUENCE: List[SequenceTouchRule] = [
    SequenceTouchRule(
        touch_number=1,
        channel="email",
        delay_days=0,
        intent="Researched Observation & Relevance Hook",
        description="Reference a specific public event, product launch, hiring initiative, or company milestone to demonstrate genuine research and relevance."
    ),
    SequenceTouchRule(
        touch_number=2,
        channel="linkedin",
        delay_days=3,
        intent="Insight & Light Engagement",
        description="Share a tailored, high-value insight or observation relevant to their specific role and business challenges without being overly pushy."
    ),
    SequenceTouchRule(
        touch_number=3,
        channel="email",
        delay_days=7,
        intent="Social Proof & Case Study",
        description="Present a concrete case study or data point showing how a similar company achieved tangible ROI or overcame a common industry hurdle."
    ),
    SequenceTouchRule(
        touch_number=4,
        channel="email",
        delay_days=12,
        intent="Polite Breakup & Open Door",
        description="Respectfully acknowledge their busy schedule, leave value on the table, and offer a no-friction invitation to connect whenever timing is better."
    )
]

@dataclass
class AppConfig:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
    db_path: str = os.getenv("DB_PATH", "outreach_pipeline.db")
    max_search_results: int = 5
    sender: SenderProfile = field(default_factory=SenderProfile)
    sequence_rules: List[SequenceTouchRule] = field(default_factory=lambda: DEFAULT_SEQUENCE)

config = AppConfig()
