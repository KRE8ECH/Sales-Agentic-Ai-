import { NextResponse } from "next/server";
import { runPipeline } from "@/lib/engine";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body?.leadId) {
    return NextResponse.json({ error: "leadId is required" }, { status: 400 });
  }
  const result = await runPipeline(String(body.leadId));
  return NextResponse.json(result, { status: result.ok ? 200 : 400 });
}
