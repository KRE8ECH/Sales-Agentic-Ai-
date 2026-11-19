import { NextResponse } from "next/server";
import { listReplies, getLead } from "@/lib/repo";
import { classifyReplyAsync } from "@/lib/engine";
import { saveClassification, markReplyHandled, addDecision, addEvent } from "@/lib/repo";
import { decideNextStep, computeHealth } from "@/lib/brain";
import { getSequence, getTouches, updateLead, setSequenceStatus } from "@/lib/repo";
import { fullSim } from "@/lib/format";

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const reply = listReplies().find((r) => r.id === id);
  if (!reply) return NextResponse.json({ error: "Reply not found" }, { status: 404 });
  const lead = getLead(reply.leadId);
  if (!lead) return NextResponse.json({ error: "Lead not found" }, { status: 404 });

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
  addEvent(lead.id, "classifier", `Classified ${lead.name}'s reply as ${result.intent.replace("_", " ")}.`);

  const seq = getSequence(lead.id);
  if (seq) {
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
    const remaining = touches.filter((t) => t.status === "scheduled");
    const health = computeHealth(replies);
    if (decision.action === "escalate") {
      setSequenceStatus(seq.id, "paused");
      updateLead(lead.id, { status: "escalated", health, nextAction: "Hand to human rep" });
    } else if (decision.action === "pause") {
      setSequenceStatus(seq.id, "paused");
      updateLead(lead.id, { status: "paused", health, nextAction: "Paused — resume after return" });
    } else if (decision.action === "stop") {
      setSequenceStatus(seq.id, "stopped");
      updateLead(lead.id, { status: "stopped", health, nextAction: "Stopped" });
    } else {
      updateLead(lead.id, {
        status: "active",
        health,
        nextAction:
          remaining.length > 0
            ? `Next touch ${remaining[0] ? fullSim(remaining[0].sendAt) : ""}`.trim()
            : "Sequence sent — awaiting reply",
      });
    }
  }
  return NextResponse.json({ ok: true, intent: result.intent });
}
