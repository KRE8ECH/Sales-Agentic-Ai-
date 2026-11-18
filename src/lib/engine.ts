import { getDb } from "./db";
import { addDays, runGraph, seededUnit } from "./graph";
import {
  addDecision,
  addEvent,
  createSequence,
  getBrief,
  getDefaultPlaybook,
  getHooks,
  getLead,
  getSequence,
  getSimNow,
  getTouches,
  getTouch,
  insertReply,
  insertTouch,
  listReplies,
  markReplyHandled,
  saveBrief,
  saveClassification,
  saveHook,
  saveTouchDraft,
  setSequenceStatus,
  setSimNow,
  setTouchStatus,
  updateLead,
} from "./repo";
import {
  classifyReply,
  computeHealth,
  decideNextStep,
  draftTouch,
  researchLead,
  SENDER,
  type ClassifyResult,
  type DraftResult,
  type ResearchResult,
} from "./brain";
import { replyBody, replyIntentFor, replyLagDays, willReply } from "./replies";
import { chat, extractJson, llmStatus } from "./llm";
import { ensureSeed } from "./seed";
import { formatSim, fullSim } from "./format";
import { OFFER } from "./kb";
import type {
  Lead,
  NextAction,
  Reply,
  ReplyIntent,
  ResearchHook,
  SequenceRow,
  Touch,
} from "./types";

/* ------------------------------- pipeline ---------------------------------- */

interface PipelineCtx {
  lead: Lead;
  now: string;
  research: ResearchResult | null;
  briefId: string | null;
  hooks: ResearchHook[];
  sequenceId: string | null;
  touches: Touch[];
  drafts: DraftResult[];
}

export async function runPipeline(leadId: string): Promise<{ ok: boolean; message: string }> {
  const lead = getLead(leadId);
  if (!lead) return { ok: false, message: "Lead not found" };

  const existing = getSequence(leadId);
  if (existing && getTouches(existing.id).length > 0) {
    return { ok: false, message: "Sequence already exists for this lead" };
  }

  const now = getSimNow();
  const ctx: PipelineCtx = {
    lead,
    now,
    research: null,
    briefId: null,
    hooks: [],
    sequenceId: null,
    touches: [],
    drafts: [],
  };

  const result = await runGraph<PipelineCtx>(
    [
      { name: "research", run: nodeResearch },
      { name: "plan", run: nodePlan },
      { name: "draft", run: nodeDraft },
      { name: "send", run: nodeSend },
    ],
    ctx
  );

  return {
    ok: true,
    message: `Pipeline complete for ${lead.name}: ${result.touches.length} touches planned, ${result.touches.filter((t) => t.status === "sent").length} sent.`,
  };
}

async function nodeResearch(ctx: PipelineCtx): Promise<PipelineCtx> {
  const { lead } = ctx;
  let brief = getBrief(lead.id);
  let hooks = getHooks(lead.id);
  let research: ResearchResult;

  if (brief && hooks.length > 0) {
    research = {
      snapshot: brief.snapshot,
      roleContext: brief.roleContext,
      personaNotes: brief.personaNotes,
      hooks: hooks.map((h) => ({
        title: h.title,
        detail: h.detail,
        source: h.source,
        kind: h.kind,
        publishedAt: h.publishedAt,
      })),
      matchedKb: true,
      decision: { action: "research_reused", reason: "Existing brief reused.", evidence: "", confidence: 0.9 },
    };
  } else {
    research = researchLead(lead);
    const briefId = saveBrief(lead.id, {
      snapshot: research.snapshot,
      roleContext: research.roleContext,
      personaNotes: research.personaNotes,
    });
    for (const h of research.hooks) {
      saveHook(lead.id, briefId, h);
    }
    hooks = getHooks(lead.id);
    brief = getBrief(lead.id);
  }

  addDecision({
    leadId: lead.id,
    agent: "research",
    action: research.decision.action,
    reason: research.decision.reason,
    evidence: research.decision.evidence,
    confidence: research.decision.confidence,
    meta: { hookCount: hooks.length, matchedKb: research.matchedKb },
  });
  addEvent(
    lead.id,
    "research",
    research.matchedKb
      ? `Research brief ready for ${lead.name} — ${hooks.length} hooks with citations.`
      : `Research brief inferred for ${lead.name} — no knowledge-base match.`
  );

  return { ...ctx, research, briefId: brief?.id ?? null, hooks };
}

