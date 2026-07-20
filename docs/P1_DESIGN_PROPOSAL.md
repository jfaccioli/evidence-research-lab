# P1 Design Proposal — Holdout integrity, trial ledger, immutable lineage

**Status:** **Approved in principle** (final documentation amendments incorporated).  
**Implementation:** **Not authorized** until a separate engineering plan is approved.  
**Revision:** Final review amendments — governed epoch vs legacy, sensitivity/citation policy resolution, power-based prospective endpoint, accrual isolation, SQLite consistent snapshot, resolved human decisions.  
**Scope:** Scientific integrity after P0 (PnL identity, total-return accounting, annualization-consistent Bonferroni / non-DSR proxy, test-slice 2× stress).  
**Out of scope:** Funding research implementation, paper/live trading, gate threshold changes, architecture rewrite, creating a Git remote without explicit authorization.

Success metric remains: **knowledge per research-budget unit**, not candidate count.

---

## Goals

1. Make confirmatory holdouts **programme-level, cohort-based, and burnable** — not per-hypothesis peeks.  
2. Make reservation **irreversible** (no return to AVAILABLE after RESERVED).  
3. Make multiplicity **lineage-persistent** across renames, code changes, and programme versions when prior results influenced design.  
4. Make trial classification **factual and policy-derived**, not agent-supplied.  
5. Derive history completeness from **reconciliation**, not caller flags.  
6. Separate a **governed epoch** (can become COMPLETE prospectively) from **legacy history** (never COMPLETE).  
7. Combine **SQLite operational atomicity** with **hash-chain + external anchor** for tamper evidence.  
8. Make run/cohort artifacts **immutable** with ledger digests and post-event checkpoints.  
9. Treat all **currently available BTC history as burned** for genuine confirmatory promotion.  
10. Freeze calendar/timing semantics in split manifests (warm-up, decision, execution timestamps).  
11. Label existing curated KB documents as **legacy pre-P1 evidence**.  
12. Specify an adversarial **test plan** before any code lands.

---

## 0. Governed epoch versus legacy history

### 0.1 Identities

| Identity | Role |
|----------|------|
| `research_lineage_id` | Continuous lab research history |
| `governance_epoch_id` | Span of research under full P1 controls (ledger, holdout machine, checkpoints) |
| `programme_lineage_id` / `programme_version_id` | Programme family and sealed version (§3) |

A **new governance epoch** begins only when P1 controls are live and sealed. All prior work is **legacy** relative to that epoch.

### 0.2 Completeness by era

| Era | Allowed completeness labels | Can become `COMPLETE`? |
|-----|----------------------------|-------------------------|
| **Governed epoch** (post-P1 cutover) | `COMPLETE`, `INCOMPLETE_KNOWN_GAPS`, `INCOMPLETE_UNBOUNDED` | **Yes** — prospectively, when invariants hold |
| **Legacy history** (pre-P1 / pre-epoch) | `LEGACY_RECONSTRUCTED_CONSERVATIVELY` or `INCOMPLETE_UNBOUNDED` only | **Never** |

**Hard rules**

- Legacy backfill **never** transitions to `COMPLETE`.  
- Future **promotion** requires **both**:  
  1. `COMPLETE` status for the **governed epoch** relevant to the cohort; **and**  
  2. a **human-approved conservative upper bound** on legacy analytical trials, included in **N_global**.  
- If no defensible legacy upper bound exists, **promotion remains blocked** indefinitely.

### 0.3 Separate read-only legacy census

A **read-only legacy census** (no mutation of historical scientific conclusions) shall establish whether a defensible upper bound on pre-epoch selection-capable trials is possible. Outputs:

- proposed bound and methodology;  
- known gaps;  
- human approval or rejection of the bound.

Until that census is approved, treat legacy as blocking for promotion via missing (b).

---

## 1. Programme splits and holdout scope

### 1.1 Permanent calendar-based programme splits

**Problem:** Fractional splits recompute when data grows; observations can migrate across train/val/test.

**Proposal:** Immutable **Programme Split Manifest** once frozen:

