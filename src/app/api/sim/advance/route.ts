import { NextResponse } from "next/server";
import { advanceSim } from "@/lib/engine";
import { fullSim } from "@/lib/format";

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const days = Number(body?.days ?? 1);
  if (!Number.isFinite(days) || days <= 0 || days > 60) {
    return NextResponse.json({ error: "days must be between 1 and 60" }, { status: 400 });
  }
  const result = await advanceSim(days);
  const summary =
    `clock → ${fullSim(result.now)} · ${result.sent} touch(es) sent · ` +
    `${result.replies.length} reply(ies) classified · ${result.decisions} decision(s)`;
  return NextResponse.json({ ...result, summary });
}
