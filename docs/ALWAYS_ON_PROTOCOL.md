# Always-on research protocol

**Status:** **ON** (human enabled 2026-07-31)  
**Goal:** Autotrade with better odds of profit — via honest tests, not forced winners.

---

## 1. Default behaviour

Every session (or scheduled run), without waiting for “what next?”:

1. Read queue + belief state + last report  
2. Pick **one** highest-EV next test (or dual-Grok scan if queue empty)  
3. Dual-Grok internal QA on the plan when non-trivial  
4. Run under **frozen gates** (temp registry / research reports)  
5. Update thesis/beliefs/queue  
6. Commit + push  
7. Repeat **within the session budget**  
8. Stop cleanly when budget hits or a human interrupt fires  

---

## 2. Guardrails (token / time / science)

### Recommended session budget (default)

| Limit | Default | Why |
|-------|---------|-----|
| **Wall clock** | **Default ~90–120 min**; **override up to ~24h** when human says so (tokens available) | Long runs OK if prioritised; still soft-stop cleanly |
| **Major science programmes** | Default **≤ 2**; long-run **≤ ~8–12** distinct pre-reg families (not threshold spam) | Quality > spam; new angle each time |
| **Confirmatory runs** | **≤ 1** per session (only if earned) | Confirmatory budget is scarce |
| **Commits** | Prefer batching; push at end of each programme | Avoid noise |
| **New architecture** | None unless a test is blocked | Stay evidence-driven |

**2 hours is a solid default.**  
- **Less (45–60 min):** safer on tokens if sessions are frequent.  
- **More (3–4h):** only if you explicitly want a long run day.

### Soft stop (preferred)

When budget is nearly used:

1. Finish the **current** test (don’t leave half-written state)  
2. Write 5-line status in `docs/RESEARCH_QUEUE.md`  
3. Push  
4. Exit — resume next session from the queue  

### Hard stops (always — you)

- API keys / secrets  
- Paid data spend  
- Paper / shadow / live trading enable  
- Softening gates  
- Destructive git / security  

---

## 3. What “always-on” is *not*

- Not a background process while your laptop sleeps (unless you add a separate cron/scheduler later)  
- Not unlimited token burn  
- Not permission to skip dual-Grok QA on non-trivial science  
- Not live trading  

---

## 4. Efficiency vs tokens

| Approach | Tokens | Progress quality |
|----------|--------|------------------|
| No budget | Can drain hard | Mixed |
| **90–120 min + ≤2 programmes** | Predictable | Best EV |
| Many tiny chats | Overhead of re-context | Often worse |

**Recommendation:** keep **~2h max per session**, **≤2 programmes**, resume next day/session. That maximises **honest progress per dollar of tokens**.

---

## 5. Human overrides

You can say anytime:

- `pause always-on`  
- `budget 60m` / `budget 3h`  
- `one test only`  

---

*Autonomous research under `docs/AQRO_CONSTITUTION.md` and `docs/AUTONOMOUS_CHARTER.md`.*
