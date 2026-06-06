"""LCOE: TNO reference reproduction, hybrid heat/cool economics, design choice."""

from src.lcoe import (
    REFERENCE_LCOE_EUR_GJ,
    HeatCase,
    heat_economics,
    validate_reference,
    well_cost_mln,
)
from src.surface import SchemeConfig, size_design_a, size_design_b
from src.tornado import tornado_data


def test_reproduces_tno_heat_reference():
    """The validation gate: our financed-LCOE engine must reproduce the stock
    TNO workbook's heat case (5.769 EUR/GJ) to within 0.001."""
    assert abs(validate_reference() - REFERENCE_LCOE_EUR_GJ) < 1e-3


def test_well_cost_polynomial_matches_workbook():
    # TNO: 1.5 * (0.2*1800^2 + 700*1800 + 250000) * 1e-6 = 3.237 mln EUR/well.
    assert abs(well_cost_mln(1800.0, 1.5) - 3.237) < 1e-3


def test_default_heatcase_is_the_reference():
    assert abs(heat_economics(HeatCase())["lcoe_eur_gj"] - REFERENCE_LCOE_EUR_GJ) < 1e-3


def test_our_scheme_costs_more_than_tno_reference():
    """Cooler (77 C), less productive reservoir + a 4-well 2-doublet scheme ->
    heat LCOE materially above the 93.7 C TNO benchmark. This is the honest
    finding, so guard it rather than massage it away."""
    cfg = SchemeConfig()
    heat = heat_economics(cfg.heat_case(), heat_mwth=cfg.heat_delivered_mwth)
    assert heat["lcoe_eur_gj"] > REFERENCE_LCOE_EUR_GJ
    assert 8.0 < heat["lcoe_eur_gj"] < 16.0
    assert heat["subsurface_capex_mln"] > 12.0  # four wells


def test_design_a_beats_b_on_cooling_and_diverts_no_heat():
    """Recommendation guard: Design A has lower cooling LCOE and consumes no
    geothermal heat for cooling; Design B diverts ~7 MWth to a chiller."""
    cfg = SchemeConfig()
    a, b = size_design_a(cfg), size_design_b(cfg)
    assert a["lcoe_cool_eur_gj"] < b["lcoe_cool_eur_gj"]
    assert a["geo_heat_consumed_for_cooling_mwth"] == 0.0
    assert b["geo_heat_consumed_for_cooling_mwth"] > 6.0


def test_flat_profile_reproduces_scalar_and_reference():
    """The time-varying-energy path must be a faithful generalisation: a flat MWth
    profile equal to nameplate reproduces both the scalar result and, on the TNO
    reference case, the 5.769 gate."""
    import numpy as np
    ref = HeatCase()  # TNO reference
    mw = heat_economics(ref)["heat_mwth"]
    flat = heat_economics(ref, heat_mwth=mw, mwth_profile=np.full(40, mw))
    assert abs(flat["lcoe_eur_gj"] - REFERENCE_LCOE_EUR_GJ) < 1e-3


def test_longer_economic_life_lowers_lcoe():
    """The asset outlives the 15-yr loan; running it to 30 yr (loan unchanged)
    lowers LCOE because energy keeps being delivered against sunk wells."""
    cfg = SchemeConfig()
    l15 = heat_economics(cfg.heat_case(), heat_mwth=cfg.heat_delivered_mwth, lifetime_yr=15)
    l30 = heat_economics(cfg.heat_case(), heat_mwth=cfg.heat_delivered_mwth, lifetime_yr=30)
    assert l30["lcoe_eur_gj"] < l15["lcoe_eur_gj"]
    assert l15["lcoe_eur_gj"] - l30["lcoe_eur_gj"] > 0.5


def test_blended_lcoe_is_heat_dominated():
    """The widest tornado spread should be a heat-side driver, not a cooling one
    (the system is heat-dominated)."""
    td = tornado_data()
    top = td.sort_values("spread").iloc[-1]["driver"]
    assert top in {"Heat delivered (MWth)", "Heat load hours", "Drilling cost scaling"}
