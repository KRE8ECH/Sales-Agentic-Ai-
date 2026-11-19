import Link from "next/link";
import { listEvents, listLeads, listReplies, getSequence, getTouches, getSimNow } from "@/lib/repo";
import { addDays } from "@/lib/graph";
import { Card, SectionTitle, StatusChip, Health } from "@/components/ui";
import { fullSim } from "@/lib/format";
import { ArrowRight, Radar } from "lucide-react";

const STATUS_ORDER = [
  "new",
  "researching",
  "sequencing",
  "active",
  "paused",
  "escalated",
  "stopped",
  "won",
] as const;

export default function OverviewPage() {
  const leads = listLeads();
  const events = listEvents(14);
  const now = getSimNow();

  const counts = new Map<string, number>();
  for (const l of leads) counts.set(l.status, (counts.get(l.status) ?? 0) + 1);
  const total = leads.length || 1;

  const active = leads.filter((l) => l.status === "active").length;
  const paused = leads.filter((l) => l.status === "paused").length;
  const untouched = leads.filter((l) => l.status === "new").length;

  const replies = listReplies();
  const sentTouches = leads.reduce((a, l) => {
    const seq = getSequence(l.id);
    return a + (seq ? getTouches(seq.id).filter((t) => t.status !== "scheduled").length : 0);
  }, 0);
  const dueNext7 = leads.reduce((a, l) => {
    const seq = getSequence(l.id);
    if (!seq) return a;
    return (
      a +
      getTouches(seq.id).filter(
        (t) => t.status === "scheduled" && t.sendAt && t.sendAt <= addDays(now, 7)
      ).length
    );
  }, 0);
  const escalated = leads.filter((l) => l.status === "escalated").length;
  const forecast = [
    {
      label: "Human handoffs",
      value: String(escalated),
      sub: "leads the agent says you should own",
    },
    {
      label: "Reply rate",
      value: sentTouches ? `${Math.round((replies.length / sentTouches) * 100)}%` : "—",
      sub: `${replies.length} replies on ${sentTouches} touches`,
    },
    {
      label: "Touches due in 7 days",
      value: String(dueNext7),
      sub: "scheduled by the planner",
    },
    {
      label: "Coverage",
      value: `${Math.round(((leads.length - untouched) / total) * 100)}%`,
      sub: "leads with a live sequence",
    },
  ];

  const attention = leads
    .filter((l) => ["escalated", "paused", "new", "researching"].includes(l.status))
    .slice(0, 6);

  const stats = [
    { label: "Active sequences", value: active, tone: "text-accent-strong" },
    { label: "Escalated to human", value: escalated, tone: "text-warn" },
    { label: "Paused (OOO)", value: paused, tone: "text-info" },
    { label: "Untouched leads", value: untouched, tone: "text-ink-soft" },
  ];

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-[22px] font-semibold tracking-[-0.02em]">Overview</h1>
          <p className="mt-1 text-[13px] text-ink-soft">
            Autonomous multi-touch outreach across {leads.length} leads · sim time{" "}
            <span className="font-mono text-[12px]">{fullSim(now)}</span>
          </p>
        </div>
        <Link href="/leads" className="btn btn-primary">
          <Radar size={14} /> Open pipeline
        </Link>
      </header>

      <div className="grid grid-cols-4 gap-3">
        {stats.map((s) => (
          <Card key={s.label} className="card-pad">
            <div className={`text-[26px] font-semibold tracking-[-0.02em] ${s.tone}`}>
              {s.value}
            </div>
            <div className="label mt-1">{s.label}</div>
          </Card>
        ))}
      </div>

      <Card className="card-pad">
        <div className="flex items-center justify-between gap-6">
          {forecast.map((f) => (
            <div key={f.label} className="min-w-0">
              <div className="text-[19px] font-semibold tracking-[-0.015em] text-ink">
                {f.value}
              </div>
              <div className="label mt-0.5">{f.label}</div>
              <div className="mt-1 text-[11.5px] text-ink-faint">{f.sub}</div>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-5 gap-4">
        <Card className="card-pad col-span-2 space-y-4">
          <SectionTitle hint={`${leads.length} total`}>Pipeline by stage</SectionTitle>
          <div className="space-y-2">
            {STATUS_ORDER.map((status) => {
              const n = counts.get(status) ?? 0;
              return (
                <div key={status} className="flex items-center gap-2.5">
                  <span className="w-[86px] shrink-0 font-mono text-[10.5px] uppercase tracking-wider text-ink-faint">
                    {status}
                  </span>
                  <div className="h-[14px] flex-1 rounded-[3px] bg-paper-deep overflow-hidden">
                    <div
                      className={`h-full rounded-[3px] transition-all duration-300 ${
                        status === "escalated"
                          ? "bg-warn"
                          : status === "stopped"
                            ? "bg-bad/70"
                            : status === "active"
                              ? "bg-accent"
                              : "bg-line-strong"
                      }`}
                      style={{ width: `${Math.max(n > 0 ? 4 : 0, (n / total) * 100)}%` }}
                    />
                  </div>
                  <span className="w-6 text-right font-mono text-[11px] text-ink-soft">{n}</span>
                </div>
              );
            })}
          </div>
          <p className="text-[12px] leading-relaxed text-ink-faint">
            Stage is driven by the next-step agent, not by hand. Escalations are the leads a
            human should take over today.
          </p>
        </Card>

        <div className="col-span-3 space-y-4">
          <Card className="card-pad">
            <SectionTitle hint="action needed">Needs attention</SectionTitle>
            {attention.length === 0 ? (
              <p className="mt-3 text-[13px] text-ink-soft">
                Nothing needs you right now. The agents are working the rest.
              </p>
            ) : (
              <ul className="mt-2 divide-y divide-line">
                {attention.map((l) => (
                  <li key={l.id}>
                    <Link
                      href={`/leads/${l.id}`}
                      className="flex items-center gap-3 py-2.5 group"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="text-[13px] font-medium text-ink group-hover:text-accent-strong transition-colors">
                          {l.name} <span className="text-ink-faint font-normal">· {l.company}</span>
                        </div>
                        <div className="text-[12px] text-ink-soft truncate">{l.nextAction}</div>
                      </div>
                      <Health value={l.health} />
                      <StatusChip status={l.status} />
                      <ArrowRight size={13} className="text-ink-faint group-hover:text-ink transition-colors" />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card className="card-pad">
            <SectionTitle hint="latest">Agent activity</SectionTitle>
            {events.length === 0 ? (
              <p className="mt-3 text-[13px] text-ink-soft">No activity yet.</p>
            ) : (
              <ul className="mt-2 space-y-0">
                {events.map((e) => (
                  <li key={e.id} className="flex gap-3 border-b border-line py-2 last:border-0">
                    <span className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full bg-accent/70" />
                    <div className="min-w-0">
                      <p className="text-[12.5px] leading-snug text-ink">{e.message}</p>
                      <p className="font-mono text-[10.5px] text-ink-faint mt-0.5">
                        {fullSim(e.createdAt)}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
