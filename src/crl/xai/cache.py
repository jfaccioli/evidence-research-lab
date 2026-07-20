"""Disk cache for xAI / search calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class DiskCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _key(self, namespace: str, payload: dict[str, Any]) -> Path:
        h = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:24]
        return self.root / namespace / f"{h}.json"

    def get(self, namespace: str, payload: dict[str, Any]) -> Any | None:
        path = self._key(namespace, payload)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def set(self, namespace: str, payload: dict[str, Any], value: Any) -> None:
        path = self._key(namespace, payload)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, default=str))
