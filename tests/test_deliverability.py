"""Deliverability: ThermoGIS loader, Darcy reconciliation, Monte-Carlo MWth."""

import numpy as np

from src.constants import INJECTION_TEMP_C
from src.deliverability import (
    darcy_flow_m3h,
    delta_t_c,
    deliverability_table,
    thermal_power_mw,
)
from src.montecarlo import (
    ates_cooling_adequacy,
    fit_lognormal,
    simulate_all,
    summarise,
)
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


def test_split_lognormal_reproduces_thermogis_band_exactly():
    """Unlike the single-sigma fit, the split fit must hit BOTH published tails:
    the sampled P90 and P10 reproduce ThermoGIS's flow band, not just the average
    spread. BLT-01 flow 17/105/469: the old fit overshot P10 to ~551."""
    from src.montecarlo import _sample_split_lognormal, fit_split_lognormal
    mu, s_lo, s_hi = fit_split_lognormal(17.0, 105.0, 469.0)
    rng = np.random.default_rng(0)
    draws = _sample_split_lognormal(rng, mu, s_lo, s_hi, 200_000)
    assert abs(np.percentile(draws, 50) - 105.0) / 105.0 < 0.02
    assert abs(np.percentile(draws, 10) - 17.0) / 17.0 < 0.05   # P90 low
    assert abs(np.percentile(draws, 90) - 469.0) / 469.0 < 0.05  # P10 high (was ~551)


def test_flow_cap_bounds_the_optimistic_tail_not_the_median():
    """The pump/sand-control ceiling de-rates only the upper tail: no realisation
    exceeds the cap, the capped optimistic P10 is well below the uncapped one, and
    the P50 headline is untouched."""
    capped = simulate_all(n=20_000, anchor="flow")               # default cap 300
    uncapped = simulate_all(n=20_000, anchor="flow", q_max_m3h=None)
    blt_c = capped[capped["well"] == "BLT-01"]
    blt_u = uncapped[uncapped["well"] == "BLT-01"]
    assert blt_c["flow_m3h"].max() <= 300.0 + 1e-9
    s_c = summarise(blt_c, 10.0, n_doublets=1).iloc[0]
    s_u = summarise(blt_u, 10.0, n_doublets=1).iloc[0]
    assert s_c["mwth_p10"] < s_u["mwth_p10"] - 3.0          # tail pulled in materially
    assert abs(s_c["mwth_p50"] - s_u["mwth_p50"]) < 0.1     # median untouched


def test_mc_blt_p50_is_about_5MWth_single_doublet():
    """Headline finding: a single BLT-01 doublet is ~5 MWth at P50 (below the
    10 MWth heating demand) with only a ~31% chance of clearing it alone."""
    mc = simulate_all(n=10_000, anchor="flow")
    blt = mc[mc["well"] == "BLT-01"]
    s1 = summarise(blt, 10.0, n_doublets=1).iloc[0]
    assert 4.0 < s1["mwth_p50"] < 6.5
    assert 0.25 < s1["p_ge_10MWth"] < 0.40


def test_mc_two_doublets_are_independent_not_rescaled():
    """Two doublets are modelled as a sum of INDEPENDENT realisations, not one
    draw rescaled by 2. The independent scheme reaches ~14 MWth P50 with a ~64%
    chance of clearing 10 MWth; perfect-correlation rescaling would force exactly
    2x the single P50 (~10.1) and P(>=10)~=P(single>=5)~=0.50. This guards against
    the correlation artifact silently returning."""
    mc = simulate_all(n=10_000, anchor="flow")
    blt = mc[mc["well"] == "BLT-01"]
    s1 = summarise(blt, 10.0, n_doublets=1).iloc[0]
    s2 = summarise(blt, 10.0, n_doublets=2).iloc[0]
    # Summing independents reduces skew: the scheme P50 rises FASTER than 2x.
    assert s2["mwth_p50"] > 2.0 * s1["mwth_p50"] + 1.0   # i.e. clearly > 10.1
    assert 12.5 < s2["mwth_p50"] < 16.0
    assert s2["p_ge_10MWth"] > 0.55


def test_mc_uneconomic_wells_are_zero():
    """EVD-01 and PKP-01 carry ThermoGIS Flow = 0 -> ~0 MWth."""
    mc = simulate_all(n=2_000, anchor="flow")
    for w in ("EVD-01", "PKP-01"):
        assert mc[mc["well"] == w]["mwth"].max() == 0.0


def test_ates_cooling_clears_demand_at_six_pairs_not_four():
    """Cooling adequacy is probabilised over the 0.5-2.0 MWth/pair ATES range.
    Four pairs (the old midpoint-sized design) fail the 5 MWth demand most of the
    time at conservative throughput; six pairs clear it with high confidence."""
    four = ates_cooling_adequacy(n_pairs=4)
    six = ates_cooling_adequacy(n_pairs=6)
    assert four["p_meets_demand"] < 0.5            # under-sized at the low end
    assert six["p_meets_demand"] > 0.95            # robust
    assert six["supply_p90"] >= 5.0                # even the conservative P90 clears
