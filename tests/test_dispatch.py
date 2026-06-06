"""8760-h dispatch: temperature year, demand profiles, derived load-hours, sizing."""

import numpy as np

from src.dispatch import (
    DispatchConfig,
    demand_profiles,
    dispatch_cooling,
    lcoe_at_simulated_loadhours,
    nl_hourly_temperature,
    simulate_dispatch,
    sizing_table,
)


def test_temperature_year_is_realistic_nl():
    t = nl_hourly_temperature(seed=0)
    assert len(t) == 8760
    assert 8.0 < t.mean() < 12.0           # NL annual mean ~10 C
    assert t.min() < -3.0                   # winter design lows
    assert t.max() > 25.0                   # summer peaks
    # reproducible
    assert np.allclose(t, nl_hourly_temperature(seed=0))


def test_demand_peaks_match_design():
    d = demand_profiles(DispatchConfig())
    assert abs(d["heat_mwth"].max() - 10.0) < 1e-6
    assert abs(d["cool_mwth"].max() - 5.0) < 1e-6
    assert d["heat_mwth"].min() >= 1.5 - 1e-9   # DHW baseload floor


def test_peak_sized_geothermal_is_underutilised():
    """The honest finding: geothermal sized to the full 10 MWth peak runs far below
    the assumed 6000 FLEQ — heating demand is too peaky to baseload it at peak."""
    s = simulate_dispatch(DispatchConfig(geo_capacity_mwth=10.12))
    assert s["geo_coverage"] > 0.99             # covers ~all energy...
    assert s["geo_fleq_h"] < 4000               # ...but utilisation is poor


def test_baseload_sizing_recovers_the_assumed_loadhours():
    """Sizing geothermal down toward baseload (~1 doublet) lifts FLEQ to ~6000 and
    still covers the bulk of annual heat; the heat pump picks up the peak."""
    st = sizing_table(capacities=(5.05, 10.12)).set_index("geo_capacity_mwth")
    assert st.loc[5.05, "geo_fleq_h"] > 5000
    assert st.loc[5.05, "geo_coverage_pct"] > 85.0
    assert st.loc[5.05, "geo_fleq_h"] > st.loc[10.12, "geo_fleq_h"]   # monotone


def test_ates_pair_count_is_validated_by_peak_cooling():
    c = dispatch_cooling(demand_profiles(DispatchConfig())["cool_mwth"], DispatchConfig())
    assert c["ates_pairs"] == 4                  # ceil(5 / 1.5)
    assert c["ates_supply_fraction"] > 0.9       # ATES covers the modest cooling energy


def test_simulated_loadhours_raise_lcoe_vs_assumed():
    r = lcoe_at_simulated_loadhours()
    assert r["fleq_simulated_h"] < r["fleq_assumed_h"]
    assert r["lcoe_heat_simulated"] > r["lcoe_heat_assumed"]
