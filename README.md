# SimpleResolve

**An AI-native system that replaces binary account freezes with proportional, scope-aware
interventions — and turns raw transaction data into FINTRAC-ready investigation narratives.**

---

## What This Is, and Why It Exists

Imagine a client whose crypto withdrawal triggered a fraud flag. The bank freezes every account
they hold — chequing, TFSA, savings — for three weeks while a human manually reviews 18 months
of transaction history. The client can't pay rent. The analyst is buried in raw data. The fraud
team is overwhelmed by a queue of false positives.

This isn't a speed problem. It's an *architecture* problem. The system is binary: flag → freeze
everything → queue → wait → human resolves. That architecture exists because traditional rules
engines can only output on/off. They cannot reason about *which* capabilities should be restricted
or *why* the restriction should be proportional to the specific trigger.

SimpleResolve replaces that architecture with one that couldn't exist without AI. It operates
in four graduated layers:

1. **Behavioral Intelligence** — maintains a living risk profile for every client
2. **Graduated Response Engine** — Gemini reasons about the *scope* of restrictions
3. **Investigation Orchestrator** — a multi-agent pipeline assembles evidence and drafts STRs
4. **Human Boundary** — the analyst makes one decision: file the STR or don't

---

## The Intuition Behind the Architecture

### Why Four Layers?

Good software architecture separates concerns. Each layer has *one responsibility* and produces
a well-defined output that the next layer consumes. This makes the system:

- **Testable**: you can test each layer independently
- **Replaceable**: you can swap Gemini for another LLM without touching Layer 1
- **Understandable**: a new developer can understand one layer at a time

The layers form a pipeline with progressive enrichment:

```
Raw transactions → Risk profile → Restriction decision → Evidence package → Human decision
```

Each stage converts raw data into richer, more structured knowledge. This is a fundamental
pattern in data engineering: *enrich as you go*.

### Why Does Layer 1 Pre-compute?

The biggest mistake in real-time systems is doing expensive computation at query time.
Layer 1 maintains a *living behavioral fingerprint* for every client — updated continuously —
so that when a risk event fires, the investigation doesn't need to scan years of transaction
history from scratch. It just reads what's already computed.

This is the principle of **materialised views**: pre-compute the aggregates you'll need,
update them incrementally, and serve them instantly.

### Why Is Layer 2 an LLM Task?

A rules engine can escalate a risk level (low → medium → high). But it cannot answer:
*"Given that this client's suspicious activity involves crypto sends, which of their other
capabilities — chequing, TFSA, RRSP — should remain untouched?"*

That requires understanding the *semantic relationship* between a trigger and a set of
capabilities. It's a language and reasoning task, not a matching task. This is the test for
whether a problem genuinely benefits from an LLM: if it requires understanding *meaning and
context* rather than matching patterns, an LLM belongs there.

### Why LangGraph for Layer 3?

The investigation pipeline has three characteristics that make it a natural fit for a
directed acyclic graph (DAG) executor:

1. Some steps are independent and could run in parallel (tagging transactions doesn't need
   the cross-client correlation result and vice versa)
2. There's a conditional branch at the end (de-escalate vs fast-track vs full investigation)
3. The state accumulates — each node adds to what the previous nodes built

LangGraph expresses this as a typed state object that flows through nodes. Even though the
prototype runs the nodes sequentially, the graph structure documents the *intended* architecture
and makes parallelisation a one-line change.

### Why Is the Human Irreducible in Layer 4?

Three reasons that cannot be engineered away:

1. **Legal liability**: Under Canada's PCMLTFA, filing or failing to file an STR is a
   criminal act. A compliance officer signs it personally. No AI can absorb that liability.

2. **Subjective judgment**: "Reasonable grounds to suspect" (the filing standard) requires
   weighing cultural context, the plausibility of explanations, and experience-based pattern
   recognition. These resist formalisation.

3. **Bias circuit-breaking**: If the AI disproportionately flags clients from certain
   demographics, the human reviewer is where that pattern is caught and corrected.
   AI systems inherit the biases of their training data. Humans must remain in the loop.

---

## The File Structure, Explained from First Principles

