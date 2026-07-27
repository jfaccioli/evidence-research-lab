# P1 PR5 Design — External anchor + off-machine backup

**Status:** Implementation in progress under dual-Grok after ChatGPT independent ACCEPT of PR4 residual 0035.  
**Unblocked by:** handoff 0035 (ChatGPT manual independent ACCEPT of residual 0032).  

**Depends on:** `docs/P1_DESIGN_PROPOSAL.md` §7.2–7.3, `docs/P1_ENGINEERING_PLAN.md` PR5.  
**Out of scope:** GitHub remotes, credentials, network in default tests, promotion enablement, live registry, paper/live trading.

---

## 1. Goal

Make external trust and off-machine durability **first-class, fail-closed, append-only** controls so that:

1. Unanchored events still **count** as selection-capable trials when exposed.
2. Unanchored / unverified-backup state **cannot** support promotion or authoritative Thesis Tree conclusions.
3. Later anchoring or backup verification is a **new ledger event**, never a rewrite of prior rows.
4. Default runtime needs **no network and no secrets**.

PR4 already forces `promotion_blocked=True` via local-only checkpoints and hard-coded PR5 gap strings. PR5 replaces those placeholders with **derived** state from real interfaces + optional tables, without ever minting `COMPLETE` while anchors/backups are missing.

---

## 2. Concepts

| Term | Meaning |
|------|---------|
| **External anchor** | Cryptographic or content attestation that a ledger tip (or checkpoint) existed at a time, outside the local machine trust boundary |
| **Off-machine backup** | Verified copy of a **consistent** SQLite snapshot (+ required artefact bundles) stored outside the primary workstation |
| **UNANCHORED_PENDING** | Default status: event/checkpoint recorded locally; no external attestation yet |
| **ANCHORED** | A later append-only event attests a specific prior tip/checkpoint |
| **BACKUP_VERIFIED** | A later append-only event records successful verification of an off-machine copy |

Hard rules from design proposal:

- `UNANCHORED_PENDING` is **not** a promotion pathway.
- Anchoring later = **new event**; prior event rows immutable.
- No credentials in repo; no remote creation in this PR.

---

## 3. Module layout (expected)

```
src/crl/research/anchor/
  __init__.py
  types.py          # enums, dataclasses, errors
  base.py           # AnchorProvider, OffMachineBackupVerifier protocols
  null_provider.py  # default providers: always pending / never network
  service.py        # record_anchor_attempt, record_backup_verification (append-only)
tests/
  test_anchor_null_provider.py
  test_anchor_promotion_blocks.py
  test_backup_verification_blocks.py
  test_anchor_append_only.py
```

Optional later (not PR5): `github_audit_branch.py` behind explicit human authorization.

---

## 4. Types (`types.py`)

```python
class AnchorStatus(str, Enum):
    UNANCHORED_PENDING = "UNANCHORED_PENDING"
    ANCHORED = "ANCHORED"

class BackupStatus(str, Enum):
    BACKUP_UNVERIFIED = "BACKUP_UNVERIFIED"
    BACKUP_VERIFIED = "BACKUP_VERIFIED"

@dataclass(frozen=True)
class AnchorTarget:
    """What is being attested — always content-addressed."""
    research_lineage_id: str
    final_event_seq: int
    final_event_hash: str
    checkpoint_id: Optional[str]  # if anchoring a PR4 checkpoint
    database_snapshot_hash: Optional[str]
    artifact_aggregate_root: Optional[str]

@dataclass(frozen=True)
class AnchorReceipt:
    status: AnchorStatus
    provider_id: str
    target: AnchorTarget
    external_ref: Optional[str]  # opaque provider reference; never a secret
    attested_at: str  # UTC text
    detail: Mapping[str, Any]  # non-secret metadata only

@dataclass(frozen=True)
class BackupVerificationRequest:
    research_lineage_id: str
    snapshot_relative_path: str  # under explicit backup root, not repo defaults
    expected_snapshot_sha256: str
    expected_size_bytes: int
    final_event_seq: int
    final_event_hash: str

@dataclass(frozen=True)
class BackupVerificationReceipt:
    status: BackupStatus
    provider_id: str
    request: BackupVerificationRequest
    verified_at: str
    detail: Mapping[str, Any]
```

