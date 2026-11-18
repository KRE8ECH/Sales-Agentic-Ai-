import { NextResponse } from "next/server";
import { resetSim } from "@/lib/engine";

export const dynamic = "force-dynamic";

/** Convenience GET so the demo can be reset from a link. */
export async function GET() {
  resetSim();
  return NextResponse.json({ ok: true, message: "Simulation reseeded." });
}

export async function POST() {
  resetSim();
  return NextResponse.json({ ok: true, message: "Simulation reseeded." });
}
