"""Deterministic confirmatory-cohort membership sealing.

PR2 does not evaluate strategies. It defines the immutable membership identity
that must exist before a programme holdout can be reserved. The cohort row also
binds a separate protocol-manifest hash covering preregistered specs, metrics,
costs, gates, code/config identities, and multiplicity policy.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Sequence


class CohortDefinitionError(ValueError):
    """The proposed cohort is empty, duplicated, or malformed."""


def _require_identifier(value: str, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise CohortDefinitionError(f"{field} must be non-empty")
    return text


def _require_sha256(value: str, field: str) -> str:
    text = str(value).strip()
    if (
        len(text) != 64
        or text != text.lower()
        or any(ch not in "0123456789abcdef" for ch in text)
    ):
        raise CohortDefinitionError(
            f"{field} must be a 64-character lowercase SHA-256 digest"
        )
    return text


@dataclass(frozen=True)
class CohortMember:
    """One preregistered candidate in declared cohort order."""

    candidate_id: str
    spec_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidate_id",
            _require_identifier(self.candidate_id, "candidate_id"),
        )
        object.__setattr__(
            self,
            "spec_hash",
            _require_sha256(self.spec_hash, "spec_hash"),
        )


def canonical_membership_bytes(members: Sequence[CohortMember]) -> bytes:
    """Return canonical ordered membership bytes.

    Order is scientifically meaningful and is preserved through an explicit
    ordinal in the database. Candidate identifiers must be unique.
    """
    if not members:
        raise CohortDefinitionError("a confirmatory cohort must contain members")
    seen: set[str] = set()
    payload: list[dict[str, str]] = []
    for member in members:
        if member.candidate_id in seen:
            raise CohortDefinitionError(
                f"duplicate candidate_id in cohort: {member.candidate_id}"
            )
        seen.add(member.candidate_id)
        payload.append(
            {
                "candidate_id": member.candidate_id,
                "spec_hash": member.spec_hash,
            }
        )
    return (
        json.dumps(
            {"members": payload},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def membership_hash(members: Iterable[CohortMember]) -> str:
    """Hash an ordered, non-empty cohort membership."""
    sequence = tuple(members)
    return hashlib.sha256(canonical_membership_bytes(sequence)).hexdigest()
