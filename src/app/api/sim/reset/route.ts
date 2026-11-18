import { NextResponse } from "next/server";
import { resetSim } from "@/lib/engine";

export async function POST() {
  resetSim();
  return NextResponse.json({ ok: true, message: "Simulation reseeded." });
}
