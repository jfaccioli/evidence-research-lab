# Autonomous operating charter (human-light)

**Effective:** 2026-07-27 (updated: 2026-07-28 **Standing Autonomy Directive**)  
**Authority:** Human standing order — agent may proceed without per-step confirmation along the **promotion ladder toward live automated trading**, except hard stops below.

**Also see (superseding where conflict):**  
`docs/STANDING_RESEARCH_DIRECTOR_DIRECTIVE.md` — primary Research Director mandate.  
Also: `docs/STANDING_AUTONOMY_DIRECTIVE.md`, `docs/RESEARCH_QUEUE.md`, `docs/ROADMAP_AUTOTrading_V1.md`.

**Default after any milestone:** re-rank `docs/RESEARCH_QUEUE.md` and execute next highest-EV programme — do not wait for routine “what next?” approval.

---

## 1. Destination vs honesty

**Agreed destination:** a system that *can* do tiny live automated trading (AUD 10–20, spot BTC, kill-switch) when **earned**.

**Not allowed:** skip research / soften gates / enable live early so it “feels done.”

| Horizon | Meaning |
|---------|---------|
| **Now** | Phase 2 discovery + build paper/shadow **scaffolding** (LIVE hard-disabled) |
| **Before paper capital clock** | ≥2–3 **independent confirmatory survivors** (different mechanisms) under frozen gates |
| **Paper** | Clock-synced sim, fees, ≥1 month stability |
| **Shadow** | Live signals, **no orders**, reconcile would-have path |
| **Tiny live** | Human opens Phase 5 (`CRL_PHASE5_LIVE_ENABLED` + config) + keys + independent safety review |

See `docs/PROMOTION_LADDER.md` and `src/crl/production/`.

| Usable milestone | Not success |
|------------------|-------------|
| Research loop solid | Impressive backtests alone |
| Paper broker + shadow logger tested | Softening gates to invent candidates |
| LIVE path exists but **fail-closed** | Silent live orders |
| Thesis Tree current | “Ship trading app” without survivors |

---

## 2. Dual-Grok / independent review policy

| Work type | Review mode |
|-----------|-------------|
| Research design, batches, autopsy, thesis updates | **Grok primary + dual-Grok internal QA** (read diffs, re-check gate tables, no self-congratulation) |
| P1 freeze items (ledger, holdout, immutability, release) | **Independent review required** (Codex automation or ChatGPT paste) before treating as frozen |
| HUMAN_REQUIRED / security / live keys | **Human only** |

Codex automation status may be **PAUSED** — do not block research. For P1 freezes, use ChatGPT independent ACCEPT protocol under `.handoffs/` when needed.

**Same-model cannot clear its own HUMAN_REQUIRED.**

---

## 3. Agent may do without asking

1. Design ≤N pre-registered programmes (lock hyps before seeing results).  
2. Fetch **public** market data (OHLCV, funding, OI) already used by the lab.  
3. Run exploratory/confirmatory under **frozen gates** on **temp registries** first.  
4. Gate autopsy + Thesis Tree + LEARNINGS updates.  
5. Commit on the working research branch with clear messages.  
6. Add tests for scientific correctness bugs.  
7. Dual-Grok internal QA of own diffs before commit.  
8. Continue to the next highest **information-gain** step automatically.

---

## 4. Hard stops — must ask human

| Stop | Why |
|------|-----|
| API keys, secrets, `.env`, credentials | Security |
| Enabling live / paper / shadow execution | Promotion ladder + human authority |
| Softening gates or costs to create survivors | Scientific integrity |
| Force-push, delete remote history, destructive infra | Irreversible |
| Force-push or rewrite published history | Irreversible; confirm first |
| First-time remote create (done: `evidence-research-lab`) | Was human; now `git push` is routine |
| Spending paid third-party APIs (X, Polymarket premium, etc.) | Cost + keys |
| Writing science results into **live** registry as authoritative without noting temp vs live | Evidence governance |

---

## 5. Priority queue (default) — dual track

**Track A — Discovery (required for live)** — **selective only**  
1. **Closed for clone wave:** `docs/PHASE2_CLOSEOUT.md`.  
2. **Next classes (when opened, design-first):** flow/whale → X PIT → Polymarket (deferred programme docs).  
3. Confirmatory only for true exploratory survivors (budget-aware).  
4. Autopsy + thesis when any experiment runs (never skip).  
5. **Never:** re-mine spent locks; **never leverage** as vehicle (`docs/POLICY_NO_LEVERAGE.md`).  
6. **Notify human when close to tiny live** (closeout §6 criteria) — not before.

**Track B — Lab reliability + live-readiness scaffolding (default focus)**  
1. Doctor / status / run-programme / autopsy / tests (`make check`).  
2. Paper + shadow path hardening (no capital).  
3. Risk envelope + kill-switch; LIVE dual-flag + no exchange adapter.  
4. Docs and inventory accuracy.  
5. **Never:** wire real API keys or enable LIVE without human Phase-5 open.

---

## 6. Session continuity

Each session should:

1. Read `AGENTS.md`, this charter, Thesis Tree summary.  
2. Resume the priority queue without re-asking “how to proceed?”  
3. Commit when a coherent unit of knowledge is locked.  
4. Leave a short “NEXT” note in commit body or `research_kb/LEARNINGS.md` if context may drop.

Human should only need to: supply keys/remotes when asked, and eventually open paper/live phases.