async function nodePlan(ctx: PipelineCtx): Promise<PipelineCtx> {
  const { lead, now } = ctx;
  const playbook = getDefaultPlaybook();
  if (!playbook) throw new Error("No playbook configured");

  const sequenceId = createSequence(lead.id, playbook.id, now);
  for (const step of playbook.steps) {
    insertTouch(
      sequenceId,
      lead.id,
      step.step,
      step.channel,
      step.intent,
      step.dayOffset,
      addDays(now, step.dayOffset)
    );
  }
  const touches = getTouches(sequenceId);

  addDecision({
    leadId: lead.id,
    agent: "planner",
    action: "sequence_created",
    reason: `Built a ${touches.length}-touch sequence from playbook "${playbook.name}". Intent escalates insight → proof → ask → break-up with a ${playbook.steps
      .map((s) => s.dayOffset)
      .join("/")} day cadence.`,
    evidence: touches
      .map((t) => `touch ${t.step}: ${t.channel}/${t.intent} day ${t.dayOffset}`)
      .join(" · "),
    confidence: 0.9,
    meta: { playbookId: playbook.id, playbookName: playbook.name },
  });
  addEvent(
    lead.id,
    "planner",
    `Sequence planned for ${lead.name}: ${touches.length} touches, ${playbook.name}.`
  );

  updateLead(lead.id, { sequenceId, status: "sequencing" });
  return { ...ctx, sequenceId, touches };
}

async function nodeDraft(ctx: PipelineCtx): Promise<PipelineCtx> {
  const { lead, hooks, touches, now } = ctx;
  if (touches.length === 0) return ctx;

  const usedHookIds: string[] = [];
  const drafts: DraftResult[] = [];

  for (const touch of touches) {
    let draft = await draftWithLlm(lead, hooks, touch, usedHookIds);
    if (!draft) {
      draft = draftTouch({
        lead,
        hooks,
        intent: touch.intent,
        channel: touch.channel,
        step: touch.step,
        totalSteps: touches.length,
        usedHookIds,
      });
    }
    saveTouchDraft(touch.id, draft.subject ?? "", draft.body, draft.hookIds, draft.lineRefs);
    usedHookIds.push(...draft.hookIds);
    drafts.push(draft);

    addDecision({
      leadId: lead.id,
      agent: "drafter",
      action: "draft_completed",
      reason: draft.rationale,
      evidence: draft.hookIds.length
        ? `References ${draft.hookIds.length} research hook(s); subject: "${draft.subject ?? "n/a"}"`
        : "No hook reference available for this touch.",
      confidence: 0.8,
      meta: { touchId: touch.id, step: touch.step, hookIds: draft.hookIds },
    });
  }

  addEvent(
    lead.id,
    "drafter",
    `Drafted ${drafts.length} personalized touch(es) for ${lead.name}.`
  );

  return { ...ctx, drafts, now };
}

async function nodeSend(ctx: PipelineCtx): Promise<PipelineCtx> {
  const { lead, now } = ctx;
  const sent = dispatchDueTouches(now);
  const touches = ctx.sequenceId ? getTouches(ctx.sequenceId) : [];
  const next = touches.filter((t) => t.status === "scheduled").sort((a, b) =>
    (a.sendAt ?? "").localeCompare(b.sendAt ?? "")
  )[0];

  updateLead(lead.id, {
    status: "active",
    nextAction:
      sent > 0
        ? "Waiting for reply"
        : `Next touch ${next ? `due ${formatSim(next.sendAt)}` : ""}`.trim(),
    nextTouchAt: next?.sendAt ?? null,
  });

  addDecision({
    leadId: lead.id,
    agent: "sender",
    action: "sequence_activated",
    reason: `Sequence activated on the simulated sender. ${sent} touch(es) sent at kickoff; remaining touches fire on cadence.`,
    evidence: `sim time ${formatSim(now)} · ${sent} sent · ${touches.filter((t) => t.status === "scheduled").length} scheduled`,
    confidence: 0.95,
  });
  addEvent(lead.id, "sender", `Sequence live for ${lead.name}. First touch sent.`);

  return { ...ctx, touches };
}

