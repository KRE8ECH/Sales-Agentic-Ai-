import { NextResponse } from "next/server";
import { DB_MODE } from "@/lib/db";
import { llmStatus } from "@/lib/llm";
import { getSimNow, listLeads } from "@/lib/repo";
import { BOOT_ID } from "@/lib/boot";

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
