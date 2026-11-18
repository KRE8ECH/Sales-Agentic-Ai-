import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sales_agent.config import config

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

            # Sequence Touches Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS touches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                touch_number INTEGER NOT NULL,
                channel TEXT NOT NULL,
                subject TEXT,
                content TEXT NOT NULL,
                researched_evidence_used TEXT,
                status TEXT DEFAULT 'DRAFTED',
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
                SET research_dossier = ?, status = 'RESEARCHED', updated_at = ?
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
                VALUES (?, ?, ?, ?, ?, ?, 'DRAFTED', ?)
            """, (lead_id, touch_number, channel, subject, content, evidence, now))
            conn.commit()
            return cursor.lastrowid

    def mark_touch_sent(self, touch_id: int):
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE touches SET status = 'SENT', sent_at = ? WHERE id = ?
            """, (now, touch_id))
            conn.commit()

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
