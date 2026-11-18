"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Play, Loader2 } from "lucide-react";

export default function RunPipeline({ leadId }: { leadId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setMsg(null);
    try {
      const res = await fetch("/api/pipeline/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ leadId }),
      });
      const data = await res.json();
      setMsg(data.message ?? (res.ok ? "Pipeline complete" : "Failed"));
      router.refresh();
    } catch {
      setMsg("Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      {msg ? <span className="font-mono text-[11px] text-ink-faint">{msg}</span> : null}
      <button className="btn btn-primary" onClick={run} disabled={busy}>
        {busy ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
        {busy ? "Running…" : "Run pipeline"}
      </button>
    </div>
  );
}
