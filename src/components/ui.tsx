import type { ReactNode } from "react";
import type { Intent, LeadStatus, ReplyIntent } from "@/lib/types";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function SectionTitle({
  children,
  hint,
}: {
  children: ReactNode;
  hint?: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <h2 className="text-[13px] font-semibold tracking-[-0.01em] text-ink">{children}</h2>
      {hint ? <span className="label">{hint}</span> : null}
    </div>
  );
}

const INTENT_STYLES: Record<Intent, string> = {
  insight: "border-info/30 bg-info-wash text-info",
  proof: "border-accent/30 bg-accent-wash text-accent-strong",
  ask: "border-warn/30 bg-warn-wash text-warn",
  breakup: "border-line-strong bg-paper-deep text-ink-soft",
};

export function IntentBadge({ intent }: { intent: Intent | string }) {
  return <span className={`chip ${INTENT_STYLES[intent as Intent] ?? ""}`}>{intent}</span>;
}

const REPLY_STYLES: Record<ReplyIntent, string> = {
  interested: "border-accent/30 bg-accent-wash text-accent-strong",
  objection: "border-warn/30 bg-warn-wash text-warn",
  ooo: "border-info/30 bg-info-wash text-info",
  not_interested: "border-bad/30 bg-bad-wash text-bad",
  no_reply: "border-line-strong bg-paper-deep text-ink-faint",
};

export function ReplyBadge({ intent }: { intent: ReplyIntent | string | null }) {
  if (!intent) return <span className="chip">unclassified</span>;
  return (
    <span className={`chip ${REPLY_STYLES[intent as ReplyIntent] ?? ""}`}>
      {intent.replace("_", " ")}
    </span>
  );
}

const STATUS_STYLES: Record<LeadStatus, string> = {
  new: "border-line-strong bg-paper-deep text-ink-soft",
  researching: "border-info/30 bg-info-wash text-info",
  sequencing: "border-info/30 bg-info-wash text-info",
  active: "border-accent/30 bg-accent-wash text-accent-strong",
  paused: "border-warn/30 bg-warn-wash text-warn",
  escalated: "border-warn/30 bg-warn-wash text-warn",
  stopped: "border-bad/30 bg-bad-wash text-bad",
  won: "border-accent/30 bg-accent-wash text-accent-strong",
};

export function StatusChip({ status }: { status: LeadStatus | string }) {
  return <span className={`chip ${STATUS_STYLES[status as LeadStatus] ?? ""}`}>{status}</span>;
}

export function Health({ value }: { value: number }) {
  const color =
    value >= 70 ? "bg-accent" : value >= 45 ? "bg-warn" : "bg-bad";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1 w-14 rounded-full bg-paper-deep overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="font-mono text-[11px] text-ink-faint">{value}</span>
    </div>
  );
}

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="card card-pad flex flex-col items-start gap-2 py-10">
      <p className="text-[13px] font-semibold text-ink">{title}</p>
      <p className="text-[13px] text-ink-soft max-w-md leading-relaxed">{body}</p>
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}

export function HookKindChip({ kind }: { kind: string }) {
  return <span className="chip">{kind}</span>;
}

export function Avatar({ name }: { name: string }) {
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
  return (
    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-ink text-[10px] font-semibold text-paper">
      {initials}
    </div>
  );
}