```yaml
programme_version_id: btc_usdt_spot_daily_pv1
programme_lineage_id: btc_usdt_spot_daily
research_lineage_id: crl_btc_research_v0
governance_epoch_id: crl_governed_epoch_1   # null / legacy for pre-P1 work
parent_programme_version_id: null
version_reason: "initial sealed calendar after P0"
prior_results_available_at_creation: true
dataset_id: binance_public_BTCUSDT_1d_<sha12>
interval: 1d
timezone: UTC

raw_data_start: "2017-08-17T00:00:00Z"
raw_data_end:   "YYYY-MM-DDT00:00:00Z"
feature_warm_up:
  min_bars: 200
  eligible_decision_start: "YYYY-MM-DDT00:00:00Z"
signal_availability_rule: "features use only data with close_time <= decision_time"
candle_semantics:
  open_time_field: open_time_utc
  close_time_field: close_time_utc
  incomplete_open_candle: drop
decision_timestamp: "bar close_time (signal time)"
execution_timestamp: "next bar open_time (fill model)"
dataset_vintage_freeze_time: "ISO-8601 when this dataset_id was frozen"

boundaries:
  train_start: "..."
  train_end:   "..."
  val_end:     "..."
  holdout_start: "..."   # confirmatory / prospective — see §1.2, §8
  holdout_end:   "..."   # frozen endpoint from power analysis when prospective
```

**Rules**

- Splits are **calendar endpoints**, not fractions.  
- Extending market data does **not** move past boundaries; new bars require a **new programme_version_id**.  
- Runs must reference `programme_version_id` + `dataset_id` (+ `governance_epoch_id` when governed); mismatch → hard fail.  
- Silent boundary edits are forbidden.

### 1.2 Programme-level holdout (replaces per-hypothesis test leases)

**Replace** per-hypothesis `saw_test` leases with:

| Concept | Definition |
|---------|------------|
| **Programme holdout** | Fixed calendar window and/or prospective accrual window for confirmatory evaluation |
| **Confirmatory cohort** | Immutable preregistered set of candidates evaluated together against one holdout opening |
| **One opening event** | Exactly one reservation/opening of a given holdout for a given programme version |

**Before reservation, freeze (immutable):**

- cohort membership (hypothesis versions / `spec_hash` list);  
- specs, metrics definitions, cost model, gates;  
- code/config hashes;  
- multiplicity method and census scope;  
- split manifest and dataset vintage.

**After reservation:**

- **No hypotheses may be appended** to the cohort.  
- Holdout data must not enter ordinary feature caches or evaluation dataframes **before** reservation.  
- Once **any** cohort result may have been exposed (screen, log, partial report, interactive session), the holdout is **burned for all later adaptively derived hypotheses** under this research lineage (not only cohort members).

---

## 2. Irreversible reservation state machine

### States

```
AVAILABLE → RESERVED → CONSUMED
                   └→ ABORTED_BURNED
```

**Forbidden:** `RESERVED → AVAILABLE`.

| Transition | Meaning |
|------------|---------|
| AVAILABLE → RESERVED | Atomic open for a frozen cohort; trial + budget registration in same transaction |
| RESERVED → CONSUMED | Cohort evaluation finished; metrics + gates + artifacts persisted |
| RESERVED → ABORTED_BURNED | Crash, kill, timeout, or any failure after reservation; **holdout burned** even if **no metrics persisted** |

### Crash policy

- Absence of metrics **does not** prove absence of access.  
- Any process that obtained RESERVED has potentially exposed holdout information → **ABORTED_BURNED**, not “retry clean.”  
- A new confirmatory attempt requires a **new holdout** (new calendar / prospective window / new programme_version with declared parent and `version_reason`).

### Data access

- Holdout bars must not be loaded into default `load_or_build_features` paths or exploratory dataframes prior to RESERVED.  
- Implementation sketch (later): `HoldoutDataHandle` obtainable only after RESERVED commit.

---

## 3. Research lineage and multiplicity

### 3.1 Permanent identities

| Identity | Role |
|----------|------|
| `research_lineage_id` | Lab-wide continuous research history |
| `governance_epoch_id` | P1-governed era (§0) |
| `programme_lineage_id` | Family of related programmes |
| `programme_version_id` | Specific sealed programme configuration |
| `parent_programme_version_id` | Prior version (nullable only for true genesis) |
| `version_reason` | Why the version exists |
| `prior_results_available_at_creation` | Whether designers had access to prior outcomes |

**Hard rule:** Changing names, code, thresholds, features, horizons, datasets, or programme versions **does not reset multiplicity** when prior research influenced the change. Influence is presumed if `prior_results_available_at_creation=true` or parent linkage exists.

### 3.2 Multiplicity quantities (both required)

| Quantity | Definition |
|----------|------------|
| **N_global** | Every **selection-capable** trial in the persistent `research_lineage_id` up to the decision time, **including** the human-approved conservative **legacy upper bound** (§0) when promoting |
| **N_cohort** | Every preregistered candidate opened in the confirmatory cohort (and selection-capable sensitivity per §4) |

