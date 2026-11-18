"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Plus, X } from "lucide-react";

export default function AddLeadForm() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    name: "",
    role: "",
    company: "",
    email: "",
    linkedin: "",
  });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name || !form.company || !form.role) return;
    setBusy(true);
    try {
      const res = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        const lead = await res.json();
        router.push(`/leads/${lead.id}`);
        router.refresh();
      }
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button className="btn btn-primary" onClick={() => setOpen(true)}>
        <Plus size={14} /> Add lead
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-ink/25 p-6 pt-[12vh]">
      <div className="card w-full max-w-[460px] card-pad space-y-4 shadow-pop">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-[15px] font-semibold">Add a lead</h2>
            <p className="mt-0.5 text-[12.5px] text-ink-soft">
              The research agent will try to match the company in the knowledge base.
            </p>
          </div>
          <button className="btn btn-quiet -mr-2 -mt-2" onClick={() => setOpen(false)}>
            <X size={14} />
          </button>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <Field label="Full name" required>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Mara Whitfield"
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Role" required>
              <input
                className="input"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                placeholder="VP Revenue Operations"
              />
            </Field>
            <Field label="Company" required>
              <input
                className="input"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                placeholder="Northwind Freight"
              />
            </Field>
          </div>
          <Field label="Work email">
            <input
              className="input"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="name@company.com"
            />
          </Field>
          <Field label="LinkedIn">
            <input
              className="input"
              value={form.linkedin}
              onChange={(e) => setForm({ ...form, linkedin: e.target.value })}
              placeholder="linkedin.com/in/handle"
            />
          </Field>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Adding…" : "Add lead"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="label mb-1.5 block">
        {label}
        {required ? <span className="text-bad"> *</span> : null}
      </span>
      {children}
    </label>
  );
}
