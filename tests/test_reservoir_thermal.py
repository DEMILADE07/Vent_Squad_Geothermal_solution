"""Doublet thermal breakthrough (Gringarten-Sauty) and produced-temperature decline."""

import numpy as np

from src.reservoir_thermal import (
    breakthrough_time_yr,
    decline_summary,
    mwth_profile,
    produced_temperature_profile,
)


def test_breakthrough_scales_with_geometry_and_flow():
    """t_bt ~ L^2 / Q: doubling spacing quadruples it; doubling flow halves it."""
    base = breakthrough_time_yr(105.0, 114.0, 0.17, spacing_m=1000.0)
    assert abs(breakthrough_time_yr(105.0, 114.0, 0.17, spacing_m=2000.0) / base - 4.0) < 1e-6
    assert abs(breakthrough_time_yr(210.0, 114.0, 0.17, spacing_m=1000.0) / base - 0.5) < 1e-6


def test_base_design_is_breakthrough_safe():
    """The recommended 1.3 km doublet breaks through well beyond a 30-yr life, so
    the produced temperature — and MWth — is flat across the economic life."""
    ds = decline_summary(105.0, 114.0, 0.17, 77.0, lifetime_yr=30, spacing_m=1300.0)
    assert ds["breakthrough_yr"] > 100.0
    assert ds["breakthrough_within_life"] is False
    assert ds["temp_decline_c"] == 0.0
    assert abs(ds["energy_retention"] - 1.0) < 1e-9


def test_tight_spacing_brings_breakthrough_into_life_and_declines():
    """At an impractically tight spacing the front arrives within life and the
    produced temperature declines — the model responds in the right direction."""
    t_bt = breakthrough_time_yr(105.0, 114.0, 0.17, spacing_m=400.0)
    assert t_bt < 30.0
    years = np.arange(1, 31)
    t_prod = produced_temperature_profile(years, 77.0, t_bt, t_inj_c=35.0)
    assert t_prod[0] == 77.0                 # pre-breakthrough: full reservoir T
    assert t_prod[-1] < 77.0                 # post-breakthrough: cooled
    assert t_prod[-1] >= 35.0                # never below injection T


def test_mwth_profile_is_nonincreasing():
    years = np.arange(1, 41)
    mw = mwth_profile(years, 105.0, 114.0, 0.17, 77.0, spacing_m=500.0)
    assert np.all(np.diff(mw) <= 1e-9)
    assert mw[0] > mw[-1]