**Require both** global and cohort-level correction.  

**Do not** reduce raw counts for correlation; default is **no correlation discount**.

### 3.3 Future programmes (e.g. funding)

**Default:** same `research_lineage_id` as existing BTC research (H5 resolved).  

A funding programme must still declare:

- relationship / `parent_programme_version_id` where applicable;  
- `prior_results_available_at_creation`;  
- that it does **not** silently reset N_global.

Any fork to a new lineage requires **later independent programme review** — not a silent tool default.

---

## 4. Trial classification (factual fields + policy-derived counts)

### 4.1 Immutable factual fields (system-written)

| Field | Notes |
|-------|--------|
| `trial_kind` | hypothesis_eval, sensitivity_point, feature/threshold/horizon/interaction/aggregation_variant, reproduction, synthetic_fixture, benchmark_bh, cost_stress_base, cost_stress_2x, aborted_eval, … |
| `selection_capable` | Derived: could the outcome have influenced selection/promotion? |
| `synthetic` | true for unit/E2E fixtures |
| `immutable_input_hash` | Sealed inputs hash |
| `result_exposed` | true if any human/agent-visible path existed |
| `registration_time` | Before execution |
| `execution_state` | registered, running, completed, aborted, error |

### 4.2 `counts_for_multiplicity` is policy-derived only

**Never** accept an agent- or caller-supplied Boolean as authoritative.

### 4.3 Sensitivity policy (H6 resolved)

1. **Every evaluated and researcher-visible neighbour** capable of affecting selection or promotion **counts**.  
2. **Preregistration** defines the **permitted** sensitivity grid but **does not exempt** grid members from counting.  
3. An **ad-hoc unregistered neighbour** still **counts** and creates a **governance violation** that **blocks promotion** pending human review.

### 4.4 Count (selection-capable, non-excluded)

- visible hypothesis, parameter, feature, threshold, horizon, interaction, aggregation variants;  
- all sensitivity points under §4.3;  
- **changed-input** reruns;  
- aborted evaluations where a result **may** have been exposed (including RESERVED→ABORTED_BURNED).

### 4.5 Do **not** separately count (when verified)

- verified **byte-identical** deterministic reproductions;  
- **synthetic** unit/E2E fixtures;  
- retries where reservation **never committed** and **no** result was exposed;  
- predetermined **buy-and-hold**;  
- mandatory preregistered **base and 2× cost** evaluations of the **same** sealed candidate (one selection unit, two cost diagnostics).

### 4.6 Citation / double-count policy (H9 resolved)

- Every historical analytical trial is **counted once** in the ledger when it occurs.  
- Later **citation or narrative reuse does not count it again**.  
- Any **new formulation** derived from that evidence **counts when evaluated**.

### 4.7 Post-hoc diagnostics

If diagnostic choices are altered **after** results are observed, the **alternatives count**.

---

## 5. Derived history completeness (no authoritative caller flag)

### Remove

Authoritative caller-controlled `trial_history_complete=True` as a pass key.

### Derived completeness enum

| Value | Meaning | Promotion? |
|-------|---------|------------|
| `COMPLETE` | All reconciliation invariants hold for a **governed epoch** | Eligible **only** for governed epoch (plus §0 legacy bound) |
| `INCOMPLETE_KNOWN_GAPS` | Gaps enumerated | Fail closed |
| `INCOMPLETE_UNBOUNDED` | Cannot bound missing peeks | Fail closed; legacy may remain here |
| `LEGACY_RECONSTRUCTED_CONSERVATIVELY` | Pre-epoch backfill with upper-bound trial counts | **Never** COMPLETE; non-promotable era; bound feeds N_global only after human approval |

### Promotion prerequisites (summary)

1. Governed epoch status = **COMPLETE**.  
2. Human-approved **conservative legacy N upper bound** included in **N_global**.  
3. Cohort holdout CONSUMED under valid protocol; artifacts anchored or rules in §7.3 applied.  
4. No open governance violations (e.g. unregistered sensitivity).

If (2) is missing → **promotion blocked**.

### Reconciliation invariants (minimum)

Across hypotheses, runs, ledger events, artifact bundles, datasets, split manifests, feature hashes, budgets, report paths, holdout reservations:

