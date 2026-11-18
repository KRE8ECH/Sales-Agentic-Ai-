import { NextResponse } from "next/server";
import { createPlaybook, listPlaybooks, setDefaultPlaybook } from "@/lib/repo";
import type { PlaybookStep } from "@/lib/types";

export async function GET() {
  return NextResponse.json(listPlaybooks());
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body?.name || !Array.isArray(body?.steps)) {
    return NextResponse.json({ error: "name and steps are required" }, { status: 400 });
  }
  const steps = (body.steps as PlaybookStep[]).map((s, i) => ({
    step: Number(s.step ?? i + 1),
    channel: (s.channel === "linkedin" ? "linkedin" : "email") as PlaybookStep["channel"],
    intent: (["insight", "proof", "ask", "breakup"].includes(String(s.intent))
      ? s.intent
      : "insight") as PlaybookStep["intent"],
    dayOffset: Number(s.dayOffset ?? i * 3),
  }));
  const pb = createPlaybook({
    name: String(body.name),
    description: String(body.description ?? ""),
    steps,
    isDefault: Boolean(body.isDefault),
  });
  return NextResponse.json(pb, { status: 201 });
}

export async function PATCH(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body?.id) return NextResponse.json({ error: "id is required" }, { status: 400 });
  setDefaultPlaybook(String(body.id));
  return NextResponse.json({ ok: true });
}