/* ------------------------------- simulation -------------------------------- */

export function dispatchDueTouches(now: string): number {
  const db = getDb();
  const due = db
    .prepare("SELECT * FROM touches WHERE status = 'scheduled' AND send_at IS NOT NULL AND datetime(send_at) <= datetime(?) ORDER BY datetime(send_at)")
    .all(now) as Array<{ id: string; lead_id: string; step: number; channel: string; intent: string }>;

  for (const t of due) {
    setTouchStatus(t.id, "sent", now);
    const lead = getLead(t.lead_id);
    addDecision({
      leadId: t.lead_id,
      agent: "sender",
      action: "send_touch",
      reason: `Touch ${t.step} (${t.channel}, ${t.intent}) reached its cadence slot.`,
      evidence: `send_at ${formatSim(now)} · to ${lead?.email ?? t.lead_id}`,
      confidence: 0.95,
      meta: { touchId: t.id, step: t.step, channel: t.channel },
    });
    addEvent(
      t.lead_id,
      "send",
      `${t.channel === "linkedin" ? "LinkedIn" : "Email"} touch ${t.step} sent to ${lead?.name ?? "lead"}.`
    );
  }

  // refresh lead next-touch pointers
  if (due.length > 0) {
    const leads = new Set(due.map((d) => d.lead_id));
    for (const leadId of leads) {
      const seq = getSequence(leadId);
      if (!seq) continue;
      const remaining = getTouches(seq.id).filter((t) => t.status === "scheduled");
      const lead = getLead(leadId);
      if (!lead) continue;
      updateLead(leadId, {
        nextTouchAt: remaining[0]?.sendAt ?? null,
        nextAction:
          lead.status === "active"
            ? remaining.length > 0
              ? `Next touch ${remaining[0] ? formatSim(remaining[0].sendAt) : ""}`.trim()
              : "Sequence sent — awaiting reply"
            : lead.nextAction,
      });
    }
  }
  return due.length;
}

export function simulateReplies(now: string): string[] {
  const db = getDb();
  const leads = db
    .prepare("SELECT DISTINCT lead_id FROM touches WHERE status = 'sent'")
    .all() as Array<{ lead_id: string }>;
  const created: string[] = [];

  for (const { lead_id } of leads) {
    const lead = getLead(lead_id);
    if (!lead) continue;
    if (lead.status === "stopped" || lead.status === "won") continue;
    const seq = getSequence(lead_id);
    if (!seq || seq.status === "stopped") continue;
    const touches = getTouches(seq.id).filter((t) => t.status === "sent");
    const existing = listReplies(lead_id);
    const repliedTouchIds = new Set(existing.map((r) => r.touchId).filter(Boolean));

    for (const touch of touches) {
      if (touch.sentAt && repliedTouchIds.has(touch.id)) continue;
      const sentAt = touch.sentAt ?? touch.sendAt;
      if (!sentAt) continue;
      const lag = replyLagDays(lead_id, touch.id);
      if (new Date(sentAt).getTime() + lag * 86_400_000 > new Date(now).getTime()) continue;
      if (!willReply(lead_id, touch.id, touch.step)) continue;

      const intent = replyIntentFor(lead_id, touch.id);
      if (intent === "no_reply") continue;

      const arrivedAt = new Date(new Date(sentAt).getTime() + lag * 86_400_000).toISOString();
      const body = replyBody(lead, touch, intent);
      const id = insertReply({
        leadId: lead_id,
        touchId: touch.id,
        body,
        fromEmail: lead.email,
        channel: touch.channel,
        arrivedAt,
        groundTruth: intent,
      });
      addEvent(lead_id, "reply", `Reply received from ${lead.name} (${intent.replace("_", " ")}).`);
      created.push(id);
    }
  }
  return created;
}

