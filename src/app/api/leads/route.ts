import { NextResponse } from "next/server";
import { createLead, listLeads } from "@/lib/repo";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body?.name || !body?.company || !body?.role) {
    return NextResponse.json({ error: "name, role and company are required" }, { status: 400 });
  }
  const lead = createLead({
    name: String(body.name),
    role: String(body.role),
    company: String(body.company),
    email: String(body.email ?? ""),
    linkedin: String(body.linkedin ?? ""),
    persona: String(body.persona ?? ""),
  });
  return NextResponse.json(lead, { status: 201 });
}

export async function GET() {
  return NextResponse.json(listLeads());
}
