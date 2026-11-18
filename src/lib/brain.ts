import { findKbEntry, OFFER } from "./kb";
import type {
  Channel,
  Intent,
  Lead,
  NextAction,
  Reply,
  ReplyIntent,
  ResearchHook,
  SequenceRow,
  Touch,
} from "./types";

export const SENDER = {
  name: "Alex Rao",
  firstName: "Alex",
  title: "Account Executive, Cadence",
  email: "alex.rao@cadence.ai",
};

/* ------------------------------- utilities -------------------------------- */

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h << 5) - h + s.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

function pick<T>(arr: T[], seed: string): T {
  if (arr.length === 0) throw new Error("pick: empty array");
  return arr[hash(seed) % arr.length];
}

function first(name: string): string {
  return name.trim().split(/\s+/)[0] ?? name;
}

const PERSONA_PAIN: Record<string, string> = {
  "operator-turned-vp": "pipeline reviews that still get assembled by hand",
  "first-growth-hire": "building repeatable pipeline without adding headcount",
  "enterprise-cro": "a forecast the board can actually trust",
  "enterprise-svp": "ramping a large AE team without inconsistent prospecting",
  "promoted-operator": "keeping digital promises and store execution in sync",
  "new-field-leader": "a real pipeline instead of founder-led heroics",
  founder: "spending days on outreach instead of the product",
  "scaling-cro": "pipeline coverage without bloating the team",
};

function painFor(lead: Lead): string {
  if (PERSONA_PAIN[lead.persona]) return PERSONA_PAIN[lead.persona];
  const role = lead.role.toLowerCase();
  if (role.includes("rev") || role.includes("operations")) return "pipeline reporting that still depends on spreadsheets";
  if (role.includes("founder") || role.includes("ceo")) return "wearing too many hats on growth";
  if (role.includes("growth") || role.includes("marketing")) return "pipeline volume without a repeatable motion";
  return "outbound that sounds generic instead of specific";
}

const HOOK_PRIORITY: Record<ResearchHook["kind"], number> = {
  social: 0,
  role: 1,
  funding: 2,
  news: 3,
  product: 4,
  event: 5,
};

function chooseHook(
  hooks: ResearchHook[],
  used: string[],
  seed: string
): ResearchHook | null {
  const fresh = hooks.filter((h) => !used.includes(h.id));
  const pool = fresh.length > 0 ? fresh : hooks;
  if (pool.length === 0) return null;
  const sorted = [...pool].sort((a, b) => {
    const pa = HOOK_PRIORITY[a.kind] ?? 9;
    const pb = HOOK_PRIORITY[b.kind] ?? 9;
    if (pa !== pb) return pa - pb;
    return b.publishedAt.localeCompare(a.publishedAt);
  });
  // deterministic variation when multiple hooks tie at the top
  return sorted[hash(seed) % Math.min(sorted.length, 3)] ?? sorted[0];
}

/* -------------------------------- research --------------------------------- */

export interface ResearchResult {
  snapshot: string;
  roleContext: string;
  personaNotes: string;
  hooks: Array<Omit<ResearchHook, "id" | "briefId" | "leadId">>;
  matchedKb: boolean;
  decision: { action: string; reason: string; evidence: string; confidence: number };
}

export function researchLead(lead: Lead): ResearchResult {
  const kb = findKbEntry(lead.company);
  if (kb) {
    return {
      snapshot: kb.snapshot,
      roleContext: kb.roleContext,
      personaNotes: kb.personaNotes,
      hooks: kb.hooks.map((h) => ({
        title: h.title,
        detail: h.detail,
        source: h.source,
        kind: h.kind,
        publishedAt: h.publishedAt,
      })),
      matchedKb: true,
      decision: {
        action: "research_complete",
        reason: `Matched ${kb.company} in the knowledge base; compiled ${kb.hooks.length} dated hooks.`,
        evidence: kb.hooks.map((h) => `${h.title} (${h.source})`).join(" · "),
        confidence: 0.94,
      },
    };
  }
  // Inferred research for unknown companies: honest, specific to the fields we have.
  const hooks: ResearchResult["hooks"] = [
    {
      title: `${lead.name} serves as ${lead.role} at ${lead.company}`,
      detail: `Role context is the strongest available signal — ${lead.role} implies ownership of the buying motion we target.`,
      source: "Inferred from profile",
      kind: "role",
      publishedAt: new Date().toISOString().slice(0, 10),
    },
    {
      title: `${lead.company} is in an active buying window for outbound tooling`,
      detail:
        "No public news matched this company, so the brief is inferred from role and industry signals rather than cited.",
      source: "Inferred",
      kind: "news",
      publishedAt: new Date().toISOString().slice(0, 10),
    },
  ];
  return {
    snapshot: `${lead.company} — no knowledge-base match. Outreach will be based on the lead profile and ${lead.role}'s typical remit rather than cited public context.`,
    roleContext: `${lead.name} is ${lead.role} at ${lead.company}. Add public context (news, funding, role changes) to sharpen this brief.`,
    personaNotes: `Persona not classified. Default to a concise, numbers-first message and avoid assumptions about stack or budget.`,
    hooks,
    matchedKb: false,
    decision: {
      action: "research_complete",
      reason: "No knowledge-base match; produced an inferred brief and flagged it as low-confidence.",
      evidence: `${lead.company} not found in knowledge base · ${hooks.length} inferred hooks`,
      confidence: 0.42,
    },
  };
}

/* -------------------------------- drafting --------------------------------- */

export interface DraftResult {
  subject: string | null;
  body: string;
  hookIds: string[];
  lineRefs: Record<string, string>;
  rationale: string;
}

export function draftTouch(input: {
  lead: Lead;
  hooks: ResearchHook[];
  intent: Intent;
  channel: Channel;
  step: number;
  totalSteps: number;
  usedHookIds: string[];
}): DraftResult {
  const { lead, hooks, intent, channel, step, totalSteps } = input;
  const hook = chooseHook(hooks, input.usedHookIds, `${lead.id}:${intent}:${step}`);
  const hookIds = hook ? [hook.id] : [];
  const lineRefs: Record<string, string> = {};
  const pain = painFor(lead);
  const f = first(lead.name);
  const isLi = channel === "linkedin";

  const hookSentence = hook
    ? `${hook.title} — ${hook.detail.split(".")[0]}.`
    : `${lead.company} is on my list this quarter.`;

  if (hook) lineRefs[hook.id] = hookSentence;

  let subject: string | null = null;
  let body = "";
  let rationale = "";

  if (intent === "insight") {
    const open = pick(
      [
        `${hookSentence}`,
        `Saw that ${hookSentence.charAt(0).toLowerCase()}${hookSentence.slice(1)}`,
        `${hook ? hook.title : "Quick one"} — thought of you.`,
      ],
      lead.id + step
    );
    const tie = pick(
      [
        `That usually shows up as ${pain} for teams at this stage.`,
        `For a ${lead.role} at a company like ${lead.company}, that tends to mean ${pain}.`,
        `Which matters because teams your size are usually dealing with ${pain}.`,
      ],
      lead.id + step + "tie"
    );
    rationale = hook
      ? `Opened on the ${hook.kind} hook "${hook.title}" (${hook.source}) — the most specific recent signal for ${lead.company}. Tied it to the ${lead.persona || "target"} pain (${pain}) and stopped short of an ask: touch ${step}/${totalSteps} is insight-only per the cadence.`
      : `No hooks available; used a neutral opener and avoided a hard ask.`;

    if (isLi) {
      body = `Hi ${f} — ${open}\n\n${tie}\n\nWe help ${OFFER.icpShort ?? "teams like yours"} with exactly that. Open to a quick chat this week?`;
    } else {
      subject = hook ? `${hook.title} — quick thought` : `Quick thought for ${lead.company}`;
      body = `Hi ${f},\n\n${open}\n\n${tie}\n\nWe help ${OFFER.icp} fix exactly that. Worth 15 minutes this week?\n\n— ${SENDER.firstName}`;
    }
  } else if (intent === "proof") {
    const proof = pick(OFFER.proofPoints, lead.id + step);
    const tie = pick(
      [
        `That is the part most ${lead.role} buyers want to see before a call.`,
        `It is also why teams your size stop worrying about follow-up gaps.`,
        `Happy to show you how it would look for ${lead.company}.`,
      ],
      lead.id + step + "p"
    );
    rationale = hook
      ? `Used proof instead of another hook because touch ${step} needs evidence, not novelty. Anchored on "${hook.title}" and attached a concrete outcome (${proof.split(".")[0]}).`
      : `Proof touch without a hook; anchored on the offer's strongest outcome.`;
    if (isLi) {
      body = `Hi ${f}, following up on my note about ${hook ? hook.title : "outreach"}.\n\n${proof} ${tie}\n\nWorth 15 minutes?`;
    } else {
      subject = `Proof, not promises — ${lead.company}`;
      body = `Hi ${f},\n\nFollowing up on my note about ${hook ? hook.title : "this"}.\n\n${proof}\n\n${tie}\n\nI would rather show you than describe it. 15 minutes this week or next?\n\n— ${SENDER.firstName}`;
    }
  } else if (intent === "ask") {
    const outcome = pick(OFFER.outcomes, lead.id + step);
    const dayOption = pick(
      ["Tuesday or Wednesday morning", "Thursday after 2pm", "a slot that suits you"],
      lead.id + step + "d"
    );
    rationale = hook
      ? `Direct ask on touch ${step}. Re-referenced "${hook.title}" so the ask stays specific, then named the outcome (${outcome}) and offered concrete times. No new hook needed — repetition of the first signal is intentional at this stage.`
      : `Direct ask with a concrete outcome and time options.`;
    if (isLi) {
      body = `Hi ${f} — last one from me.\n\nIf ${outcome} is a priority at ${lead.company}, let's talk. Open to a short call ${dayOption}?`;
    } else {
      subject = `Worth 15 minutes, ${f}?`;
      body = `Hi ${f},\n\nLast note from me.\n\n${hook ? hookSentence : ""}\n\nIf ${outcome} is a priority for ${lead.company} this quarter, let's talk. I can walk you through how a team like yours approached it.\n\nAre you open to a short call ${dayOption}? If not, no hard feelings — I'll close the file.\n\n— ${SENDER.firstName}`;
    }
  } else {
    // breakup
    const congrats = hook ? `Congrats on ${hook.title}.` : `Wishing you a strong quarter.`;
    rationale = hook
      ? `Break-up touch: honest, short, and references "${hook.title}" so it lands as a human sign-off rather than a sequence artifact. Intent is to leave the door open without another ask.`
      : `Break-up touch: honest close, no ask.`;
    if (isLi) {
      body = `Hi ${f}, I'll stop here — clearly bad timing. If outreach ever comes up, my inbox is open. ${congrats}`;
    } else {
      subject = `Leaving it here`;
      body = `Hi ${f},\n\nI'll leave it here — clearly bad timing. If ${pain.split(" ").slice(0, 4).join(" ")} ever comes up, my inbox is open.\n\n${congrats}\n\n— ${SENDER.firstName}`;
    }
  }

  return { subject, body, hookIds, lineRefs, rationale };
}

/* ------------------------------ classification ----------------------------- */

export interface ClassifyResult {
  intent: ReplyIntent;
  confidence: number;
  evidence: string;
  rationale: string;
  suggestedAngle: string;
}

const ANGLES: Record<ReplyIntent, string> = {
  interested: "Hand to the human rep now with the research brief and a suggested opener.",
  objection: "Send a targeted touch that addresses the objection with proof, then re-evaluate.",
  ooo: "Pause the sequence; resume after the return date.",
  not_interested: "Stop the sequence and mark the lead as not interested.",
  no_reply: "Continue the sequence on the defined cadence.",
};

/**
 * Weighted signal rules. Each match adds its weight to that intent; the highest
 * score wins, with a fixed priority order breaking ties. Negation is handled
 * explicitly so "not interested" never scores as interest.
 */
const RULES: Array<{ intent: ReplyIntent; re: RegExp; w?: number }> = [
  { intent: "ooo", re: /\b(out of (the )?office|\booo\b|auto.?reply)\b/i, w: 2 },
  { intent: "ooo", re: /\b(on vacation|on leave|away until|away this week|returning on)\b/i },
  { intent: "ooo", re: /\bback (on )?(monday|tuesday|wednesday|thursday|friday)\b/i },
  { intent: "ooo", re: /\bget back to you\b/i },

  { intent: "not_interested", re: /\bnot interested\b/i, w: 2 },
  { intent: "not_interested", re: /\b(unsubscribe|remove me|do not contact|don'?t contact)\b/i, w: 2 },
  {
    intent: "not_interested",
    re: /\b(do not|don'?t) (follow up|email|send)\b/i,
  },
  { intent: "not_interested", re: /\b(not a fit|wrong (person|company)|no thanks|no thank you)\b/i },
  { intent: "not_interested", re: /\bstop (emailing|sending|contacting)\b/i },
  { intent: "not_interested", re: /\bnot evaluating\b/i },

  { intent: "interested", re: /\binterested\b/i, w: 2 },
  {
    intent: "interested",
    re: /\b(let'?s (talk|chat|meet|set up)|book|schedule)\b/i,
  },
  { intent: "interested", re: /\b(send (me )?(more|the|info|details|pricing))\b/i },
  { intent: "interested", re: /\b(pricing|budget|proposal|what does it cost)\b/i },
  { intent: "interested", re: /\b(demo|call|meeting|zoom|quick chat)\b/i },
  { intent: "interested", re: /\b(set up|quick call|onboarding|demo link|20 minutes|30 minutes)\b/i },
  { intent: "interested", re: /\b(yes|sure|sounds good|love to|happy to)\b/i },

  { intent: "objection", re: /\b(too (expensive|much)|pricey|high price|cost)\b/i },
  { intent: "objection", re: /\b(already (use|have|working with)|current vendor|competitor)\b/i },
  { intent: "objection", re: /\b(not (a )?priority|not now|bad timing|no bandwidth|too busy)\b/i },
  { intent: "objection", re: /\b(not looking to switch|internal build|heads-down)\b/i },
  { intent: "objection", re: /\b(send over|just (send|email) (me )?(info|details))\b/i },
];

/** Priority used to break score ties: OOO overrides, then rejection, then interest, then objection. */
const PRIORITY: ReplyIntent[] = ["ooo", "not_interested", "interested", "objection"];

export function classifyReply(body: string): ClassifyResult {
  const text = body.trim();

  const scores = new Map<ReplyIntent, number>([
    ["interested", 0],
    ["not_interested", 0],
    ["objection", 0],
    ["ooo", 0],
  ]);
  const hits: Partial<Record<ReplyIntent, string[]>> = {};

  for (const rule of RULES) {
    const m = text.match(rule.re);
    if (!m) continue;
    scores.set(rule.intent, (scores.get(rule.intent) ?? 0) + (rule.w ?? 1));
    (hits[rule.intent] ??= []).push(m[0]);
  }

  // Negation: "not interested" must never count as interest.
  if (/\bnot interested\b/i.test(text)) {
    scores.set("interested", 0);
    hits.interested = [];
  }

  const ranked = [...scores.entries()].sort((a, b) => {
    if (b[1] !== a[1]) return b[1] - a[1];
    return PRIORITY.indexOf(a[0]) - PRIORITY.indexOf(b[0]);
  });
  const [topIntent, topScore] = ranked[0];

  if (topScore === 0) {
    const shortAffirmative =
      /^(hi|hey)?[,!\s]*(yes|yeah|yep|sure|sounds good|love to|happy to|let'?s do it|interested)[.!,\s]*$/i.test(
        text
      );
    if (shortAffirmative) {
      return {
        intent: "interested",
        confidence: 0.82,
        evidence: text.slice(0, 80),
        rationale: "Short affirmative reply with no objection language; treated as interest.",
        suggestedAngle: ANGLES.interested,
      };
    }
    return {
      intent: "no_reply",
      confidence: 0.6,
      evidence: "No reply language detected",
      rationale: "No intent signal found; defaulting to no_reply so the cadence can continue.",
      suggestedAngle: ANGLES.no_reply,
    };
  }

  const matched = hits[topIntent] ?? [];
  const confidence = Math.min(0.95, 0.62 + topScore * 0.1);
  const runnerUp = ranked.find(([intent, s]) => intent !== topIntent && s > 0);
  return {
    intent: topIntent,
    confidence,
    evidence: matched.slice(0, 3).join(" · "),
    rationale:
      `Scored "${topIntent}" highest (${topScore} signal(s): ${matched
        .slice(0, 2)
        .join(", ")}).` +
      (runnerUp ? ` Runner-up: ${runnerUp[0]} (${runnerUp[1]}).` : ""),
    suggestedAngle: ANGLES[topIntent],
  };
}

/* ------------------------------- next step --------------------------------- */

export interface NextStepResult {
  action: NextAction;
  reason: string;
  evidence: string;
  confidence: number;
  handoffSummary?: string;
}

export function decideNextStep(input: {
  lead: Lead;
  sequence: SequenceRow;
  touches: Touch[];
  replies: Reply[];
}): NextStepResult {
  const { lead, sequence, touches, replies } = input;
  const classified = replies.filter((r) => r.intent !== null);
  // listReplies returns newest-first, so the latest classified reply is the decision input.
  const last = classified[0];
  const remaining = touches.filter((t) => t.status === "scheduled");

  if (last?.intent === "interested") {
    const brief = replies.find((r) => r.id === last.id);
    return {
      action: "escalate",
      reason:
        `Lead replied with interest (${Math.round((last.confidence ?? 0) * 100)}% confidence). ` +
        `Policy: interest is a human moment — the rep should take the conversation, not the sequence.`,
      evidence: brief ? `Reply: "${brief.body.slice(0, 160)}"` : "Classification: interested",
      confidence: last.confidence ?? 0.8,
      handoffSummary:
        `${lead.name} (${lead.role}, ${lead.company}) replied interested. ` +
        `Sequence had ${remaining.length} touch(es) left — paused so the rep owns the thread. ` +
        `Suggested opener: reference the last touch and propose two times.`,
    };
  }

  if (last?.intent === "objection") {
    if (remaining.length > 0) {
      return {
        action: "continue",
        reason:
          "Objection detected but the sequence has touches left. Policy: answer the objection with proof rather than escalating or stopping.",
        evidence: `Reply: "${last.body.slice(0, 140)}"`,
        confidence: last.confidence ?? 0.7,
      };
    }
    return {
      action: "escalate",
      reason: "Objection with no touches left — a human should decide whether to re-engage.",
      evidence: `Reply: "${last.body.slice(0, 140)}"`,
      confidence: 0.72,
      handoffSummary: `${lead.name} raised an objection at the end of the sequence. Hand to the rep to handle personally.`,
    };
  }

  if (last?.intent === "ooo") {
    return {
      action: "pause",
      reason:
        "Out-of-office detected. Policy: pause, do not keep sending into an empty inbox; resume after the return window.",
      evidence: `Reply: "${last.body.slice(0, 120)}"`,
      confidence: last.confidence ?? 0.8,
    };
  }

  if (last?.intent === "not_interested") {
    return {
      action: "stop",
      reason: "Lead asked to be removed. Policy: stop immediately and never re-enter the sequence.",
      evidence: `Reply: "${last.body.slice(0, 120)}"`,
      confidence: last.confidence ?? 0.85,
    };
  }

  // No classified reply yet (or only no_reply).
  if (remaining.length > 0) {
    return {
      action: "continue",
      reason: `No reply yet; ${remaining.length} touch(es) remain in the cadence. Policy: keep the sequence moving.`,
      evidence: `${touches.filter((t) => t.status === "sent").length} sent · ${remaining.length} scheduled`,
      confidence: 0.75,
    };
  }

  return {
    action: "stop",
    reason: "Sequence exhausted with no reply. Policy: stop rather than inventing new touches.",
    evidence: `${touches.length} touches sent · 0 replies classified`,
    confidence: 0.7,
  };
}

/* --------------------------------- health ---------------------------------- */

export function computeHealth(
  replies: Reply[],
  base = 50
): number {
  let h = base;
  for (const r of replies) {
    if (!r.intent) continue;
    if (r.intent === "interested") h += 30;
    else if (r.intent === "objection") h += 5;
    else if (r.intent === "ooo") h -= 5;
    else if (r.intent === "not_interested") h -= 40;
  }
  return Math.max(0, Math.min(100, h));
}
