"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Sparkles, Send } from "lucide-react";
import type { Lead, ReplyIntent } from "@/lib/types";

const SIM_INTENTS: Array<{ intent: ReplyIntent; label: string }> = [
  { intent: "interested", label: "Interested" },
  { intent: "objection", label: "Objection" },
  { intent: "ooo", label: "Out of office" },
  { intent: "not_interested", label: "Not interested" },
];

export default function ReplyConsole({ leads }: { leads: Lead[] }) {
  const router = useRouter();
  const [leadId, setLeadId] = useState(leads[0]?.id ?? "");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  async function post(url: string, payload: Record<string, unknown>) {
    setBusy(true);
    setNote(null);
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setNote(data.message ?? (res.ok ? "Done" : data.error ?? "Failed"));
      setBody("");
      router.refresh();
    } catch {
      setNote("Request failed");
    } finally {
      setBusy(false);
    }
  }

  if (leads.length === 0) {
    return (
      <p className="text-[13px] text-ink-soft">
        Add and run a lead first — then you can drive the inbox from here.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div>
        <label className="label mb-1.5 block">Lead</label>
        <select
          className="input"
          value={leadId}
          onChange={(e) => setLeadId(e.target.value)}
        >
          {leads.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name} · {l.company}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="label mb-1.5 block">Simulate a reply</label>
        <div className="flex flex-wrap gap-1.5">
          {SIM_INTENTS.map((s) => (
            <button
              key={s.intent}
              className="btn btn-ghost text-[12px]"
              disabled={busy || !leadId}
              onClick={() => post("/api/inbox/simulate", { leadId, intent: s.intent })}
            >
              <Sparkles size={12} /> {s.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="label mb-1.5 block">Or paste a real reply</label>
        <textarea
          className="input min-h-[92px] resize-y"
          placeholder="Paste the reply text exactly as it arrived…"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        <div className="mt-2 flex items-center gap-2">
          <button
            className="btn btn-primary"
            disabled={busy || !body.trim() || !leadId}
            onClick={() => post("/api/inbox/reply", { leadId, body })}
          >
            <Send size={13} /> Classify & decide
          </button>
          {note ? (
            <span className="font-mono text-[11px] text-ink-faint">{note}</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}
