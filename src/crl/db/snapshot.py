"""Consistent SQLite snapshot via the online backup API.

A naive copy/hash of the live DB file under writers is forbidden. Snapshots are
built through a unique temporary sibling and published by atomic no-replace
link (never ``os.replace``).
"""

from __future__ import annotations

import errno
import hashlib
import os
import re
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from crl.db.schema import SchemaError, connect_p1, get_schema_version
from crl.research.ledger.hash_chain import GENESIS_PREV_EVENT_HASH, verify_hash_chain

_SAFE_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SnapshotError(RuntimeError):
    """Consistent snapshot capture or verification failed."""


@dataclass(frozen=True)
class SnapshotMetadata:
    """Metadata for a published consistent snapshot."""

    destination: Path
    method: str
    sha256: str
    byte_size: int
    ledger_tip_seq: int
    ledger_tip_hash: str
    schema_version: Optional[int]


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_sql_ident(name: str, *, field: str) -> str:
    text = str(name).strip()
    if not _SAFE_IDENT_RE.fullmatch(text):
        raise SnapshotError(f"unsafe SQL identifier for {field}: {name!r}")
    return text


def _ledger_tip(conn: sqlite3.Connection) -> tuple[int, str]:
    row = conn.execute(
        """
        SELECT event_seq, event_hash
        FROM ledger_events
        ORDER BY event_seq DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return 0, GENESIS_PREV_EVENT_HASH
    return int(row[0]), str(row[1])


def _publish_file_noreplace(src: Path, dst: Path, *, _race_hook=None) -> None:
    """Publish file via hard-link then unlink temp (fails if dest exists)."""
    if dst.exists() or dst.is_symlink():
        raise SnapshotError(f"snapshot destination already exists: {dst}")
    if _race_hook is not None:
        _race_hook(dst)
    if dst.exists() or dst.is_symlink():
        raise SnapshotError(f"snapshot destination already exists: {dst}")
    try:
        os.link(str(src), str(dst))
    except FileExistsError as exc:
        raise SnapshotError(f"snapshot destination already exists: {dst}") from exc
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            raise SnapshotError(
                f"snapshot destination already exists: {dst}"
            ) from exc
        raise SnapshotError(f"snapshot no-replace publish failed: {exc}") from exc
    try:
        os.unlink(str(src))
    except OSError:
        # Destination published; temp cleanup is best-effort.
        pass


def create_consistent_snapshot(
    source_path: str | Path,
    destination_path: str | Path,
    *,
    expected_tip_seq: Optional[int] = None,
    expected_tip_hash: Optional[str] = None,
    expected_contents: Optional[Mapping[str, Any]] = None,
    _race_hook=None,
) -> SnapshotMetadata:
    """Create a consistent snapshot using ``sqlite3`` backup API.

    - Refuses destination overwrite (atomic no-replace link).
    - Builds into a unique temporary sibling on the same filesystem.
    - Opens source read-only when possible.
    - Reopens the snapshot, runs integrity/FK/schema checks, verifies tip.
    """
    source = Path(source_path).resolve()
    dest = Path(destination_path).resolve()
    if source.is_symlink():
        raise SnapshotError(f"source database must not be a symlink: {source}")
    if not source.is_file():
        raise SnapshotError(f"source database not found: {source}")
    if dest.exists() or dest.is_symlink():
        raise SnapshotError(f"snapshot destination already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    token = uuid.uuid4().hex
    tmp = dest.parent / f".{dest.name}.snapshot-tmp-{token}"
    if tmp.exists() or tmp.is_symlink():
        raise SnapshotError(f"temporary snapshot path collision: {tmp}")

    src_conn: Optional[sqlite3.Connection] = None
    dst_conn: Optional[sqlite3.Connection] = None
    published = False
    try:
        # Prefer read-only open of the source (no write intent).
        try:
            src_conn = sqlite3.connect(
                source.as_uri() + "?mode=ro", uri=True
            )
        except sqlite3.Error:
            src_conn = sqlite3.connect(str(source))
        src_conn.execute("PRAGMA foreign_keys = ON")
        dst_conn = sqlite3.connect(str(tmp))
        src_conn.backup(dst_conn)
        dst_conn.close()
        dst_conn = None
        src_conn.close()
        src_conn = None

        # Reopen snapshot and verify independently of the live writer.
        verify_conn = connect_p1(tmp)
        try:
            verify_conn.execute("PRAGMA foreign_keys = ON")
            integrity = verify_conn.execute("PRAGMA integrity_check").fetchall()
            if not integrity or integrity[0][0] != "ok" or len(integrity) != 1:
                raise SnapshotError("snapshot integrity_check failed")
            fk_violations = verify_conn.execute("PRAGMA foreign_key_check").fetchall()
            if fk_violations:
                raise SnapshotError(
                    f"snapshot foreign_key_check failed ({len(fk_violations)} rows)"
                )
            version = get_schema_version(verify_conn)
            chain = verify_hash_chain(verify_conn)
            if not chain.ok:
                raise SnapshotError(
                    "snapshot ledger hash chain invalid: "
                    + "; ".join(chain.errors[:3])
                )
            tip_seq, tip_hash = _ledger_tip(verify_conn)
            if expected_tip_seq is not None and tip_seq != int(expected_tip_seq):
                raise SnapshotError(
                    f"snapshot tip seq {tip_seq} != expected {expected_tip_seq}"
                )
            if expected_tip_hash is not None and tip_hash != str(expected_tip_hash):
                raise SnapshotError(
                    f"snapshot tip hash mismatch: {tip_hash} != {expected_tip_hash}"
                )
            if expected_contents:
                for table, predicates in expected_contents.items():
                    table_s = _safe_sql_ident(table, field="table")
                    if not isinstance(predicates, Mapping):
                        raise SnapshotError("expected_contents values must be mappings")
                    for col, val in predicates.items():
                        col_s = _safe_sql_ident(col, field="column")
                        row = verify_conn.execute(
                            f'SELECT 1 FROM "{table_s}" WHERE "{col_s}" = ? LIMIT 1',
                            (val,),
                        ).fetchone()
                        if row is None:
                            raise SnapshotError(
                                f"snapshot missing expected {table}.{col}={val!r}"
                            )
        finally:
            verify_conn.close()

        digest = _file_sha256(tmp)
        size = tmp.stat().st_size
        _publish_file_noreplace(tmp, dest, _race_hook=_race_hook)
        published = True
        return SnapshotMetadata(
            destination=dest,
            method="sqlite_backup",
            sha256=digest,
            byte_size=size,
            ledger_tip_seq=tip_seq,
            ledger_tip_hash=tip_hash,
            schema_version=version,
        )
    except SchemaError as exc:
        raise SnapshotError(str(exc)) from exc
    finally:
        if src_conn is not None:
            try:
                src_conn.close()
            except Exception:
                pass
        if dst_conn is not None:
            try:
                dst_conn.close()
            except Exception:
                pass
        if not published and tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