function applyNextStep(
  lead: Lead,
  seq: SequenceRow,
  action: NextAction,
  decision: ReturnType<typeof decideNextStep>,
  replies: Reply[]
): void {
  const touches = getTouches(seq.id);
  const remaining = touches.filter((t) => t.status === "scheduled");
  const health = computeHealth(replies);

  if (action === "escalate") {
    setSequenceStatus(seq.id, "paused");
    updateLead(lead.id, {
      status: "escalated",
      health,
      nextAction: "Hand to human rep",
    });
    addEvent(
      lead.id,
      "escalation",
      `Escalated to human: ${decision.handoffSummary ?? decision.reason}`
    );
  } else if (action === "pause") {
    setSequenceStatus(seq.id, "paused");
    updateLead(lead.id, {
      status: "paused",
      health,
      nextAction: "Paused — resume after return",
    });
  } else if (action === "stop") {
    setSequenceStatus(seq.id, "stopped");
    updateLead(lead.id, { status: "stopped", health, nextAction: "Stopped" });
  } else {
    updateLead(lead.id, {
      status: "active",
      health,
      nextAction:
        remaining.length > 0
          ? `Next touch ${remaining[0] ? formatSim(remaining[0].sendAt) : ""}`.trim()
          : "Sequence sent — awaiting reply",
    });
  }
}

/** Async classification with LLM preference + deterministic fallback. */
export async function classifyReplyAsync(body: string, lead: Lead): Promise<ClassifyResult> {
  if (llmStatus().available) {
    const raw = await chat([
      {
        role: "system",
        content:
          "You classify sales outreach replies. Respond with JSON only: {intent, confidence, evidence, rationale, suggestedAngle}. intent must be one of: interested, not_interested, objection, ooo, no_reply.",
      },
      {
        role: "user",
        content: `Lead: ${lead.name}, ${lead.role} at ${lead.company}.\nReply:\n"""${body}"""`,
      },
    ]);
    if (raw) {
      const parsed = extractJson<{
        intent?: string;
        confidence?: number;
        evidence?: string;
        rationale?: string;
        suggestedAngle?: string;
      }>(raw);
      const valid: ReplyIntent[] = ["interested", "not_interested", "objection", "ooo", "no_reply"];
      if (parsed && parsed.intent && valid.includes(parsed.intent as ReplyIntent)) {
        return {
          intent: parsed.intent as ReplyIntent,
          confidence: typeof parsed.confidence === "number" ? parsed.confidence : 0.75,
          evidence: parsed.evidence ?? "",
          rationale: parsed.rationale ?? "",
          suggestedAngle: parsed.suggestedAngle ?? "",
        };
      }
    }
  }
  return classifyReply(body);
}

