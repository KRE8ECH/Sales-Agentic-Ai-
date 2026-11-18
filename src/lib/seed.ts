import { getDb, uid } from "./db";
import { KB } from "./kb";
import type { PlaybookStep } from "./types";

export const SIM_START = "2026-11-18T09:00:00.000Z";

const PLAYBOOKS: Array<{
  id: string;
  name: string;
  description: string;
  steps: PlaybookStep[];
  isDefault: boolean;
}> = [
  {
    id: "pb_standard",
    name: "Standard 4-touch",
    description:
      "Insight → proof → ask → break-up across email and LinkedIn. Balanced cadence for mid-market leads.",
    isDefault: true,
    steps: [
      { step: 1, channel: "email", intent: "insight", dayOffset: 0 },
      { step: 2, channel: "linkedin", intent: "proof", dayOffset: 2 },
      { step: 3, channel: "email", intent: "ask", dayOffset: 5 },
      { step: 4, channel: "linkedin", intent: "breakup", dayOffset: 9 },
    ],
  },
  {
    id: "pb_tight",
    name: "Tight 3-touch",
    description:
      "Compressed cadence for high-intent or competitive deals: insight, direct ask, honest break-up.",
    isDefault: false,
    steps: [
      { step: 1, channel: "email", intent: "insight", dayOffset: 0 },
      { step: 2, channel: "linkedin", intent: "ask", dayOffset: 3 },
      { step: 3, channel: "email", intent: "breakup", dayOffset: 7 },
    ],
  },
];

export function ensureSeed(): boolean {
  const db = getDb();
  const row = db.prepare("SELECT COUNT(*) AS c FROM leads").get() as { c: number };
  if (row.c > 0) return false;

  db.prepare("INSERT INTO sim_state (key, value) VALUES (?, ?)").run("now", SIM_START);

  const now = SIM_START;
  const insPb = db.prepare(
    "INSERT INTO playbooks (id, name, description, steps, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?)"
  );
  for (const pb of PLAYBOOKS) {
    insPb.run(pb.id, pb.name, pb.description, JSON.stringify(pb.steps), pb.isDefault ? 1 : 0, now);
  }

  const insLead = db.prepare(
    `INSERT INTO leads (id, name, role, company, email, linkedin, persona, status, health, next_action, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, 'new', 50, 'Awaiting research', ?, ?)`
  );
  // Briefs and hooks are intentionally NOT seeded: the research agent builds them
  // on the first pipeline run so the demo shows research happening.
  // Deterministic IDs: seeded leads must be addressable from any serverless
  // instance, otherwise deep links 404 when the request lands on a fresh instance.
  for (const k of KB) {
    const leadId = `lead_${k.slug}`;
    insLead.run(leadId, k.name, k.role, k.company, k.email, k.linkedin, k.persona, now, now);
  }

  db.prepare(
    "INSERT INTO events (id, lead_id, kind, message, created_at) VALUES (?, NULL, ?, ?, ?)"
  ).run(
    uid("evt"),
    "system",
    `Seeded ${KB.length} leads and the built-in knowledge base. Simulation clock set to ${SIM_START}.`,
    now
  );

  return true;
}