```
simple_resolve/
├── docker-compose.yml        ← Infrastructure: PostgreSQL database
├── backend/
│   ├── requirements.txt      ← Python dependencies
│   ├── .env.example          ← Template for secrets (never commit .env)
│   └── app/
│       ├── main.py           ← FastAPI app entry point: registers routes, starts DB
│       ├── core/
│       │   ├── config.py     ← Reads .env into a typed Settings object
│       │   └── database.py   ← SQLAlchemy engine + session factory
│       ├── models/           ← SQLAlchemy ORM classes (the shape of the database)
│       │   ├── base.py       ← DeclarativeBase all models inherit from
│       │   ├── client.py     ← Client + KYC info
│       │   ├── transaction.py← Every financial event
│       │   ├── profile.py    ← BehavioralProfile (Layer 1's output)
│       │   ├── restriction.py← AccountRestriction (Layer 2's output)
│       │   └── investigation.py ← Investigation + STRDraft + AuditEntry
│       ├── services/         ← Business logic (the "brains")
│       │   ├── gemini.py     ← Thin wrapper: send prompt → get JSON back
│       │   ├── layer1_behavioral.py ← Risk scoring, archetype, fingerprint
│       │   ├── layer2_response.py   ← Gemini scope reasoning, restriction upsert
│       │   └── layer3_orchestrator.py ← Full investigation pipeline
│       ├── api/              ← HTTP endpoints (thin wrappers around services)
│       │   ├── clients.py    ← GET /clients, GET /clients/{id}
│       │   ├── transactions.py ← GET /transactions
│       │   ├── restrictions.py ← GET/POST/PATCH /restrictions
│       │   ├── investigations.py ← trigger, list, decide
│       │   └── dashboard.py  ← summary stats, activity feed
│       ├── schemas.py        ← Pydantic response models (what the API returns)
│       └── seed/
│           └── seed_data.py  ← Creates 7 synthetic clients demonstrating all scenarios
└── frontend/
    └── src/
        ├── app/              ← Next.js App Router pages
        │   ├── page.tsx      ← Dashboard
        │   ├── clients/      ← Client list + profile
        │   └── investigations/ ← Investigation list + detail
        ├── components/       ← Reusable UI pieces
        │   ├── Navbar.tsx
        │   ├── RiskTimeline.tsx   ← Recharts area chart with threshold lines
        │   ├── MoneyFlowGraph.tsx ← D3.js force-directed money flow
        │   ├── CrossClientNetwork.tsx ← D3.js linked client graph
        │   └── STRReview.tsx      ← STR narrative + approve/dismiss
        └── lib/
            └── api.ts        ← All fetch() calls in one typed module
```

### The Separation Between `models/`, `services/`, and `api/`

This is a classic layered architecture pattern:

- **`models/`** defines the *shape of data* in the database. It says nothing about business rules.
- **`services/`** implements *business logic*. It operates on models but doesn't know about HTTP.
- **`api/`** is the *HTTP interface*. It receives requests, calls services, returns responses.

Why separate them? Because a service might be called from an API endpoint, from a background
task, from the seed script, or from a test — without any HTTP involved. Mixing HTTP concerns
into business logic couples them unnecessarily.

The Pydantic **`schemas.py`** is the *contract* between the backend and the frontend. It
defines exactly what JSON shape the API returns. The TypeScript types in `frontend/src/lib/api.ts`
mirror these schemas, giving you type safety across the full stack.

### Why ORM + Pydantic?

**SQLAlchemy** (the ORM) gives you Python classes that map to database tables. You write Python,
it writes SQL. This prevents SQL injection by construction, because parameters are never
interpolated as strings.

**Pydantic** validates incoming and outgoing data against a schema. If the database returns a
string where a number is expected, Pydantic raises an error before the frontend ever sees it.
Together, they form a type-safe data pipeline from database to client.

---

## The AI Concepts in Play

### Prompt Engineering (Layer 2 and 3)

The quality of an LLM system depends almost entirely on how well the prompts are structured.
In this codebase, every prompt follows the same pattern:

1. **Role**: *"You are a risk response engine for a Canadian investment platform."* — LLMs
   perform better when given a clear role that frames their reasoning.

2. **Context**: The client's behavioral profile, products held, risk scores. The LLM cannot
   reason proportionally without knowing what "normal" looks like for this client.

3. **Task**: A precise, unambiguous instruction. Not "assess this client" but "determine
   which specific capabilities to restrict and which to explicitly leave accessible."

