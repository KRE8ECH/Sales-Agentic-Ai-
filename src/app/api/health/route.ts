import { NextResponse } from "next/server";
import { DB_MODE, getDb } from "@/lib/db";
import { llmStatus } from "@/lib/llm";
import { getSimNow, listLeads } from "@/lib/repo";
import { BOOT_ID } from "@/lib/boot";

export const dynamic = "force-dynamic";

export async function GET() {
  const db = getDb();
  const count = (t: string) =>
    (db.prepare(`SELECT COUNT(*) AS c FROM ${t}`).get() as { c: number }).c;
  return NextResponse.json({
    instance: BOOT_ID,
    dbMode: DB_MODE,
    llm: llmStatus(),
    simNow: getSimNow(),
    leads: listLeads().length,
    sequences: count("sequences"),
    touches: count("touches"),
    decisions: count("decisions"),
    vercel: Boolean(process.env.VERCEL),
  });
}
