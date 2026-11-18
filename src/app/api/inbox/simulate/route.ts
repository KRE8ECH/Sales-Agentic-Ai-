import { NextResponse } from "next/server";
import { simulateReply } from "@/lib/engine";
import type { ReplyIntent } from "@/lib/types";

const VALID: ReplyIntent[] = ["interested", "not_interested", "objection", "ooo", "no_reply"];

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body?.leadId || !VALID.includes(body?.intent)) {
    return NextResponse.json(
      { error: "leadId and a valid intent are required" },
      { status: 400 }
    );
  }
  const result = await simulateReply(String(body.leadId), String(body.intent) as ReplyIntent);
  return NextResponse.json(result, { status: result.ok ? 200 : 400 });
}