1. Every completed selection-capable evaluation has trial registration **before** `execution_state=completed`.  
2. Every `run_id` maps to exactly one artifact bundle digest (or explicit failure event).  
3. Every RESERVED holdout ends in CONSUMED or ABORTED_BURNED.  
4. Budget debits match billable registered trials.  
5. No sealed report path without a ledger event (volatile `latest_*` excluded).  
6. Feature matrix hash matches lineage at registration.  
7. Event sequence contiguous; hash chain unbroken.  
8. Synthetic trials never appear in promotable evidence sets.  
9. Database snapshot hashes used in checkpoints come from **consistent backup/snapshot operations** (§7.2), not live-file hashes mid-WAL.

Legacy remains **non-promotable** even after conservative backfill.

---

## 6. SQLite operational store + tamper evidence

### 6.1 Single SQLite database (operational atomicity)

- foreign keys ON;  
- strict state transitions;  
- append-only `events`;  
- triggers rejecting UPDATE/DELETE on events and sealed digest rows;  
- `event_seq`, `prev_event_hash`, `event_hash`;  
- trial registration + research-budget reservation (+ holdout RESERVED when applicable) in **one transaction**.

### 6.2 SQLite is not the external trust anchor

Requires hash chain, artifact digests, checkpoints, and optional external anchor (§7.3).

---

## 7. Artifact and checkpoint integrity

### 7.1 Immutable bundles

- content hash or Merkle root;  
- digest in ledger;  
- no normal update/delete;  
- corrections = superseding events only.

### 7.2 Post-event checkpoint

After each scientific event:

| Field | Purpose |
|-------|---------|
| `final_event_seq` / `final_event_hash` | Chain tip |
| `database_snapshot_hash` | Hash of a **consistent SQLite backup/snapshot** (e.g. `sqlite3.backup` API or equivalent online backup), **not** a hash of the live DB file while WAL writes may be outstanding |
| `artifact_merkle_root` | Sealed bundles |
| `timestamp` | UTC |
| `code_identity` | git_sha / package version / dirty flag |

**Off-machine backup (H8):** An event is not **authoritative** for promotion or authoritative Thesis Tree conclusions until the corresponding consistent DB snapshot (and required artifacts) have been **copied off-machine** per operational policy. Local-only state remains operational but non-authoritative.

### 7.3 External anchor unavailable

If anchor provider is unset or unreachable (current default):

1. Event still counts as a visible analytical trial when selection-capable / exposed.  
2. Mark **`UNANCHORED_PENDING`**.  
3. **Cannot** support promotion or authoritative Thesis Tree conclusions.  
4. Later anchoring = **new event**, no rewrite.

**H1/H2 (resolved for design intent):** External anchor **deferred**. Recommended future option after **explicit human authorization**: protected **private GitHub audit branch** (or equivalent) as anchor channel — **not** created or assumed now. No remote exists; none is authorized by this document.

---

## 8. Prospective confirmation (burned history)

### 8.1 Burn statement

**All previously available BTC history is burned for genuine confirmatory promotion** under this lab’s `research_lineage_id`.

### 8.2 Allowed uses of historical data

Exploration, debugging, power estimation, negative evidence, non-promotable replication — with trial registration when selection-capable or exposed.

### 8.3 Future confirmatory cohort

Must:

1. Freeze candidate set, code, costs, gates, and **endpoint** before new data accrue;  
2. Avoid inspecting **sealed cohort strategy performance** during accrual;  
3. Evaluate **once** at the predetermined endpoint;  
4. Remain **research-only** (no paper/live trading).

### 8.4 Prospective endpoint (H3 resolved — no example day counts)

Remove fixed example waits (e.g. 90/180 days) as design defaults.

The **endpoint must be frozen** from a **documented pre-accrual power analysis** based on:

- expected signal / trade frequency;  
- minimum observations / trades;  
- dependence assumptions;  
- target power;  
- resulting **fixed calendar endpoint**.

**Human-only authority** may unblind the cohort (not agents, not automated jobs).

### 8.5 Cohort isolation during accrual

- Sealed cohort **membership, specs, code, costs, and gates cannot change** during accrual.  
- Exploratory work may continue **only** if it **cannot modify** the sealed cohort (separate sandbox; no shared mutable candidate objects).  
- Premature **strategy-performance calculation or exposure** for sealed members **burns** the holdout.  
- **Raw public market observation** (prices accruing in public) does **not** authorize computing the sealed cohort’s performance early.

---

## 9. Split manifest checklist

Required: raw data start/end; feature warm-up; eligible decision start; signal availability rule; candle open/close semantics; decision timestamp; execution timestamp; dataset vintage/freeze time; lineage IDs including `governance_epoch_id`; holdout start/end (power-derived when prospective).

---

## 10. Evidence releases vs volatile state

### 10.1 Legacy pre-P1 evidence (H4 resolved)

