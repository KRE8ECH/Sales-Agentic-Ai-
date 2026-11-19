export type LeadStatus =
  | "new"
  | "researching"
  | "sequencing"
  | "active"
  | "paused"
  | "escalated"
  | "stopped"
  | "won";

export type Channel = "email" | "linkedin";
export type Intent = "insight" | "proof" | "ask" | "breakup";
export type ReplyIntent =
  | "interested"
  | "not_interested"
  | "objection"
  | "ooo"
  | "no_reply";
export type NextAction = "continue" | "pause" | "escalate" | "stop";
export type AgentName =
  | "research"
  | "planner"
  | "drafter"
  | "sender"
  | "classifier"
  | "nextstep";

export interface Lead {
  id: string;
  name: string;
  role: string;
  company: string;
  email: string;
  linkedin: string;
  persona: string;
  status: LeadStatus;
  health: number;
  nextAction: string | null;
  nextTouchAt: string | null;
  sequenceId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ResearchBrief {
  id: string;
  leadId: string;
  snapshot: string;
  roleContext: string;
  personaNotes: string;
  createdAt: string;
}

export interface ResearchHook {
  id: string;
  briefId: string;
  leadId: string;
  title: string;
  detail: string;
  source: string;
  kind: "news" | "funding" | "role" | "product" | "event" | "social";
  publishedAt: string;
}

export interface SequenceRow {
  id: string;
  leadId: string;
  playbookId: string;
  status: "draft" | "active" | "paused" | "completed" | "stopped";
  startedAt: string | null;
  createdAt: string;
}

export interface Touch {
  id: string;
  sequenceId: string;
  leadId: string;
  step: number;
  channel: Channel;
  intent: Intent;
  dayOffset: number;
  subject: string | null;
  body: string | null;
  status: "scheduled" | "sent" | "replied" | "skipped";
  sendAt: string | null;
  sentAt: string | null;
  hookIds: string[];
}

export interface Reply {
  id: string;
  leadId: string;
  touchId: string | null;
  body: string;
  fromEmail: string;
  channel: Channel;
  arrivedAt: string;
  groundTruth: ReplyIntent | null;
  handled: boolean;
  intent: ReplyIntent | null;
  confidence: number | null;
}

export interface Classification {
  id: string;
  replyId: string;
  leadId: string;
  intent: ReplyIntent;
  confidence: number;
  evidence: string;
  rationale: string;
  suggestedAngle: string;
  createdAt: string;
}

export interface Decision {
  id: string;
  leadId: string | null;
  agent: AgentName;
  action: string;
  reason: string;
  evidence: string;
  confidence: number | null;
  meta: Record<string, unknown> | null;
  createdAt: string;
}

export interface EventRow {
  id: string;
  leadId: string | null;
  kind: string;
  message: string;
  createdAt: string;
}

export interface Playbook {
  id: string;
  name: string;
  description: string;
  steps: PlaybookStep[];
  isDefault: boolean;
  createdAt: string;
}

export interface PlaybookStep {
  step: number;
  channel: Channel;
  intent: Intent;
  dayOffset: number;
}

export interface SimState {
  now: string;
}
