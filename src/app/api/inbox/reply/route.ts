import { NextResponse } from "next/server";
import { handleIncomingReply } from "@/lib/engine";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body?.leadId || !body?.body) {
    return NextResponse.json({ error: "leadId and body are required" }, { status: 400 });
  }
  const result = await handleIncomingReply({
    leadId: String(body.leadId),
    body: String(body.body),
    touchId: body.touchId ? String(body.touchId) : null,
    groundTruth: body.groundTruth ? (String(body.groundTruth) as never) : null,
  });
  return NextResponse.json(result, { status: result.ok ? 200 : 400 });
}
