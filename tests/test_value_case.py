"""Value case: CO2 abatement, SDE++ subsidy, and project NPV/IRR."""

from src.lcoe import heat_economics
from src.surface import SchemeConfig
from src.value_case import (
    co2_abated_t_per_yr,
    project_npv_irr,
    sde_plus,
    value_summary,
)


def test_co2_abatement_nets_grid_power_against_displaced_gas():
    c = co2_abated_t_per_yr(heat_gj=218_592, elec_mwh=2_249)
    assert c["displaced_gas_t"] > c["net_abated_t"] > 0      # power consumption nets off
    assert 10_000 < c["net_abated_t"] < 16_000               # ~13 kt/yr for this scheme


def test_sde_pays_only_the_gap_and_caps_at_zero():
    """SDE++ pays base minus correction while positive; a high gas price -> no subsidy."""
    low_gas = sde_plus(11.66, 8.0, 218_592)
    high_gas = sde_plus(11.66, 15.0, 218_592)
    assert abs(low_gas["subsidy_eur_gj"] - 3.66) < 0.01
    assert high_gas["subsidy_eur_gj"] == 0.0                 # market beats cost -> unsubsidised


def test_irr_equals_hurdle_when_tariff_equals_lcoe():
    """Internal consistency: a flat tariff equal to the LCOE (no subsidy) returns the
    required equity return exactly — the value model is the LCOE model, extended."""
    cfg = SchemeConfig()
    econ = heat_economics(cfg.heat_case(), heat_mwth=cfg.heat_delivered_mwth)
    r = project_npv_irr(econ, tariff_eur_gj=econ["lcoe_eur_gj"], subsidy_eur_gj=0.0)
    assert abs(r["equity_irr"] - 0.15) < 1e-3
    assert abs(r["equity_npv_eur"]) < 1.0


def test_sde_makes_the_project_clear_the_hurdle():
    """At a realistic gas-linked tariff the unsubsidised project is under water, and
    the SDE++ top-up lifts the equity IRR above the 15 % hurdle."""
    v = value_summary(market_ref_eur_gj=8.0, tariff_eur_gj=9.0)
    assert v["equity_npv_no_sde_meur"] < 0.0
    assert v["equity_irr_with_sde"] > 0.15


def test_abatement_cost_is_auction_competitive():
    """The SDE++ ranking metric (EUR per tonne CO2) should be in the fundable range
    for geothermal heat (well under the ~300 EUR/t SDE++ ceiling)."""
    v = value_summary(market_ref_eur_gj=8.0)
    assert 0 < v["sde_abatement_cost_eur_t"] < 150
