# Cadence — Personalized Multi-Touch Sales Outreach Agent

## Status (2026-11-18)

Phases 0–4 are built and verified end-to-end in the running preview.

- ✅ Scaffold: Next.js 16 + TS + Tailwind v4, paper-console design system, SQLite schema, seeded 8 leads + knowledge base.
- ✅ Engine: LangGraph-style runner, typed decision/event log, NVIDIA provider + deterministic fallback brain, all 5 agents.
- ✅ Pipeline UI: Overview (funnel + forecast + activity), Leads, Lead detail (brief, timeline, hooks, decision log, escalation card).
- ✅ Inbox & classification: reply console (simulate + paste), confidence + evidence, accuracy tracking.
- ✅ Playbooks (create / set default), Analytics (accuracy, reply rate, hook coverage, funnel, intent donut).
- ✅ Command palette (`/` or `Ctrl/Cmd+K`), bulk "Run pending", simulation clock (+1d/+7d/reset).
- ✅ Phase 5: deployed to Vercel — https://cadence-outreach.vercel.app (serverless in-memory DB fallback; persistent Turso/Postgres documented as the one remaining seam).

Verified: all 8 seeded leads run the full pipeline; 32 touches, 100% hook coverage, 12 replies
classified at 100% accuracy against simulator ground truth, next-step agent producing
continue / pause / resume / escalate / stop with reasons; all routes return 200; production
build passes; Vercel deployment READY and serving the seeded console.

> Track D · Sales, Growth & Revenue Agents (Advanced)
> Problem statement: build an agent that researches each lead, drafts a personalized
> multi-touch outreach sequence (email + LinkedIn across 3–4 touches), and adapts the
> sequence based on how the lead responds — continuing, escalating to a human, or stopping.

---

## 1. The idea

A single-rep sales operating console. A rep adds a lead (or imports a list), and an
autonomous multi-agent system runs the full outreach lifecycle for that lead:

**Research → Plan sequence → Draft personalized touches → Send (simulated) →
Listen & classify replies → Decide next step → Forecast**

The rep never loses control: every agent decision is written to a visible decision log
with its reasoning and evidence, and the system escalates to a human at the right
moments instead of blasting on blindly.

Working name: **Cadence** (alternatives: Relay, Handoff, Circuit — your call).

### The 5 agents (one graph node each)

| # | Agent | Input | Output |
|---|-------|-------|--------|
| 1 | **Research** | lead (name, role, company, email, LinkedIn) | research brief: company snapshot, role context, 3–5 personalization hooks, each with a source citation |
| 2 | **Planner** | brief + playbook | 3–4 touch sequence: channel, day offset, intent level (insight → proof → ask → break-up) |
| 3 | **Drafting** | hook + intent + persona | subject + body + "why this line" annotations tying each claim to a research hook |
| 4 | **Classifier** | reply text | intent: interested / not interested / objection / out-of-office / no reply + confidence + evidence quote |
| 5 | **Next-step** | lead state + classification | action: continue / pause / escalate to human / stop + reason + handoff summary |

### How it scores on the evaluation parameters

- **Personalization quality** — every drafted touch cites the research hooks it uses;
  a per-message "personalization audit" shows hook coverage, so it's provably not a template.
- **Soundness of sequence logic & timing** — a real cadence engine (day gaps, channel mix,
  escalating intent), editable playbooks, reply-aware branching, and a visible schedule.
- **Accuracy of reply classification** — classifier returns intent + confidence + evidence;
  analytics track accuracy against ground truth in the simulator.
- **Appropriateness of escalation** — an explicit escalation policy (escalate on
  interested/objection with high-value signals, stop on not-interested, pause on OOO),
  with a human handoff card: full context summary + suggested reply.

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────┐
│  Web console — Next.js (App Router) · TypeScript · Tailwind │
│  Overview · Leads · Lead detail · Inbox · Decisions ·        │
│  Playbooks · Analytics                                      │
└───────────────────────────▲────────────────────────────────┘
                            │ JSON route handlers
