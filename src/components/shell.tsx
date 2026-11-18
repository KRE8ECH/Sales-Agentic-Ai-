"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Inbox,
  Layers,
  ScrollText,
  Users,
} from "lucide-react";
import SimClock from "./sim-clock";
import CommandPalette, { type PaletteItem } from "./command-palette";

const NAV = [
  { href: "/", label: "Overview", icon: BarChart3 },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/decisions", label: "Decisions", icon: ScrollText },
  { href: "/playbooks", label: "Playbooks", icon: Layers },
];

export default function Shell({
  children,
  now,
  leads,
  dbMode,
}: {
  children: React.ReactNode;
  now: string;
  leads: Array<{ id: string; name: string; company: string }>;
  dbMode: "file" | "memory";
}) {
  const pathname = usePathname();

  const paletteItems: PaletteItem[] = [
    ...NAV.map((n) => ({ id: `nav:${n.href}`, label: n.label, group: "page", href: n.href })),
    ...leads.map((l) => ({
      id: `lead:${l.id}`,
      label: l.name,
      hint: l.company,
      group: "lead",
      href: `/leads/${l.id}`,
    })),
  ];
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-[228px] shrink-0 flex-col border-r border-line bg-paper-deep">
        <div className="flex items-center gap-2.5 px-4 h-14 border-b border-line">
          <div className="flex h-6 w-6 items-center justify-center rounded-[4px] bg-accent">
            <div className="grid grid-cols-2 gap-[2px]">
              <span className="h-[3px] w-[3px] rounded-full bg-white/90" />
              <span className="h-[3px] w-[3px] rounded-full bg-white/40" />
              <span className="h-[3px] w-[3px] rounded-full bg-white/40" />
              <span className="h-[3px] w-[3px] rounded-full bg-white/90" />
            </div>
          </div>
          <div className="leading-none">
            <div className="text-[13px] font-semibold tracking-[-0.01em]">Cadence</div>
            <div className="label mt-1">outreach console</div>
          </div>
        </div>

        <nav className="flex flex-col gap-0.5 px-2 py-3">
          {NAV.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 rounded-[4px] px-2.5 py-[7px] text-[13px] transition-colors duration-150 ${
                  active
                    ? "bg-white text-ink font-medium border border-line"
                    : "text-ink-soft hover:text-ink hover:bg-white/60 border border-transparent"
                }`}
              >
                <Icon size={15} strokeWidth={1.8} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto px-3 pb-4">
          <SimClock now={now} />
          {dbMode === "memory" ? (
            <p className="mt-2 rounded-[3px] border border-warn/30 bg-warn-wash px-2 py-1.5 font-mono text-[9.5px] leading-relaxed text-warn">
              ephemeral data · serverless build
            </p>
          ) : null}
          <p className="mt-2 text-center font-mono text-[10px] text-ink-faint">
            press <span className="text-ink-soft">/</span> to jump
          </p>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-[1180px] px-7 py-6">{children}</div>
      </main>
      <CommandPalette items={paletteItems} />
    </div>
  );
}
