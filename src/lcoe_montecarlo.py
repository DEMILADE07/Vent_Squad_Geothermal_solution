"""Probabilistic LCOE — propagate resource + cost uncertainty to an LCOE distribution.

The deterministic engine (src/lcoe.py) returns one number from one set of inputs.
The headline LCOE, though, inherits two layers of uncertainty: the *resource*
(the bounded Monte-Carlo MWth of src/montecarlo.py, the top tornado driver) and the
*cost/market* inputs (drilling cost, heat load hours, electricity price, cooling
kit).  This module draws both jointly and pushes each realisation through the
financed model, so the output is an LCOE *distribution* — P10/P50/P90 and a CDF —
rather than a point.  That converts "11.7 EUR/GJ" into "11.7, with a 90 % band",
which is the honest way to state a number whose dominant input is a coin-flip
resource.

Coherence with the tornado.  The cost inputs are sampled from triangular
distributions whose (low, mode, high) are exactly the tornado's low/base/high
swing points (src/tornado.py).  The tornado says *which* inputs matter and by how
much at the extremes; this MC says *how they combine* into the spread of the
headline number.  Same assumptions, two complementary views.

Discount rate is treated as a *scenario* axis, not an aleatory draw: the required
equity return is a policy/financing choice, so we report the LCOE distribution at
each hurdle rate (10/15/20 %) rather than blurring them into one cloud.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.lcoe import (
    CoolingCase,
    Financing,
    HeatCase,
    cooling_economics,
    heat_economics,
)
from src.montecarlo import simulate_well
from src.surface import SchemeConfig
from src.thermogis import load_thermogis


@dataclass(frozen=True)
class LcoeUncertainty:
    """Triangular (low, mode, high) ranges for the sampled cost/market inputs.

    Modes are the base case; the low/high match the tornado swing points so the
    two analyses tell one consistent story.
    """
    well_cost_scaling: tuple = (1.2, 1.5, 1.8)        # TNO drilling-cost factor
    heat_loadhours: tuple = (5000.0, 6000.0, 7000.0)  # full-load equivalent hours
    electricity_price: tuple = (80.0, 150.0, 250.0)   # EUR/MWh, pumps + heat pumps
    ates_capex_per_pair: tuple = (0.5, 0.7, 1.0)      # mln EUR / ATES pair
    cooling_loadhours: tuple = (1500.0, 2000.0, 2500.0)
    cooling_system_cop: tuple = (7.0, 10.0, 14.0)


def _tri(rng, n, lo_mode_hi):
    lo, mode, hi = lo_mode_hi
    return rng.triangular(lo, mode, hi, size=n)


def simulate_lcoe(cfg: SchemeConfig | None = None,
                  unc: LcoeUncertainty | None = None,
                  n: int = 10_000, seed: int = 0,
                  equity_return: float = 0.15,
                  lifetime_yr: int | None = None,
                  anchor_well: str = "BLT-01") -> pd.DataFrame:
    """Draw n joint realisations and return per-draw LCOE (heat, cool, blended).

    Resource MWth is the bounded Monte-Carlo (split-lognormal + 300 m3/h pump cap)
    summed over ``n_doublets`` *independent* doublet draws — two well pairs sample
    the play independently, so we do NOT rescale one draw by k. Heat *delivered* is
    then capped at the heating demand (we cannot sell beyond it), so resource upside
    cannot spuriously cheapen the LCOE; only resource *shortfall* and the cost/market
    draws move it — which is exactly the honest upper tail. Each resource draw is
    paired with an independent cost/market draw.
    """
    cfg = cfg or SchemeConfig()
    unc = unc or LcoeUncertainty()
    rng = np.random.default_rng(seed)

    # Resource: n_doublets INDEPENDENT single-doublet draws at the anchor well.
    df_tg = load_thermogis()
    resource = np.zeros(n)
    for d in range(cfg.n_doublets):
        resource = resource + simulate_well(
            df_tg, anchor_well, n=n, seed=seed + 101 + d)["mwth"].to_numpy()
    # Heat sold is demand-capped: the surplus resource de-risks delivery, it does
    # not lower the unit cost (there is no buyer for heat beyond the demand).
    scheme_mwth = np.minimum(resource, cfg.demand_heating_mwth)
    scheme_mwth = np.maximum(scheme_mwth, 1e-3)  # avoid div-by-zero LCOE blow-ups

    scaling = _tri(rng, n, unc.well_cost_scaling)
    loadh = _tri(rng, n, unc.heat_loadhours)
    elec = _tri(rng, n, unc.electricity_price)
    ates_cap = _tri(rng, n, unc.ates_capex_per_pair)
    cool_loadh = _tri(rng, n, unc.cooling_loadhours)
    cool_cop = _tri(rng, n, unc.cooling_system_cop)

    fin = Financing(equity_return=equity_return)
    base_heat = cfg.heat_case()
    rows = np.empty(n, dtype=[("lcoe_heat", "f8"), ("lcoe_cool", "f8"),
                              ("lcoe_blended", "f8")])

    for i in range(n):
        hc = HeatCase(
            n_wells=cfg.n_wells, ah_depth_m=base_heat.ah_depth_m,
            t_prod_c=cfg.t_prod_c, t_outlet_c=cfg.t_prod_c,
            t_reinject_c=cfg.t_reinject_c,
            heat_loadhours=float(loadh[i]), well_cost_scaling=float(scaling[i]),
            electricity_price_eur_mwh=float(elec[i]), fin=fin)
        h = heat_economics(hc, heat_mwth=float(scheme_mwth[i]), lifetime_yr=lifetime_yr)

        kc = CoolingCase(
            cooling_mwth=cfg.demand_cooling_mwth, ates_pairs=6,
            ates_capex_mln_per_pair=float(ates_cap[i]),
            cooling_loadhours=float(cool_loadh[i]),
            system_cop_cooling=float(cool_cop[i]),
            electricity_price_eur_mwh=float(elec[i]), fin=fin)
        k = cooling_economics(kc)

        e = h["npv_energy_gj"] + k["npv_energy_gj"]
        blended = (h["lcoe_eur_gj"] * h["npv_energy_gj"]
                   + k["lcoe_eur_gj"] * k["npv_energy_gj"]) / e if e else np.nan
        rows[i] = (h["lcoe_eur_gj"], k["lcoe_eur_gj"], blended)

    out = pd.DataFrame(rows)
    out.insert(0, "draw", np.arange(n))
    out["heat_mwth"] = scheme_mwth
    out["well_cost_scaling"] = scaling
    out["heat_loadhours"] = loadh
    out["electricity_price"] = elec
    out["equity_return"] = equity_return
    return out


def summarise_lcoe(df: pd.DataFrame,
                   cols=("lcoe_heat", "lcoe_cool", "lcoe_blended")) -> pd.DataFrame:
    """P10/P50/P90 (+ mean) for each LCOE column. P10 = optimistic (low) cost."""
    rows = []
    for c in cols:
        x = df[c].to_numpy()
        x = x[np.isfinite(x)]
        rows.append({
            "metric": c,
            "p10_low": round(float(np.percentile(x, 10)), 2),
            "p50": round(float(np.percentile(x, 50)), 2),
            "p90_high": round(float(np.percentile(x, 90)), 2),
            "mean": round(float(x.mean()), 2),
        })
    return pd.DataFrame(rows)


def lcoe_scenarios_by_hurdle(cfg: SchemeConfig | None = None,
                             unc: LcoeUncertainty | None = None,
                             n: int = 10_000, seed: int = 0,
                             hurdles=(0.10, 0.15, 0.20),
                             lifetime_yr: int | None = None) -> pd.DataFrame:
    """Heat-LCOE P10/P50/P90 at each required equity return (scenario axis)."""
    rows = []
    for r in hurdles:
        df = simulate_lcoe(cfg, unc, n=n, seed=seed, equity_return=r,
                           lifetime_yr=lifetime_yr)
        x = df["lcoe_heat"].to_numpy()
        rows.append({
            "equity_return": r,
            "lcoe_heat_p10": round(float(np.percentile(x, 10)), 2),
            "lcoe_heat_p50": round(float(np.percentile(x, 50)), 2),
            "lcoe_heat_p90": round(float(np.percentile(x, 90)), 2),
        })
    return pd.DataFrame(rows)


def plot_lcoe_distribution(df: pd.DataFrame, col: str = "lcoe_heat",
                           save_path=None):
    """Histogram + empirical CDF of the LCOE, with P10/P50/P90 markers."""
    import matplotlib.pyplot as plt

    x = np.sort(df[col].to_numpy())
    x = x[np.isfinite(x)]
    p10, p50, p90 = (float(np.percentile(x, q)) for q in (10, 50, 90))
    cdf = np.arange(1, len(x) + 1) / len(x)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(x, bins=60, density=True, color="#9ec6dd", edgecolor="white", alpha=0.8)
    ax.set_xlabel("LCOE (EUR/GJ)")
    ax.set_ylabel("density")
    ax2 = ax.twinx()
    ax2.plot(x, cdf, color="#1F4E5F", lw=2, label="CDF")
    ax2.set_ylabel("cumulative probability")
    for p, lab, c in ((p10, "P10", "#3b7dab"), (p50, "P50", "#c1432b"),
                      (p90, "P90", "#3b7dab")):
        ax.axvline(p, color=c, lw=1.5, ls="--")
        ax.text(p, ax.get_ylim()[1] * 0.92, f" {lab}={p:.1f}", color=c, fontsize=9)
    ax.set_title(f"Probabilistic LCOE — {col} (n={len(x)})")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig, ax


if __name__ == "__main__":
    df = simulate_lcoe(n=10_000)
    print(summarise_lcoe(df).to_string(index=False))
    print()
    print(lcoe_scenarios_by_hurdle(n=4_000).to_string(index=False))
