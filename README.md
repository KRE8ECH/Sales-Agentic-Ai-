# Cadence — Personalized Multi-Touch Sales Outreach Agent

Track D (Sales, Growth & Revenue Agents, Advanced). A single-rep sales operating console
where an autonomous multi-agent system runs the whole outreach lifecycle per lead:

**Research → Plan sequence → Draft personalized touches → Send (simulated) →
Listen & classify replies → Decide next step → Forecast**

Every agent action is written to a visible decision log with its reasoning and evidence.

---

## Quick start

```bash
npm install
npm run dev          # http://localhost:3000
```

No API key required. The built-in deterministic brain runs the entire pipeline offline.
Production build: `npm run build && npm run start`.

### Optional: NVIDIA NIM (free tier)

```bash
cp .env.example .env.local   # then paste your key
```

`NVIDIA_API_KEY` + `NVIDIA_MODEL` (default `google/gemma-4-31b-it`). With a key set,
drafting and classification use the LLM; without one, the deterministic brain takes over
automatically. The app never breaks either way.

NVIDIA retires models from its free catalog over time (the previous default,
`meta/llama-3.1-8b-instruct`, reached end of life on 2026-08-26 and now returns HTTP 410).
To pick a currently served model, call `GET /api/health/llm?list=1` with the key set, then
set `NVIDIA_MODEL` to one of the returned ids. `GET /api/health/llm?probe=1` verifies the
key and model with a real completion.

---

## The 60-second demo

1. **Leads → Run pending.** The research agent matches each company in the built-in
   knowledge base and writes a brief with cited hooks.
2. Open a lead. Read the **research brief** and the **sequence timeline** — every touch
   shows the hooks it cites and a personalization score.
3. **Advance the clock** (sidebar, `+1 day` / `+7 days`). Touches fire on cadence; replies
   arrive in the **Inbox** and get classified with intent, confidence, and evidence.
4. Watch the **next-step agent** continue, pause (out-of-office), stop (not interested), or
   **escalate** — escalations come with a handoff summary for the human rep.
5. Read **Decisions** for the full audit trail, and **Analytics** for classification
   accuracy against simulator ground truth.

`/` (or `Ctrl/Cmd+K`) opens the command palette to jump anywhere.

---

## Architecture

```
Web console (Next.js App Router, TypeScript, Tailwind v4)
        │  JSON route handlers
API layer (/api/leads, /api/pipeline/run, /api/inbox/*, /api/sim/*)
        │
Agent engine — LangGraph-style runner: typed state flows through named nodes
  research → plan → draft → send        (per-lead pipeline)
  classify → decide                     (per-reply pipeline)
        │
Providers:  LLM = NVIDIA NIM (OpenAI-compatible) | deterministic fallback brain
            Research = built-in knowledge base | pluggable web search
            Messaging = simulated inbox (never real unsolicited sends)
        │
SQLite (node:sqlite) — leads, briefs, hooks, sequences, touches, messages,
                       replies, classifications, decisions, events, playbooks, sim_state
```

**Simulation clock.** `sim_state.now` is the clock the whole app obeys. Sending schedules
touches at cadence offsets; advancing the clock dispatches due touches, generates replies,
classifies them, and runs the next-step agent. Timestamps in the decision log are simulation
time, so the audit trail reads consistently.

### The five agents

| Agent | What it decides | Where it shows up |
|-------|-----------------|-------------------|
| Research | Which public context matters; writes the brief + cited hooks | Lead detail → Research brief |
| Planner | Channel mix, day gaps, intent escalation (insight → proof → ask → break-up) | Sequence timeline |
| Drafter | What each touch says, and which hook justifies each line | Touch card → "hooks used" |
| Classifier | interested / not interested / objection / out-of-office / no reply + confidence + evidence | Inbox, Analytics |
| Next-step | continue / pause / escalate / stop, with a reason and handoff summary | Decision log, lead header |

---

## API

| Method | Route | Purpose |
|--------|-------|---------|
| GET/POST | `/api/leads` | List / create leads |
| GET/POST | `/api/pipeline/run` | `{leadId}` — run research → plan → draft → send (GET reads it from the query string) |
| POST | `/api/sim/advance` | `{days}` — advance the clock, dispatch, reply, classify, decide |
| GET/POST | `/api/sim/reset` | Reseed everything (GET for link-driven demos) |
| POST | `/api/inbox/simulate` | `{leadId, intent}` — generate a realistic reply, classify, decide |
| POST | `/api/inbox/reply` | `{leadId, body}` — paste a real reply, classify, decide |
| POST | `/api/replies/[id]/classify` | Re-run classification + next-step |
| GET | `/api/decisions` | Audit log (`?leadId=`, `?agent=`) |
| GET/POST/PATCH | `/api/playbooks` | Cadence templates |
| GET | `/api/health` | Instance id, DB mode, LLM status, sim clock, lead count |
| GET | `/api/health/llm` | Provider status; `?probe=1` makes a real call, `?list=1` lists the live model catalog, `?model=<id>` overrides the model |

---

## How it answers the evaluation criteria

- **Personalization quality** — every drafted touch cites a research hook with a source and
  date; the touch card shows hook coverage, and Analytics reports aggregate hook coverage.
- **Sequence logic & timing** — a real cadence engine with day gaps, channel mix, and an
  escalating intent curve; playbooks are editable and the default is used by the planner.
- **Classification accuracy** — the classifier returns intent + confidence + evidence, and
  Analytics scores it against simulator ground truth.
- **Escalation appropriateness** — policy is explicit and logged: interest escalates, OOO
  pauses and auto-resumes, not-interested stops, objections get answered while touches
  remain.

## Deployment

**Live:** https://cadence-outreach.vercel.app (Vercel project `cadence-outreach`, repo
`KRE8ECH/Sales-Agentic-Ai-`, branch `arena/5d801a47-sales-agentic-ai`).

Data lives in `data/cadence.sqlite` locally (gitignored). Vercel's serverless filesystem is
read-only, so the app detects `VERCEL=1` and switches to a per-instance in-memory database
that seeds itself on first use — everything works, data is ephemeral (the UI shows an
"ephemeral data · serverless build" badge). Force the same mode locally with
`CADENCE_DB=memory`.

For persistent multi-instance storage on Vercel, attach a network database (Turso/libSQL or
Vercel Postgres) and set `DATABASE_URL`; `src/lib/db.ts` is the single seam to implement it.
Build/deploy: `npm run build && npm run start`, or push to the branch and Vercel deploys.

### Adding the NVIDIA key on Vercel

Project → Settings → Environment Variables → add `NVIDIA_API_KEY` (and optionally
`NVIDIA_MODEL`) → redeploy. Without it the app runs on the deterministic fallback brain.

## Design notes (anti-slop)

Warm paper surface, ink text, one deep-teal accent, hairline borders, mono for IDs and
timestamps. No gradients, no glass, no emoji icons, no stock illustrations. Hand-drawn SVG
charts with real data. Real loading, empty, and error states. Motion is 150ms and disabled
under `prefers-reduced-motion`.