┌───────────────────────────┴────────────────────────────────┐
│  API layer                                                 │
│  /api/leads · /api/pipeline/run · /api/inbox · /api/decisions│
└───────────────────────────▲────────────────────────────────┘
┌───────────────────────────┴────────────────────────────────┐
│  Agent engine — LangGraph-style graph runner (TypeScript)  │
│  nodes: research → plan → draft → send → listen →          │
│         classify → decide                                  │
│  every node emits typed events → decision log + timeline    │
└───────────────────────────▲────────────────────────────────┘
┌───────────────────────────┴────────────────────────────────┐
│  Pluggable providers                                       │
│  LLM: NVIDIA NIM (OpenAI-compatible) / local fallback brain │
│  Search: built-in knowledge base · web-search slot later    │
│  Messaging: simulated inbox (default)                       │
└───────────────────────────▲────────────────────────────────┘
┌───────────────────────────┴────────────────────────────────┐
│  SQLite                                                    │
│  leads · research_briefs · hooks · sequences · touches ·    │
│  messages · replies · classifications · decisions · events  │
│  playbooks · sim_state                                     │
└────────────────────────────────────────────────────────────┘
```

**Simulation clock** — a `sim_now` timestamp lives in the DB. Sending schedules touches
at cadence offsets from `sim_now`; an "advance time" control moves the clock, which
triggers due sends, reply arrivals, classification, and next-step decisions. The whole
demo runs itself and is fully reproducible.

---

## 3. Data model (core tables)

`leads` · `research_briefs` · `research_hooks` · `sequences` · `touches` · `messages` ·
`replies` · `classifications` · `decisions` · `events` · `playbooks` · `sim_state`

Every agent action = one `decisions` row (agent, action, reason, evidence, confidence)
plus one `events` row for the global activity feed.

---

## 4. Pages & experience

**Design language — "operator console", not AI slop.**
Warm paper background, ink text, one deep-teal accent, 1px hairlines, small radii,
Inter for UI + IBM Plex Mono for IDs and timestamps. No gradients, no glassmorphism,
no emoji icons, no stock illustrations, no "AI-powered" badges. Real states everywhere
(loading skeletons, empty states, error recovery). Subtle 150ms motion, respects
`prefers-reduced-motion`. Keyboard-first (`/` command palette, j/k to move between leads).

| Route | Purpose |
|-------|---------|
| `/` | Overview: pipeline funnel, today's actions, live agent activity feed, forecast strip |
| `/leads` | Lead table: stage chips, health, next action; add lead form; CSV import |
| `/leads/[id]` | **The core page** — research brief, sequence timeline, message thread with classification badges, per-lead decision log, escalation panel |
| `/inbox` | Unified reply inbox: classify queue, simulate-reply controls, paste-a-real-reply |
| `/decisions` | Global audit stream, filterable by agent / action / intent |
| `/playbooks` | Cadence template editor (touches, day gaps, channel mix, intent curve) |
| `/analytics` | Classification accuracy, reply rate by touch, funnel, escalation outcomes |

**Anti-slop rules we hold to:** charts are hand-drawn SVG with real data (no library
bloat); copy is written like a sales operator, not a chatbot; every screen works with
zero data and with full data; nothing placeholder.

---

## 5. Finalized decisions (2026-11-18)

| Decision | Choice |
|----------|--------|
| LLM | **NVIDIA NIM free API** (`integrate.api.nvidia.com`, OpenAI-compatible, `NVIDIA_API_KEY`). Default model `google/gemma-4-31b-it`, configurable. **Deterministic fallback brain** runs everything with no key, so the app is never dead in the demo. |
| Offer / ICP | Placeholder, editable in-app: product = **Cadence** (this tool), ICP = sales leaders at 50–500-person B2B companies. Self-referential demo: the tool sells itself. |
| Research source | **Built-in knowledge base** — 8 seeded fictional-but-realistic companies with news/funding/events. Pluggable slot for a real web-search API later. (Adzuna is job-listing data — not a fit for company research.) |
| Sending | **Simulated inbox** only (per the brief: never real unsolicited sends). |
| Theme | **Light paper console** — warm off-white, ink, deep-teal accent, hairlines, mono details. |
| Data | SQLite, seeded with 8 leads + knowledge base; single-user (no auth, hackathon scope). |
| Deploy | Sandbox preview first; Vercel config at the end. |

> Note: the sandbox blocks outbound calls to NVIDIA, so live LLM calls run on your
> machine / Vercel. In the sandbox preview the fallback brain keeps the full pipeline
> working end-to-end.

---

## 6. What "totally working" means (acceptance bar)

A stranger can open the app, click **Run pipeline** on a seeded lead, watch research →
plan → draft → send happen step by step, advance the clock, see replies arrive and get
classified, watch the next-step agent continue/pause/escalate with reasons, and read the
full decision log — with no external service required thanks to the fallback brain.

---

## 7. Build phases (locked)

- **Phase 0 — Scaffold:** Next.js + TS + Tailwind v4, design tokens, SQLite schema + seed, app shell.
- **Phase 1 — Engine:** graph runner, typed event log, provider layer, 5 agents.
- **Phase 2 — Pipeline UI:** leads, lead detail, sequence timeline, decision log.
- **Phase 3 — Inbox & classification.**
- **Phase 4 — Playbooks, analytics, polish.**
- **Phase 5 — Deploy prep + README + scripted demo.**

---

## 8. Deployment status (2026-11-18)

Live: **https://cadence-outreach.vercel.app** — Vercel project `cadence-outreach`
(`prj_xEF1dd7r8sOtpAiyDxXhB56o8sU7`), linked to `KRE8ECH/Sales-Agentic-Ai-`, production
branch `main`. `NVIDIA_API_KEY` is stored as an encrypted production env var.

### Storage: ephemeral on serverless (accepted)

Vercel serverless functions have no writable shared filesystem, so `src/lib/db.ts` runs
`node:sqlite` in **memory mode** when `VERCEL=1` (file mode locally). Consequences:

- Seeded lead ids are **deterministic** (`lead_${slug}`, e.g. `lead_northwind-freight`), so
  deep links resolve on any instance. Verified live.
- A warm instance keeps full pipeline state; when the platform rotates the instance (idle
  recycling, deploys, bursts), state returns to the fresh seed. The sidebar badges this as
  `ephemeral data · serverless`. `GET /api/health` exposes the per-boot instance id, DB
  mode, LLM status, sim clock and lead count to make rotation visible.
- A persistent store needs an async driver (Turso/libSQL `execute()` is async-only, which
  cannot wrap the synchronous `node:sqlite` layer without a full async rewrite). Vercel
  Postgres via `CADENCE_DATABASE_URL` is the upgrade path; the seam is `src/lib/db.ts`.

### LLM model

NVIDIA retired `meta/llama-3.1-8b-instruct` (end of life 2026-08-26, HTTP 410). Default is
now `google/gemma-4-31b-it`, verified live through
`GET /api/health/llm?probe=1`. `?list=1` returns the live catalog (32 models at time of
writing) so the model can be swapped without a code change.