Errors: `AnchorError`, `BackupVerificationError` — fail closed, no partial promotion side effects.

---

## 5. Protocols (`base.py`)

```python
class AnchorProvider(Protocol):
    provider_id: str
    def anchor(self, target: AnchorTarget) -> AnchorReceipt:
        """May return UNANCHORED_PENDING; must not raise merely because offline.
        Must not mutate ledger; service layer records events."""

class OffMachineBackupVerifier(Protocol):
    provider_id: str
    def verify(self, request: BackupVerificationRequest, *, backup_root: Path) -> BackupVerificationReceipt:
        """Read-only verification under explicit backup_root.
        No network. Fail closed on path escape / hash mismatch."""
```

### Null providers (`null_provider.py`)

- `NullAnchorProvider.anchor` → always `UNANCHORED_PENDING`, `external_ref=None`.
- `NullBackupVerifier.verify` → always `BACKUP_UNVERIFIED` **or** optionally perform local path hash check if `backup_root` supplied and file exists — recommend:

  **Preferred null behaviour:** if file missing → `BACKUP_UNVERIFIED`; if present and hash matches → still **do not** auto-promote; only `LocalPathBackupVerifier` (same PR, no network) can return `BACKUP_VERIFIED` after explicit call.

Split:

| Provider | Network | Can return VERIFIED/ANCHORED? |
|----------|---------|-------------------------------|
| `NullAnchorProvider` | No | No — always PENDING |
| `LocalPathBackupVerifier` | No | Yes — SHA-256 + size + regular file under explicit root |
| Future GitHub provider | Yes | Out of PR5 |

Default factory: null anchor + local path backup verifier (tests use temp roots only).

---

## 6. Schema (v5 — explicit migration only)

Extend P1 schema version **5** (PR4 is v4). Rules: transactional, idempotent, never on import; compatibility open of v1–v4 unchanged; unknown >5 fail closed.

### 6.1 New append-only tables

**`external_anchors`**

| Column | Notes |
|--------|-------|
| `anchor_id` | PK, safe id |
| `provider_id` | text |
| `status` | `UNANCHORED_PENDING` \| `ANCHORED` |
| `research_lineage_id` | FK/text |
| `final_event_seq` | int |
| `final_event_hash` | text |
| `checkpoint_id` | nullable |
| `database_snapshot_hash` | nullable |
| `artifact_aggregate_root` | nullable |
| `external_ref` | nullable, non-secret |
| `registration_event_seq` | FK → ledger_events |
| `attested_at` | UTC |
| `detail_json` | canonical JSON |

Triggers: no UPDATE/DELETE.

**`off_machine_backups`**

| Column | Notes |
|--------|-------|
| `backup_id` | PK |
| `provider_id` | text |
| `status` | `BACKUP_UNVERIFIED` \| `BACKUP_VERIFIED` |
| `research_lineage_id` | |
| `snapshot_relative_path` | relative under caller root only |
| `snapshot_sha256` | |
| `snapshot_size_bytes` | |
| `final_event_seq` / `final_event_hash` | tip bound |
| `registration_event_seq` | FK |
| `verified_at` | UTC |
| `detail_json` | |

Triggers: no UPDATE/DELETE. Corrections = **new rows** + new events.

### 6.2 Ledger event types (add to CHECK + ALLOWED_EVENT_TYPES)

- `external_anchor_recorded`
- `off_machine_backup_recorded`

Payload must include status, target tip hashes, provider_id, and content digests. Never include tokens/secrets.

### 6.3 What not to do

- Do **not** UPDATE `ledger_events` or checkpoints to flip a flag in place.
- Do **not** store API keys, PATs, or remote URLs with embedded credentials.
- Do **not** create git remotes or push.

---

## 7. Service semantics (`service.py`)

```text
record_anchor(conn, provider, target) -> AnchorReceipt
  1. receipt = provider.anchor(target)  # pure side-effect free re: DB
  2. in caller's txn (or new explicit txn):
       append_event(external_anchor_recorded, ...)
       INSERT external_anchors (...)
  3. return receipt

record_backup_verification(conn, verifier, request, backup_root) -> BackupVerificationReceipt
  1. receipt = verifier.verify(request, backup_root=backup_root)
  2. append_event + INSERT off_machine_backups
  3. return receipt
```

