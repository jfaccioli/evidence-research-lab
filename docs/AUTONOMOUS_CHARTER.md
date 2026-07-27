# Autonomous operating charter (human-light)

**Effective:** 2026-07-27  
**Authority:** Human standing order — agent may proceed without per-step confirmation until the lab is **operationally usable for Phase 2 research**, except hard stops below.

---

## 1. What “operationally usable” means here

This project is a **research lab**, not a trading bot.

| Usable | Not the goal yet |
|--------|------------------|
| `crl plan` / `run` / `batch` / `learn` / `thesis` work on pinned data | Live orders / exchange API trading |
| Frozen gates + registry + reports | Softening gates to force a candidate |
| Clear Thesis Tree + programme docs after batches | Paper/shadow/live (blocked until promotion ladder) |
| Pre-reg programmes for new mechanisms without babysitting | “App that makes money” |

**Phase 2 target:** reduce uncertainty until **2–3 independent confirmatory survivors** from **different** mechanisms — or honest null that the daily long-only space is exhausted under these gates. Paper trading only after that + human go (`docs/PROMOTION_LADDER.md`).

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
| Pushing to remote if no remote / unclear | Needs remote URL once |
| Spending paid third-party APIs (X, Polymarket premium, etc.) | Cost + keys |
| Writing science results into **live** registry as authoritative without noting temp vs live | Evidence governance |

---

## 5. Research priority queue (default)

When idle, pick the next item **in order**, skip exhausted lines:

1. Underrepresented mechanisms with **existing** features (`capacity_tiny_friction`, etc.).  
2. Confirmatory only for true exploratory survivors (budget-aware).  
3. Autopsy + thesis (never skip).  
4. Operator UX (runbook, CLI clarity) if research is blocked on usability.  
5. New external PIT series only with design-first programme (no proxy laundering).  
6. **Never:** re-mine funding/OI thresholds on spent programme data.

---

## 6. Session continuity

Each session should:

1. Read `AGENTS.md`, this charter, Thesis Tree summary.  
2. Resume the priority queue without re-asking “how to proceed?”  
3. Commit when a coherent unit of knowledge is locked.  
4. Leave a short “NEXT” note in commit body or `research_kb/LEARNINGS.md` if context may drop.

Human should only need to: supply keys/remotes when asked, and eventually open paper/live phases.
