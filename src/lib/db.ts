import { DatabaseSync } from "node:sqlite";
import fs from "node:fs";
import path from "node:path";
import { ensureSeed } from "./seed";

const DATA_DIR = path.join(process.cwd(), "data");
export const DB_PATH = path.join(DATA_DIR, "cadence.sqlite");

let db: DatabaseSync | null = null;

/** Fingerprint of this module instance's database handle (diagnoses per-route module duplication). */
export const DB_ID = crypto.randomUUID();

/**
 * Local runs use a real SQLite file. Serverless (Vercel) has no writable
 * filesystem, so we fall back to a per-instance in-memory database that is
 * seeded on first use — the app stays fully functional, data is ephemeral.
 * Set CADENCE_DB="memory" to force it locally.
 */
export const DB_MODE: "file" | "memory" =
  process.env.CADENCE_DB === "memory" || process.env.VERCEL === "1"
    ? "memory"
    : "file";

const SCHEMA = `
CREATE TABLE IF NOT EXISTS sim_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  company TEXT NOT NULL,
  email TEXT NOT NULL,
  linkedin TEXT NOT NULL DEFAULT '',
  persona TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'new',
  health INTEGER NOT NULL DEFAULT 50,
  next_action TEXT,
  next_touch_at TEXT,
  sequence_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_briefs (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES leads(id),
  snapshot TEXT NOT NULL,
  role_context TEXT NOT NULL,
  persona_notes TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_hooks (
  id TEXT PRIMARY KEY,
  brief_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  title TEXT NOT NULL,
  detail TEXT NOT NULL,
  source TEXT NOT NULL,
  kind TEXT NOT NULL,
  published_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sequences (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES leads(id),
  playbook_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  started_at TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS touches (
  id TEXT PRIMARY KEY,
  sequence_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  step INTEGER NOT NULL,
  channel TEXT NOT NULL,
  intent TEXT NOT NULL,
  day_offset INTEGER NOT NULL,
  subject TEXT,
  body TEXT,
  status TEXT NOT NULL DEFAULT 'scheduled',
  send_at TEXT,
  sent_at TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS touch_hooks (
  touch_id TEXT NOT NULL,
  hook_id TEXT NOT NULL,
  line_ref TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (touch_id, hook_id)
);

CREATE TABLE IF NOT EXISTS replies (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL,
  touch_id TEXT,
  body TEXT NOT NULL,
  from_email TEXT NOT NULL,
  channel TEXT NOT NULL,
  arrived_at TEXT NOT NULL,
  ground_truth TEXT,
  handled INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classifications (
  id TEXT PRIMARY KEY,
  reply_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  intent TEXT NOT NULL,
  confidence REAL NOT NULL,
  evidence TEXT NOT NULL,
  rationale TEXT NOT NULL,
  suggested_angle TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY,
  lead_id TEXT,
  agent TEXT NOT NULL,
  action TEXT NOT NULL,
  reason TEXT NOT NULL,
  evidence TEXT NOT NULL,
  confidence REAL,
  meta TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  lead_id TEXT,
  kind TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS playbooks (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  steps TEXT NOT NULL,
  is_default INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_touches_lead ON touches(lead_id);
CREATE INDEX IF NOT EXISTS idx_touches_status ON touches(status);
CREATE INDEX IF NOT EXISTS idx_replies_lead ON replies(lead_id);
CREATE INDEX IF NOT EXISTS idx_decisions_lead ON decisions(lead_id);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_classifications_reply ON classifications(reply_id);
`;

export function getDb(): DatabaseSync {
  if (db) return db;

  if (DB_MODE === "memory") {
    db = new DatabaseSync(":memory:");
  } else {
    try {
      fs.mkdirSync(DATA_DIR, { recursive: true });
      db = new DatabaseSync(DB_PATH);
      db.exec("PRAGMA journal_mode = WAL;");
    } catch {
      // Read-only filesystem: degrade to in-memory rather than crashing.
      db = new DatabaseSync(":memory:");
    }
  }
  db.exec("PRAGMA foreign_keys = ON;");
  db.exec(SCHEMA);

  // Seed on first use so route handlers work without rendering the layout.
  if (DB_MODE === "memory") {
    ensureSeed();
  }
  return db;
}

export function uid(prefix = ""): string {
  const id = crypto.randomUUID();
  return prefix ? `${prefix}_${id}` : id;
}

export function nowIso(): string {
  return new Date().toISOString();
}
