"""Deliverability: ThermoGIS loader, Darcy reconciliation, Monte-Carlo MWth."""

import numpy as np

from src.constants import INJECTION_TEMP_C
from src.deliverability import (
    darcy_flow_m3h,
    delta_t_c,
    deliverability_table,
    thermal_power_mw,
)
from src.montecarlo import fit_lognormal, simulate_all, summarise
from src.thermogis import load_thermogis, thermogis_property


def test_thermogis_keys_off_sheet_not_header():
    """The BLT-01 sheet's value-column header is mislabelled 'PKP-01'; the loader
    must still attribute BLT-01's coordinates (x~141577) to BLT-01."""
    df = load_thermogis()
    blt = df[df["well"] == "BLT-01"].iloc[0]
    assert abs(blt["x"] - 141_577) < 5
    # Flow Rate is published as a real P-distribution for the anchor well.
    fr = thermogis_property(df, "BLT-01", "Flow Rate")
    assert fr["p90"] < fr["p50"] < fr["p10"]


def test_thermal_power_identity():
    # 100 m^3/h at dT=42 C: rho*cp*Q*dT / 1e6.
    p = thermal_power_mw(100.0, 42.0)
    assert abs(p - (1000 * 4180 * (100 / 3600) * 42 / 1e6)) < 1e-9


def test_injection_temp_recovers_thermogis_dt():
    # ThermoGIS BLT-01 (T=77) implies dT = 42 at the 35 C injection temp.
    assert delta_t_c(77.0, INJECTION_TEMP_C) == 42.0


def test_darcy_reconciles_thermogis_p50_flow():
    """Calibrated Darcy model reproduces ThermoGIS Flow P50 to within 3%
    (BLT-01 ~0.8%, JUT-01 ~2.2% — the single 16.5 bar drawdown splits the two
    wells' slightly different ThermoGIS-implied drawdowns)."""
    d = deliverability_table().set_index("well")
    for w in ("BLT-01", "JUT-01"):
        model, tg = d.loc[w, "flow_model_p50"], d.loc[w, "flow_tg_p50"]
        assert abs(model - tg) / tg < 0.03


def test_fit_lognormal_recovers_median():
    mu, sigma = fit_lognormal(1.3, 9.3, 66.1)
    assert abs(np.exp(mu) - 9.3) < 1e-9
    assert sigma > 0


def test_mc_blt_p50_is_about_5MWth_single_doublet():
    """Headline finding: a single BLT-01 doublet is ~5 MWth at P50 (below the
    10 MWth heating demand); two doublets reach ~10 MWth."""
    mc = simulate_all(n=5_000, anchor="flow")
    blt = mc[mc["well"] == "BLT-01"]
    s1 = summarise(blt, 10.0, n_doublets=1).iloc[0]
    s2 = summarise(blt, 10.0, n_doublets=2).iloc[0]
    assert 4.0 < s1["mwth_p50"] < 6.5
    assert s1["p_ge_10MWth"] < 0.5
    assert s2["mwth_p50"] >= 9.5


def test_mc_uneconomic_wells_are_zero():
    """EVD-01 and PKP-01 carry ThermoGIS Flow = 0 -> ~0 MWth."""
    mc = simulate_all(n=2_000, anchor="flow")
    for w in ("EVD-01", "PKP-01"):
        assert mc[mc["well"] == w]["mwth"].max() == 0.0