4. **Rules**: Hard constraints that override LLM discretion (e.g., "Level 4 MUST NOT be
   triggered by a risk score alone"). LLMs will hallucinate reasonable-sounding answers
   without guardrails.

5. **Output format**: Exact JSON schema with key names specified. This makes the output
   machine-readable and reduces parsing failures.

### Structured Output

All Layer 2 and Layer 3 classification calls use `response_mime_type="application/json"` in
the Gemini generation config. This instructs the model to return valid JSON rather than
markdown-wrapped prose. The `gemini.py` wrapper handles JSON parsing and graceful fallback.

### The Fallback Pattern

Every LLM call has a fallback — a hardcoded rule-based response used when the API is
unavailable or returns unparseable output. This is a critical pattern for production AI systems:
*the system should degrade gracefully, not crash*. During development you can work without a
Gemini API key; the system uses the fallback responses automatically.

### Behavioral Profiling as Feature Engineering

The FINTRAC detectors in `layer1_behavioral.py` are essentially *feature extractors*. They
transform raw transaction sequences into scalar signals (confidence scores 0.0–1.0) that
encode domain knowledge:

- `_detect_structuring`: counts transactions within 20% of the $10K reporting threshold
- `_detect_layering`: counts distinct products touched within a single day
- `_detect_rapid_crypto_conversion`: finds deposit→crypto-send pairs within 4 hours

This is *hand-engineered feature extraction* — the same technique used before neural networks
dominated, still appropriate here because the features have clear regulatory definitions
(FINTRAC Guideline 2) that must be explainable to a compliance auditor.

### The Pipeline Pattern (LangGraph)

The investigation orchestrator is structured as a **directed acyclic graph** (DAG) of
pure functions. Each node:

1. Receives the current state dictionary
2. Does exactly one thing (tag transactions, build money flow, etc.)
3. Returns an updated state dictionary

This functional, stateless design makes each node independently testable and the overall
flow easy to trace. The same pattern appears in machine learning pipelines (sklearn Pipeline),
data processing (Apache Airflow), and workflow automation (LangGraph, Temporal).

---

## The Software Engineering Concepts in Play

### Dependency Injection (FastAPI's `Depends`)

FastAPI's `Depends(get_db)` is dependency injection: instead of each endpoint creating its own
database connection, the framework injects a shared connection. This means:

- Connections are properly closed even if an endpoint raises an exception
- Tests can inject a test database instead of the real one
- The connection lifecycle is managed in one place

### Environment-Based Configuration

`config.py` uses `pydantic-settings` to read environment variables into a typed `Settings`
object. The `.env.example` documents every variable. The actual `.env` is gitignored.

Rule: *secrets never live in code, only in environment variables*.

### Audit Trails as First-Class Data

Every state change in the system — restriction applied, investigation opened, STR filed —
writes an `AuditEntry` record. This is not optional or afterthought; it's a design requirement
for any regulated system. When a compliance regulator asks "who did what and when?", the
audit trail is the answer.

### Idempotent Seeding

The seed script deletes all data before re-inserting. Running it twice produces the same
database state. This property — *idempotence* — is essential for reproducible demo environments
and automated testing.

---

## Demo Scenarios Seeded

| Client | Scenario | Expected Layer 2 | Expected Layer 3 |
|--------|----------|-------------------|-------------------|
| Alice Normal | Clean baseline | Level 0 (no action) | No investigation |
| Bob Struct | 3× near-$10K deposits + crypto conversion | Level 3 (crypto restricted) | full_investigation → STR draft |
| Carl Layer | fiat → BTC → ETH → wallet in 4 hrs | Level 3 (crypto restricted) | full_investigation → STR draft |
| Dana, Eve, Frank | All send to 0x7a3* wallet cluster | Level 3 (coordinated) | full_investigation (coordinated, 3-client STR) |
| Grace Hill | $22K deposits vs $32K stated income | Level 2 (step-up auth) | fast_track → brief |

---

## How to Run

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ and npm

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env (optional — fallback responses work without it)
```

### 3. Seed the database

```bash
python -m app.seed.seed_data
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
# API is at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 5. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
# UI is at http://localhost:3000
```

### 6. Demo workflow

1. Open `http://localhost:3000` → Dashboard shows seeded clients and restrictions
2. Click **Clients** → see Alice (clean), Bob/Carl/Dana/Eve/Frank (Level 3), Grace (Level 2)
3. Click **Bob Struct** → see risk timeline spike, FINTRAC indicators, current restriction
4. Click **Investigations** → trigger one for Bob via `POST /investigations/trigger/{bob_id}`
   (or use the FastAPI docs at `/docs`)
5. Refresh Investigations → see the pipeline run: status moves from `open` → `running` → `str_drafted`
6. Click the investigation → see money flow graph, FINTRAC-tagged transactions, STR narrative
7. Click **Approve & File STR** → investigation status moves to `filed`
8. Dashboard shows updated STR count

---

## Key Files to Read First

If you're studying this codebase, read in this order:

1. [backend/app/models/](backend/app/models/) — understand the data shapes before anything else
2. [backend/app/services/layer1_behavioral.py](backend/app/services/layer1_behavioral.py) — the FINTRAC detectors and risk scoring
3. [backend/app/services/layer2_response.py](backend/app/services/layer2_response.py) — the Gemini scope-reasoning prompt
4. [backend/app/services/layer3_orchestrator.py](backend/app/services/layer3_orchestrator.py) — the full investigation pipeline
5. [frontend/src/lib/api.ts](frontend/src/lib/api.ts) — how the frontend talks to the backend
6. [frontend/src/app/investigations/[id]/page.tsx](frontend/src/app/investigations/[id]/page.tsx) — the human decision interface

---

## What "AI-Native" Actually Means

A system is AI-native when removing the AI causes it to collapse — not into a slower version
of itself, but into nothing at all.

Test it: remove Gemini from SimpleResolve.

- Maintaining real-time behavioral profiles for millions of clients? Gone.
- Reasoning about *which capabilities* to restrict based on the semantic relationship between
  a trigger and an account? Gone — rules engines can only do on/off.
- Cross-client coordination detection in real time? Gone — humans work one case at a time.
- Synthesising behavioral baseline + FINTRAC indicators + network data into a coherent legal
  narrative? Gone.

The *workflow shape* is fundamentally different. This is AI-native design.
