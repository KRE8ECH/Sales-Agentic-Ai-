"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Clock, RotateCcw } from "lucide-react";
import { fullSim } from "@/lib/format";

export default function SimClock({ now }: { now: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  async function advance(days: number) {
    setBusy(true);
    setNote(null);
    try {
      const res = await fetch("/api/sim/advance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days }),
      });
      const data = await res.json();
      if (data?.summary) setNote(data.summary);
      router.refresh();
    } catch {
      setNote("Advance failed");
    } finally {
      setBusy(false);
    }
  }

  async function reset() {
    if (!confirm("Reset the simulation? All leads, replies, and decisions will be reseeded.")) return;
    setBusy(true);
    try {
      await fetch("/api/sim/reset", { method: "POST" });
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card card-pad space-y-2.5">
      <div className="flex items-center gap-2">
        <Clock size={13} className="text-ink-faint" />
        <span className="label">Simulation clock</span>
      </div>
      <div className="font-mono text-[12.5px] text-ink">{fullSim(now)}</div>
      <div className="flex items-center gap-1.5">
        <button
          className="btn btn-ghost flex-1 justify-center"
          disabled={busy}
          onClick={() => advance(1)}
        >
          +1 day
        </button>
        <button
          className="btn btn-ghost flex-1 justify-center"
          disabled={busy}
          onClick={() => advance(7)}
        >
          +7 days
        </button>
      </div>
      <button
        className="btn btn-quiet w-full justify-center text-[12px]"
        disabled={busy}
        onClick={reset}
      >
        <RotateCcw size={12} /> Reset simulation
      </button>
      {note ? (
        <p className="font-mono text-[10.5px] leading-relaxed text-ink-faint">{note}</p>
      ) : null}
    </div>
  );
}
