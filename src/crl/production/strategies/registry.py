"""Approved production strategy IDs — empty until confirmatory survivors exist."""

from __future__ import annotations

from typing import Iterable

# Only hypothesis ids that passed confirmatory + human nomination may be listed.
APPROVED: tuple[str, ...] = ()


def is_approved(strategy_id: str) -> bool:
    return strategy_id in APPROVED


def assert_approved(strategy_id: str) -> None:
    if not is_approved(strategy_id):
        raise RuntimeError(
            f"Strategy {strategy_id!r} is not in production.strategies.APPROVED. "
            "No confirmatory survivors are approved for paper-clock/live yet."
        )


def list_approved() -> list[str]:
    return list(APPROVED)


def validate_no_unapproved(candidates: Iterable[str]) -> None:
    bad = [c for c in candidates if not is_approved(c)]
    if bad:
        raise RuntimeError(f"Unapproved strategy ids: {bad}")
