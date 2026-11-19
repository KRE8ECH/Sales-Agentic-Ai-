import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sales_agent.config import config

DEMO_LEADS_DATA = {
    "founder": {
        "name": "Alex Rivera",
        "company": "KiteFlow AI",
        "role": "Founder & CEO",
        "email": "alex@kiteflow.ai",
        "industry": "Developer Tools & AI",
        "dossier": {
            "company_overview": "KiteFlow AI builds autonomous QA and regression testing agents for high-velocity software engineering teams.",
            "search_status": "DEMO_REALISTIC_CONTEXT",
            "search_warning": None,
            "facts": [
                {
                    "fact": "Raised $4.2M Seed funding led by Amplify Partners in January 2025 to scale autonomous test execution.",
                    "source_url": "https://techcrunch.com/2025/01/kiteflow-seed",
                    "source_title": "TechCrunch: KiteFlow AI Secures $4.2M Seed"
                },
                {
                    "fact": "Surpassed 12,000 GitHub stars and 50 enterprise pilots within 4 months of releasing their open-source SDK.",
                    "source_url": "https://github.com/kiteflow-ai/agent-sdk",
                    "source_title": "GitHub: KiteFlow Open Source Agent SDK"
                },
                {
                    "fact": "Keynote speaker at AI Engineer World's Fair on multi-agent test evaluation and deterministic LLM CI/CD.",
                    "source_url": "https://ai.engineer/talks/alex-rivera",
                    "source_title": "AI Engineer World's Fair 2025 Session Roster"
                },
                {
                    "fact": "Currently expanding founding engineering and solutions architecture teams in San Francisco and remotely.",
                    "source_url": "https://kiteflow.ai/careers",
                    "source_title": "KiteFlow AI Careers Portal"
                }
            ],
            "role_priorities": [
                "Acquiring high-intent engineering leads and enterprise design partners.",
                "Balancing product engineering roadmap with founder-led sales outreach."
            ],
            "potential_pain_points": [
                "Limited bandwidth to manually personalize outreach to prospective CTOs and VP Eng prospects.",
                "High noise-to-signal ratio from generic cold inbound."
            ],
            "tailored_hooks": [
                "Congratulating on the $4.2M Amplify Partners seed round and explosive GitHub momentum.",
                "Connecting on scaling outbound enterprise developer relationships without hiring an army of SDRs."
            ],
            "confidence_score": 0.95
        }
    },
    "hr": {
        "name": "Maya Patel",
        "company": "Lumina Health",
        "role": "Chief People Officer",
        "email": "maya.patel@luminahealth.com",
        "industry": "HealthTech & Digital Health",
        "dossier": {
            "company_overview": "Lumina Health provides digital healthcare operations and tele-health infrastructure across hospitals and clinics.",
            "search_status": "DEMO_REALISTIC_CONTEXT",
            "search_warning": None,
            "facts": [
                {
                    "fact": "Scaled distributed organization from 140 to 380 employees across 12 countries over the past 14 months.",
                    "source_url": "https://luminahealth.com/press/global-growth",
                    "source_title": "Lumina Press: Scaling Global Workforce"
                },
                {
                    "fact": "Named among Top 50 Healthcare HR Leaders 2024 for pioneering transparent remote compensation and mobility tracks.",
                    "source_url": "https://healthcare-executive.org/top-hr-leaders",
                    "source_title": "Healthcare Executive: 2024 HR Leaders"
                },
                {
                    "fact": "Partnered with premier medical networks to launch clinician wellness and retention programs.",
                    "source_url": "https://luminahealth.com/news/clinical-partnerships",
                    "source_title": "Lumina Health Newsroom"
                },
                {
                    "fact": "Rolling out unified engineering and clinical hiring standards for upcoming Q3 expansion.",
                    "source_url": "https://linkedin.com/pulse/lumina-talent-scaling",
                    "source_title": "LinkedIn Pulse: Talent Scaling at Lumina"
                }
            ],
            "role_priorities": [
                "Accelerating technical and clinical recruitment while maintaining high hiring bar.",
                "Reducing recruiter manual workload and improving candidate outreach conversion."
            ],
            "potential_pain_points": [
                "Recruiters spending hours writing repetitive cold candidate emails.",
                "Maintaining authentic communication at rapid scale."
            ],
            "tailored_hooks": [
                "Acknowledging the recent 140 to 380 employee scaling milestone.",
                "Discussing how automated yet authentic outreach reduces recruiter coordination fatigue."
            ],
            "confidence_score": 0.95
        }
    },
    "cto": {
        "name": "Marcus Sterling",
        "company": "Apex Payments",
        "role": "Chief Technology Officer",
        "email": "marcus.sterling@apexpayments.io",
        "industry": "Fintech & Payments Infrastructure",
        "dossier": {
            "company_overview": "Apex Payments builds high-throughput, low-latency transaction processing APIs and multi-currency ledgers.",
            "search_status": "DEMO_REALISTIC_CONTEXT",
            "search_warning": None,
            "facts": [
                {
                    "fact": "Completed zero-downtime multi-region cloud migration processing 45M daily transactions at sub-15ms latency.",
                    "source_url": "https://apexpayments.io/engineering/ledger-architecture",
                    "source_title": "Apex Engineering Blog: Zero Downtime Ledger"
                },
                {
                    "fact": "Achieved Level 1 PCI-DSS and SOC 2 Type II re-certification across AWS and GCP infrastructure.",
                    "source_url": "https://apexpayments.io/security/compliance-2025",
                    "source_title": "Apex Security & Compliance Report"
                },
                {
                    "fact": "Open-sourced high-throughput event streaming connector for Kafka and Apache Flink with over 2,000 forks.",
                    "source_url": "https://github.com/apexpayments/flink-kafka-connector",
                    "source_title": "GitHub: Apex Flink Kafka Connector"
                },
                {
                    "fact": "Announced direct settlement API integration with major international banking rails.",
                    "source_url": "https://fintechnews.com/apex-stripe-integration",
                    "source_title": "FinTech News: Apex Payments International Rail Expansion"
                }
            ],
            "role_priorities": [
                "Ensuring 99.999% system uptime and sub-15ms transaction execution under high load.",
                "Automating infrastructure operations and evaluating mission-critical technology partners."
            ],
            "potential_pain_points": [
                "Inundated with generic, spammy sales emails that show zero understanding of payments architecture.",
                "Strict compliance and vendor vetting requirements."
            ],
            "tailored_hooks": [
                "Commending their zero-downtime ledger migration architecture.",
                "Reaching out with zero fluff, acknowledging their 45M daily transaction scale."
            ],
            "confidence_score": 0.95
        }
    }
}

