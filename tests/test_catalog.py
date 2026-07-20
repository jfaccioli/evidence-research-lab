from crl.research.hypotheses.catalog import CATALOG, catalog_count, write_catalog
from crl.research.hypotheses.rules import eval_rule
from crl.shared.types import Taxonomy


def test_catalog_size_phase2_wave():
    n = catalog_count()
    # Wave 1–3; grow via families not framework churn
    assert 90 <= n <= 250


def test_catalog_ids_unique():
    slugs = [c["slug"] for c in CATALOG]
    assert len(slugs) == len(set(slugs))


def test_catalog_taxonomies_valid(tmp_path):
    for c in CATALOG:
        Taxonomy(c["taxonomy"])  # raises if invalid
        # rules parse
        row = {
            "close": 1, "sma_200": 0.5, "ret_20": 0.1, "ret_30": 0.1, "ret_90": 0.1,
            "rvol_below_median": 1, "rvol_above_median": 0,
            "sma_50": 1, "sma_20": 1, "sma_100": 1,
            "ema_200": 1, "ema_50": 1, "ema_20": 1, "ema_100": 1,
            "dist_sma_20": -0.1, "dist_sma_50": -0.1,
            "price_z_20": -2, "price_z_60": -2,
            "atr_pct": 0.02, "rvol_20_chg": -0.1, "rvol_20": 0.5,
            "vol_z_20": 1, "vol_z_60": 1, "vol_ratio_20": 1.2,
            "ret_5": 0.01, "ret_10": 0.01, "ret_60": 0.01,
            "is_weekend": 0, "is_monday": 0, "is_friday": 0,
            "is_month_start": 0, "is_month_end": 0, "mom_pos_20": 1,
            "above_donch_20": 1, "below_donch_20": 0,
            "above_donch_55": 1, "below_donch_55": 0,
            "above_donch_100": 1, "below_donch_100": 0,
            "above_atr_trail": 1, "mom_accel_20_60": 0.1, "mom_accel_10_30": 0.1,
        }
        eval_rule(c["entry"], row)
        eval_rule(c["exit"], row)
    paths = write_catalog(tmp_path)
    assert len(paths) == catalog_count()
