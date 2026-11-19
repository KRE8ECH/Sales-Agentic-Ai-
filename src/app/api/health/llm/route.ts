import { NextResponse } from "next/server";
import { chat, getLastLlmError, getLastLlmRaw, llmStatus } from "@/lib/llm";
import { classifyReplyAsync, draftWithLlm } from "@/lib/engine";
import { getLead, getHooks } from "@/lib/repo";
import { researchLead } from "@/lib/brain";
import type { Touch } from "@/lib/types";

export const dynamic = "force-dynamic";

/** Diagnostic: provider status; ?probe=1 real call; ?list=1 model catalog; ?draft=1 runs the real drafting agent. */
export async function GET(req: Request) {
  const url = new URL(req.url);
  const status = llmStatus();

  if (url.searchParams.has("classify")) {
    const leadId = url.searchParams.get("lead") ?? "lead_northwind-freight";
    const lead = getLead(leadId);
    const body = url.searchParams.get("body") ?? "";
    if (!lead) return NextResponse.json({ ok: false, error: "lead not found" }, { status: 404 });
    const started = Date.now();
    const result = await classifyReplyAsync(body, lead);
    return NextResponse.json({
      ok: Boolean(body),
      latencyMs: Date.now() - started,
      lead: lead.company,
      result,
      error: Boolean(body) ? null : "empty body",
    });
  }

  if (url.searchParams.has("draft")) {
    const leadId = url.searchParams.get("lead") ?? "lead_northwind-freight";
    const lead = getLead(leadId);
    if (!lead) return NextResponse.json({ ok: false, error: "lead not found" }, { status: 404 });
    let hooks = getHooks(lead.id);
    if (hooks.length === 0) {
      hooks = researchLead(lead).hooks.map((h, i) => ({
        ...h,
        id: `probe-hook-${i}`,
        briefId: "probe",
        leadId: lead.id,
      }));
    }
    const touch: Touch = {
      id: "probe-touch",
      sequenceId: "probe",
      leadId: lead.id,
      step: 1,
      channel: "email",
      intent: "insight",
      dayOffset: 0,
      subject: null,
      body: null,
      status: "scheduled",
      sendAt: null,
      sentAt: null,
      hookIds: [],
    };
    const started = Date.now();
    const override = url.searchParams.get("model") ?? undefined;
    const draft = await draftWithLlm(lead, hooks, touch, [], override);
    return NextResponse.json({
      ok: Boolean(draft),
      latencyMs: Date.now() - started,
      lead: lead.company,
      hookCount: hooks.length,
      usedModel: override ?? status.model,
      draft,
      error: draft ? null : getLastLlmError(),
      raw: url.searchParams.has("debug") ? getLastLlmRaw() : undefined,
    });
  }

  if (url.searchParams.has("list")) {
    const key = process.env.NVIDIA_API_KEY;
    if (!key) return NextResponse.json({ available: false, models: [] });
    const base = process.env.NVIDIA_BASE_URL || "https://integrate.api.nvidia.com/v1";
    try {
      const res = await fetch(`${base}/models`, {
        headers: { Authorization: `Bearer ${key}` },
        signal: AbortSignal.timeout(30_000),
      });
      if (!res.ok) {
        return NextResponse.json({ available: false, error: `http ${res.status}` });
      }
      const data = (await res.json()) as { data?: Array<{ id: string }> };
      const models = (data.data ?? []).map((m) => m.id).sort();
      return NextResponse.json({ available: true, count: models.length, models });
    } catch (e) {
      return NextResponse.json({
        available: false,
        error: e instanceof Error ? e.message : String(e),
      });
    }
  }

  if (!url.searchParams.has("probe")) {
    return NextResponse.json({ ...status, probed: false });
  }
  if (!status.available) {
    return NextResponse.json({ ...status, probed: true, ok: false, error: "no key" });
  }
  const started = Date.now();
  const override = url.searchParams.get("model") ?? undefined;
  const text = await chat(
    [
      { role: "system", content: "Reply with one short sentence." },
      { role: "user", content: "Say that the outreach agent is online." },
    ],
    { maxTokens: 400, temperature: 0.2, model: override }
  );
  return NextResponse.json({
    ...status,
    probed: true,
    ok: Boolean(text),
    latencyMs: Date.now() - started,
    usedModel: override ?? status.model,
    sample: text,
    error: text ? null : getLastLlmError(),
    raw: url.searchParams.has("debug") ? getLastLlmRaw() : undefined,
  });
}
