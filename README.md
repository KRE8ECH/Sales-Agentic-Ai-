# Personalized Multi-Touch Sales Outreach Agent (Track D)

An autonomous, stateful Multi-Agent AI system built in **Python** using **Local Ollama LLM** and **DuckDuckGo RAG Web Search**.

Designed to prospect, personalize, listen, and adaptively route outbound sales communications across email and LinkedIn channels with high precision, grounded research, and transparent audit logging.

---

## 🎯 Architecture Overview & Problem Statement Mapping

This implementation maps directly to the **Track D - Sales, Growth & Revenue Agents (Advanced)** specification:

```
[Target Lead] ──> [1. DuckDuckGo Web Search & RAG] ──> [Lead Research Dossier]
                                                               │
                                                               ▼
[5. Adaptive Next-Step Agent] <── [4. Reply Classifier] <── [2. Sequence Planner & 3. Personalized Drafter]
  ├─ CONTINUE (Advance Cadence)         ▲                      │
  ├─ PAUSE (Out of Office)              │                      ▼
  ├─ ESCALATE (Interested / Objection)  └──────── [Simulated Multi-Touch Outreach (Email & LinkedIn)]
  └─ STOP (Unsubscribe / Max Touches)
                                                               │
                                                               ▼
                                              [Persistent SQLite State & Audit Logs]
```

### 1. Per-Lead Research Agent (`sales_agent/agents/research_agent.py`)
- Executes multi-angle live queries on **DuckDuckGo** for company news, leadership moves, product launches, and strategic priorities.
- Uses a local **RAG engine** (`rag_engine.py`) to chunk, score, and rank the most relevant public context snippets.
- Synthesizes a structured **Lead Research Dossier** with verifiable source citations, company overview, recent events, and custom conversational hooks.

### 2. Multi-Touch Sequence Planner (`sales_agent/agents/sequence_planner.py`)
- Implements a standardized 4-touch outreach schedule spanning 12 days with escalating intent:
  - **Touch 1 (Day 1 - Email)**: Researched Observation & Relevance Hook.
  - **Touch 2 (Day 3 - LinkedIn)**: Insight & Light Engagement.
  - **Touch 3 (Day 7 - Email)**: Social Proof, ROI, & Case Study.
  - **Touch 4 (Day 12 - Email)**: Polite Breakup & Low-Friction Meeting Invite.

### 3. Personalized Message-Drafting Agent (`sales_agent/agents/drafting_agent.py`)
- References specific research points from the dossier (never generic templates).
- Adapts copy to channel formatting constraints (concise, high-impact emails vs. punchy LinkedIn notes).
- Explicitly logs `researched_evidence_used` for complete transparency and compliance.

### 4. Reply-Classification Agent (`sales_agent/agents/reply_classifier.py`)
- Evaluates inbound prospect messages and classifies them into:
  - `INTERESTED`: Positive buying signals, meeting requests, demo interest.
  - `NOT_INTERESTED`: Explicit rejection or unsubscribe request.
  - `OBJECTION`: Categorized into Subtypes (`TIMING`, `BUDGET`, `COMPETITOR`, `WRONG_PERSON`).
  - `OUT_OF_OFFICE`: Detects autoresponder and extracts return dates.
  - `NO_REPLY`: Cadence elapsed without interaction.

### 5. Adaptive Next-Step Decision Engine (`sales_agent/agents/decision_agent.py`)
- **`ESCALATE_TO_HUMAN`**: Instantly halts bots when a lead expresses interest or raises a nuanced objection, notifying sales reps to prepare a high-touch proposal or demo.
- **`PAUSE`**: Snoozes sequence until prospect returns from out-of-office vacation.
- **`STOP`**: Respects unsubscribes or ends sequence after Touch 4 without response.
- **`CONTINUE_SEQUENCE`**: Advances cadence and drafts next touchpoint.

### 6. State Machine & Persistent Audit Logs (`sales_agent/db.py`)
- Persisted locally in SQLite (`outreach_pipeline.db`).
- Records complete conversation states, touch status, incoming messages, and **transparent decision reasoning logs** (`Timestamp`, `Stage`, `Decision`, `Reasoning`).

---

## 🚀 Quick Start Guide

### 1. Requirements & Environment
The project runs on standard Python 3.9+. Dependencies are already installed in `.venv`.

To activate the virtual environment:
```bash
source .venv/bin/activate
```

*(Optional if installing on a new machine)*:
```bash
pip install -r requirements.txt
```

---

### 2. Local Ollama Setup
Ensure Ollama is running on your machine:
```bash
ollama serve
```

Pull your preferred model (e.g. `llama3`, `mistral`, `qwen2.5`, `llama3.2`):
```bash
ollama pull llama3
```

> **Note**: The system is built with resilient fallback heuristics. If Ollama is offline or starting up, the agents remain functional and continue pipeline execution without crashing.

---

### 3. Launching the Agent

You have two interfaces available:

#### Option A: Interactive Web UI & Dashboard (Recommended)
Launch the browser UI:
```bash
python main.py --web
```
Or specify a custom port / model:
```bash
python main.py --web --port 8000 --model llama3
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser:
- 💬 **Agent Chatbot**: Natural language lead research and command execution.
- 👥 **Pipeline Kanban**: Real-time state machine tracking each lead across touches.
- 🔍 **RAG Dossier & Sequence Viewer**: Inspect DuckDuckGo web citations and generated drafts.
- 📥 **Reply Simulator**: Send test prospect replies and watch the agent classify and route.
- 📜 **Decision Logs**: Transparent reasoning audit table.

---

#### Option B: Interactive Rich Terminal CLI
Launch the terminal chatbot:
```bash
python main.py
```

Available CLI commands:
- `add`: Prospect a new lead (runs DuckDuckGo search + RAG + Sequence Plan + Touch 1).
- `leads` or `list`: Display all active leads and their current state machine status.
- `show <lead_id>`: Inspect the research dossier, touch drafts, and replies for a lead.
- `reply <lead_id>`: Simulate an inbound prospect reply (test Interested, Objection, OOO).
- `advance <lead_id>`: Advance sequence cadence (simulates no-reply timeout).
- `logs <lead_id>`: View the step-by-step decision reasoning audit logs.
- `models`: Check local Ollama connection and installed models.
- Type any question: The conversational AI assistant answers sales strategy questions.

---

## 🧪 Automated Pipeline Verification Test

To verify the end-to-end multi-agent pipeline in automated headless mode:
```bash
python tests/test_pipeline.py
```
This tests:
1. Lead Onboarding & DuckDuckGo RAG search
2. Sequence Planning & Touch #1 Drafting
3. `INTERESTED` classification & `ESCALATE_TO_HUMAN` decision
4. `OUT_OF_OFFICE` classification & `PAUSE` decision
5. `NOT_INTERESTED` classification & `STOP` decision
6. SQLite state persistence and audit trail logging