DEFAULT_PRODUCT_FEATURES = [
    {
        "id": "feat_rag_recon",
        "name": "Autonomous RAG Market Recon",
        "headline": "Real-Time Company & Leadership Intelligence",
        "description": "Scrapes DuckDuckGo live web search to verify executive leadership, recent funding milestones, and product announcements before outreach.",
        "target_trigger": "Companies scaling AI infrastructure, launching hardware, or expanding leadership teams.",
        "pitch_angle": "Cite verified public news with 100% accuracy to establish instant executive credibility."
    },
    {
        "id": "feat_direct_email",
        "name": "1-Click Direct Email Dispatch",
        "headline": "Native Gmail & Mailto Workflow Without API Keys",
        "description": "Instant handoff to Gmail Compose or local mail client with pre-filled verified prospect addresses, tailored subject lines, and formatted copy.",
        "target_trigger": "High-velocity sales teams, founders, and SDRs tired of SMTP setup hurdles and deliverability penalties.",
        "pitch_angle": "Empower your team to review and dispatch outreach in 1-click directly from their authentic inbox, ensuring 40%+ open rates."
    },
    {
        "id": "feat_crm_state_machine",
        "name": "Finite State Pipeline Governance",
        "headline": "Zero-Loss Lead Progression & Compliance Tracking",
        "description": "Strict state transitions (Discovered → Researched → Drafted → Approved → In Sequence → Converted) preventing duplicate touches.",
        "target_trigger": "Enterprise teams losing track of prospect touchpoints or requiring strict human authorization before sending.",
        "pitch_angle": "Gain total audit transparency with an immutable reasoning trail and mandatory human authorization checkpoints for every touch."
    },
    {
        "id": "feat_cadence_sequencer",
        "name": "Multi-Touch Cadence Sequencer",
        "headline": "Omnichannel Email & LinkedIn Cadence Scheduling",
        "description": "Orchestrates multi-day follow-up touches (Observation, Light Engagement, Case Study Proof, Polite Breakup) with adaptive delay controls.",
        "target_trigger": "B2B SaaS companies with multi-stakeholder deals requiring persistent, respectful multi-week follow-up.",
        "pitch_angle": "Keep prospects engaged across 4 progressive touches without manual tracking, lifting reply rates by 3.4x."
    }
]

