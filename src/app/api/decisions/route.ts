import { NextResponse } from "next/server";
import { listDecisions } from "@/lib/repo";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const leadId = url.searchParams.get("leadId") ?? undefined;
  const agent = url.searchParams.get("agent") ?? undefined;
  return NextResponse.json(listDecisions({ leadId, agent, limit: 200 }));
}
