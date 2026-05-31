"""Surface-system sizing — Challenge 2.

Two designs supply the same district demand (>=10 MWth heating, >=5 MWth
cooling) from the same 2-doublet Rotliegend heat source, and differ only in how
they make cold:

  Design A (recommended)  geothermal doublets -> plate HX -> district hot loop;
                          cooling from seasonal ATES (cold banked in winter) with
                          an electric heat pump trimming the summer peak.

  Design B (contrast)     same heat source, but cooling from a LiBr/H2O
                          absorption chiller driven by geothermal heat.

The point of carrying both is to make the recommendation auditable.  Design B's
absorption chiller needs ~7 MWth of driving heat to make 5 MWth of cold — heat
that Design A keeps for sale.  On a reservoir whose heat LCOE is already ~2x the
Dutch benchmark, spending heat to make cold is the wrong trade, and the cost
comparison shows it rather than asserting it.

Heat MWth is taken from the Monte-Carlo P50 deliverability of the chosen scheme
(see src/montecarlo.py), not a nominal flow rate, so the economics inherit the
ThermoGIS-reconciled resource uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.constants import DEMAND_COOLING_MWTH, DEMAND_HEATING_MWTH
from src.lcoe import (
    AbsorptionCoolingCase,
    CoolingCase,
    HeatCase,
    cooling_economics,
    cooling_economics_absorption,
    heat_economics,
)


@dataclass(frozen=True)
class SchemeConfig:
    """The shared 2-doublet heat source and demand both designs are sized to."""
    n_doublets: int = 2
    wells_per_doublet: int = 2
    ah_depth_m: float = 2000.0          # deviated NL Rotliegend doublet, along-hole
    t_prod_c: float = 77.0              # BLT-01 ThermoGIS P50 temperature
    t_reinject_c: float = 35.0          # ThermoGIS standard reinjection
    heat_mwth_p50: float = 10.12        # MC P50 for the 2-doublet scheme
    heat_loadhours: float = 6000.0
    demand_heating_mwth: float = DEMAND_HEATING_MWTH
    demand_cooling_mwth: float = DEMAND_COOLING_MWTH

    @property
    def n_wells(self) -> int:
        return self.n_doublets * self.wells_per_doublet

    def heat_case(self) -> HeatCase:
        return HeatCase(n_wells=self.n_wells, ah_depth_m=self.ah_depth_m,
                        t_prod_c=self.t_prod_c, t_outlet_c=self.t_prod_c,
                        t_reinject_c=self.t_reinject_c,
                        heat_loadhours=self.heat_loadhours)


def size_design_a(cfg: SchemeConfig, ates_pairs: int = 4) -> dict:
    """Design A — geothermal heat + ATES/heat-pump cooling."""
    heat = heat_economics(cfg.heat_case(), heat_mwth=cfg.heat_mwth_p50)
    cool = cooling_economics(CoolingCase(cooling_mwth=cfg.demand_cooling_mwth,
                                         ates_pairs=ates_pairs))
    meets_heat = heat["heat_mwth"] >= cfg.demand_heating_mwth
    meets_cool = cool["ates_supply_mwth"] >= cfg.demand_cooling_mwth
    return {
        "design": "A (ATES + heat pump)",
        "heat_mwth": heat["heat_mwth"],
        "cooling_mwth": cool["cooling_mwth"],
        "geo_heat_consumed_for_cooling_mwth": 0.0,
        "ates_pairs": ates_pairs,
        "lcoe_heat_eur_gj": heat["lcoe_eur_gj"],
        "lcoe_cool_eur_gj": cool["lcoe_eur_gj"],
        "capex_total_mln": heat["capex_mln"] + cool["capex_mln"],
        "cooling_elec_mwh_yr": cool["elec_mwh"],
        "meets_heating": meets_heat,
        "meets_cooling": meets_cool,
        "_heat": heat,
        "_cool": cool,
    }


def size_design_b(cfg: SchemeConfig) -> dict:
    """Design B — geothermal heat + LiBr/H2O absorption-chiller cooling."""
    heat = heat_economics(cfg.heat_case(), heat_mwth=cfg.heat_mwth_p50)
    cool = cooling_economics_absorption(
        AbsorptionCoolingCase(cooling_mwth=cfg.demand_cooling_mwth),
        heat_lcoe_eur_gj=heat["lcoe_eur_gj"])
    driving = cool["driving_heat_mwth"]
    # The chiller's driving heat competes with the heat we sell: net heat that can
    # be delivered to the district while the chiller runs is reduced by `driving`.
    net_heat_during_cooling = heat["heat_mwth"] - driving
    return {
        "design": "B (absorption chiller)",
        "heat_mwth": heat["heat_mwth"],
        "cooling_mwth": cool["cooling_mwth"],
        "geo_heat_consumed_for_cooling_mwth": driving,
        "ates_pairs": 0,
        "lcoe_heat_eur_gj": heat["lcoe_eur_gj"],
        "lcoe_cool_eur_gj": cool["lcoe_eur_gj"],
        "capex_total_mln": heat["capex_mln"] + cool["capex_mln"],
        "cooling_elec_mwh_yr": cool["elec_mwh"],
        "net_heat_while_cooling_mwth": net_heat_during_cooling,
        "meets_heating": heat["heat_mwth"] >= cfg.demand_heating_mwth,
        "meets_cooling": True,
        "_heat": heat,
        "_cool": cool,
    }


def comparison_table(cfg: SchemeConfig | None = None,
                     ates_pairs: int = 4) -> pd.DataFrame:
    """Side-by-side Design A vs Design B for the deck and report."""
    cfg = cfg or SchemeConfig()
    a, b = size_design_a(cfg, ates_pairs), size_design_b(cfg)
    cols = ["design", "heat_mwth", "cooling_mwth",
            "geo_heat_consumed_for_cooling_mwth", "ates_pairs",
            "lcoe_heat_eur_gj", "lcoe_cool_eur_gj", "capex_total_mln",
            "cooling_elec_mwh_yr", "meets_heating", "meets_cooling"]
    rows = [{k: d.get(k) for k in cols} for d in (a, b)]
    df = pd.DataFrame(rows)
    for c in ("heat_mwth", "cooling_mwth", "geo_heat_consumed_for_cooling_mwth",
              "lcoe_heat_eur_gj", "lcoe_cool_eur_gj", "capex_total_mln"):
        df[c] = df[c].round(2)
    df["cooling_elec_mwh_yr"] = df["cooling_elec_mwh_yr"].round(0)
    return df


if __name__ == "__main__":
    import pandas as pd
    pd.set_option("display.width", 160, "display.max_columns", 20)
    print(comparison_table().to_string(index=False))
