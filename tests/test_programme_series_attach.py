"""Programme INDEX + series attach capability."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from crl.ops.lag_sensitivity import lag_sensitivity_grid, shift_event_times
from crl.ops.new_programme import scaffold_programme
from crl.ops.programme_index import load_programme_index
from crl.ops.research_queue_state import load_queue_state, record_programme_result, save_queue_state
from crl.ops.series_attach import list_local_series, series_readiness
from crl.shared.data.external_series import validate_external_events


def test_load_flow_index():
    idx = load_programme_index("examples/batch/flow")
    assert idx.external is not None
    assert idx.external.kind == "flow"
    assert idx.external.series_id.startswith("cmd_")


def test_series_readiness_missing():
    from crl.ops.programme_index import ExternalAttach

    r = series_readiness(
        ExternalAttach(kind="external", series_id="does_not_exist_xyz")
    )
    assert r["ready"] is False


def test_scaffold_programme(tmp_path: Path, monkeypatch):
    # scaffold writes under project examples/batch — use unique slug
    slug = "_test_scaffold_cap_v1"
    hyp = Path("examples/batch") / slug
    if hyp.exists():
        import shutil

        shutil.rmtree(hyp)
    design = f"docs/PROGRAMME_{slug.upper()}_V1.md"
    out = scaffold_programme(
        slug,
        design_rel=design,
        mechanism="test only",
        external_kind="external",
        series_id="future_series_v1",
        prefix="ts",
        placeholder_hyps=2,
    )
    assert Path(out["hyp_dir"]).exists() or (Path("examples/batch") / slug).exists()
    idx = load_programme_index(f"examples/batch/{slug}")
    assert idx.external is not None
    assert idx.external.series_id == "future_series_v1"
    # cleanup
    import shutil

    shutil.rmtree(Path("examples/batch") / slug)
    dp = Path(design)
    if dp.exists():
        dp.unlink()


def test_lag_sensitivity_grid():
    ev = validate_external_events(
        pd.DataFrame(
            {
                "event_time": pd.to_datetime(
                    ["2020-01-01", "2020-01-02"], utc=True
                ),
                "value": [1.0, 2.0],
            }
        )
    )

    def run_fn(events, lag):
        return {"n_passed_val": lag, "n_run": 1, "n_candidates": 0}

    rows = lag_sensitivity_grid(
        ev, time_col="event_time", lag_days_list=[0, 1, 2], run_fn=run_fn
    )
    assert [r["extra_lag_days"] for r in rows] == [0, 1, 2]
    shifted = shift_event_times(ev, 1, "event_time")
    assert shifted["event_time"].iloc[0] > ev["event_time"].iloc[0]


def test_queue_state_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "crl.ops.research_queue_state.state_path",
        lambda root=None: tmp_path / "q.json",
    )
    record_programme_result("demo", n_passed_val=1, n_run=5, n_candidates=0)
    st = load_queue_state()
    assert any(c["id"] == "demo" for c in st["completed"])
