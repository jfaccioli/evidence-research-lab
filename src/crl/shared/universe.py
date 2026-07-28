"""Spot universe allow-list (multi-asset plumbing).

Phase-1 started BTC-only. Mandate now allows a small, config-defined
spot USDT set (default: BTC + ETH). Expanding the list is a product decision;
it is not a licence to scan many alts for a lucky backtest.

See docs/MULTI_ASSET_V1.md.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

# Canonical display form: BASE/QUOTE
DEFAULT_SPOT_ASSETS: tuple[str, ...] = ("BTC/USDT", "ETH/USDT")


def normalize_asset(asset: str) -> str:
    """Normalize ``BTCUSDT`` / ``btc/usdt`` / ``BTC-USDT`` → ``BTC/USDT``."""
    s = str(asset or "").strip().upper().replace("-", "/").replace("_", "/")
    if not s:
        return ""
    if "/" in s:
        parts = [p for p in s.split("/") if p]
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
        return parts[0] if parts else ""
    # Compact exchange form e.g. BTCUSDT, ETHUSDT
    for quote in ("USDT", "USD", "BUSD", "USDC"):
        if s.endswith(quote) and len(s) > len(quote):
            return f"{s[: -len(quote)]}/{quote}"
    return s


def asset_to_binance_symbol(asset: str) -> str:
    """``ETH/USDT`` → ``ETHUSDT``."""
    a = normalize_asset(asset)
    return a.replace("/", "")


def binance_symbol_to_asset(symbol: str) -> str:
    return normalize_asset(symbol)


def _cfg_spot_assets(cfg: dict[str, Any] | None) -> tuple[str, ...]:
    if not cfg:
        return DEFAULT_SPOT_ASSETS
    uni = cfg.get("universe") or {}
    raw = uni.get("spot_assets") or uni.get("assets")
    if not raw:
        # legacy single-symbol config
        sym = cfg.get("symbol_binance") or cfg.get("asset")
        if sym:
            return (normalize_asset(str(sym)),)
        return DEFAULT_SPOT_ASSETS
    out = tuple(normalize_asset(str(x)) for x in raw if str(x).strip())
    return out if out else DEFAULT_SPOT_ASSETS


def allowed_spot_assets(cfg: dict[str, Any] | None = None) -> frozenset[str]:
    return frozenset(_cfg_spot_assets(cfg))


def allowed_binance_symbols(cfg: dict[str, Any] | None = None) -> frozenset[str]:
    return frozenset(asset_to_binance_symbol(a) for a in allowed_spot_assets(cfg))


def is_asset_allowed(asset: str, cfg: dict[str, Any] | None = None) -> bool:
    return normalize_asset(asset) in allowed_spot_assets(cfg)


def is_symbol_allowed(symbol: str, cfg: dict[str, Any] | None = None) -> bool:
    return asset_to_binance_symbol(symbol) in allowed_binance_symbols(cfg)


def assert_symbol_allowed(
    symbol: str,
    cfg: dict[str, Any] | None = None,
    *,
    context: str = "symbol",
) -> str:
    """Return normalized Binance symbol or raise."""
    sym = asset_to_binance_symbol(symbol)
    allowed = allowed_binance_symbols(cfg)
    if sym not in allowed:
        raise ValueError(
            f"{context}: {symbol!r} not in spot universe {sorted(allowed)}. "
            "See configs/default.yaml universe.spot_assets / docs/MULTI_ASSET_V1.md"
        )
    return sym


def default_binance_symbol(cfg: dict[str, Any] | None = None) -> str:
    """Primary symbol for fetch when none specified (config default)."""
    if cfg:
        if cfg.get("symbol_binance"):
            return asset_to_binance_symbol(str(cfg["symbol_binance"]))
        assets = _cfg_spot_assets(cfg)
        if assets:
            return asset_to_binance_symbol(assets[0])
    return "BTCUSDT"
