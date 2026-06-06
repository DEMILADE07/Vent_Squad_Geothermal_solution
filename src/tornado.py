"""LCOE sensitivity tornado — top drivers of the blended hybrid LCOE.

Each driver is swung between a low and high value while everything else is held
at the base case; the bars are sorted by the spread they open in the blended
system LCOE.  This is the figure that tells the board *which* assumptions the
recommendation actually hinges on (resource deliverability and the equity hurdle
dominate; the cooling-side knobs barely move it).
"""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.lcoe import CoolingCase, Financing, cooling_economics, heat_economics
from src.surface import SchemeConfig


def _blended_lcoe(cfg: SchemeConfig, cool: CoolingCase) -> float:
    h = heat_economics(cfg.heat_case(), heat_mwth=cfg.heat_delivered_mwth)
    k = cooling_economics(cool)
    e = h["npv_energy_gj"] + k["npv_energy_gj"]
    return (h["lcoe_eur_gj"] * h["npv_energy_gj"]
            + k["lcoe_eur_gj"] * k["npv_energy_gj"]) / e


def _with(cfg: SchemeConfig, cool: CoolingCase, *,
          fin=None, cfg_kw=None, heat_kw=None, cool_kw=None):
    """Rebuild (cfg, cool) with selective overrides, sharing one Financing."""
    fin = fin or Financing()
    base_heat = cfg.heat_case()
    heat = replace(base_heat, fin=fin, **(heat_kw or {}))
    cfg2 = replace(cfg, **(cfg_kw or {}))
    # carry the overridden HeatCase by monkey-binding through cfg2.heat_case():
    cfg2 = _CfgWithHeat(cfg2, heat)
    cool2 = replace(cool, fin=fin, **(cool_kw or {}))
    return cfg2, cool2


class _CfgWithHeat:
    """Adapter: a SchemeConfig that returns a pre-built HeatCase."""
    def __init__(self, cfg: SchemeConfig, heat):
        self._cfg = cfg
        self._heat = heat

    def __getattr__(self, name):
        return getattr(self._cfg, name)

    def heat_case(self):
        return self._heat


# (driver label, builder for low case, builder for high case)
def tornado_data(cfg: SchemeConfig | None = None,
                 cool: CoolingCase | None = None) -> pd.DataFrame:
    cfg = cfg or SchemeConfig()
    cool = cool or CoolingCase(cooling_mwth=cfg.demand_cooling_mwth, ates_pairs=6)
    base = _blended_lcoe(cfg, cool)

    drivers = {
        "Heat delivered (MWth)": (
            _with(cfg, cool, cfg_kw={"heat_delivered_mwth": 13.0}),  # more sold -> low LCOE
            _with(cfg, cool, cfg_kw={"heat_delivered_mwth": 8.0}),
        ),
        "Equity return (disc.)": (
            _with(cfg, cool, fin=Financing(equity_return=0.10)),
            _with(cfg, cool, fin=Financing(equity_return=0.20)),
        ),
        "Drilling cost scaling": (
            _with(cfg, cool, heat_kw={"well_cost_scaling": 1.2}),
            _with(cfg, cool, heat_kw={"well_cost_scaling": 1.8}),
        ),
        "Heat load hours": (
            _with(cfg, cool, heat_kw={"heat_loadhours": 7000.0}),
            _with(cfg, cool, heat_kw={"heat_loadhours": 5000.0}),
        ),
        "Electricity price": (
            _with(cfg, cool, heat_kw={"electricity_price_eur_mwh": 80.0},
                  cool_kw={"electricity_price_eur_mwh": 80.0}),
            _with(cfg, cool, heat_kw={"electricity_price_eur_mwh": 250.0},
                  cool_kw={"electricity_price_eur_mwh": 250.0}),
        ),
        "ATES capex / pair": (
            _with(cfg, cool, cool_kw={"ates_capex_mln_per_pair": 0.5}),
            _with(cfg, cool, cool_kw={"ates_capex_mln_per_pair": 1.0}),
        ),
        "Cooling load hours": (
            _with(cfg, cool, cool_kw={"cooling_loadhours": 2500.0}),
            _with(cfg, cool, cool_kw={"cooling_loadhours": 1500.0}),
        ),
        "Cooling system COP": (
            _with(cfg, cool, cool_kw={"system_cop_cooling": 14.0}),
            _with(cfg, cool, cool_kw={"system_cop_cooling": 7.0}),
        ),
    }

    rows = []
    for label, ((cfg_lo, cool_lo), (cfg_hi, cool_hi)) in drivers.items():
        lo = _blended_lcoe(cfg_lo, cool_lo)
        hi = _blended_lcoe(cfg_hi, cool_hi)
        rows.append({"driver": label, "low": lo, "high": hi, "base": base,
                     "spread": abs(hi - lo)})
    df = pd.DataFrame(rows).sort_values("spread", ascending=True).reset_index(drop=True)
    return df


def plot_tornado(df: pd.DataFrame, base: float, save_path=None):
    """Horizontal tornado of low/high LCOE bars around the base case."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    y = range(len(df))
    for i, r in df.iterrows():
        lo, hi = sorted((r["low"], r["high"]))
        ax.barh(i, hi - lo, left=lo, color="#3b7dab", edgecolor="#1F4E5F")
    ax.axvline(base, color="#c1432b", lw=2, label=f"base = {base:.2f} EUR/GJ")
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["driver"])
    ax.set_xlabel("Blended system LCOE (EUR/GJ)")
    ax.set_title("Hybrid LCOE sensitivity — top drivers")
    ax.legend(loc="lower right")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig, ax


if __name__ == "__main__":
    from src.paths import FIGURES
    df = tornado_data()
    base = df["base"].iloc[0]
    print(df[["driver", "low", "high", "spread"]].to_string(index=False))
    FIGURES.mkdir(parents=True, exist_ok=True)
    plot_tornado(df, base, save_path=FIGURES / "lcoe_tornado.png")
    print("\nsaved", FIGURES / "lcoe_tornado.png")
