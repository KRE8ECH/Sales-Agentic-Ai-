"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Play, Loader2 } from "lucide-react";

export default function RunPendingButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  async function runAll() {
    setBusy(true);
    setNote("running…");
    try {
      const res = await fetch("/api/leads");
      const leads = (await res.json()) as Array<{ id: string; name: string; status: string }>;
      const pending = leads.filter((l) => l.status === "new" || l.status === "researching");
      let done = 0;
      for (const lead of pending) {
        const r = await fetch("/api/pipeline/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ leadId: lead.id }),
        });
        if (r.ok) done++;
      }
      setNote(`${done}/${pending.length} pipelines started`);
      router.refresh();
    } catch {
      setNote("Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      {note ? <span className="font-mono text-[11px] text-ink-faint">{note}</span> : null}
      <button className="btn btn-ghost" onClick={runAll} disabled={busy}>
        {busy ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
        Run pending
      </button>
    </div>
  );
}
