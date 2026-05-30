"""Petrophysics transforms and the Rotliegend net summary."""

import numpy as np

from src.lithostrat import rotliegend_pick
from src.petrophysics import (
    add_petrophysics,
    density_porosity,
    rotliegend_summary,
    vshale_larionov_older,
)
from src.wells_io import load_all


def test_vshale_endpoints():
    # Clean sand (IGR=0) -> 0. At IGR=1 the Larionov-older transform yields
    # 0.33*(2^2 - 1) = 0.99, not exactly 1 (a property of the transform).
    assert vshale_larionov_older(40.0, 40.0, 140.0) == 0.0
    assert vshale_larionov_older(140.0, 40.0, 140.0) == np.float64(0.99)
    # Larionov-older sits below the linear index for intermediate GR.
    mid = vshale_larionov_older(90.0, 40.0, 140.0)  # IGR = 0.5
    assert 0.0 < mid < 0.5


def test_density_porosity_known():
    # rhob = matrix -> 0 porosity; rhob = fluid -> 1.
    assert density_porosity(2.65) == 0.0
    assert density_porosity(1.0) == 1.0
    assert density_porosity(2.30) == np.float64((2.65 - 2.30) / (2.65 - 1.0))


def test_blt01_rotliegend_is_strong():
    """BLT-01 is the anchor: high NTG, porosity near the ThermoGIS 17%."""
    logs = add_petrophysics(load_all())
    s = rotliegend_summary(logs, rotliegend_pick("BLT-01"))
    assert s["ntg"] > 0.8
    assert 0.12 < s["phi_mean_net"] < 0.20
    assert s["n_samples"] > 1500


def test_pkp01_is_tight():
    """PKP-01 must come out poor (ThermoGIS k P50 = 1 mD)."""
    logs = add_petrophysics(load_all())
    s = rotliegend_summary(logs, rotliegend_pick("PKP-01"))
    assert s["ntg"] < 0.25
