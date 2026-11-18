import { listLeads, listReplies, getSimNow } from "@/lib/repo";
import { Card, SectionTitle, ReplyBadge } from "@/components/ui";
import ReplyConsole from "@/components/reply-console";
import { formatSim, relDay } from "@/lib/format";
import { Mail, Globe } from "lucide-react";

export default function InboxPage() {
  const leads = listLeads();
  const replies = listReplies();
  const now = getSimNow();
  const leadById = new Map(leads.map((l) => [l.id, l]));
  const runnable = leads.filter((l) => l.status !== "new");

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-[22px] font-semibold tracking-[-0.02em]">Inbox</h1>
        <p className="mt-1 text-[13px] text-ink-soft">
          Replies land here, get classified, and drive the next-step agent. Simulate a reply
          or paste a real one.
        </p>
      </header>

      <div className="grid grid-cols-5 gap-4">
        <Card className="card-pad col-span-2">
          <SectionTitle hint="simulated sender">Reply console</SectionTitle>
          <div className="mt-3">
            <ReplyConsole leads={runnable} />
          </div>
        </Card>

        <Card className="col-span-3">
          <table className="w-full">
            <thead>
              <tr>
                <th className="th">Lead</th>
                <th className="th">Channel</th>
                <th className="th">Classified</th>
                <th className="th">Reply</th>
                <th className="th">When</th>
              </tr>
            </thead>
            <tbody>
              {replies.length === 0 ? (
                <tr>
                  <td className="td" colSpan={5}>
                    <span className="text-ink-soft">
                      No replies yet. Use the console, or advance the simulation clock.
                    </span>
                  </td>
                </tr>
              ) : (
                replies.map((r) => {
                  const lead = leadById.get(r.leadId);
                  return (
                    <tr key={r.id}>
                      <td className="td">
                        <div className="font-medium text-ink">{lead?.name ?? r.leadId}</div>
                        <div className="text-[12px] text-ink-faint">{lead?.company}</div>
                      </td>
                      <td className="td">
                        <span className="flex items-center gap-1.5 font-mono text-[11px] text-ink-soft">
                          {r.channel === "email" ? <Mail size={12} /> : <Globe size={12} />}
                          {r.channel}
                        </span>
                      </td>
                      <td className="td">
                        <div className="flex items-center gap-2">
                          <ReplyBadge intent={r.intent} />
                          {r.confidence ? (
                            <span className="font-mono text-[10.5px] text-ink-faint">
                              {Math.round(r.confidence * 100)}%
                            </span>
                          ) : null}
                        </div>
                      </td>
                      <td className="td max-w-[340px]">
                        <span className="line-clamp-2 text-ink-soft">{r.body}</span>
                      </td>
                      <td className="td font-mono text-[11px] text-ink-soft whitespace-nowrap">
                        {formatSim(r.arrivedAt)} · {relDay(r.arrivedAt, now)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}
