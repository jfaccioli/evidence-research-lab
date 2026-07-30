"""US spot BTC ETF daily net flows from Farside Investors public table (free delayed).

Source: https://farside.co.uk/bitcoin-etf-flow-all-data/
Units: US$ millions (Farside native). Aggregate Total column across major US spot BTC ETFs.

PIT policy (binding for this adapter)
-------------------------------------
Farside tables are public delayed research compilations without a revision journal.
We apply a conservative fixed publish lag:

  observation calendar day D → flow_time = end-of-D UTC + publish_lag_days

Default ``publish_lag_days=1``: day-D total net flow is usable only after the next
UTC day completes (no same-day look-ahead). Free-research grade, not vendor-grade PIT.

Sign convention for this series
-------------------------------
**Positive net_flow = net creations / inflows into US spot BTC ETFs (US$m).**
This is *not* exchange deposit/withdraw (retired CMD free-netflow family).

Attribution: data compiled by Farside Investors (https://farside.co.uk).
Verify ToS before redistributing; pin is for local research only.
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pandas as pd

from crl.shared.config import project_root
from crl.shared.data.flow import flow_events_content_hash, validate_flow_events

DEFAULT_URL = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
SERIES_ID = "us_spot_btc_etf_net_flow_usd_m_farside_v1"
ATTRIBUTION = (
    "Bitcoin ETF flow table compiled by Farside Investors "
    "(https://farside.co.uk/bitcoin-etf-flow-all-data/). Local research pin only."
)


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_td = False
        self.in_table = False
        self.tables: list[list[list[str]]] = []
        self.cur: list[list[str]] = []
        self.row: list[str] = []
        self.cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.in_table = True
            self.cur = []
        elif tag == "tr" and self.in_table:
            self.row = []
        elif tag in ("td", "th") and self.in_table:
            self.in_td = True
            self.cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self.in_td:
            self.in_td = False
            self.row.append("".join(self.cell).strip())
        elif tag == "tr" and self.in_table:
            if self.row:
                self.cur.append(self.row)
        elif tag == "table" and self.in_table:
            self.in_table = False
            self.tables.append(self.cur)

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.cell.append(data)


def _parse_farside_number(raw: str) -> float | None:
    s = (raw or "").strip()
    if not s or s == "-":
        return None
    # parentheses = negative in Farside tables
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "").replace("%", "").strip()
    if not s or s == "-":
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _parse_farside_date(raw: str) -> datetime | None:
    s = (raw or "").strip()
    # e.g. 11 Jan 2024
    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s, fmt)
            return d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def fetch_farside_html(url: str = DEFAULT_URL, timeout: float = 60.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "crl-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_farside_daily_total(html: str) -> pd.DataFrame:
    """Return obs_day (UTC midnight) and total_usd_m from the all-data table."""
    p = _TableParser()
    p.feed(html)
    if not p.tables:
        raise ValueError("no HTML tables found on Farside page")
    best = max(p.tables, key=len)
    if not best:
        raise ValueError("empty Farside table")
    header = [c.strip() for c in best[0]]
    # Total column preferred
    try:
        total_idx = next(i for i, h in enumerate(header) if h.lower() == "total")
    except StopIteration:
        total_idx = len(header) - 1
    date_idx = 0
    rows: list[dict[str, Any]] = []
    for r in best[1:]:
        if not r or len(r) <= max(date_idx, total_idx):
            continue
        if (r[0] or "").strip().lower() in {
            "total",
            "average",
            "maximum",
            "minimum",
            "fee",
            "date",
        }:
            continue
        day = _parse_farside_date(r[date_idx])
        if day is None:
            continue
        total = _parse_farside_number(r[total_idx])
        if total is None:
            continue
        rows.append(
            {
                "obs_day": day.replace(hour=0, minute=0, second=0, microsecond=0),
                "total_usd_m": total,
            }
        )
    if not rows:
        raise ValueError("no dated flow rows parsed from Farside")
    df = pd.DataFrame(rows).drop_duplicates(subset=["obs_day"], keep="last")
    df = df.sort_values("obs_day").reset_index(drop=True)
    return df


def farside_to_flow_events(
    daily: pd.DataFrame,
    *,
    publish_lag_days: int = 1,
) -> pd.DataFrame:
    if publish_lag_days < 0:
        raise ValueError("publish_lag_days must be >= 0")
    out: list[dict[str, Any]] = []
    for _, r in daily.iterrows():
        day = pd.Timestamp(r["obs_day"]).to_pydatetime()
        if day.tzinfo is None:
            day = day.replace(tzinfo=timezone.utc)
        # end of observation day + lag
        flow_time = day + timedelta(days=1) - timedelta(seconds=1)
        flow_time = flow_time + timedelta(days=int(publish_lag_days))
        out.append(
            {
                "flow_time": flow_time,
                "net_flow": float(r["total_usd_m"]),
            }
        )
    return validate_flow_events(pd.DataFrame(out))


def ingest_farside_etf_flows(
    *,
    out_dir: Path | None = None,
    url: str = DEFAULT_URL,
    publish_lag_days: int = 1,
    series_id: str = SERIES_ID,
) -> dict[str, Any]:
    """Fetch Farside all-data table, write parquet under data/processed/etf/."""
    root = project_root()
    out_dir = out_dir or (root / "data" / "processed" / "etf")
    out_dir.mkdir(parents=True, exist_ok=True)
    html = fetch_farside_html(url)
    daily = parse_farside_daily_total(html)
    events = farside_to_flow_events(daily, publish_lag_days=publish_lag_days)
    path = out_dir / f"{series_id}.parquet"
    events.to_parquet(path, index=False)
    h = flow_events_content_hash(events)
    meta = {
        "series_id": series_id,
        "path": str(path),
        "n_events": int(len(events)),
        "content_hash": h,
        "publish_lag_days": publish_lag_days,
        "source_url": url,
        "attribution": ATTRIBUTION,
        "units": "US$m aggregate net flow into US spot BTC ETFs",
        "sign": "positive = net creations / inflows (not exchange deposits)",
        "first_flow_time": str(events["flow_time"].iloc[0]),
        "last_flow_time": str(events["flow_time"].iloc[-1]),
        "first_obs_day": str(daily["obs_day"].iloc[0].date()),
        "last_obs_day": str(daily["obs_day"].iloc[-1].date()),
        "pit_note": (
            "Fixed publish_lag_days applied to Farside public daily table; "
            "not vendor-grade revision-aware PIT."
        ),
        "mechanism": "ineff_etf_create_redeem",
        "eir": "docs/EVIDENCE_INVESTMENT_REVIEW_INEFFICIENCY_2026-07-30.md",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / f"{series_id}.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta
