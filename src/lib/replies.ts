import type { Lead, ReplyIntent, Touch } from "./types";
import { SENDER } from "./brain";
import { seededUnit } from "./graph";

/**
 * Simulated inbox. Deterministic per (lead, touch) so the demo is reproducible
 * and ground truth is known for classification-accuracy tracking.
 */

const DISTRIBUTION: Array<{ intent: ReplyIntent; weight: number }> = [
  { intent: "interested", weight: 0.27 },
  { intent: "objection", weight: 0.22 },
  { intent: "ooo", weight: 0.1 },
  { intent: "not_interested", weight: 0.12 },
  { intent: "no_reply", weight: 0.29 },
];

/** Reply propensity falls as the sequence progresses: 90% → 62% across four touches. */
export function willReply(leadId: string, touchId: string, step = 1): boolean {
  const p = [0.9, 0.82, 0.72, 0.62][Math.min(Math.max(step, 1), 4) - 1] ?? 0.6;
  return seededUnit(`reply:${leadId}:${touchId}`) < p;
}

export function replyIntentFor(leadId: string, touchId: string): ReplyIntent {
  const u = seededUnit(`intent:${leadId}:${touchId}`);
  let acc = 0;
  for (const d of DISTRIBUTION) {
    acc += d.weight;
    if (u < acc) return d.intent;
  }
  return "no_reply";
}

export function replyLagDays(leadId: string, touchId: string): number {
  const u = seededUnit(`lag:${leadId}:${touchId}`);
  return 0.6 + u * 2.2; // 0.6 – 2.8 days
}

function first(name: string): string {
  return name.trim().split(/\s+/)[0] ?? name;
}

export function replyBody(lead: Lead, touch: Touch, intent: ReplyIntent): string {
  const f = first(lead.name);
  const hookLine = touch.subject ? ` re: ${touch.subject}` : "";
  switch (intent) {
    case "interested":
      return pick(
        [
          `Hi ${SENDER.firstName}, this is actually well-timed. We have been looking at exactly this problem. Can you send over pricing and a short demo link?`,
          `Hey — saw${hookLine}. Would be open to a quick call this week. What does onboarding look like?`,
          `Thanks for the detail. A few of the points landed. Let's set up 20 minutes — Thursday works best.`,
        ],
        lead.id + touch.id
      );
    case "objection":
      return pick(
        [
          `Thanks, but we already use a competitor and are not looking to switch right now.`,
          `Appreciate the note. It feels a bit pricey for a team our size at this stage. Send over a lighter option if you have one.`,
          `Not a priority for us this quarter — we are heads-down on an internal build.`,
          `Interesting, but we have no bandwidth to evaluate anything new until January.`,
        ],
        lead.id + touch.id
      );
    case "ooo":
      return pick(
        [
          `I am out of office until Nov 24 with limited email access. I will reply when I am back.`,
          `Away this week at a conference, back Monday. Will get back to you then.`,
          `Out of office — auto-reply. Please follow up after I return on Nov 25.`,
        ],
        lead.id + touch.id
      );
    case "not_interested":
      return pick(
        [
          `Not a fit for us right now. Please remove me from your list.`,
          `Thanks but no thanks — we are not evaluating this category.`,
          `Not interested. Please do not follow up again.`,
        ],
        lead.id + touch.id
      );
    default:
      return "";
  }
}

function pick<T>(arr: T[], seed: string): T {
  return arr[Math.floor(seededUnit(seed) * arr.length) % arr.length];
}
