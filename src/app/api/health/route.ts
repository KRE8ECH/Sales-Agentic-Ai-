import { NextResponse } from "next/server";
import { DB_MODE } from "@/lib/db";
import { llmStatus } from "@/lib/llm";
import { getSimNow, listLeads } from "@/lib/repo";

// Unique per serverless instance — used to detect whether consecutive requests
// are served by the same warm instance or rotated to a fresh one.
const BOOT_ID = crypto.randomUUID();

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    instance: BOOT_ID,
    dbMode: DB_MODE,
    llm: llmStatus(),
    simNow: getSimNow(),
    leads: listLeads().length,
    vercel: Boolean(process.env.VERCEL),
  });
}
