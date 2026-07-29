"""LEDA-0 protocol helpers: validate evidence series and layer claims."""

from __future__ import annotations

from typing import Any, Sequence

import pandas as pd

from crl.leda.types import LAYER_CONTRACTS, EvidenceRecord, EvidenceSink, LayerName


def validate_evidence_frame(
    df: pd.DataFrame,
    *,
    channel_id: str,
    version: int,
    sink: EvidenceSink,
) -> None:
    """Require columns for a channel time series of scores."""
    need = {"asof_time", "score", "inputs_hash"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"{channel_id}: missing columns {missing}")
    if df["score"].isna().any():
        raise ValueError(f"{channel_id}: score contains NaN (fail closed)")
    if ((df["score"] < 0) | (df["score"] > 1)).any():
        raise ValueError(f"{channel_id}: score outside [0,1]")
    # Touch contract fields for documentation completeness
    _ = (channel_id, version, sink)


def records_from_frame(
    df: pd.DataFrame,
    *,
    channel_id: str,
    version: int,
    sink: EvidenceSink,
) -> list[EvidenceRecord]:
    validate_evidence_frame(df, channel_id=channel_id, version=version, sink=sink)
    out: list[EvidenceRecord] = []
    for _, row in df.iterrows():
        meta = row["meta"] if "meta" in df.columns and isinstance(row.get("meta"), dict) else {}
        out.append(
            EvidenceRecord(
                channel_id=channel_id,
                version=version,
                sink=sink,
                asof_time=str(row["asof_time"]),
                score=float(row["score"]),
                inputs_hash=str(row["inputs_hash"]),
                meta=meta or {},
            )
        )
    return out


def layer_contract(layer: LayerName) -> dict[str, Any]:
    return dict(LAYER_CONTRACTS[layer])


def protocol_summary() -> dict[str, Any]:
    return {
        "architecture": "LEDA",
        "layers": {L.value: layer_contract(L) for L in LayerName},
        "evidence_score_scale": "[0,1] per channel design doc",
        "promotion": "Full stack under frozen economic gates only",
        "forbidden": [
            "Free-text LLM votes as promotion evidence",
            "Same-bar look-ahead in any channel",
            "Fitting portfolio map on confirmatory test",
        ],
    }
