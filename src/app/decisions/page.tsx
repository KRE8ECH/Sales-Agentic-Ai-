import { listDecisions, listLeads } from "@/lib/repo";
import { Card, SectionTitle } from "@/components/ui";
import { fullSim } from "@/lib/format";

const AGENTS = ["research", "planner", "drafter", "sender", "classifier", "nextstep"];

export default async function DecisionsPage({
  searchParams,
}: {
  searchParams: Promise<{ agent?: string }>;
}) {
  const { agent } = await searchParams;
  const decisions = listDecisions({ agent, limit: 300 });
  const leads = listLeads();
  const leadById = new Map(leads.map((l) => [l.id, l]));

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-[22px] font-semibold tracking-[-0.02em]">Decision log</h1>
          <p className="mt-1 text-[13px] text-ink-soft">
            Every agent action, its reasoning, and the evidence it relied on. This is the
            audit trail — nothing happens here without a record.
          </p>
        </div>
        <div className="flex gap-1.5">
          <a
            href="/decisions"
            className={`btn text-[12px] ${!agent ? "btn-primary" : "btn-ghost"}`}
          >
            All
          </a>
          {AGENTS.map((a) => (
            <a
              key={a}
              href={`/decisions?agent=${a}`}
              className={`btn text-[12px] ${agent === a ? "btn-primary" : "btn-ghost"}`}
            >
              {a}
            </a>
          ))}
        </div>
      </header>

      <Card className="card-pad">
        {decisions.length === 0 ? (
          <p className="text-[13px] text-ink-soft">No decisions recorded yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {decisions.map((d) => {
              const lead = d.leadId ? leadById.get(d.leadId) : null;
              return (
                <li key={d.id} className="grid grid-cols-[96px_150px_150px_1fr] gap-3 py-3">
                  <span className="font-mono text-[10.5px] uppercase tracking-wider text-ink-faint pt-0.5">
                    {d.agent}
                  </span>
                  <span className="font-mono text-[11px] text-accent-strong pt-0.5">
                    {d.action}
                  </span>
                  <span className="text-[12px] text-ink-soft pt-0.5">
                    {lead ? (
                      <a href={`/leads/${lead.id}`} className="hover:text-accent-strong">
                        {lead.name}
                      </a>
                    ) : (
                      <span className="text-ink-faint">system</span>
                    )}
                  </span>
                  <div className="min-w-0">
                    <p className="text-[12.5px] leading-relaxed text-ink">{d.reason}</p>
                    {d.evidence ? (
                      <p className="mt-0.5 font-mono text-[10.5px] leading-relaxed text-ink-faint">
                        {d.evidence}
                      </p>
                    ) : null}
                    <p className="mt-0.5 font-mono text-[10px] text-ink-faint">
                      {fullSim(d.createdAt)}
                      {d.confidence ? ` · confidence ${Math.round(d.confidence * 100)}%` : ""}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