class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Settings Table for "My Product"
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)

            # Leads Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                company TEXT NOT NULL,
                role TEXT,
                linkedin_url TEXT,
                industry TEXT,
                status TEXT DEFAULT 'NEW',
                current_touch INTEGER DEFAULT 0,
                next_touch_date TEXT,
                research_dossier TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """)

            # Sequence Touches Table (default AWAITING_APPROVAL)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS touches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                touch_number INTEGER NOT NULL,
                channel TEXT NOT NULL,
                subject TEXT,
                content TEXT NOT NULL,
                researched_evidence_used TEXT,
                status TEXT DEFAULT 'AWAITING_APPROVAL',
                sent_at TEXT,
                created_at TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """)

            # Inbound Replies Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                in_response_to_touch INTEGER,
                reply_text TEXT NOT NULL,
                classification TEXT,
                confidence REAL,
                sentiment TEXT,
                extracted_intent TEXT,
                received_at TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """)

            # Decision Audit Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                decision TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                metadata_json TEXT,
                timestamp TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """)

            # Set default product settings if not existing
            cursor.execute("SELECT COUNT(*) FROM settings")
            if cursor.fetchone()[0] == 0:
                defaults = [
                    ("product_name", "OutreachIQ"),
                    ("what_it_does", "AI assistant that researches enterprise leads and drafts personalized multi-touch sequences"),
                    ("sender_name", "Alex Rivera"),
                    ("company_name", "NextGen Solutions"),
                    ("calendly_link", "https://cal.com/nextgen/demo"),
                    ("product_features", json.dumps(DEFAULT_PRODUCT_FEATURES))
                ]
                cursor.executemany("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", defaults)

            conn.commit()

    # Product Settings operations
    def get_product_settings(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            settings = {
                "product_name": "OutreachIQ",
                "what_it_does": "AI assistant that researches enterprise leads and drafts personalized multi-touch sequences",
                "sender_name": "Alex Rivera",
                "company_name": "NextGen Solutions",
                "calendly_link": "",
                "product_features": json.dumps(DEFAULT_PRODUCT_FEATURES)
            }
            for row in rows:
                settings[row["key"]] = row["value"]
            if not settings.get("product_features"):
                settings["product_features"] = json.dumps(DEFAULT_PRODUCT_FEATURES)
            return settings

    def save_product_settings(self, settings: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for k, v in settings.items():
                if isinstance(v, (list, dict)):
                    val_str = json.dumps(v)
                else:
                    val_str = str(v if v is not None else "")
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, val_str))
            conn.commit()

    # Lead operations
    def create_lead(self, name: str, company: str, role: str = "", email: str = "", linkedin_url: str = "", industry: str = "") -> int:
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leads (name, email, company, role, linkedin_url, industry, status, current_touch, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'NEW', 0, ?, ?)
            """, (name, email, company, role, linkedin_url, industry, now, now))
            conn.commit()
            return cursor.lastrowid

    def get_lead(self, lead_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
            row = cursor.fetchone()
            if row:
                lead = dict(row)
                if lead["research_dossier"]:
                    try:
                        lead["research_dossier"] = json.loads(lead["research_dossier"])
                    except Exception:
                        pass
                return lead
            return None

    def list_leads(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                lead = dict(row)
                if lead["research_dossier"]:
                    try:
                        lead["research_dossier"] = json.loads(lead["research_dossier"])
                    except Exception:
                        pass
                results.append(lead)
            return results

    def update_lead_status(self, lead_id: int, status: str, current_touch: Optional[int] = None, next_touch_date: Optional[str] = None):
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if current_touch is not None:
                cursor.execute("""
                    UPDATE leads 
                    SET status = ?, current_touch = ?, next_touch_date = ?, updated_at = ?
                    WHERE id = ?
                """, (status, current_touch, next_touch_date, now, lead_id))
            else:
                cursor.execute("""
                    UPDATE leads 
                    SET status = ?, next_touch_date = COALESCE(?, next_touch_date), updated_at = ?
                    WHERE id = ?
                """, (status, next_touch_date, now, lead_id))
            conn.commit()

    def save_research_dossier(self, lead_id: int, dossier: Dict[str, Any]):
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE leads 
                SET research_dossier = ?, status = 'DRAFT_PENDING', updated_at = ?
                WHERE id = ?
            """, (json.dumps(dossier, ensure_ascii=False), now, lead_id))
            conn.commit()

    # Touch operations
    def save_touch(self, lead_id: int, touch_number: int, channel: str, subject: str, content: str, evidence: str) -> int:
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO touches (lead_id, touch_number, channel, subject, content, researched_evidence_used, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'AWAITING_APPROVAL', ?)
            """, (lead_id, touch_number, channel, subject, content, evidence, now))
            conn.commit()
            return cursor.lastrowid

    def approve_and_send_touch(self, touch_id: int) -> Dict[str, Any]:
        """Human approval action: marks touch as SENT and advances lead state."""
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM touches WHERE id = ?", (touch_id,))
            touch_row = cursor.fetchone()
            if not touch_row:
                raise ValueError(f"Touch #{touch_id} not found.")
            touch = dict(touch_row)

            # Update touch status
            cursor.execute("""
                UPDATE touches SET status = 'SENT', sent_at = ? WHERE id = ?
            """, (now, touch_id))

            # Update lead state
            cursor.execute("""
                UPDATE leads SET status = 'IN_SEQUENCE', current_touch = ?, updated_at = ? WHERE id = ?
            """, (touch["touch_number"], now, touch["lead_id"]))

            conn.commit()

            touch["status"] = "SENT"
            touch["sent_at"] = now

        # Log human approval in audit logs
        self.log_decision(
            lead_id=touch["lead_id"],
            stage="APPROVAL",
            decision="TOUCH_APPROVED_AND_SENT",
            reasoning=f"Human user approved Touch #{touch['touch_number']} ({touch['channel'].upper()}). Simulated dispatch recorded.",
            metadata={"touch_id": touch_id, "subject": touch.get("subject", "")}
        )

        return touch

    def get_touch(self, touch_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM touches WHERE id = ?", (touch_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_touches_for_lead(self, lead_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM touches WHERE lead_id = ? ORDER BY touch_number ASC", (lead_id,))
            return [dict(row) for row in cursor.fetchall()]

    # Reply operations
    def record_reply(self, lead_id: int, reply_text: str, in_response_to: int, classification: str, confidence: float, sentiment: str, intent: str) -> int:
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO replies (lead_id, in_response_to_touch, reply_text, classification, confidence, sentiment, extracted_intent, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (lead_id, in_response_to, reply_text, classification, confidence, sentiment, intent, now))
            conn.commit()
            return cursor.lastrowid

    def get_replies_for_lead(self, lead_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM replies WHERE lead_id = ? ORDER BY received_at ASC", (lead_id,))
            return [dict(row) for row in cursor.fetchall()]

    # Decision Log operations
    def log_decision(self, lead_id: int, stage: str, decision: str, reasoning: str, metadata: Optional[Dict[str, Any]] = None):
        now = datetime.utcnow().isoformat()
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO decision_logs (lead_id, stage, decision, reasoning, metadata_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (lead_id, stage, decision, reasoning, meta_str, now))
            conn.commit()

    def get_decision_logs(self, lead_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if lead_id:
                cursor.execute("SELECT * FROM decision_logs WHERE lead_id = ? ORDER BY timestamp DESC", (lead_id,))
            else:
                cursor.execute("SELECT * FROM decision_logs ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            logs = []
            for row in rows:
                item = dict(row)
                if item["metadata_json"]:
                    try:
                        item["metadata_json"] = json.loads(item["metadata_json"])
                    except Exception:
                        pass
                logs.append(item)
            return logs

    # Demo lead creation
    def create_demo_lead(self, demo_type: str = "founder") -> int:
        demo = DEMO_LEADS_DATA.get(demo_type.lower()) or DEMO_LEADS_DATA["founder"]
        lead_id = self.create_lead(
            name=demo["name"],
            company=demo["company"],
            role=demo["role"],
            email=demo["email"],
            industry=demo["industry"]
        )
        self.save_research_dossier(lead_id, demo["dossier"])
        return lead_id