Fail closed: if event insert fails, no digest row; if row fails, rollback event.

Query helpers:

- `latest_anchor_status(conn, research_lineage_id, final_event_seq) -> AnchorStatus`
- `latest_backup_status(conn, research_lineage_id, final_event_seq) -> BackupStatus`
- Prefer **tip-specific** lookups; a verified backup of tip N does not verify tip N+k.

---

## 8. Completeness / promotion integration

Today (`completeness.py`):

- always appends `missing_external_anchor_pr5`, `missing_verified_off_machine_backup_pr5`
- always `promotion_blocked=True`

PR5 change:

```text
if latest_anchor for assessed tip is not ANCHORED:
    gaps += missing_external_anchor
    block_reasons += ...
if latest_backup for assessed tip is not BACKUP_VERIFIED:
    gaps += missing_verified_off_machine_backup
    block_reasons += ...
# COMPLETE still requires ALL of design §0/§4 list including legacy N, etc.
# Null provider world ⇒ still never COMPLETE (correct).
```

Assessments without a concrete tip still block promotion (cannot claim anchored).

**Authoritative Thesis Tree** (PR6 will consume): refuse authoritative mode unless anchor + backup verified for the governing tip. PR5 only supplies the predicates.

---

## 9. Relationship to PR4 checkpoints

PR4 checkpoints are **local-only** (`is_local_only=1`, `is_authoritative=0`).

PR5 does not flip those bits in place. Instead:

1. Checkpoint recorded (PR4).
2. Consistent snapshot file exists under explicit artefact/backup root.
3. `LocalPathBackupVerifier` verifies copy at off-machine path.
4. Optional null/external anchor attests checkpoint tip + snapshot hash.
5. Completeness reads append-only verification rows.

---

## 10. Tests (acceptance mapping)

| Requirement | Test |
|-------------|------|
| Unanchored cannot promote | `assess_completeness` with only null anchors → `promotion_blocked` and gap present |
| Unverified backup cannot promote | same for backup |
| No network in default tests | null/local providers; monkeypatch/block socket if desired |
| Interface accepts future provider | structural Protocol test / dummy provider returning ANCHORED in unit test without schema break |
| Later anchor appends new event | insert pending then anchored; prior row unchanged; event count +2 |
| Prior event rows immutable | UPDATE/DELETE triggers fire |
| Path escape on backup root | `../` and symlink escape rejected |
| Hash mismatch | BACKUP_UNVERIFIED or hard error; never VERIFIED |
| Migration v4→v5 | temp DB; rollback partial; idempotent |
| Full suite | focused PR5 + complete safe suite |

---

## 11. Allowlist (when implementation authorized)

**Create**

- `src/crl/research/anchor/**`
- `tests/test_anchor_*.py`, `tests/test_backup_*.py`
- docs already this file

**Modify**

- `src/crl/db/migrations/__init__.py` (v5)
- `src/crl/db/schema.py` (verify v5)
- `src/crl/research/ledger/events.py` (ALLOWED_EVENT_TYPES)
- `src/crl/research/ledger/completeness.py` (derived PR5 gaps)
- `src/crl/research/ledger/__init__.py` (exports)
- `tests/test_schema_migrations.py`

**Forbidden**

- live registry; remotes; credentials; research_kb rewrites; thresholds; PR6/7 scope; funding; trading

---

## 12. Implementation order (when unblocked)

1. Types + null/local providers + pure unit tests (no DB).
2. Schema v5 + migration tests.
3. Service append-only writers + immutability tests.
4. Completeness derivation wiring.
5. Full safe suite.
6. Dual-Grok internal QA → queue independent review.

---

## 13. Non-goals reminder

- Not a reliability substitute for honest signals.
- Not Polymarket/X.
- Not enabling promotion in null-provider mode.
- Not creating GitHub audit branch without separate human authorization after this PR.

---

**End of PR5 design.** Implement only after PR4 independent ACCEPT + this design independent review (or human explicit authorization to implement under dual-Grok with later independent review).
