"""LEDA evidence channels (numeric, PIT, versioned)."""

from crl.leda.channels.trend import (
    CHANNEL_ID as TREND_CHANNEL_ID,
    CHANNEL_VERSION as TREND_CHANNEL_VERSION,
    build_trend_evidence,
    evaluate_trend_forecast_skill,
)
from crl.leda.channels.vol_risk import (
    CHANNEL_ID as VOL_RISK_CHANNEL_ID,
    CHANNEL_VERSION as VOL_RISK_CHANNEL_VERSION,
    build_vol_risk_evidence,
    evaluate_vol_forecast_skill,
)
from crl.leda.channels.xasset import (
    CHANNEL_ID as XASSET_CHANNEL_ID,
    CHANNEL_VERSION as XASSET_CHANNEL_VERSION,
    build_xasset_evidence,
    evaluate_xasset_forecast_skill,
)

__all__ = [
    "TREND_CHANNEL_ID",
    "TREND_CHANNEL_VERSION",
    "VOL_RISK_CHANNEL_ID",
    "VOL_RISK_CHANNEL_VERSION",
    "XASSET_CHANNEL_ID",
    "XASSET_CHANNEL_VERSION",
    "build_trend_evidence",
    "build_vol_risk_evidence",
    "build_xasset_evidence",
    "evaluate_trend_forecast_skill",
    "evaluate_vol_forecast_skill",
    "evaluate_xasset_forecast_skill",
]
