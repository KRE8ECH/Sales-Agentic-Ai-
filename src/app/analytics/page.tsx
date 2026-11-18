import { listLeads, listReplies, listPlaybooks, getSimNow } from "@/lib/repo";
import { getSequence, getTouches } from "@/lib/repo";
import { Card, SectionTitle } from "@/components/ui";
import type { ReplyIntent } from "@/lib/types";

const INTENT_COLORS: Record<string, string> = {
  interested: "#0e6b62",
  objection: "#9a6700",
  ooo: "#2f5bd7",
  not_interested: "#b42318",
  no_reply: "#8d877d",
};

export default function AnalyticsPage() {
  const leads = listLeads();
  const replies = listReplies();
  const playbooks = listPlaybooks();
  const now = getSimNow();

  const sentTouches = leads.flatMap((l) => {
    const seq = getSequence(l.id);
    return seq ? getTouches(seq.id).filter((t) => t.status === "sent" || t.status === "replied") : [];
  });

  const classified = replies.filter((r) => r.intent !== null);
  const scored = classified.filter((r) => r.groundTruth !== null);
  const correct = scored.filter((r) => r.groundTruth === r.intent).length;
  const accuracy = scored.length ? correct / scored.length : null;
  const avgConfidence = classified.length
    ? classified.reduce((a, r) => a + (r.confidence ?? 0), 0) / classified.length
    : null;

  const intentCounts = new Map<string, number>();
  for (const r of classified) {
    intentCounts.set(r.intent!, (intentCounts.get(r.intent!) ?? 0) + 1);
  }

  const hookCoverage = (() => {
    let withHooks = 0;
    let total = 0;
    for (const l of leads) {
      const seq = getSequence(l.id);
      if (!seq) continue;
      for (const t of getTouches(seq.id)) {
        if (t.status === "scheduled" || t.status === "sent" || t.status === "replied") {
          total++;
          if (t.hookIds.length > 0) withHooks++;
        }
      }
    }
    return total ? withHooks / total : null;
  })();

  const stats = [
    { label: "Classification accuracy", value: accuracy === null ? "—" : `${Math.round(accuracy * 100)}%`, sub: `${correct}/${scored.length} graded` },
    { label: "Avg confidence", value: avgConfidence === null ? "—" : `${Math.round(avgConfidence * 100)}%`, sub: `${classified.length} classified` },
    { label: "Reply rate", value: sentTouches.length ? `${Math.round((replies.length / sentTouches.length) * 100)}%` : "—", sub: `${replies.length} replies / ${sentTouches.length} sent` },
    { label: "Hook coverage", value: hookCoverage === null ? "—" : `${Math.round(hookCoverage * 100)}%`, sub: "touches citing research" },
  ];

  const statusCounts = new Map<string, number>();
  for (const l of leads) statusCounts.set(l.status, (statusCounts.get(l.status) ?? 0) + 1);
  const maxStatus = Math.max(1, ...statusCounts.values());

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-[22px] font-semibold tracking-[-0.02em]">Analytics</h1>
        <p className="mt-1 text-[13px] text-ink-soft">
          The four things the brief asks you to prove: personalization, cadence soundness,
          classification accuracy, and escalation judgment.
        </p>
      </header>

      <div className="grid grid-cols-4 gap-3">
        {stats.map((s) => (
          <Card key={s.label} className="card-pad">
            <div className="text-[24px] font-semibold tracking-[-0.02em] text-accent-strong">
              {s.value}
            </div>
            <div className="label mt-1">{s.label}</div>
            <div className="mt-1 font-mono text-[10.5px] text-ink-faint">{s.sub}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-5 gap-4">
        <Card className="card-pad col-span-2 space-y-3">
          <SectionTitle hint={`${leads.length} leads`}>Pipeline funnel</SectionTitle>
          <div className="space-y-2">
            {[...statusCounts.entries()].map(([status, n]) => (
              <div key={status} className="flex items-center gap-2.5">
                <span className="w-[86px] shrink-0 font-mono text-[10.5px] uppercase tracking-wider text-ink-faint">
                  {status}
                </span>
                <div className="h-[16px] flex-1 rounded-[3px] bg-paper-deep overflow-hidden">
                  <div
                    className="h-full bg-accent/85 rounded-[3px]"
                    style={{ width: `${(n / maxStatus) * 100}%` }}
                  />
                </div>
                <span className="w-6 text-right font-mono text-[11px] text-ink-soft">{n}</span>
              </div>
            ))}
          </div>
          <p className="text-[12px] leading-relaxed text-ink-faint">
            Funnel movement is agent-driven: escalations and stops are decisions, not manual
            edits.
          </p>
        </Card>

        <Card className="card-pad col-span-3 space-y-3">
          <SectionTitle hint="classifier output">Reply intents</SectionTitle>
          {classified.length === 0 ? (
            <p className="text-[13px] text-ink-soft">No replies classified yet.</p>
          ) : (
            <>
              <Donut counts={intentCounts} />
              <ul className="grid grid-cols-2 gap-x-6 gap-y-1.5">
                {[...intentCounts.entries()].map(([intent, n]) => (
                  <li key={intent} className="flex items-center gap-2 text-[12.5px]">
                    <span
                      className="h-2.5 w-2.5 rounded-[2px]"
                      style={{ background: INTENT_COLORS[intent] ?? "#8d877d" }}
                    />
                    <span className="text-ink-soft">{intent.replace("_", " ")}</span>
                    <span className="ml-auto font-mono text-[11px] text-ink-faint">{n}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </Card>
      </div>

      <Card className="card-pad space-y-3">
        <SectionTitle hint={`${playbooks.length} templates`}>Reading the numbers</SectionTitle>
        <ul className="grid grid-cols-2 gap-x-8 gap-y-2 text-[13px] leading-relaxed text-ink-soft">
          <li>
            <span className="font-medium text-ink">Hook coverage</span> — share of drafted
            touches that cite a research hook. Anything below ~90% means the drafter fell back
            to a generic opener.
          </li>
          <li>
            <span className="font-medium text-ink">Classification accuracy</span> — compares the
            classifier against ground truth recorded by the simulator. It is honest only when
            replies were generated, not hand-picked.
          </li>
          <li>
            <span className="font-medium text-ink">Escalation judgment</span> — check the decision
            log: every escalate should trace to an interested reply or a late objection, never
            to silence.
          </li>
          <li>
            <span className="font-medium text-ink">Cadence soundness</span> — the planner never
            puts two touches on the same day, and intent always escalates toward a break-up.
          </li>
        </ul>
        <p className="font-mono text-[10.5px] text-ink-faint">
          sim time {now.slice(0, 10)} · data is local to this workspace
        </p>
      </Card>
    </div>
  );
}

function Donut({ counts }: { counts: Map<string, number> }) {
  const entries = [...counts.entries()];
  const total = entries.reduce((a, [, n]) => a + n, 0) || 1;
  const R = 34;
  const C = 2 * Math.PI * R;
  let offset = 0;
  return (
    <div className="flex items-center gap-5">
      <svg width="96" height="96" viewBox="0 0 96 96" role="img" aria-label="Reply intent distribution">
        <circle cx="48" cy="48" r={R} fill="none" stroke="#f3f1ec" strokeWidth="12" />
        {entries.map(([intent, n]) => {
          const frac = n / total;
          const dash = frac * C;
          const el = (
            <circle
              key={intent}
              cx="48"
              cy="48"
              r={R}
              fill="none"
              stroke={INTENT_COLORS[intent] ?? "#8d877d"}
              strokeWidth="12"
              strokeDasharray={`${dash} ${C - dash}`}
              strokeDashoffset={-offset}
              transform="rotate(-90 48 48)"
            />
          );
          offset += dash;
          return el;
        })}
        <text x="48" y="46" textAnchor="middle" fontSize="17" fontWeight="600" fill="#1a1917">
          {total}
        </text>
        <text x="48" y="60" textAnchor="middle" fontSize="8.5" fill="#8d877d" fontFamily="monospace">
          replies
        </text>
      </svg>
      <p className="text-[12px] leading-relaxed text-ink-faint">
        Intent mix across classified replies. A healthy sequence should produce more interest
        and objections than outright rejections.
      </p>
    </div>
  );
}
