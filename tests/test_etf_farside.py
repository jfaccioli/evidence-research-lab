"""Farside US spot BTC ETF flow free-path pin (no network in unit tests)."""

from __future__ import annotations

from crl.shared.data.sources.etf_farside import (
    farside_to_flow_events,
    parse_farside_daily_total,
)


SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Date</th><th>IBIT</th><th>FBTC</th><th>Total</th></tr>
<tr><td>11 Jan 2024</td><td>100.0</td><td>50.0</td><td>150.0</td></tr>
<tr><td>12 Jan 2024</td><td>(10.0)</td><td>5.0</td><td>(5.0)</td></tr>
<tr><td>Total</td><td>90.0</td><td>55.0</td><td>145.0</td></tr>
</table>
</body></html>
"""


def test_parse_and_lag():
    daily = parse_farside_daily_total(SAMPLE_HTML)
    assert len(daily) == 2
    assert float(daily.iloc[0]["total_usd_m"]) == 150.0
    assert float(daily.iloc[1]["total_usd_m"]) == -5.0
    events = farside_to_flow_events(daily, publish_lag_days=1)
    assert len(events) == 2
    assert events.iloc[0]["net_flow"] == 150.0
    # obs 11 Jan → end of 11th + 1 day lag → 12 Jan 23:59:59
    assert events.iloc[0]["flow_time"].day == 12
