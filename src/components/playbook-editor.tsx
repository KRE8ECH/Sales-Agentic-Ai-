"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Plus, Star } from "lucide-react";
import type { Playbook } from "@/lib/types";

export default function PlaybookEditor({ playbooks }: { playbooks: Playbook[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [rows, setRows] = useState([
    { channel: "email", intent: "insight", dayOffset: 0 },
    { channel: "linkedin", intent: "proof", dayOffset: 2 },
    { channel: "email", intent: "ask", dayOffset: 5 },
    { channel: "linkedin", intent: "breakup", dayOffset: 9 },
  ]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await fetch("/api/playbooks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          steps: rows.map((r, i) => ({ ...r, step: i + 1 })),
        }),
      });
      if (res.ok) {
        setOpen(false);
        setName("");
        setDescription("");
        router.refresh();
      }
    } finally {
      setBusy(false);
    }
  }

  async function makeDefault(id: string) {
    await fetch("/api/playbooks", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    router.refresh();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-[13px] text-ink-soft">
          Cadence templates: channel mix, day gaps, and the intent curve.
        </p>
        <button className="btn btn-primary" onClick={() => setOpen(!open)}>
          <Plus size={14} /> New playbook
        </button>
      </div>

      {open ? (
        <form onSubmit={submit} className="card card-pad space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <input
              className="input"
              placeholder="Playbook name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <input
              className="input"
              placeholder="Short description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <table className="w-full">
            <thead>
              <tr>
                <th className="th">Step</th>
                <th className="th">Channel</th>
                <th className="th">Intent</th>
                <th className="th">Day offset</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td className="td font-mono text-[11px] text-ink-faint">{i + 1}</td>
                  <td className="td">
                    <select
                      className="input"
                      value={r.channel}
                      onChange={(e) =>
                        setRows(rows.map((x, j) => (j === i ? { ...x, channel: e.target.value } : x)))
                      }
                    >
                      <option value="email">email</option>
                      <option value="linkedin">linkedin</option>
                    </select>
                  </td>
                  <td className="td">
                    <select
                      className="input"
                      value={r.intent}
                      onChange={(e) =>
                        setRows(rows.map((x, j) => (j === i ? { ...x, intent: e.target.value } : x)))
                      }
                    >
                      <option value="insight">insight</option>
                      <option value="proof">proof</option>
                      <option value="ask">ask</option>
                      <option value="breakup">breakup</option>
                    </select>
                  </td>
                  <td className="td">
                    <input
                      className="input w-20"
                      type="number"
                      min={0}
                      value={r.dayOffset}
                      onChange={(e) =>
                        setRows(
                          rows.map((x, j) =>
                            j === i ? { ...x, dayOffset: Number(e.target.value) } : x
                          )
                        )
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="btn btn-ghost text-[12px]"
              onClick={() => setRows([...rows, { channel: "email", intent: "ask", dayOffset: 12 }])}
            >
              <Plus size={12} /> Add step
            </button>
            <div className="ml-auto flex gap-2">
              <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy || !name}>
                Save playbook
              </button>
            </div>
          </div>
        </form>
      ) : null}

      <div className="grid grid-cols-2 gap-3">
        {playbooks.map((pb) => (
          <div key={pb.id} className="card card-pad space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[14px] font-semibold">{pb.name}</span>
                  {pb.isDefault ? <span className="chip border-accent/30 bg-accent-wash text-accent-strong">default</span> : null}
                </div>
                <p className="mt-1 text-[12.5px] text-ink-soft leading-relaxed">{pb.description}</p>
              </div>
              {!pb.isDefault ? (
                <button
                  className="btn btn-quiet text-[12px]"
                  onClick={() => makeDefault(pb.id)}
                  title="Make default"
                >
                  <Star size={13} />
                </button>
              ) : null}
            </div>
            <ol className="space-y-1.5">
              {pb.steps.map((s) => (
                <li key={s.step} className="flex items-center gap-2 font-mono text-[11px] text-ink-soft">
                  <span className="text-ink-faint">{s.step}.</span>
                  <span className="uppercase tracking-wider">{s.channel}</span>
                  <span className="text-accent-strong">{s.intent}</span>
                  <span className="ml-auto">day {s.dayOffset}</span>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </div>
  );
}
