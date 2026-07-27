# P1 Engineering Plan — Independently reviewable PRs

**Status:** Design/engineering plan only — **no implementation authorized by this file alone**.
**Depends on:** Approved scientific design in `docs/P1_DESIGN_PROPOSAL.md`.
**Rule:** Each PR stops for **independent review** before the next begins.

---

## Global engineering constraints (all PRs)

| Constraint | Rule |
|------------|------|
| Databases | **Temporary DBs only** for development and tests |
| Live registry | **No migration/write** without separate human approval |
| Research artifacts | **No** report / Thesis Tree / budget / scientific-result regeneration |
| Funding | **No** funding data or hypotheses |
| Execution | **No** paper/live work |
| Gates | **No** promotion threshold changes |
| Git | **No** remote creation or push |
| Verification | **Every PR** runs **focused tests for that PR** and the **complete safe test suite** (temp roots only; exclude root-writing E2E against live paths) |

### Schema / migration rules (all PRs that touch DB)

| Rule | Detail |
|------|--------|
| Compatibility open | Opening a **legacy** database under **compatibility mode** must **not** automatically migrate or change its bytes |
| Fail closed | **Unknown / newer** schema versions **fail closed** (no best-effort read/write) |
| Explicit migrations only | Migrations are **explicit**, **transactional**, and **idempotent**; they **never** run merely because `HypothesisRegistry` (or equivalent) is instantiated, nor on import |
| Downgrade | Unsupported downgrade **fails closed** |

### Cutover from P0 fail-closed multiple-testing (when)

| Phase | Behaviour |
|-------|-----------|
| **Today (post-P0, pre-P1 cutover)** | Legacy: `trial_history_complete=False` / fail-closed Bonferroni hygiene; no proven analytical-trial census |
| **During PR1–PR6** | P0 fail-closed remains **default for promotable decisions** until cutover flag is flipped under human approval |
| **Cutover (after PR7 + approval)** | Replace hard-coded legacy fail-closed with **derived completeness** (`COMPLETE` governed epoch + approved legacy N bound + anchor + off-machine backup). Until then, P1 ledgers may use **audit-only dual-write** (research-governance instrumentation that records trials for audit; **not** shadow trading and **not** enabling promotion) |
| **Never** | Soften thresholds to “make up for” incomplete history |

---

## PR1 — Schema foundation

### Objective
Introduce lineage/epoch/split models, validators, and a schema-migration mechanism **without behavioural cutover**.

### Expected files/modules
- `src/crl/shared/types.py` or new `src/crl/governance/` / `src/crl/programme/`
- `src/crl/research/programme/split_manifest.py` (model + validator)
- `src/crl/research/programme/lineage.py`
- `src/crl/db/` or `src/crl/research/ledger/schema.py` + `migrations/`
- `tests/test_programme_split_manifest.py`, `tests/test_schema_migrations.py`
- Config stubs under `configs/programmes/` (examples only, unused by live path)

### Database/schema changes
- New tables or versioned schema for: `governance_epochs`, `programme_versions`, `split_manifests` (or JSON documents with content hash).
- `schema_version` table.
- **No** write/migrate of live `registry/crl.sqlite`.

### Backward compatibility
- Existing pipeline continues to use fractional splits and P0 fail-closed MT.
- New models are **import-only** in PR1 — **not** wired into the live pipeline (no behaviour-changing feature flag).
- Legacy hyp/run rows remain with null epoch / legacy labels — **never auto-COMPLETE**.
- Opening a legacy DB in **compatibility mode** does not migrate or mutate bytes.
- Unknown/newer schema versions fail closed.

### Failure/rollback
- Migrations applied only via **explicit** API to temp DBs in tests (never on Registry construction).
- Failed migration transaction leaves DB and schema version unchanged.
- Repeated migrate to same target is idempotent.
- Rollback of a PR = drop temp DB / revert branch; main remains non-cutover.

### Acceptance tests
- Manifest validates required calendar/timing fields (§9 design); deterministic content hash.
- Invalid manifests rejected (each calendar/timing condition).
- Explicit migration success on temp DB; rollback after injected failure; idempotent repeat.
- Unknown newer version rejection; legacy null epoch never COMPLETE.
- **Focused PR1 tests + complete safe suite** (exclude root-writing E2E).

### Commands permitted
- `pytest` (temp DB fixtures); focused + full safe suite
- `python -m compileall` optional
- **Not:** `crl run`, `crl batch`, `crl learn`, live DB migrate

### Must not change
- Live registry data; promotion thresholds; research_kb; reports; backtest math; production execution.

---

## PR2 — Cohort and irreversible holdout state machine

### Objective
Programme-level cohort + holdout state machine with sealed membership and access boundary.

### Expected files/modules
- `src/crl/research/holdout/state_machine.py`
- `src/crl/research/holdout/cohort.py`
- `src/crl/research/holdout/data_handle.py` (`HoldoutDataHandle`)
- Ledger/DB tables for holdouts/cohorts
- `tests/test_holdout_state_machine.py`, concurrency/crash tests

