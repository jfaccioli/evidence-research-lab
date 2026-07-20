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
| Verification | Prefer focused unit/integration tests; temp roots only; no root-writing E2E against live paths |

### Cutover from P0 fail-closed multiple-testing (when)

| Phase | Behaviour |
|-------|-----------|
| **Today (post-P0, pre-P1 cutover)** | Legacy: `trial_history_complete=False` / fail-closed Bonferroni hygiene; no proven analytical-trial census |
| **During PR1–PR6** | P0 fail-closed remains **default for promotable decisions** until cutover flag is flipped under human approval |
| **Cutover (after PR7 + approval)** | Replace hard-coded legacy fail-closed with **derived completeness** (`COMPLETE` governed epoch + approved legacy N bound + anchor + off-machine backup). Until then, P1 ledgers may run in **shadow/parallel** mode without enabling promotion |
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
- New models unused by default (`feature_flag` / import-only).
- Legacy hyp/run rows remain with null epoch / legacy labels — **never auto-COMPLETE**.

### Failure/rollback
- Migrations applied only to temp DBs in tests.
- Rollback = drop temp DB; main branch code remains non-cutover.

### Acceptance tests
- Manifest validates required calendar/timing fields (§9 design).
- Invalid manifests rejected.
- Migration up/down (or forward-only version chain) on empty temp DB.
- Legacy null epoch records do not become COMPLETE under any default.

### Commands permitted
- `pytest` (temp DB fixtures)
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
- Crash after RESERVED must leave ABORTED_BURNED (tested).
- No transition back to AVAILABLE.

### Acceptance tests
- Concurrent reservation: one winner.
- Crash after reservation burns holdout.
- Reopen burned holdout fails.
- Append member after reservation fails.
- Direct holdout dataframe access without handle fails.
- No per-hypothesis “fresh lease” API for promotable confirmatory.

### Commands permitted
- `pytest` only (temp DBs)

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
- Ledger may record **shadow** trials if dual-write is enabled; shadow does not enable COMPLETE.

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
- `pytest` (temp DB)

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
- Legacy report paths may remain readable; **new** code writes to `artifacts/runs/{run_id}/` when enabled.
- **Legacy reports untouched** (no rewrite of historical report files).

### Failure/rollback
- Bundle write failure aborts run completion event.
- Snapshot must use backup API; live-file hash path rejected by tests.

### Acceptance tests
- Bundle collision/overwrite rejected.
- Checkpoint `database_snapshot_hash` differs from naive live-file hash under concurrent write simulation where feasible.
- Lineage fields present: config, spec, split, data, feature, dependency lock hash.
- Supersede event required for corrections.

### Commands permitted
- `pytest`; optional local temp filesystem inspection

### Must not change
- Existing `reports/*` content; live scientific conclusions; thresholds.

---

## PR5 — External-anchor adapter

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
- Later anchor = **new event**.

### Acceptance tests
- Unanchored cannot promote.
- Unverified off-machine backup cannot promote.
- No network calls required in default tests.
- Interface accepts future private audit-branch provider without schema break.

### Commands permitted
- `pytest` only

### Must not change
- Create remotes; push; store secrets; enable promotion for unanchored events.

---

## PR6 — Evidence governance

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
- `pytest`; optional dry-run of release packaging to **temp dir only**

### Must not change
- Live research_kb historical files without human release approval; no mass conclusion rewrite.

---

## PR7 — Integration / adversarial tests

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
- `pytest`
- Optional rehearsal script with explicit `--temp-dir` (fail if path looks like live registry)

### Must not change
- Live registry without separate human approval; research_kb; production thresholds; funding; remotes.

---

## Cutover checklist (after PR7 + human approval)

1. Read-only legacy census complete; legacy N upper bound approved.
2. Governed epoch opened; P1 path dual-run validated on fixtures.
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
