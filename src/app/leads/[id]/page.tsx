import { notFound } from "next/navigation";
import Link from "next/link";
import {
  getBrief,
  getHooks,
  getLead,
  getSequence,
  getTouches,
  listDecisions,
  listReplies,
} from "@/lib/repo";
import { Card, SectionTitle, StatusChip, Health, IntentBadge, ReplyBadge, HookKindChip, Avatar } from "@/components/ui";
import RunPipeline from "@/components/run-pipeline";
import { formatSim, fullSim, relDay } from "@/lib/format";
import type { Touch } from "@/lib/types";
import { ArrowLeft, Mail, Globe } from "lucide-react";

export default async function LeadDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const lead = getLead(id);
  if (!lead) notFound();

  const brief = getBrief(id);
  const hooks = getHooks(id);
  const sequence = getSequence(id);
  const touches = sequence ? getTouches(sequence.id) : [];
  const replies = listReplies(id);
  const decisions = listDecisions({ leadId: id, limit: 120 });
  const now = sequence?.startedAt ?? lead.createdAt;

  const escalation = [...decisions]
    .reverse()
    .find((d) => d.agent === "nextstep" && d.action === "escalate");

  const hookById = new Map(hooks.map((h) => [h.id, h]));

  return (
    <div className="space-y-5">
      <div>
        <Link href="/leads" className="btn btn-quiet -ml-2 mb-3 text-[12px]">
          <ArrowLeft size={13} /> All leads
        </Link>
        <Card className="card-pad">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <Avatar name={lead.name} />
              <div>
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h1 className="text-[19px] font-semibold tracking-[-0.015em]">{lead.name}</h1>
                  <StatusChip status={lead.status} />
                </div>
                <p className="mt-0.5 text-[13px] text-ink-soft">
                  {lead.role} · {lead.company}
                </p>
                <p className="mt-1.5 font-mono text-[11px] text-ink-faint">
                  {lead.email} {lead.linkedin ? `· ${lead.linkedin}` : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="label mb-1">Health</div>
                <Health value={lead.health} />
              </div>
              {lead.status === "new" || lead.status === "researching" ? (
                <RunPipeline leadId={lead.id} />
              ) : null}
            </div>
          </div>
          <hr className="rule my-4" />
          <div className="grid grid-cols-3 gap-4">
            <Meta label="Next action" value={lead.nextAction ?? "—"} />
            <Meta
              label="Next touch"
              value={
                lead.nextTouchAt
                  ? `${formatSim(lead.nextTouchAt)} · ${relDay(lead.nextTouchAt, now)}`
                  : "—"
              }
            />
            <Meta
              label="Sequence"
              value={
                sequence
                  ? `${touches.length} touches · ${sequence.status}`
                  : "not planned yet"
              }
            />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 space-y-4">
          <Card className="card-pad space-y-4">
            <SectionTitle hint={brief ? "research agent" : "not run"}>
              Research brief
            </SectionTitle>
            {brief ? (
              <>
                <BriefBlock label="Company" text={brief.snapshot} />
                <BriefBlock label="Role" text={brief.roleContext} />
                <BriefBlock label="Persona" text={brief.personaNotes} />
                <div>
                  <div className="label mb-2">Personalization hooks</div>
                  <ul className="space-y-2">
                    {hooks.map((h) => (
                      <li key={h.id} className="flex gap-2.5 border-b border-line pb-2 last:border-0 last:pb-0">
                        <HookKindChip kind={h.kind} />
                        <div className="min-w-0">
                          <div className="text-[13px] font-medium leading-snug">{h.title}</div>
                          <div className="text-[12px] text-ink-soft leading-relaxed mt-0.5">
                            {h.detail}
                          </div>
                          <div className="font-mono text-[10.5px] text-ink-faint mt-1">
                            {h.source} · {h.publishedAt}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            ) : (
              <p className="text-[13px] text-ink-soft">
                No brief yet. Run the pipeline and the research agent will build one from the
                knowledge base.
              </p>
            )}
          </Card>

          <Card className="card-pad space-y-4">
            <SectionTitle hint={sequence ? sequence.status : "planner"}>
              Sequence timeline
            </SectionTitle>
            {touches.length === 0 ? (
              <p className="text-[13px] text-ink-soft">
                No touches planned. Run the pipeline to generate the cadence.
              </p>
            ) : (
              <ol className="space-y-3">
                {touches.map((t) => (
                  <TouchCard key={t.id} touch={t} hookById={hookById} now={now} />
                ))}
              </ol>
            )}
          </Card>
        </div>

        <div className="space-y-4">
          {lead.status === "escalated" && escalation ? (
            <Card className="card-pad space-y-2 border-warn/40 bg-warn-wash/40">
              <SectionTitle>Escalated to human</SectionTitle>
              <p className="text-[12.5px] leading-relaxed text-ink">
                {(escalation.meta as { handoffSummary?: string } | null)?.handoffSummary ??
                  escalation.reason}
              </p>
              <p className="font-mono text-[10.5px] text-ink-faint">
                {fullSim(escalation.createdAt)}
              </p>
            </Card>
          ) : null}

          <Card className="card-pad space-y-3">
            <SectionTitle hint={`${replies.length}`}>Replies</SectionTitle>
            {replies.length === 0 ? (
              <p className="text-[13px] text-ink-soft">
                No replies yet. Advance the simulation clock to let the inbox run.
              </p>
            ) : (
              <ul className="space-y-3">
                {replies.map((r) => (
                  <li key={r.id} className="border-b border-line pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <ReplyBadge intent={r.intent} />
                      <span className="font-mono text-[10.5px] text-ink-faint">
                        {r.confidence ? `${Math.round(r.confidence * 100)}%` : "—"}
                      </span>
                      <span className="font-mono text-[10.5px] text-ink-faint ml-auto">
                        {formatSim(r.arrivedAt)}
                      </span>
                    </div>
                    <p className="mt-1.5 text-[12.5px] leading-relaxed text-ink whitespace-pre-wrap">
                      {r.body}
                    </p>
                    {r.intent === "objection" ? (
                      <p className="mt-1 font-mono text-[10.5px] text-warn">
                        objection — next touch should answer it
                      </p>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>

      <Card className="card-pad space-y-3">
        <SectionTitle hint={`${decisions.length} records`}>Decision log</SectionTitle>
        {decisions.length === 0 ? (
          <p className="text-[13px] text-ink-soft">
            Every agent choice lands here with its reasoning. Nothing to show yet.
          </p>
        ) : (
          <ul className="divide-y divide-line">
            {decisions.map((d) => (
              <li key={d.id} className="grid grid-cols-[86px_132px_1fr] gap-3 py-2.5">
                <span className="font-mono text-[10.5px] uppercase tracking-wider text-ink-faint pt-0.5">
                  {d.agent}
                </span>
                <span className="font-mono text-[11px] text-accent-strong pt-0.5">{d.action}</span>
                <div className="min-w-0">
                  <p className="text-[12.5px] leading-relaxed text-ink">{d.reason}</p>
                  {d.evidence ? (
                    <p className="mt-0.5 font-mono text-[10.5px] leading-relaxed text-ink-faint">
                      {d.evidence}
                    </p>
                  ) : null}
                  <p className="mt-0.5 font-mono text-[10px] text-ink-faint">
                    {fullSim(d.createdAt)}
                    {d.confidence ? ` · ${Math.round(d.confidence * 100)}%` : ""}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="label mb-1">{label}</div>
      <div className="text-[13px] text-ink">{value}</div>
    </div>
  );
}

function BriefBlock({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <div className="label mb-1">{label}</div>
      <p className="text-[13px] leading-relaxed text-ink">{text}</p>
    </div>
  );
}

function TouchCard({
  touch,
  hookById,
  now,
}: {
  touch: Touch;
  hookById: Map<string, { title: string; source: string }>;
  now: string;
}) {
  const channel = touch.channel === "email" ? "Email" : "LinkedIn";
  const Icon = touch.channel === "email" ? Mail : Globe;
  const refs = touch.hookIds
    .map((hid) => hookById.get(hid))
    .filter(Boolean)
    .map((h) => h!.title);
  const audit = touch.hookIds.length > 0 ? 100 : 0;

  return (
    <li className="card card-pad">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="chip">touch {touch.step}</span>
        <span className="flex items-center gap-1 font-mono text-[10.5px] uppercase tracking-wider text-ink-soft">
          <Icon size={11} /> {channel}
        </span>
        <IntentBadge intent={touch.intent} />
        <span className="chip">{touch.status}</span>
        <span className="ml-auto font-mono text-[10.5px] text-ink-faint">
          day {touch.dayOffset} · {touch.sendAt ? `${formatSim(touch.sendAt)} · ${relDay(touch.sendAt, now)}` : "—"}
        </span>
      </div>

      {touch.subject ? (
        <div className="mt-3 text-[13px] font-semibold text-ink">{touch.subject}</div>
      ) : null}
      {touch.body ? (
        <p className="mt-1 text-[13px] leading-relaxed text-ink-soft whitespace-pre-wrap">
          {touch.body}
        </p>
      ) : (
        <p className="mt-2 text-[12.5px] text-ink-faint">Draft pending.</p>
      )}

      <div className="mt-3 flex items-center gap-2 flex-wrap border-t border-line pt-2.5">
        <span className="label">hooks used</span>
        {refs.length === 0 ? (
          <span className="font-mono text-[10.5px] text-bad">none — generic risk</span>
        ) : (
          refs.map((r, i) => (
            <span key={i} className="chip border-accent/30 bg-accent-wash text-accent-strong">
              {r}
            </span>
          ))
        )}
        <span className="ml-auto flex items-center gap-1.5">
          <span className="label">personalization</span>
          <span className="font-mono text-[10.5px] text-ink-soft">{audit}%</span>
        </span>
      </div>
    </li>
  );
}