### Database/schema changes
- `holdouts(state, programme_version_id, …)`
- `cohorts(membership sealed hash, …)`
- Transitions: AVAILABLE → RESERVED → CONSUMED | ABORTED_BURNED only

### Backward compatibility
- Default exploratory path unchanged (no holdout access).
- Confirmatory path **not** cut over until PR7 + approval (or explicit dual-path flag still fail-closed).

### Failure/rollback
- **Crash recovery** (a recovery path / next opener — **not** the crashed process itself) detects **stale RESERVED** records and records **ABORTED_BURNED** on recovery; the crashed process cannot be relied upon to do so.
- No transition back to AVAILABLE.

### Acceptance tests
- Concurrent reservation: one winner.
- Crash after reservation: recovery records ABORTED_BURNED; never AVAILABLE.
- Reopen burned holdout fails.
- Append member after reservation fails.
- Direct holdout dataframe access without handle fails.
- No per-hypothesis “fresh lease” API for promotable confirmatory.
- **Focused PR2 tests + complete safe suite.**

### Commands permitted
- `pytest` only (temp DBs); focused + full safe suite

### Must not change
- Live registry; thresholds; research results; funding; execution adapters.

---

## PR3 — Analytical-trial ledger and budget atomicity

### Objective
Append-only event ledger with hash chain; policy-derived multiplicity; governed-epoch completeness; atomic trial+budget registration.

### Expected files/modules
- `src/crl/research/ledger/events.py`, `hash_chain.py`, `trials.py`, `completeness.py`
- Budget integration with ledger transactions
- `tests/test_ledger_hash_chain.py`, `tests/test_multiplicity_policy.py`, `tests/test_budget_atomicity.py`

### Database/schema changes
- `events` append-only (seq, prev_hash, hash, payload)
- `trials` factual fields; **no** agent-writable `counts_for_multiplicity`
- Budget reservation rows linked to trial/event ids
- Triggers: block UPDATE/DELETE on events

### Backward compatibility
- P0 path remains default for promotion hygiene until cutover.
- Ledger may record trials via **audit-only dual-write** when enabled (research-governance instrumentation, **not** shadow trading); dual-write does **not** enable COMPLETE or promotion.

### Failure/rollback
- Failed txn rolls back trial **and** budget together.
- Hash gap detection fails reconciliation → INCOMPLETE_*.

### Acceptance tests
- Policy: sensitivity neighbours count; unregistered neighbour blocks promotion flag.
- Citation does not double-count.
- N_global / N_cohort both computed.
- Legacy cannot be COMPLETE; promotion blocked without approved legacy bound field.
- UPDATE/DELETE on events fails.
- Global+cohort correction inputs present for MT caller (still fail-closed if epoch incomplete).

### Commands permitted
- `pytest` (temp DB); focused + full safe suite

### Must not change
- Gate numeric thresholds; live registry migration; research_kb conclusions.

---

## PR4 — Immutable run/cohort bundles

### Objective
Content-addressed bundles, full lineage, collision protection, consistent SQLite snapshot API, checkpoint generation.

### Expected files/modules
- `src/crl/research/artifacts/bundle.py`, `merkle.py`, `checkpoint.py`
- `src/crl/db/snapshot.py` (backup API wrapper)
- tests for overwrite/collision and snapshot consistency

### Database/schema changes
- `artifact_digests(run_id/cohort_id, merkle_root, …)` append-only
- `checkpoints(event_seq, db_snapshot_hash, artifact_merkle_root, …)`

### Backward compatibility
- Legacy report paths may remain readable; **new** code writes to `artifacts/runs/{run_id}/{artifact_id}/` (exclusive run identity + sealed child) when enabled.
- **Legacy reports untouched** (no rewrite of historical report files).

### Failure/rollback
- Bundle write failure aborts run completion event.
- Snapshot must use the **consistent SQLite backup API** (not a naive live-file copy under writers).

### Acceptance tests
- Bundle collision/overwrite rejected.
- Snapshot tests verify a **consistent, reopenable** snapshot and **expected contents**; do **not** require that the snapshot hash differ from a live-file hash.
- Lineage fields present: config, spec, split, data, feature, dependency lock hash.
- Supersede event required for corrections.
- **Focused PR4 tests + complete safe suite.**

### Commands permitted
- `pytest`; optional local temp filesystem inspection; focused + full safe suite

### Must not change
- Existing `reports/*` content; live scientific conclusions; thresholds.

---

## PR5 — External-anchor adapter

### Design status
**Detailed design:** `docs/P1_PR5_DESIGN.md` (handoff 0034).  
**PR4 residual independent ACCEPT:** handoff 0035 (ChatGPT manual).  
**Implementation:** handoff 0036 (dual-Grok producer); schema v5 + `src/crl/research/anchor/**` on branch `p1/pr4-artifact-checkpoints` (uncommitted).

### Objective
Provider-neutral anchor interface; default UNANCHORED_PENDING; off-machine backup interface and verification state.

### Expected files/modules
- `src/crl/research/anchor/base.py`, `null_provider.py`, `types.py`
- Off-machine backup verifier interface (path/config stub)
- tests for promotion block when unanchored / backup unverified

