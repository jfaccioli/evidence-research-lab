"""Capability-checked holdout data access for PR2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from crl.research.holdout.state_machine import (
    HoldoutReservation,
    HoldoutStateMachine,
)


T = TypeVar("T")


class HoldoutAccessError(RuntimeError):
    """Holdout data was requested without a valid reserved-cohort capability."""


_ISSUER = object()


@dataclass(frozen=True)
class HoldoutDataHandle(Generic[T]):
    """An unforgeable-by-public-constructor capability for one reservation."""

    _machine: HoldoutStateMachine
    _reservation: HoldoutReservation
    _issuer: object

    def __post_init__(self) -> None:
        if self._issuer is not _ISSUER:
            raise HoldoutAccessError(
                "HoldoutDataHandle may only be issued after reservation commit"
            )

    @classmethod
    def _issue(
        cls,
        machine: HoldoutStateMachine,
        reservation: HoldoutReservation,
    ) -> "HoldoutDataHandle[Any]":
        machine.assert_active_reservation(reservation)
        return cls(machine, reservation, _ISSUER)

    @property
    def holdout_id(self) -> str:
        return self._reservation.holdout_id

    @property
    def cohort_id(self) -> str:
        return self._reservation.cohort_id

    def load(self, loader: Callable[[str, str], T]) -> T:
        """Load through an active reservation; any loader error burns access."""
        if not callable(loader):
            raise HoldoutAccessError("holdout loader must be callable")
        self._machine.assert_active_reservation(self._reservation)
        try:
            return loader(
                self._reservation.holdout_id,
                self._reservation.programme_version_id,
            )
        except BaseException as exc:
            self._machine.abort_burned(
                self._reservation,
                reason=f"holdout_data_access_error:{type(exc).__name__}",
            )
            raise


def load_holdout_data(
    handle: HoldoutDataHandle[T],
    loader: Callable[[str, str], T],
) -> T:
    """Reject raw/None handles and delegate only to a valid capability."""
    if not isinstance(handle, HoldoutDataHandle):
        raise HoldoutAccessError(
            "holdout data requires a HoldoutDataHandle from a committed reservation"
        )
    return handle.load(loader)