async function draftWithLlm(
  lead: Lead,
  hooks: ResearchHook[],
  touch: Touch,
  usedHookIds: string[]
): Promise<DraftResult | null> {
  if (!llmStatus().available) return null;
  const fresh = hooks.filter((h) => !usedHookIds.includes(h.id));
  const pool = fresh.length ? fresh : hooks;
  if (pool.length === 0) return null;

  const raw = await chat([
    {
      role: "system",
      content:
        "You are a top-tier B2B outbound copywriter. Write a short, specific, non-generic message. Never use bullet points, never use emojis, never claim a meeting. Respond with JSON only: {subject, body, hookId, rationale}.",
    },
    {
      role: "user",
      content: [
        `Product: ${OFFER.product} — ${OFFER.positioning}`,
        `Lead: ${lead.name}, ${lead.role} at ${lead.company}.`,
        `Persona notes: ${lead.persona}.`,
        `Touch ${touch.step}: channel=${touch.channel}, intent=${touch.intent}.`,
        `Available research hooks (pick ONE, the most specific):`,
        ...pool.map(
          (h, i) => `${i + 1}. [${h.id}] ${h.title} — ${h.detail} (source: ${h.source})`
        ),
        `Channel rules: ${touch.channel === "linkedin" ? "under 300 characters, casual, no subject." : "subject line required, under 200 words."}`,
      ].join("\n"),
    },
  ]);
  if (!raw) return null;
  const parsed = extractJson<{
    subject?: string;
    body?: string;
    hookId?: string;
    rationale?: string;
  }>(raw);
  if (!parsed || !parsed.body) return null;
  const hookId = pool.find((h) => h.id === parsed.hookId)?.id ?? pool[0].id;
  const hook = pool.find((h) => h.id === hookId)!;
  return {
    subject: parsed.subject ?? null,
    body: parsed.body,
    hookIds: [hookId],
    lineRefs: { [hookId]: `${hook.title} (${hook.source})` },
    rationale:
      parsed.rationale ??
      `LLM draft anchored on "${hook.title}" (${hook.source}) for a ${touch.intent} touch on ${touch.channel}.`,
  };
}

/* ----------------------------- manual replies ------------------------------ */

export async function handleIncomingReply(input: {
  leadId: string;
  body: string;
  touchId?: string | null;
  groundTruth?: ReplyIntent | null;
}): Promise<{ ok: boolean; message: string }> {
  const lead = getLead(input.leadId);
  if (!lead) return { ok: false, message: "Lead not found" };
  const body = input.body.trim();
  if (!body) return { ok: false, message: "Reply body is empty" };

  const now = getSimNow();
  let touchId = input.touchId ?? null;
  if (!touchId) {
    const seq = getSequence(input.leadId);
    if (seq) {
      touchId = getTouches(seq.id).find((t) => t.status === "sent")?.id ?? null;
    }
  }
  const channel = touchId ? (getTouch(touchId)?.channel ?? "email") : "email";
  const id = insertReply({
    leadId: input.leadId,
    touchId,
    body,
    fromEmail: lead.email,
    channel,
    arrivedAt: now,
    groundTruth: input.groundTruth ?? null,
  });
  addEvent(input.leadId, "reply", `Manual reply recorded from ${lead.name}.`);
  await classifyReplyAndDecideAsync(id);
  return { ok: true, message: "Reply classified and next step decided." };
}

/** Simulated reply: generates a realistic body from the persona templates. */
export async function simulateReply(
  leadId: string,
  intent: ReplyIntent
): Promise<{ ok: boolean; message: string }> {
  const lead = getLead(leadId);
  if (!lead) return { ok: false, message: "Lead not found" };
  const seq = getSequence(leadId);
  const sent = seq ? getTouches(seq.id).filter((t) => t.status === "sent") : [];
  const touch: Touch =
    sent[0] ??
    ({
      id: "none",
      sequenceId: seq?.id ?? "none",
      leadId,
      step: 1,
      channel: "email",
      intent: "insight",
      dayOffset: 0,
      subject: "Quick follow-up",
      body: "",
      status: "sent",
      sendAt: null,
      sentAt: null,
      hookIds: [],
    } as Touch);
  const body = replyBody(lead, touch, intent);
  if (!body) return { ok: false, message: "No reply template for this intent" };
  return handleIncomingReply({ leadId, body, touchId: touch.id, groundTruth: intent });
}

/* ------------------------------- advancement ------------------------------- */

export interface AdvanceResult {
  now: string;
  sent: number;
  replies: string[];
  decisions: number;
}

export async function advanceSim(days: number): Promise<AdvanceResult> {
  const start = getSimNow();
  const now = addDays(start, days);
  setSimNow(now);

  const sent = dispatchDueTouches(now);
  const replies = simulateReplies(now);
  let decisions = sent;
  for (const replyId of replies) {
    const before = getDb().prepare("SELECT COUNT(*) AS c FROM decisions").get() as { c: number };
    await classifyReplyAndDecideAsync(replyId);
    const after = getDb().prepare("SELECT COUNT(*) AS c FROM decisions").get() as { c: number };
    decisions += after.c - before.c;
  }
  resumeDue(now);

  addEvent(null, "clock", `Simulation clock advanced ${days} day(s) to ${formatSim(now)}.`);
  return { now, sent, replies, decisions };
}

