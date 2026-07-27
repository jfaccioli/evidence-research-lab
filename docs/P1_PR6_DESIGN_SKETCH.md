# P1 PR6 Design Sketch — Evidence governance

**Status:** Sketch only (not implementation-ready detail level of PR5).  
**Blocked on:** Independent ACCEPT of PR4; design/implement ACCEPT of PR5.  
**Source:** `docs/P1_ENGINEERING_PLAN.md` PR6, design proposal completeness/promotion rules.

---

## Objective

- Filter synthetic/mock evidence out of promotable sets and multiplicity.
- Legacy pre-P1 release workflow with mandatory disclaimer banners.
- Thesis Tree **authoritative vs non-authoritative** modes.
- Keep `latest_plan` / volatile planner outputs non-authoritative forever.

## Non-goals

- Rewrite historical conclusions as post-P1 validated.
- Mass mutation of `research_kb` narratives.
- Enable authoritative mode without COMPLETE + anchor + backup (PR5).

## Expected modules (sketch)

| Module | Role |
|--------|------|
| `src/crl/research/evidence/filters.py` | synthetic/mock exclusion predicates |
| `src/crl/research/evidence/releases.py` | copy-forward release packaging + legacy banner |
| Thesis Tree rebuild flags | authoritative only when predicates pass |
| tests | contamination, mode switch, latest_plan volatility |

## Predicates (draft)

Authoritative Thesis Tree / promotable evidence requires **all**:

1. Governed-epoch completeness path (not legacy COMPLETE fiction).
2. External anchor ANCHORED for governing tip (PR5).
3. Off-machine backup VERIFIED for governing tip (PR5).
4. No open governance violations / unregistered sensitivity neighbours.
5. Synthetic trials excluded from N and from export sets.
6. Human-approved legacy N bound when legacy history is cited.

## Ordering

Implement only after PR5 is independently accepted (or human override).  
This sketch exists so dual-Grok does not stall on blank paper after PR5.

---

**Not a substitute for a full PR6 design handoff.** Expand when PR5 nears ACCEPT.
