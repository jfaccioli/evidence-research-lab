"""Programme-level, irreversible confirmatory-holdout state machine.

This module is an unwired PR2 foundation. It operates only on explicitly
migrated P1 schema-v2 databases and exposes no per-hypothesis lease API.
It is not yet a promotable reservation path: PR3 must atomically couple the
RESERVED transition to trial and budget registration before PR7 cutover.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from crl.db.schema import connect_p1
from crl.research.holdout.cohort import CohortMember, membership_hash


class HoldoutState(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    ABORTED_BURNED = "ABORTED_BURNED"


class CohortState(str, Enum):
    DRAFT = "DRAFT"
    SEALED = "SEALED"


class HoldoutStateError(RuntimeError):
    """Base failure for an invalid or unavailable holdout operation."""


class HoldoutTransitionError(HoldoutStateError):
    """Requested transition is not one of the irreversible allowed edges."""


class CohortStateError(HoldoutStateError):
    """Cohort membership or sealing state is incompatible with the operation."""


class ReservationCapabilityError(HoldoutStateError):
    """The reservation token is missing, wrong, stale, or already terminal."""


def _utc_text(value: Optional[datetime] = None) -> str:
    dt = value or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}Z"


def _identifier(value: str, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} must be non-empty")
    return text


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _sha256(value: str, field: str) -> str:
    text = str(value).strip()
    if (
        len(text) != 64
        or text != text.lower()
        or any(ch not in "0123456789abcdef" for ch in text)
    ):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return text


@dataclass(frozen=True)
class HoldoutReservation:
    """Capability returned only after an AVAILABLE→RESERVED commit."""

    holdout_id: str
    programme_version_id: str
    cohort_id: str
    reservation_token: str
    reserved_at: str


class HoldoutStateMachine:
    """Atomic state transitions over an explicitly migrated temporary DB."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).resolve()
        conn = connect_p1(self.database_path, readonly=True)
        try:
            version = conn.execute(
                "SELECT version FROM crl_schema_meta WHERE component='p1_programme'"
            ).fetchone()[0]
            if int(version) < 2:
                raise HoldoutStateError("holdout state machine requires schema v2+")
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = connect_p1(self.database_path)
        conn.isolation_level = None
        return conn

    @staticmethod
    def _begin(conn: sqlite3.Connection) -> None:
        conn.execute("BEGIN IMMEDIATE")

    @staticmethod
    def _finish(conn: sqlite3.Connection, error: BaseException | None) -> None:
        if error is None:
            conn.execute("COMMIT")
        else:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass

    def create_cohort(
        self,
        *,
        cohort_id: str,
        programme_version_id: str,
        protocol_manifest_hash: str,
        created_at: Optional[datetime] = None,
    ) -> None:
        cohort_id = _identifier(cohort_id, "cohort_id")
        programme_version_id = _identifier(
            programme_version_id, "programme_version_id"
        )
        protocol_manifest_hash = _sha256(
            protocol_manifest_hash, "protocol_manifest_hash"
        )
        conn = self._connect()
        error: BaseException | None = None
        try:
            self._begin(conn)
            conn.execute(
                """
                INSERT INTO cohorts(
                    cohort_id, programme_version_id, state,
                    protocol_manifest_hash, membership_hash,
                    created_at, sealed_at
                ) VALUES (?, ?, 'DRAFT', ?, NULL, ?, NULL)
                """,
                (
                    cohort_id,
                    programme_version_id,
                    protocol_manifest_hash,
                    _utc_text(created_at),
                ),
            )
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._finish(conn, error)
            conn.close()

    def add_cohort_member(
        self,
        *,
        cohort_id: str,
        member: CohortMember,
        added_at: Optional[datetime] = None,
    ) -> None:
        cohort_id = _identifier(cohort_id, "cohort_id")
        conn = self._connect()
        error: BaseException | None = None
        try:
            self._begin(conn)
            row = conn.execute(
                "SELECT state, created_at FROM cohorts WHERE cohort_id=?",
                (cohort_id,),
            ).fetchone()
            if row is None:
                raise CohortStateError(f"unknown cohort {cohort_id!r}")
            if row["state"] != CohortState.DRAFT.value:
                raise CohortStateError("cohort membership is already sealed")
            added_text = _utc_text(added_at)
            if added_text < row["created_at"]:
                raise CohortStateError(
                    "member added_at cannot precede cohort creation"
                )
            ordinal = int(
                conn.execute(
                    "SELECT COUNT(*) FROM cohort_members WHERE cohort_id=?",
                    (cohort_id,),
                ).fetchone()[0]
            )
            conn.execute(
                """
                INSERT INTO cohort_members(
                    cohort_id, ordinal, candidate_id, spec_hash, added_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    cohort_id,
                    ordinal,
                    member.candidate_id,
                    member.spec_hash,
                    added_text,
                ),
            )
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._finish(conn, error)
            conn.close()

    def seal_cohort(
        self,
        *,
        cohort_id: str,
        sealed_at: Optional[datetime] = None,
    ) -> str:
        cohort_id = _identifier(cohort_id, "cohort_id")
        conn = self._connect()
        error: BaseException | None = None
        try:
            self._begin(conn)
            row = conn.execute(
                "SELECT state, created_at FROM cohorts WHERE cohort_id=?",
                (cohort_id,),
            ).fetchone()
            if row is None:
                raise CohortStateError(f"unknown cohort {cohort_id!r}")
            if row["state"] != CohortState.DRAFT.value:
                raise CohortStateError("cohort is not DRAFT")
            rows = conn.execute(
                """
                SELECT candidate_id, spec_hash
                FROM cohort_members
                WHERE cohort_id=?
                ORDER BY ordinal
                """,
                (cohort_id,),
            ).fetchall()
            members = tuple(
                CohortMember(candidate_id=row[0], spec_hash=row[1]) for row in rows
            )
            digest = membership_hash(members)
            sealed_text = _utc_text(sealed_at)
            if sealed_text < row["created_at"]:
                raise CohortStateError("sealed_at cannot precede cohort creation")
            changed = conn.execute(
                """
                UPDATE cohorts
                SET state='SEALED', membership_hash=?, sealed_at=?
                WHERE cohort_id=? AND state='DRAFT'
                """,
                (digest, sealed_text, cohort_id),
            ).rowcount
            if changed != 1:
                raise CohortStateError("cohort could not be sealed atomically")
            return digest
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._finish(conn, error)
            conn.close()

    def register_holdout(
        self,
        *,
        holdout_id: str,
        programme_version_id: str,
        created_at: Optional[datetime] = None,
    ) -> None:
        holdout_id = _identifier(holdout_id, "holdout_id")
        programme_version_id = _identifier(
            programme_version_id, "programme_version_id"
        )
        conn = self._connect()
        error: BaseException | None = None
        try:
            self._begin(conn)
            conn.execute(
                """
                INSERT INTO holdouts(
                    holdout_id, programme_version_id, state,
                    reserved_cohort_id, reservation_token_hash,
                    created_at, reserved_at, terminal_at, terminal_reason
                ) VALUES (?, ?, 'AVAILABLE', NULL, NULL, ?, NULL, NULL, NULL)
                """,
                (holdout_id, programme_version_id, _utc_text(created_at)),
            )
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._finish(conn, error)
            conn.close()

    def reserve_on_connection(
        self,
        conn: sqlite3.Connection,
        *,
        holdout_id: str,
        cohort_id: str,
        reserved_at: Optional[datetime] = None,
    ) -> HoldoutReservation:
        """AVAILABLE→RESERVED on an existing transaction (no begin/commit).

        Used by PR3 atomic trial+budget+holdout registration so reservation
        participates in the caller's SQLite transaction.
        """
        holdout_id = _identifier(holdout_id, "holdout_id")
        cohort_id = _identifier(cohort_id, "cohort_id")
        token = secrets.token_urlsafe(32)
        token_digest = _token_hash(token)
        reserved_text = _utc_text(reserved_at)
        holdout = conn.execute(
            """
            SELECT programme_version_id, state, created_at
            FROM holdouts
            WHERE holdout_id=?
            """,
            (holdout_id,),
        ).fetchone()
        if holdout is None:
            raise HoldoutTransitionError(f"unknown holdout {holdout_id!r}")
        cohort = conn.execute(
            """
            SELECT programme_version_id, state, protocol_manifest_hash,
                   membership_hash
            FROM cohorts
            WHERE cohort_id=?
            """,
            (cohort_id,),
        ).fetchone()
        if cohort is None:
            raise CohortStateError(f"unknown cohort {cohort_id!r}")
        if cohort["state"] != CohortState.SEALED.value:
            raise CohortStateError("cohort must be SEALED before reservation")
        if cohort["membership_hash"] is None:
            raise CohortStateError("sealed cohort is missing membership hash")
        if cohort["protocol_manifest_hash"] is None:
            raise CohortStateError("sealed cohort is missing protocol manifest")
        if cohort["programme_version_id"] != holdout["programme_version_id"]:
            raise CohortStateError(
                "cohort and holdout must share programme_version_id"
            )
        if reserved_text < holdout["created_at"]:
            raise HoldoutTransitionError(
                "reserved_at cannot precede holdout creation"
            )
        changed = conn.execute(
            """
            UPDATE holdouts
            SET state='RESERVED',
                reserved_cohort_id=?,
                reservation_token_hash=?,
                reserved_at=?
            WHERE holdout_id=? AND state='AVAILABLE'
            """,
            (cohort_id, token_digest, reserved_text, holdout_id),
        ).rowcount
        if changed != 1:
            raise HoldoutTransitionError(
                "holdout is not AVAILABLE; reservation is irreversible"
            )
        return HoldoutReservation(
            holdout_id=holdout_id,
            programme_version_id=holdout["programme_version_id"],
            cohort_id=cohort_id,
            reservation_token=token,
            reserved_at=reserved_text,
        )

    def reserve(
        self,
        *,
        holdout_id: str,
        cohort_id: str,
        reserved_at: Optional[datetime] = None,
    ) -> HoldoutReservation:
        """Atomically reserve one programme holdout for one sealed cohort."""
        conn = self._connect()
        error: BaseException | None = None
        try:
            self._begin(conn)
            return self.reserve_on_connection(
                conn,
                holdout_id=holdout_id,
                cohort_id=cohort_id,
                reserved_at=reserved_at,
            )
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._finish(conn, error)
            conn.close()

    def _terminal_transition(
        self,
        reservation: HoldoutReservation,
        *,
        state: HoldoutState,
        reason: str,
        terminal_at: Optional[datetime],
    ) -> None:
        if state not in (HoldoutState.CONSUMED, HoldoutState.ABORTED_BURNED):
            raise ValueError("terminal transition must consume or burn")
        reason = _identifier(reason, "terminal reason")
        terminal_text = _utc_text(terminal_at)
        if terminal_text < reservation.reserved_at:
            raise HoldoutTransitionError(
                "terminal_at cannot precede reservation time"
            )
        conn = self._connect()
        error: BaseException | None = None
        try:
            self._begin(conn)
            changed = conn.execute(
                """
                UPDATE holdouts
                SET state=?, terminal_at=?, terminal_reason=?
                WHERE holdout_id=?
                  AND programme_version_id=?
                  AND reserved_cohort_id=?
                  AND reservation_token_hash=?
                  AND state='RESERVED'
                """,
                (
                    state.value,
                    terminal_text,
                    reason,
                    reservation.holdout_id,
                    reservation.programme_version_id,
                    reservation.cohort_id,
                    _token_hash(reservation.reservation_token),
                ),
            ).rowcount
            if changed != 1:
                raise ReservationCapabilityError(
                    "reservation is invalid, stale, or already terminal"
                )
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._finish(conn, error)
            conn.close()

    def consume(
        self,
        reservation: HoldoutReservation,
        *,
        reason: str = "cohort_evaluation_completed",
        terminal_at: Optional[datetime] = None,
    ) -> None:
        self._terminal_transition(
            reservation,
            state=HoldoutState.CONSUMED,
            reason=reason,
            terminal_at=terminal_at,
        )

    def abort_burned(
        self,
        reservation: HoldoutReservation,
        *,
        reason: str,
        terminal_at: Optional[datetime] = None,
    ) -> None:
        self._terminal_transition(
            reservation,
            state=HoldoutState.ABORTED_BURNED,
            reason=reason,
            terminal_at=terminal_at,
        )

    def recover_stale_reservations(
        self,
        *,
        stale_before: datetime,
        recovered_at: Optional[datetime] = None,
    ) -> tuple[str, ...]:
        """Burn every RESERVED row older than ``stale_before`` atomically."""
        stale_text = _utc_text(stale_before)
        recovered_text = _utc_text(recovered_at)
        if recovered_text < stale_text:
            raise HoldoutTransitionError(
                "recovered_at cannot precede the stale cutoff"
            )
        conn = self._connect()
        error: BaseException | None = None
        try:
            self._begin(conn)
            rows = conn.execute(
                """
                SELECT holdout_id
                FROM holdouts
                WHERE state='RESERVED' AND reserved_at < ?
                ORDER BY holdout_id
                """,
                (stale_text,),
            ).fetchall()
            ids = tuple(str(row[0]) for row in rows)
            for holdout_id in ids:
                changed = conn.execute(
                    """
                    UPDATE holdouts
                    SET state='ABORTED_BURNED',
                        terminal_at=?,
                        terminal_reason='stale_reservation_recovery'
                    WHERE holdout_id=? AND state='RESERVED'
                    """,
                    (recovered_text, holdout_id),
                ).rowcount
                if changed != 1:
                    raise HoldoutTransitionError(
                        f"stale reservation changed concurrently: {holdout_id}"
                    )
            return ids
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._finish(conn, error)
            conn.close()

    def state(self, holdout_id: str) -> HoldoutState:
        conn = connect_p1(self.database_path, readonly=True)
        try:
            row = conn.execute(
                "SELECT state FROM holdouts WHERE holdout_id=?",
                (_identifier(holdout_id, "holdout_id"),),
            ).fetchone()
            if row is None:
                raise HoldoutStateError(f"unknown holdout {holdout_id!r}")
            return HoldoutState(row[0])
        finally:
            conn.close()

    def cohort_members(self, cohort_id: str) -> tuple[CohortMember, ...]:
        conn = connect_p1(self.database_path, readonly=True)
        try:
            rows = conn.execute(
                """
                SELECT candidate_id, spec_hash
                FROM cohort_members
                WHERE cohort_id=?
                ORDER BY ordinal
                """,
                (_identifier(cohort_id, "cohort_id"),),
            ).fetchall()
            return tuple(CohortMember(row[0], row[1]) for row in rows)
        finally:
            conn.close()

    def issue_data_handle(self, reservation: HoldoutReservation):
        """Create the only supported capability for loading holdout data."""
        from crl.research.holdout.data_handle import HoldoutDataHandle

        return HoldoutDataHandle._issue(self, reservation)

    def assert_active_reservation(self, reservation: HoldoutReservation) -> None:
        conn = connect_p1(self.database_path, readonly=True)
        try:
            row = conn.execute(
                """
                SELECT 1
                FROM holdouts
                WHERE holdout_id=?
                  AND programme_version_id=?
                  AND reserved_cohort_id=?
                  AND reservation_token_hash=?
                  AND state='RESERVED'
                """,
                (
                    reservation.holdout_id,
                    reservation.programme_version_id,
                    reservation.cohort_id,
                    _token_hash(reservation.reservation_token),
                ),
            ).fetchone()
            if row is None:
                raise ReservationCapabilityError(
                    "holdout data capability is not an active reservation"
                )
        finally:
            conn.close()