### Database/schema changes
- Event flag/status: `UNANCHORED_PENDING`, `ANCHORED`, `BACKUP_VERIFIED`
- No credentials stored in repo

### Backward compatibility
- Default provider = null; all new events unanchored pending.
- **No actual GitHub remote or credentials.**

### Failure/rollback
- Anchor failure leaves UNANCHORED_PENDING; still counts as trial if exposed.
- Anchoring **later** is represented by a **new append-only anchor event**; **never** by mutation of an earlier event.

### Acceptance tests
- Unanchored cannot promote.
- Unverified off-machine backup cannot promote.
- No network calls required in default tests.
- Interface accepts future private audit-branch provider without schema break.
- Later anchor appends a new event; prior event rows remain unchanged.
- **Focused PR5 tests + complete safe suite.**

### Commands permitted
- `pytest` only; focused + full safe suite

### Must not change
- Create remotes; push; store secrets; enable promotion for unanchored events.

---

## PR6 — Evidence governance

### Implementation status
**Dual-Grok implemented** (handoff 0037, `ACCEPT_INTERNAL`): `src/crl/research/evidence/**`, legacy banner template, Thesis Tree non-authoritative default. Design: `docs/P1_PR6_DESIGN.md`.

### Objective
Synthetic/mock filtering; legacy_pre_p1 release workflow; Thesis Tree authoritative modes; keep latest_plan volatile.

### Expected files/modules
- `src/crl/research/evidence/filters.py`, `releases.py`
- Thesis Tree rebuild flags: authoritative vs non-authoritative
- docs/templates for legacy_pre_p1 banner
- tests for contamination and mode switching

### Database/schema changes
- Optional `evidence_release` metadata table; no rewrite of historical hyp outcomes

### Backward compatibility
- Does **not** rewrite historical conclusions as post-P1 validated.
- Thesis Tree default non-authoritative unless COMPLETE + anchor + backup.

### Failure/rollback
- Release packaging is copy-forward with disclaimer; never mutate source narrative in place as “truth upgrade.”

### Acceptance tests
- Synthetic evidence excluded from promotable sets and multiplicity.
- `latest_plan` not treated as stable release.
- Legacy release banner required.
- Authoritative mode refused when epoch incomplete or unanchored.

### Commands permitted
- `pytest`; optional dry-run of release packaging to **temp dir only**; focused + full safe suite

### Must not change
- Live research_kb historical files without human release approval; no mass conclusion rewrite.

---

## PR7 — Integration / adversarial tests

### Implementation status
**Design §11 matrix complete** (handoff 0039): `tests/adversarial/test_p1_design_section11_matrix.py` covers scenarios **1–18** (holdout concurrency/crash/burn, cohort isolation, data-handle capability, N_global across programme versions, ledger immutability, hash-chain tamper detection, bundle no-overwrite, synthetic contamination, budget atomic rollback, unanchored/backup promotion block, split warm-up rules, sensitivity neighbours, citation non-double-count, legacy non-COMPLETE, snapshot backup API, accrual burn on loader error). Prior starters retained.

### Objective
Full 18 design scenarios + direct-entrypoint bypass + reconciliation audit + safe migration rehearsal on **temporary copies only**.

### Expected files/modules
- `tests/adversarial/test_p1_holdout_*.py`, `test_p1_ledger_*.py`, `test_p1_reconciliation.py`
- Optional `scripts/p1_migration_rehearsal.py` writing **only** under temp paths

### Database/schema changes
- None new if prior PRs complete; uses temp migrated copies of **synthetic** fixtures (not live registry unless human-approved copy path)

### Backward compatibility
- Still no automatic live cutover.

### Failure/rollback
- Rehearsal failure leaves live DB untouched.

### Acceptance tests
- All 18 scenarios from design §11 (plus engineering extras 14–18 if not already covered).
- Direct entrypoints cannot bypass reservation, trial registration, or budget txn.
- Full reconciliation audit on fixture world.
- Migration rehearsal on temp copy only.

### Commands permitted
- `pytest` (focused adversarial + complete safe suite)
- Optional rehearsal script with explicit `--temp-dir` (fail if path looks like live registry)

### Must not change
- Live registry without separate human approval; research_kb; production thresholds; funding; remotes.

---

## Cutover checklist (after PR7 + human approval)

1. Read-only legacy census complete; legacy N upper bound approved.
2. Governed epoch opened; P1 path **audit-only dual-write** validated on fixtures (not shadow trading).
3. Off-machine backup + anchor policy operational (or accept promotion remains blocked while unanchored).
4. Explicit written approval to replace P0 hard-coded fail-closed with derived completeness for promotable decisions.
5. Document cutover `governance_epoch_id` and time.
6. Still no funding/paper/live unless separate programmes approved.

---

## Explicit non-goals (entire P1 engineering programme)

- Funding research
- Paper/live execution
- Threshold changes
- Silent live-registry migration
- Regenerating historical scientific conclusions as if post-P1 validated
- Git remote creation or push without authorization

---

**End of P1 engineering plan. Implement only after per-PR independent review.**
