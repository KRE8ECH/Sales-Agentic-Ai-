import { NextResponse } from "next/server";
import { runPipeline } from "@/lib/engine";
import { BOOT_ID } from "@/lib/boot";

export const dynamic = "force-dynamic";

/** Convenience GET so a pipeline run can be triggered from a link or health check. */
export async function GET(req: Request) {
  const leadId = new URL(req.url).searchParams.get("leadId");
  if (!leadId) {
    return NextResponse.json({ error: "leadId is required" }, { status: 400 });
  }
  const result = await runPipeline(leadId);
  return NextResponse.json({ ...result, instance: BOOT_ID });
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body?.leadId) {
    return NextResponse.json({ error: "leadId is required" }, { status: 400 });
  }
  const result = await runPipeline(String(body.leadId));
  return NextResponse.json({ ...result, instance: BOOT_ID }, { status: result.ok ? 200 : 400 });
}
