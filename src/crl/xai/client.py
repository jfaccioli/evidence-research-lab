"""xAI client interface — mock by default; live wired later behind env flag."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from crl.xai.cache import DiskCache
from crl.xai.cost_ledger import CostLedger
from crl.xai.ratelimit import RateLimiter


class XAIClient(Protocol):
    def complete(self, prompt: str, **kwargs: Any) -> str: ...
    def search_web(self, query: str, **kwargs: Any) -> list[dict]: ...
    def search_x(self, query: str, **kwargs: Any) -> list[dict]: ...


@dataclass
class MockXAIClient:
    """Offline-safe mock for CI and Phase 1 core."""

    cache: DiskCache
    limiter: RateLimiter
    ledger: CostLedger

    def complete(self, prompt: str, **kwargs: Any) -> str:
        if not self.limiter.allow():
            raise RuntimeError("xAI daily rate limit exceeded")
        key = {"prompt": prompt, **kwargs}
        cached = self.cache.get("complete", key)
        if cached is not None:
            return str(cached["text"])
        text = (
            "[mock xAI] Hypothesis ideation disabled in mock mode. "
            "Use hand-authored or template hypotheses in Phase 1."
        )
        self.cache.set("complete", key, {"text": text})
        self.ledger.record("complete_mock", 1.0, note="mock")
        return text

    def search_web(self, query: str, **kwargs: Any) -> list[dict]:
        if not self.limiter.allow():
            raise RuntimeError("xAI daily rate limit exceeded")
        self.ledger.record("search_web_mock", 1.0)
        return [{"title": "mock", "snippet": f"No live search for: {query}"}]

    def search_x(self, query: str, **kwargs: Any) -> list[dict]:
        if not self.limiter.allow():
            raise RuntimeError("xAI daily rate limit exceeded")
        self.ledger.record("search_x_mock", 1.0)
        return [{"text": f"[mock] {query}"}]


def build_xai_client(cfg: dict, root: Path) -> MockXAIClient:
    x = cfg.get("xai", {})
    cache = DiskCache(root / x.get("cache_dir", "data/xai_cache"))
    limiter = RateLimiter(max_calls_per_day=int(x.get("max_calls_per_day", 50)))
    ledger = CostLedger(path=root / "data" / "xai_cost_ledger.json")
    # Phase 1: always mock unless explicitly extended later
    return MockXAIClient(cache=cache, limiter=limiter, ledger=ledger)
