import { NextResponse } from "next/server";
import { resetSim } from "@/lib/engine";
import { BOOT_ID } from "@/lib/boot";

export const dynamic = "force-dynamic";

/** Convenience GET so the demo can be reset from a link. */
export async function GET() {
  resetSim();
  return NextResponse.json({ ok: true, instance: BOOT_ID, message: "Simulation reseeded." });
}

export async function POST() {
  resetSim();
  return NextResponse.json({ ok: true, instance: BOOT_ID, message: "Simulation reseeded." });
}