Eligible for `research_kb/releases/legacy_pre_p1/` **with explicit banner** (not validated current truth):

- META report;  
- director reports;  
- Thesis Tree snapshot;  
- Learnings snapshot.

**Excluded:** `latest_plan` (and other planner “latest” outputs) — remain **volatile**.

### 10.2 Volatile

`latest_plan`, `proposed/`, live budget, machine knowledge/thesis JSON, working SQLite (plus separate backup policy).

### 10.3 Pre-existing untracked artifacts

Still untracked at design time; must not be committed as validated post-P1 truth without the legacy release process.

---

## 11. Required test plan

| # | Scenario |
|---|----------|
| 1 | Concurrent cohort reservation (one wins) |
| 2 | Crash after RESERVED → ABORTED_BURNED; never AVAILABLE |
| 3 | Attempted reopening of burned holdout |
| 4 | Attempted cohort-member append after reservation |
| 5 | Direct test-data access without reservation |
| 6 | Programme-version change does not reset N_global with parent/prior results |
| 7 | Ledger UPDATE/DELETE rejected |
| 8 | Hash-chain gap detection |
| 9 | Bundle overwrite / run_id collision rejected |
| 10 | Synthetic evidence contamination blocked |
| 11 | Budget/ledger atomic rollback |
| 12 | UNANCHORED_PENDING / non-authoritative without off-machine backup cannot promote |
| 13 | Prospective split warm-up / eligible_decision_start correctness |
| 14 | Unregistered sensitivity neighbour counts and blocks promotion |
| 15 | Citation reuse does not double-count trials |
| 16 | Legacy cannot be labeled COMPLETE; promotion blocked without approved legacy bound |
| 17 | Checkpoint DB hash rejects live-file hash path (must use consistent snapshot API) |
| 18 | Accrual isolation: exploratory mutation of sealed cohort rejected; early performance eval burns holdout |

---

## 12. Suggested later PR order (post engineering authorization only)

1. Lineage + `governance_epoch_id` + split manifest schema.  
2. Holdout state machine + cohort freeze.  
3. Trial ledger + policy-derived multiplicity + derived completeness (incl. §0).  
4. Immutable artifacts + consistent SQLite snapshot checkpoints.  
5. Anchor adapter (default UNANCHORED_PENDING).  
6. Evidence filters + legacy labels + non-authoritative Thesis Tree when incomplete/unanchored.  
7. Full test plan.

No funding hyps/data in these PRs. No threshold weakening.

---

## 13. Human decisions — resolved recommendations

| ID | Resolution |
|----|------------|
| **H1 / H2** | External anchor **deferred**. Recommended later path after **explicit authorization**: protected **private GitHub audit branch** (or equivalent). **No remote now.** Until anchored + off-machine backup, promotion blocked by §7. |
| **H3** | Endpoint from **pre-accrual power analysis** (frequency, min N/trades, dependence, target power → fixed calendar end). **Human-only unblind.** No 90/180-day defaults. |
| **H4** | META, director reports, Thesis Tree, Learnings → eligible for **`legacy_pre_p1`**. **`latest_plan` excluded** (volatile). |
| **H5** | Funding defaults to **same `research_lineage_id`**, pending any later independent programme review for a fork. |
| **H6** | **Resolved in §4.3** — all selection-capable visible neighbours count; preregistration defines permitted grid but does not exempt; ad-hoc unregistered neighbour counts **and** blocks promotion. |
| **H7** | **Separate read-only legacy census** to propose a conservative N upper bound; human approval required; never upgrades legacy to COMPLETE (§0). |
| **H8** | **Off-machine backup required** before an event is authoritative (§7.2). |
| **H9** | **Resolved in §4.6** — count once at occurrence; citation does not re-count; new derived formulations count when evaluated. |

### Still deferred (not design blockers for documentation; blockers for promotion ops)

| Item | Notes |
|------|--------|
| Exact numeric legacy bound | Output of H7 census + human sign-off |
| Anchor implementation choice | H1/H2 after authorization |
| Prospective power-analysis template details | Method must be documented per cohort; not fixed in this proposal beyond required inputs |

---

## 14. Explicit non-goals

- Implementing P1 code or funding-rate research in this amendment.  
- Paper / shadow / live trading.  
- Softening promotion thresholds.  
- Resetting research history via rename.  
- Treating SQLite alone as tamper-proof.  
- Claiming BLP Deflated Sharpe without full paper method (P0 already uses non-DSR naming).  
- Creating or pushing to any Git remote without explicit authorization.

---

**End of final P1 design documentation. Implementation not authorized by this file alone.**
