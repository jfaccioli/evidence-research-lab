"""Promotable-evidence filters (synthetic/mock contamination blocked)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from crl.research.ledger.multiplicity import MultiplicityCensus, compute_multiplicity
from crl.research.ledger.trials import TrialKind


@dataclass(frozen=True)
class EvidenceRow:
    """Minimal trial facts for promotable-set filtering."""

    trial_id: str
    trial_kind: str
    synthetic: bool
    selection_capable: bool
    is_citation: bool
    programme_version_id: str
    research_lineage_id: str
    selection_unit_id: str
    result_exposed: bool = False
    dataset_id: Optional[str] = None
    source_class: Optional[str] = None


# Mock / synthetic markers that must never enter promotable export sets.
_SYNTHETIC_SOURCE_MARKERS = frozenset(
    {
        "mock",
        "synthetic",
        "fixture",
        "test_only",
        "unit_test",
    }
)


def is_synthetic_evidence(row: EvidenceRow) -> bool:
    """True when the row must be excluded from promotable evidence sets."""
    if row.synthetic:
        return True
    if row.trial_kind == TrialKind.SYNTHETIC_FIXTURE.value:
        return True
    for field in (row.dataset_id, row.source_class, row.selection_unit_id):
        if field is None:
            continue
        text = str(field).strip().lower()
        if not text:
            continue
        for marker in _SYNTHETIC_SOURCE_MARKERS:
            if marker in text:
                return True
    return False


def filter_promotable_evidence(
    rows: Sequence[EvidenceRow],
) -> tuple[EvidenceRow, ...]:
    """Return only non-synthetic, non-citation rows eligible for promotable views.

    Does **not** grant promotion authority — callers must still pass completeness,
    anchor, backup, and multiplicity gates.
    """
    out: list[EvidenceRow] = []
    for row in rows:
        if is_synthetic_evidence(row):
            continue
        if row.is_citation or row.trial_kind == TrialKind.CITATION.value:
            continue
        if row.trial_kind == TrialKind.BENCHMARK_BH.value:
            continue
        out.append(row)
    return tuple(out)


def load_trial_evidence_rows(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
) -> tuple[EvidenceRow, ...]:
    """Load trial rows for a lineage (empty if trials table absent)."""
    try:
        rows = conn.execute(
            """
            SELECT trial_id, trial_kind, synthetic, selection_capable,
                   is_citation, programme_version_id, research_lineage_id,
                   selection_unit_id, result_exposed
            FROM trials
            WHERE research_lineage_id = ?
            ORDER BY trial_id
            """,
            (str(research_lineage_id).strip(),),
        ).fetchall()
    except sqlite3.Error:
        return ()
    out: list[EvidenceRow] = []
    for r in rows:
        out.append(
            EvidenceRow(
                trial_id=str(r[0]),
                trial_kind=str(r[1]),
                synthetic=bool(int(r[2])),
                selection_capable=bool(int(r[3])),
                is_citation=bool(int(r[4])),
                programme_version_id=str(r[5]),
                research_lineage_id=str(r[6]),
                selection_unit_id=str(r[7]),
                result_exposed=bool(int(r[8])),
            )
        )
    return tuple(out)


def promotable_trial_ids(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
) -> tuple[str, ...]:
    """Trial ids remaining after synthetic/mock contamination filter."""
    rows = filter_promotable_evidence(
        load_trial_evidence_rows(conn, research_lineage_id=research_lineage_id)
    )
    return tuple(r.trial_id for r in rows)


def multiplicity_excluding_synthetic(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    cohort_id: Optional[str] = None,
) -> MultiplicityCensus:
    """Multiplicity census (ledger already excludes synthetic from N).

    Exposed for PR6 callers that need an explicit promotable-filter boundary.
    Synthetic contamination of *exports* is handled by ``filter_promotable_evidence``.
    """
    return compute_multiplicity(
        conn,
        research_lineage_id=research_lineage_id,
        cohort_id=cohort_id,
    )


def assert_no_synthetic_in_promotable_export(
    rows: Iterable[EvidenceRow],
) -> None:
    """Fail closed if any synthetic row appears in a claimed promotable export."""
    bad = [r.trial_id for r in rows if is_synthetic_evidence(r)]
    if bad:
        raise ValueError(
            f"synthetic/mock evidence forbidden in promotable export: {bad[:5]}"
        )
