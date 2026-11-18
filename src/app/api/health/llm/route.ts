import { NextResponse } from "next/server";
import { chat, llmStatus } from "@/lib/llm";

export const dynamic = "force-dynamic";

/** Diagnostic: reports provider status, and with ?probe=1 makes one real call. */
export async function GET(req: Request) {
  const status = llmStatus();
  if (!new URL(req.url).searchParams.has("probe")) {
    return NextResponse.json({ ...status, probed: false });
  }
  if (!status.available) {
    return NextResponse.json({ ...status, probed: true, ok: false, error: "no key" });
  }
  const started = Date.now();
  const text = await chat(
    [
      { role: "system", content: "Reply with one short sentence." },
      { role: "user", content: "Say that the outreach agent is online." },
    ],
    { maxTokens: 40, temperature: 0.2 }
  );
  return NextResponse.json({
    ...status,
    probed: true,
    ok: Boolean(text),
    latencyMs: Date.now() - started,
    sample: text,
  });
}
