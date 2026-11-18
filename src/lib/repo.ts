import { getDb, uid } from "./db";
import type { SQLInputValue } from "node:sqlite";
import type {
  Decision,
  EventRow,
  Lead,
  LeadStatus,
  Playbook,
  PlaybookStep,
  Reply,
  ResearchBrief,
  ResearchHook,
  SequenceRow,
  Touch,
} from "./types";

/* ---------------------------------- leads --------------------------------- */

interface LeadRow {
  id: string;
  name: string;
  role: string;
  company: string;
  email: string;
  linkedin: string;
  persona: string;
  status: LeadStatus;
  health: number;
  next_action: string | null;
  next_touch_at: string | null;
  sequence_id: string | null;
  created_at: string;
  updated_at: string;
}

function toLead(r: LeadRow): Lead {
  return {
    id: r.id,
    name: r.name,
    role: r.role,
    company: r.company,
    email: r.email,
    linkedin: r.linkedin,
    persona: r.persona,
    status: r.status,
    health: r.health,
    nextAction: r.next_action,
    nextTouchAt: r.next_touch_at,
    sequenceId: r.sequence_id,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

export function listLeads(): Lead[] {
  const rows = getDb()
    .prepare("SELECT * FROM leads ORDER BY datetime(created_at) DESC, name ASC")
    .all() as unknown as LeadRow[];
  return rows.map(toLead);
}

export function getLead(id: string): Lead | null {
  const r = getDb().prepare("SELECT * FROM leads WHERE id = ?").get(id) as unknown as LeadRow | null;
  return r ? toLead(r) : null;
}

export interface NewLeadInput {
  name: string;
  role: string;
  company: string;
  email: string;
  linkedin?: string;
  persona?: string;
}

export function createLead(input: NewLeadInput): Lead {
  const db = getDb();
  const now = getSimNow();
  const id = uid("lead");
  db.prepare(
    `INSERT INTO leads (id, name, role, company, email, linkedin, persona, status, health, next_action, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, 'new', 50, 'Awaiting research', ?, ?)`
  ).run(
    id,
    input.name,
    input.role,
    input.company,
    input.email,
    input.linkedin ?? "",
    input.persona ?? "",
    now,
    now
  );
  return getLead(id)!;
}

export function updateLead(id: string, patch: Partial<Lead>): void {
  const db = getDb();
  const cur = getLead(id);
  if (!cur) return;
  const next = { ...cur, ...patch, id, updatedAt: getSimNow() };
  db.prepare(
    `UPDATE leads SET name=?, role=?, company=?, email=?, linkedin=?, persona=?, status=?, health=?, next_action=?, next_touch_at=?, sequence_id=?, updated_at=? WHERE id=?`
  ).run(
    next.name,
    next.role,
    next.company,
    next.email,
    next.linkedin,
    next.persona,
    next.status,
    next.health,
    next.nextAction,
    next.nextTouchAt,
    next.sequenceId,
    next.updatedAt,
    id
  );
}

/* ---------------------------------- sim ----------------------------------- */

export function getSimNow(): string {
  const r = getDb().prepare("SELECT value FROM sim_state WHERE key = 'now'").get() as
    | { value: string }
    | null;
  return r?.value ?? new Date().toISOString();
}

export function setSimNow(iso: string): void {
  getDb().prepare("UPDATE sim_state SET value = ? WHERE key = 'now'").run(iso);
}

/* --------------------------------- research -------------------------------- */

export function getBrief(leadId: string): ResearchBrief | null {
  const r = getDb().prepare("SELECT * FROM research_briefs WHERE lead_id = ?").get(leadId) as
    | {
        id: string;
        lead_id: string;
        snapshot: string;
        role_context: string;
        persona_notes: string;
        created_at: string;
      }
    | null;
  if (!r) return null;
  return {
    id: r.id,
    leadId: r.lead_id,
    snapshot: r.snapshot,
    roleContext: r.role_context,
    personaNotes: r.persona_notes,
    createdAt: r.created_at,
  };
}

export function getHooks(leadId: string): ResearchHook[] {
  const rows = getDb()
    .prepare("SELECT * FROM research_hooks WHERE lead_id = ? ORDER BY published_at DESC")
    .all(leadId) as Array<{
    id: string;
    brief_id: string;
    lead_id: string;
    title: string;
    detail: string;
    source: string;
    kind: ResearchHook["kind"];
    published_at: string;
  }>;
  return rows.map((r) => ({
    id: r.id,
    briefId: r.brief_id,
    leadId: r.lead_id,
    title: r.title,
    detail: r.detail,
    source: r.source,
    kind: r.kind,
    publishedAt: r.published_at,
  }));
}

export function saveBrief(
  leadId: string,
  brief: Omit<ResearchBrief, "id" | "leadId" | "createdAt">
): string {
  const db = getDb();
  const id = uid("brief");
  db.prepare(
    "INSERT INTO research_briefs (id, lead_id, snapshot, role_context, persona_notes, created_at) VALUES (?, ?, ?, ?, ?, ?)"
  ).run(id, leadId, brief.snapshot, brief.roleContext, brief.personaNotes, getSimNow());
  return id;
}

export function saveHook(
  leadId: string,
  briefId: string,
  hook: Omit<ResearchHook, "id" | "leadId" | "briefId" | "publishedAt"> & { publishedAt?: string }
): string {
  const db = getDb();
  const id = uid("hook");
  db.prepare(
    "INSERT INTO research_hooks (id, brief_id, lead_id, title, detail, source, kind, published_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
  ).run(
    id,
    briefId,
    leadId,
    hook.title,
    hook.detail,
    hook.source,
    hook.kind,
    hook.publishedAt ?? getSimNow().slice(0, 10)
  );
  return id;
}

/* -------------------------------- sequences -------------------------------- */

export function getSequence(leadId: string): SequenceRow | null {
  const r = getDb().prepare("SELECT * FROM sequences WHERE lead_id = ? ORDER BY created_at DESC LIMIT 1").get(leadId) as
    | {
        id: string;
        lead_id: string;
        playbook_id: string;
        status: SequenceRow["status"];
        started_at: string | null;
        created_at: string;
      }
    | null;
  if (!r) return null;
  return {
    id: r.id,
    leadId: r.lead_id,
    playbookId: r.playbook_id,
    status: r.status,
    startedAt: r.started_at,
    createdAt: r.created_at,
  };
}

export function createSequence(leadId: string, playbookId: string, startedAt: string): string {
  const db = getDb();
  const id = uid("seq");
  db.prepare(
    "INSERT INTO sequences (id, lead_id, playbook_id, status, started_at, created_at) VALUES (?, ?, ?, 'active', ?, ?)"
  ).run(id, leadId, playbookId, startedAt, getSimNow());
  return id;
}

export function setSequenceStatus(id: string, status: SequenceRow["status"]): void {
  getDb().prepare("UPDATE sequences SET status = ? WHERE id = ?").run(status, id);
}

export interface TouchRow {
  id: string;
  sequence_id: string;
  lead_id: string;
  step: number;
  channel: Touch["channel"];
  intent: Touch["intent"];
  day_offset: number;
  subject: string | null;
  body: string | null;
  status: Touch["status"];
  send_at: string | null;
  sent_at: string | null;
  created_at: string;
}

export function getTouches(sequenceId: string): Touch[] {
  const rows = getDb()
    .prepare("SELECT * FROM touches WHERE sequence_id = ? ORDER BY step ASC")
    .all(sequenceId) as unknown as TouchRow[];
  const hookStmt = getDb().prepare(
    "SELECT hook_id FROM touch_hooks WHERE touch_id = ?"
  );
  return rows.map((r) => ({
    id: r.id,
    sequenceId: r.sequence_id,
    leadId: r.lead_id,
    step: r.step,
    channel: r.channel,
    intent: r.intent,
    dayOffset: r.day_offset,
    subject: r.subject,
    body: r.body,
    status: r.status,
    sendAt: r.send_at,
    sentAt: r.sent_at,
    hookIds: (hookStmt.all(r.id) as Array<{ hook_id: string }>).map((h) => h.hook_id),
  }));
}

export function getTouch(id: string): Touch | null {
  const r = getDb().prepare("SELECT * FROM touches WHERE id = ?").get(id) as unknown as TouchRow | null;
  if (!r) return null;
  const hookIds = (
    getDb().prepare("SELECT hook_id FROM touch_hooks WHERE touch_id = ?").all(id) as Array<{
      hook_id: string;
    }>
  ).map((h) => h.hook_id);
  return {
    id: r.id,
    sequenceId: r.sequence_id,
    leadId: r.lead_id,
    step: r.step,
    channel: r.channel,
    intent: r.intent,
    dayOffset: r.day_offset,
    subject: r.subject,
    body: r.body,
    status: r.status,
    sendAt: r.send_at,
    sentAt: r.sent_at,
    hookIds,
  };
}

export function insertTouch(
  sequenceId: string,
  leadId: string,
  step: number,
  channel: Touch["channel"],
  intent: Touch["intent"],
  dayOffset: number,
  sendAt: string
): string {
  const db = getDb();
  const id = uid("touch");
  db.prepare(
    `INSERT INTO touches (id, sequence_id, lead_id, step, channel, intent, day_offset, status, send_at, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?)`
  ).run(id, sequenceId, leadId, step, channel, intent, dayOffset, sendAt, getSimNow());
  return id;
}

export function saveTouchDraft(
  touchId: string,
  subject: string,
  body: string,
  hookIds: string[],
  lineRefs: Record<string, string>
): void {
  const db = getDb();
  db.prepare("UPDATE touches SET subject = ?, body = ? WHERE id = ?").run(subject, body, touchId);
  const ins = db.prepare(
    "INSERT OR REPLACE INTO touch_hooks (touch_id, hook_id, line_ref) VALUES (?, ?, ?)"
  );
  for (const hid of hookIds) ins.run(touchId, hid, lineRefs[hid] ?? "");
}

export function setTouchStatus(id: string, status: Touch["status"], sentAt?: string): void {
  getDb()
    .prepare("UPDATE touches SET status = ?, sent_at = COALESCE(?, sent_at) WHERE id = ?")
    .run(status, sentAt ?? null, id);
}

/* --------------------------------- replies --------------------------------- */

export interface ReplyRow {
  id: string;
  lead_id: string;
  touch_id: string | null;
  body: string;
  from_email: string;
  channel: Reply["channel"];
  arrived_at: string;
  ground_truth: Reply["groundTruth"] | null;
  handled: number;
  created_at: string;
}

export function listReplies(leadId?: string): Reply[] {
  const db = getDb();
  const rows = (
    leadId
      ? db.prepare("SELECT * FROM replies WHERE lead_id = ? ORDER BY datetime(arrived_at) DESC").all(leadId)
      : db.prepare("SELECT * FROM replies ORDER BY datetime(arrived_at) DESC").all()
  ) as unknown as ReplyRow[];
  const clsStmt = db.prepare("SELECT * FROM classifications WHERE reply_id = ? LIMIT 1");
  return rows.map((r) => {
    const c = clsStmt.get(r.id) as
      | { intent: Reply["intent"]; confidence: number }
      | null;
    return {
      id: r.id,
      leadId: r.lead_id,
      touchId: r.touch_id,
      body: r.body,
      fromEmail: r.from_email,
      channel: r.channel,
      arrivedAt: r.arrived_at,
      groundTruth: r.ground_truth,
      handled: r.handled === 1,
      intent: c?.intent ?? null,
      confidence: c?.confidence ?? null,
    };
  });
}

export function getReply(id: string): Reply | null {
  const rows = listReplies();
  return rows.find((r) => r.id === id) ?? null;
}

export function insertReply(input: {
  leadId: string;
  touchId?: string | null;
  body: string;
  fromEmail: string;
  channel: Reply["channel"];
  arrivedAt: string;
  groundTruth?: Reply["groundTruth"] | null;
}): string {
  const db = getDb();
  const id = uid("reply");
  db.prepare(
    `INSERT INTO replies (id, lead_id, touch_id, body, from_email, channel, arrived_at, ground_truth, handled, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)`
  ).run(
    id,
    input.leadId,
    input.touchId ?? null,
    input.body,
    input.fromEmail,
    input.channel,
    input.arrivedAt,
    input.groundTruth ?? null,
    getSimNow()
  );
  return id;
}

export function markReplyHandled(id: string): void {
  getDb().prepare("UPDATE replies SET handled = 1 WHERE id = ?").run(id);
}

/* ------------------------------ classifications ---------------------------- */

export function saveClassification(input: {
  replyId: string;
  leadId: string;
  intent: Reply["intent"];
  confidence: number;
  evidence: string;
  rationale: string;
  suggestedAngle: string;
}): void {
  const db = getDb();
  db.prepare(
    `INSERT INTO classifications (id, reply_id, lead_id, intent, confidence, evidence, rationale, suggested_angle, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).run(
    uid("cls"),
    input.replyId,
    input.leadId,
    input.intent,
    input.confidence,
    input.evidence,
    input.rationale,
    input.suggestedAngle,
    getSimNow()
  );
}

/* -------------------------------- decisions -------------------------------- */

export function addDecision(input: {
  leadId: string | null;
  agent: Decision["agent"];
  action: string;
  reason: string;
  evidence: string;
  confidence?: number | null;
  meta?: Record<string, unknown> | null;
}): void {
  getDb()
    .prepare(
      `INSERT INTO decisions (id, lead_id, agent, action, reason, evidence, confidence, meta, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .run(
      uid("dec"),
      input.leadId,
      input.agent,
      input.action,
      input.reason,
      input.evidence,
      input.confidence ?? null,
      input.meta ? JSON.stringify(input.meta) : null,
      getSimNow()
    );
}

export function listDecisions(filter?: {
  leadId?: string;
  agent?: string;
  action?: string;
  limit?: number;
}): Decision[] {
  const db = getDb();
  const where: string[] = [];
  const params: SQLInputValue[] = [];
  if (filter?.leadId) {
    where.push("lead_id = ?");
    params.push(filter.leadId);
  }
  if (filter?.agent) {
    where.push("agent = ?");
    params.push(filter.agent);
  }
  if (filter?.action) {
    where.push("action = ?");
    params.push(filter.action);
  }
  const sql =
    "SELECT * FROM decisions " +
    (where.length ? "WHERE " + where.join(" AND ") : "") +
    " ORDER BY rowid DESC" +
    (filter?.limit ? ` LIMIT ${Math.min(filter.limit, 500)}` : "");
  const rows = db.prepare(sql).all(...params) as Array<{
    id: string;
    lead_id: string | null;
    agent: Decision["agent"];
    action: string;
    reason: string;
    evidence: string;
    confidence: number | null;
    meta: string | null;
    created_at: string;
  }>;
  return rows.map((r) => ({
    id: r.id,
    leadId: r.lead_id,
    agent: r.agent,
    action: r.action,
    reason: r.reason,
    evidence: r.evidence,
    confidence: r.confidence,
    meta: r.meta ? (JSON.parse(r.meta) as Record<string, unknown>) : null,
    createdAt: r.created_at,
  }));
}

export function addEvent(leadId: string | null, kind: string, message: string): void {
  getDb()
    .prepare("INSERT INTO events (id, lead_id, kind, message, created_at) VALUES (?, ?, ?, ?, ?)")
    .run(uid("evt"), leadId, kind, message, getSimNow());
}

export function listEvents(limit = 60): EventRow[] {
  const rows = getDb()
    .prepare("SELECT * FROM events ORDER BY rowid DESC LIMIT ?")
    .all(limit) as Array<{
    id: string;
    lead_id: string | null;
    kind: string;
    message: string;
    created_at: string;
  }>;
  return rows.map((r) => ({
    id: r.id,
    leadId: r.lead_id,
    kind: r.kind,
    message: r.message,
    createdAt: r.created_at,
  }));
}

/* -------------------------------- playbooks -------------------------------- */

export function listPlaybooks(): Playbook[] {
  const rows = getDb().prepare("SELECT * FROM playbooks ORDER BY is_default DESC, name ASC").all() as Array<{
    id: string;
    name: string;
    description: string;
    steps: string;
    is_default: number;
    created_at: string;
  }>;
  return rows.map((r) => ({
    id: r.id,
    name: r.name,
    description: r.description,
    steps: JSON.parse(r.steps) as PlaybookStep[],
    isDefault: r.is_default === 1,
    createdAt: r.created_at,
  }));
}

export function getPlaybook(id: string): Playbook | null {
  return listPlaybooks().find((p) => p.id === id) ?? null;
}

export function getDefaultPlaybook(): Playbook | null {
  return listPlaybooks().find((p) => p.isDefault) ?? listPlaybooks()[0] ?? null;
}

/* ----------------------------- playbook writes ----------------------------- */

export function createPlaybook(input: {
  name: string;
  description: string;
  steps: PlaybookStep[];
  isDefault?: boolean;
}): Playbook {
  const db = getDb();
  if (input.isDefault) {
    db.prepare("UPDATE playbooks SET is_default = 0").run();
  }
  const id = uid("pb");
  db.prepare(
    "INSERT INTO playbooks (id, name, description, steps, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?)"
  ).run(id, input.name, input.description, JSON.stringify(input.steps), input.isDefault ? 1 : 0, getSimNow());
  return getPlaybook(id)!;
}

export function setDefaultPlaybook(id: string): void {
  const db = getDb();
  db.prepare("UPDATE playbooks SET is_default = 0").run();
  db.prepare("UPDATE playbooks SET is_default = 1 WHERE id = ?").run(id);
}
