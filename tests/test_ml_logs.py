"""Bonus AI track: missing-log prediction + leave-one-well-out validation.

These lock the *framework* (which wells donate, which receive, that the fallback
verdict is derived from a genuine cross-well score and is deterministic) rather
than a brittle exact-R^2 number.  A small estimator count keeps the suite fast.
"""

import warnings

import numpy as np
import pytest

from src import ml_logs
from src.ml_logs import (
    DONOR_MIN_COVERAGE,
    TARGET_CURVES,
    curve_coverage,
    loo_cv,
    run_all,
    select_features,
)
from src.petrophysics import add_petrophysics
from src.wells_io import load_all

warnings.filterwarnings("ignore")

_FAST = {"n_estimators": 60}  # keep LightGBM quick in the test suite


@pytest.fixture(scope="module")
def logs():
    return add_petrophysics(load_all())


def test_coverage_matches_known_gaps(logs):
    cov = curve_coverage(logs)
    # NPHI is fully on BLT-01, entirely absent on EVD-01 and JUT-01.
    assert cov.loc["BLT-01", "NPHI"] > 0.9
    assert cov.loc["EVD-01", "NPHI"] == 0.0
    assert cov.loc["JUT-01", "NPHI"] == 0.0
    # GR is everywhere; it must always be an eligible predictor.
    assert (cov["GR"] > 0.9).all()


def test_features_exclude_target_and_sparse_curves(logs):
    cov = curve_coverage(logs)
    feats = select_features(cov, "NPHI", list(cov.index))
    assert "NPHI" not in feats              # never predict a curve from itself
    assert "tvd_m" in feats                 # depth is always available
    assert "RHOB" not in feats              # too sparse on EVD-01 to be portable
    assert "GR" in feats and "DTC" in feats


def test_loo_cv_is_genuinely_cross_well(logs):
    """Each fold must train and test on *disjoint* wells (no leakage)."""
    res = loo_cv(logs, "DTC", params=_FAST)
    assert res["n_test_total"] > 0
    for _, row in res["folds"].iterrows():
        assert row["held_out_well"] not in row["train_wells"].split("+")
    assert np.isfinite(res["cross_well_r2"])


def test_nphi_falls_back_to_thermogis(logs):
    """NPHI does not generalise across these few, distinct wells -> fallback.

    The honest result is the point: a negative/low cross-well R^2 must trip the
    ThermoGIS fallback rather than be trusted downstream."""
    res = loo_cv(logs, "NPHI", params=_FAST)
    assert set(res["recipients"]) >= {"EVD-01", "JUT-01"}
    assert res["cross_well_r2"] < ml_logs.R2_FALLBACK_THRESHOLD
    assert res["use_ml"] is False


def test_run_all_summary_and_predictions(logs):
    out = run_all(logs, params=_FAST)
    assert set(out["summary"]["target"]) == set(TARGET_CURVES)
    assert out["summary"]["decision"].isin(["ML", "ThermoGIS fallback"]).all()

    preds = out["predictions"]
    assert not preds.empty
    assert set(preds["curve"]).issubset(set(TARGET_CURVES))
    assert preds["value_pred"].notna().all()
    # NPHI is filled only on the wells that lacked it.
    nphi_wells = set(preds.loc[preds["curve"] == "NPHI", "well"])
    assert nphi_wells == {"EVD-01", "JUT-01"}


def test_donor_threshold_keeps_partial_nphi_donor(logs):
    """PKP-01's partial (~33%) NPHI must still count as a second donor, else NPHI
    could not be cross-validated at all."""
    cov = curve_coverage(logs)
    assert 0.25 <= cov.loc["PKP-01", "NPHI"] < 0.5
    assert cov.loc["PKP-01", "NPHI"] >= DONOR_MIN_COVERAGE


def test_deterministic(logs):
    a = loo_cv(logs, "DTC", params=_FAST)["cross_well_r2"]
    b = loo_cv(logs, "DTC", params=_FAST)["cross_well_r2"]
    assert a == b


def test_holdout_prediction_shapes_and_guard(logs):
    ho = ml_logs.holdout_prediction(logs, "DTC", "PKP-01", params=_FAST)
    assert ho["held_out_well"] == "PKP-01"
    assert len(ho["y_true"]) == len(ho["y_pred"]) == len(ho["tvd_m"]) > 0
    assert np.isfinite(ho["r2"])
    # A well that is not a donor for the target must be rejected, not silently fit.
    with pytest.raises(ValueError):
        ml_logs.holdout_prediction(logs, "NPHI", "EVD-01", params=_FAST)
