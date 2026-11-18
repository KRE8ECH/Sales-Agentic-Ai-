"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, CornerDownLeft } from "lucide-react";

export interface PaletteItem {
  id: string;
  label: string;
  hint?: string;
  group: string;
  href: string;
}

export default function CommandPalette({ items }: { items: PaletteItem[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [cursor, setCursor] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      const typing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
        return;
      }
      if (e.key === "/" && !typing) {
        e.preventDefault();
        setOpen(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (open) {
      setQ("");
      setCursor(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((i) =>
      `${i.label} ${i.hint ?? ""} ${i.group}`.toLowerCase().includes(needle)
    );
  }, [items, q]);

  function go(href: string) {
    setOpen(false);
    router.push(href);
  }

  function onInputKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(c + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(c - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const item = filtered[cursor];
      if (item) go(item.href);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-ink/25 p-6 pt-[10vh]"
      onMouseDown={() => setOpen(false)}
    >
      <div
        className="card w-full max-w-[560px] overflow-hidden shadow-pop"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2.5 border-b border-line px-3.5 py-3">
          <Search size={14} className="text-ink-faint" />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setCursor(0);
            }}
            onKeyDown={onInputKey}
            placeholder="Jump to a page or lead…"
            className="w-full bg-transparent text-[13.5px] outline-none placeholder:text-ink-faint"
          />
          <span className="font-mono text-[10px] text-ink-faint">esc</span>
        </div>
        <ul className="max-h-[320px] overflow-y-auto py-1.5">
          {filtered.length === 0 ? (
            <li className="px-4 py-6 text-[13px] text-ink-faint">No matches.</li>
          ) : (
            filtered.map((item, i) => (
              <li key={item.id}>
                <button
                  className={`flex w-full items-center gap-3 px-3.5 py-2 text-left text-[13px] ${
                    i === cursor ? "bg-accent-wash text-accent-strong" : "text-ink"
                  }`}
                  onMouseEnter={() => setCursor(i)}
                  onClick={() => go(item.href)}
                >
                  <span className="label w-[74px] shrink-0">{item.group}</span>
                  <span className="min-w-0 flex-1 truncate">{item.label}</span>
                  {item.hint ? (
                    <span className="font-mono text-[10.5px] text-ink-faint">{item.hint}</span>
                  ) : null}
                  {i === cursor ? <CornerDownLeft size={12} /> : null}
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
