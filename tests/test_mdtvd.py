"""Minimum-curvature MD->TVD: must reproduce the workbook's supplied TVD."""

import numpy as np
import pytest

from src.mdtvd import load_survey, md_to_tvd, minimum_curvature, validate_survey

WELLS = ["BLT-01", "EVD-01", "JUT-01", "PKP-01"]


@pytest.mark.parametrize("well", WELLS)
def test_mc_tvd_matches_workbook(well):
    """Recomputed station TVD must agree with the provided column to <1 m."""
    s = load_survey(well)
    mc = minimum_curvature(s.md, s.incl_deg, s.azi_deg)
    assert np.nanmax(np.abs(mc["tvd"] - s.tvd_provided)) < 1.0


@pytest.mark.parametrize("well", WELLS)
def test_md_to_tvd_hits_stations(well):
    """At survey stations the interpolant returns the station TVD exactly."""
    s = load_survey(well)
    np.testing.assert_allclose(md_to_tvd(well, s.md), s.tvd_provided, atol=1.0)


def test_tvd_never_exceeds_md():
    """TVD <= MD always (vertical projection of an along-hole length)."""
    for well in WELLS:
        s = load_survey(well)
        assert np.all(md_to_tvd(well, s.md) <= s.md + 1e-6)


def test_extrapolation_beyond_last_station_is_monotonic():
    s = load_survey("BLT-01")
    past = s.md[-1] + np.array([1.0, 50.0, 100.0])
    tvd = md_to_tvd("BLT-01", past)
    assert np.all(np.diff(tvd) > 0)
    assert tvd[0] > md_to_tvd("BLT-01", s.md[-1:])[0]


def test_validate_survey_report_keys():
    rep = validate_survey("BLT-01")
    assert rep["max_abs_resid_m"] < 1.0
    assert rep["n_stations"] == 102
