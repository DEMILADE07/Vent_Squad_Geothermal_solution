"""Probabilistic LCOE: resource + cost uncertainty propagated to an LCOE distribution."""

import numpy as np

from src.lcoe import heat_economics
from src.lcoe_montecarlo import (
    lcoe_scenarios_by_hurdle,
    simulate_lcoe,
    summarise_lcoe,
)
from src.surface import SchemeConfig


def test_median_tracks_the_deterministic_point_estimate():
    """The probabilistic P50 heat LCOE should land near the deterministic value
    computed at the P50 resource and base-case costs — the MC generalises, not
    contradicts, the point estimate."""
    cfg = SchemeConfig()
    det = heat_economics(cfg.heat_case(), heat_mwth=cfg.heat_mwth_p50)["lcoe_eur_gj"]
    df = simulate_lcoe(n=6_000, seed=1)
    p50 = float(np.percentile(df["lcoe_heat"], 50))
    assert abs(p50 - det) / det < 0.15


def test_distribution_is_ordered_and_right_skewed():
    """P10 < P50 < P90, and the resource downside makes the upper tail heavy
    (mean above median) — the cost of the resource under-delivering."""
    df = simulate_lcoe(n=6_000, seed=2)
    s = summarise_lcoe(df).set_index("metric").loc["lcoe_heat"]
    assert s["p10_low"] < s["p50"] < s["p90_high"]
    assert s["mean"] > s["p50"]                     # right-skewed by resource risk


def test_cooling_lcoe_is_tighter_than_heat():
    """Cooling carries far less resource risk, so its LCOE spread is much narrower
    than heat's — consistent with the heat-dominated tornado."""
    df = simulate_lcoe(n=6_000, seed=3)
    s = summarise_lcoe(df).set_index("metric")
    heat_spread = s.loc["lcoe_heat", "p90_high"] - s.loc["lcoe_heat", "p10_low"]
    cool_spread = s.loc["lcoe_cool", "p90_high"] - s.loc["lcoe_cool", "p10_low"]
    assert cool_spread < heat_spread


def test_higher_hurdle_rate_raises_lcoe():
    sc = lcoe_scenarios_by_hurdle(n=3_000).set_index("equity_return")
    assert sc.loc[0.10, "lcoe_heat_p50"] < sc.loc[0.20, "lcoe_heat_p50"]


def test_longer_life_shifts_distribution_down():
    p50_15 = float(np.percentile(simulate_lcoe(n=4_000, seed=4)["lcoe_heat"], 50))
    p50_30 = float(np.percentile(
        simulate_lcoe(n=4_000, seed=4, lifetime_yr=30)["lcoe_heat"], 50))
    assert p50_30 < p50_15


def test_reproducible_under_seed():
    a = simulate_lcoe(n=2_000, seed=7)["lcoe_heat"].to_numpy()
    b = simulate_lcoe(n=2_000, seed=7)["lcoe_heat"].to_numpy()
    assert np.allclose(a, b)
