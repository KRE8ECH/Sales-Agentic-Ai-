import { NextResponse } from "next/server";
import { chat, getLastLlmError, llmStatus } from "@/lib/llm";

export const dynamic = "force-dynamic";

/** Diagnostic: reports provider status, ?probe=1 makes a real call, ?list=1 lists models. */
export async function GET(req: Request) {
  const url = new URL(req.url);
  const status = llmStatus();

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
    { maxTokens: 40, temperature: 0.2, model: override }
  );
  return NextResponse.json({
    ...status,
    probed: true,
    ok: Boolean(text),
    latencyMs: Date.now() - started,
    usedModel: override ?? status.model,
    sample: text,
    error: text ? null : getLastLlmError(),
  });
}