async function classifyReplyAndDecideAsync(replyId: string): Promise<void> {
  const reply = listReplies().find((r) => r.id === replyId);
  if (!reply) return;
  const lead = getLead(reply.leadId);
  if (!lead) return;

  const result = await classifyReplyAsync(reply.body, lead);
  saveClassification({
    replyId: reply.id,
    leadId: lead.id,
    intent: result.intent,
    confidence: result.confidence,
    evidence: result.evidence,
    rationale: result.rationale,
    suggestedAngle: result.suggestedAngle,
  });
  markReplyHandled(reply.id);

  addDecision({
    leadId: lead.id,
    agent: "classifier",
    action: "reply_classified",
    reason: result.rationale,
    evidence: `Intent: ${result.intent} · ${result.evidence}`,
    confidence: result.confidence,
    meta: { replyId: reply.id, intent: result.intent },
  });
  addEvent(
    lead.id,
    "classifier",
    `Classified ${lead.name}'s reply as ${result.intent.replace("_", " ")} (${Math.round(result.confidence * 100)}%).`
  );

  const seq = getSequence(lead.id);
  if (!seq) return;
  const touches = getTouches(seq.id);
  const replies = listReplies(lead.id);
  const decision = decideNextStep({ lead, sequence: seq, touches, replies });
  addDecision({
    leadId: lead.id,
    agent: "nextstep",
    action: decision.action,
    reason: decision.reason,
    evidence: decision.evidence,
    confidence: decision.confidence,
    meta: decision.handoffSummary ? { handoff: true, handoffSummary: decision.handoffSummary } : undefined,
  });
  addEvent(
    lead.id,
    "nextstep",
    `Next-step agent: ${decision.action.toUpperCase()} for ${lead.name} — ${decision.reason.slice(0, 110)}…`
  );
  applyNextStep(lead, seq, decision.action, decision, replies);
}

function resumeDue(now: string): void {
  const db = getDb();
  const paused = db
    .prepare("SELECT * FROM leads WHERE status = 'paused'")
    .all() as Array<{ id: string }>;
  for (const { id } of paused) {
    const seq = getSequence(id);
    if (!seq || seq.status !== "paused") continue;
    const replies = listReplies(id).filter((r) => r.intent === "ooo");
    const lastOoo = replies[0];
    if (!lastOoo) continue;
    if (new Date(lastOoo.arrivedAt).getTime() + 4 * 86_400_000 > new Date(now).getTime()) continue;
    setSequenceStatus(seq.id, "active");
    updateLead(id, { status: "active", nextAction: "Resumed after OOO" });
    addDecision({
      leadId: id,
      agent: "nextstep",
      action: "resume",
      reason: "Out-of-office window passed; policy says resume the cadence rather than restart it.",
      evidence: `OOO reply ${formatSim(lastOoo.arrivedAt)}`,
      confidence: 0.8,
    });
    addEvent(id, "nextstep", "Sequence resumed after out-of-office window.");
  }
}

/* --------------------------------- reset ----------------------------------- */

export function resetSim(): void {
  const db = getDb();
  const tables = [
    "touch_hooks",
    "classifications",
    "replies",
    "touches",
    "sequences",
    "research_hooks",
    "research_briefs",
    "decisions",
    "events",
    "playbooks",
    "leads",
    "sim_state",
  ];
  for (const t of tables) db.exec(`DELETE FROM ${t};`);
  ensureSeedReimport();
}

function ensureSeedReimport(): void {
  ensureSeed();
}

/* --------------------------------- helpers --------------------------------- */

export { formatSim, fullSim } from "./format";
export { SENDER, seededUnit };
