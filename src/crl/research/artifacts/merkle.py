"""Domain-separated Merkle tree for immutable artefact manifests.

Leaves and internal nodes use distinct domain prefixes so a leaf cannot be
forged as a node via string/byte concatenation ambiguity. Leaves are ordered
by normalized relative path before hashing.

Checkpoint aggregates bind distinct artefact identities plus content roots;
identical member bytes across runs are normal and never collapse identity.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

# Domain separation prefixes (single-byte tags).
_LEAF_DOMAIN = b"\x00"
_NODE_DOMAIN = b"\x01"
# Explicit empty-tree identity (not SHA-256 of empty string alone).
_EMPTY_TREE_MATERIAL = b"CRL_MERKLE_EMPTY_V1\x00"


def _canonical_json(payload: Mapping[str, Any] | Sequence[Any] | Any) -> str:
    """Local canonical JSON to avoid circular imports with ledger package."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def empty_merkle_root() -> str:
    """Deterministic root for an empty member set."""
    return hashlib.sha256(_EMPTY_TREE_MATERIAL).hexdigest()


def leaf_hash(*, relative_path: str, content_sha256: str, byte_size: int) -> bytes:
    """Hash one manifest leaf with domain separation."""
    path = str(relative_path)
    digest = str(content_sha256).strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("content_sha256 must be lowercase SHA-256 hex")
    if int(byte_size) < 0:
        raise ValueError("byte_size must be >= 0")
    material = _canonical_json(
        {
            "byte_size": int(byte_size),
            "content_sha256": digest,
            "relative_path": path,
        }
    ).encode("utf-8")
    return hashlib.sha256(_LEAF_DOMAIN + material).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    """Hash an internal node: domain || left || right (fixed-width digests)."""
    if len(left) != 32 or len(right) != 32:
        raise ValueError("node children must be 32-byte digests")
    return hashlib.sha256(_NODE_DOMAIN + left + right).digest()


def merkle_root_from_leaves(leaves: Sequence[bytes]) -> str:
    """Compute hex Merkle root from ordered leaf digests.

    Odd-count levels promote the final unpaired node without self-hashing.
    """
    if not leaves:
        return empty_merkle_root()
    level: list[bytes] = list(leaves)
    for item in level:
        if len(item) != 32:
            raise ValueError("leaves must be 32-byte digests")
    while len(level) > 1:
        next_level: list[bytes] = []
        i = 0
        while i < len(level):
            if i + 1 < len(level):
                next_level.append(node_hash(level[i], level[i + 1]))
                i += 2
            else:
                # Explicit promote (no hash(x||x) ambiguity).
                next_level.append(level[i])
                i += 1
        level = next_level
    return level[0].hex()


def merkle_root_from_members(
    members: Iterable[tuple[str, str, int]],
) -> str:
    """Root from ``(relative_path, content_sha256, byte_size)`` members.

    Members are sorted by relative_path before leaf hashing.
    """
    ordered = sorted(members, key=lambda m: m[0])
    # Reject duplicate paths after ordering.
    seen: set[str] = set()
    leaves: list[bytes] = []
    for path, digest, size in ordered:
        if path in seen:
            raise ValueError(f"duplicate relative_path in merkle members: {path!r}")
        seen.add(path)
        leaves.append(
            leaf_hash(relative_path=path, content_sha256=digest, byte_size=size)
        )
    return merkle_root_from_leaves(leaves)


def aggregate_digest_merkle(
    artefacts: Iterable[tuple[str, str]],
) -> str:
    """Aggregate sealed artefacts into one domain-separated root.

    Each item is ``(artifact_id, content_merkle_root)``. Distinct artefact
    identities with identical content roots remain distinct leaves; content
    alone never collapses identity.
    """
    items: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for raw_id, raw_root in artefacts:
        aid = str(raw_id).strip()
        root = str(raw_root).strip().lower()
        if not aid:
            raise ValueError("artifact_id must be non-empty for aggregate merkle")
        if aid in seen_ids:
            raise ValueError(f"duplicate artifact_id in aggregate: {aid!r}")
        seen_ids.add(aid)
        if len(root) != 64 or any(ch not in "0123456789abcdef" for ch in root):
            raise ValueError(f"invalid content merkle for aggregate: {root!r}")
        items.append((aid, root))
    ordered = sorted(items, key=lambda x: x[0])
    leaves: list[bytes] = []
    for aid, root in ordered:
        material = _canonical_json(
            {"artifact_id": aid, "bundle_merkle_root": root}
        ).encode("utf-8")
        leaves.append(hashlib.sha256(_LEAF_DOMAIN + material).digest())
    return merkle_root_from_leaves(leaves)
