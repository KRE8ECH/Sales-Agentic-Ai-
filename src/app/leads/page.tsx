import Link from "next/link";
import { listLeads, getSimNow } from "@/lib/repo";
import { Card, StatusChip, Health, EmptyState } from "@/components/ui";
import { formatSim, relDay } from "@/lib/format";
import AddLeadForm from "@/components/add-lead";
import RunPendingButton from "@/components/run-pending";
import { Avatar } from "@/components/ui";

export default function LeadsPage() {
  const leads = listLeads();
  const now = getSimNow();

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-[22px] font-semibold tracking-[-0.02em]">Leads</h1>
          <p className="mt-1 text-[13px] text-ink-soft">
            {leads.length} leads in the book · {leads.filter((l) => l.status === "new").length} awaiting
            research
          </p>
        </div>
        <div className="flex items-center gap-2">
          <RunPendingButton />
          <AddLeadForm />
        </div>
      </header>

      {leads.length === 0 ? (
        <EmptyState
          title="No leads yet"
          body="Add a lead to start the pipeline. The research agent will build a brief, the planner will set a cadence, and the drafter will write every touch from real context."
        />
      ) : (
        <Card>
          <table className="w-full">
            <thead>
              <tr>
                <th className="th">Lead</th>
                <th className="th">Stage</th>
                <th className="th">Health</th>
                <th className="th">Next action</th>
                <th className="th">Next touch</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((l) => (
                <tr key={l.id} className="group">
                  <td className="td">
                    <Link href={`/leads/${l.id}`} className="flex items-center gap-2.5">
                      <Avatar name={l.name} />
                      <div>
                        <div className="font-medium text-ink group-hover:text-accent-strong transition-colors">
                          {l.name}
                        </div>
                        <div className="text-[12px] text-ink-faint">
                          {l.role} · {l.company}
                        </div>
                      </div>
                    </Link>
                  </td>
                  <td className="td">
                    <StatusChip status={l.status} />
                  </td>
                  <td className="td">
                    <Health value={l.health} />
                  </td>
                  <td className="td text-ink-soft max-w-[280px]">
                    <span className="line-clamp-1">{l.nextAction ?? "—"}</span>
                  </td>
                  <td className="td font-mono text-[11.5px] text-ink-soft whitespace-nowrap">
                    {l.nextTouchAt ? `${formatSim(l.nextTouchAt)} · ${relDay(l.nextTouchAt, now)}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
