# P1 PR6 Design — Evidence governance

**Status:** Implemented under dual-Grok (handoff 0037); `ACCEPT_INTERNAL` pending.  
**Depends on:** PR4 residual independent ACCEPT (0035), PR5 implementation (0036).  
**Sources:** `docs/P1_ENGINEERING_PLAN.md` PR6; design proposal §§0, 4, 10.

---

## Goal

Govern what may be treated as **promotable / authoritative** evidence:

1. Exclude synthetic/mock contamination from promotable export sets.
2. Package **legacy_pre_p1** releases as copy-forward with mandatory banner (no in-place truth upgrade).
3. Thesis Tree defaults to **NON-AUTHORITATIVE**; authoritative mode fail-closed without COMPLETE + unblocked promotion path.
4. `latest_plan` / `proposed/` remain **volatile** forever.

## Modules

| Path | Role |
|------|------|
| `src/crl/research/evidence/filters.py` | synthetic/mock/citation exclusion |
| `src/crl/research/evidence/releases.py` | legacy_pre_p1 packaging to explicit dest |
| `src/crl/research/evidence/authority.py` | authoritative mode decision |
| `src/crl/research/evidence/volatile.py` | volatile path detection |
| `docs/templates/legacy_pre_p1_banner.md` | banner template |
| `thesis_tree.rebuild_thesis_tree` | authoritative flag + summary mode |

## Non-goals

- Rewrite research_kb history as post-P1 truth
- Schema v6 (optional evidence_release table deferred; filesystem packaging sufficient)
- Enabling COMPLETE under null anchors
- Live registry / trading

## Acceptance mapping

| Requirement | Coverage |
|-------------|----------|
| Synthetic excluded from promotable sets | `test_evidence_filters` + adversarial |
| latest_plan not stable release | `test_evidence_releases` |
| Legacy banner required | `package_legacy_pre_p1_release` |
| Authoritative refused when incomplete/unanchored | `test_evidence_authority` |

---

**End of PR6 design.**
