"""8760-hour dispatch simulation — derive the load-hours instead of assuming them.

The LCOE leans on three numbers that the deterministic model simply *asserts*:
heat full-load-equivalent hours (6000), cooling load hours (2000), and the ATES
well-pair count (4).  Two of those are top-three tornado drivers, so assuming them
is exactly where a feasibility study should be challenged.  This module builds an
hourly district demand from a synthetic-but-realistic Utrecht temperature year and
dispatches the supply stack against it, so the load-hours, the ATES sizing and the
peak electricity draw fall *out* of a simulation rather than being typed in.

Demand.  Space heating is temperature-driven (heating-degree-hours), plus a flat
domestic-hot-water (DHW) baseload that runs year-round; total heat peak is scaled
to the 10 MWth design peak.  Cooling is temperature-driven and scaled to 5 MWth.

Supply (merit order).
  Heating  geothermal baseload (cheapest MWh) -> electric heat pump (COP ~4.2)
           for the shoulder -> backup boiler for the rare coldest hours.
  Cooling  ATES discharge (banked winter cold) -> electric chiller trim.

The headline finding this surfaces: geothermal economics live or die on *baseload
utilisation*.  A doublet sized to the full 10 MWth peak is idle most of the year
(low FLEQ, high LCOE); sized to baseload a flatter aggregate demand it reaches the
~6000 FLEQ the LCOE assumes.  The sim makes that trade explicit and feeds the
derived load-hours straight back into src/lcoe.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

HOURS = 8760


def nl_hourly_temperature(seed: int = 0) -> np.ndarray:
    """Synthetic Utrecht (De Bilt-like) hourly air temperature for one year (degC).

    Seasonal cosine (annual mean ~10.5, coldest late January) + diurnal cycle
    (warmest mid-afternoon) + a persistent AR(1) weather anomaly so cold snaps
    reach realistic winter design lows. Deterministic given ``seed``.
    """
    rng = np.random.default_rng(seed)
    h = np.arange(HOURS)
    day = h / 24.0
    seasonal = 10.5 - 8.5 * np.cos(2 * np.pi * (day - 25.0) / 365.0)
    diurnal = 3.5 * np.cos(2 * np.pi * (h % 24 - 15.0) / 24.0)
    # AR(1) daily weather anomaly, broadcast to hours
    anomaly = np.zeros(366)
    for d in range(1, 366):
        anomaly[d] = 0.82 * anomaly[d - 1] + rng.normal(0, 2.6)
    weather = anomaly[(day).astype(int)]
    return seasonal + diurnal + weather


@dataclass(frozen=True)
class DispatchConfig:
    heat_peak_mwth: float = 10.0
    cool_peak_mwth: float = 5.0
    dhw_baseload_mwth: float = 1.5        # year-round domestic hot water
    t_heat_ref_c: float = 15.5            # heating switches on below this
    t_cool_ref_c: float = 16.0            # cooling threshold (low: internal+solar gains)
    geo_capacity_mwth: float = 10.0       # geothermal capacity to district (= demand)
    hp_capacity_mwth: float = 6.0         # electric heat-pump peak capacity
    hp_cop: float = 4.2
    chiller_cop: float = 4.5
    ates_throughput_mwth_per_pair: float = 1.0   # conservative central (see constants.py)
    seed: int = 0


def demand_profiles(cfg: DispatchConfig) -> dict:
    """Hourly heat (space + DHW) and cooling demand, scaled to the design peaks."""
    t = nl_hourly_temperature(cfg.seed)
    sh = np.maximum(0.0, cfg.t_heat_ref_c - t)
    space_peak = cfg.heat_peak_mwth - cfg.dhw_baseload_mwth
    space_heat = space_peak * sh / sh.max()
    heat = space_heat + cfg.dhw_baseload_mwth

    # Cooling is driven by warm outdoor air plus daytime internal/solar gains, so
    # occupied summer hours need cooling even below the air-temp threshold.
    hour = np.arange(HOURS) % 24
    daytime = (hour >= 8) & (hour <= 20)
    cl = (np.maximum(0.0, t - cfg.t_cool_ref_c)
          + np.where(daytime & (t > 13.0), 0.6 * np.maximum(0.0, t - 13.0), 0.0))
    cool = cfg.cool_peak_mwth * cl / cl.max() if cl.max() > 0 else np.zeros(HOURS)
    return {"temperature_c": t, "heat_mwth": heat, "cool_mwth": cool,
            "space_heat_mwth": space_heat}


def dispatch_heating(heat_mwth: np.ndarray, cfg: DispatchConfig) -> dict:
    """Merit-order heating dispatch: geothermal -> heat pump -> backup boiler."""
    geo = np.minimum(heat_mwth, cfg.geo_capacity_mwth)
    residual = heat_mwth - geo
    hp = np.minimum(residual, cfg.hp_capacity_mwth)
    backup = residual - hp

    geo_energy = float(geo.sum())                 # MWh (1-h steps)
    heat_energy = float(heat_mwth.sum())
    hp_elec = hp / cfg.hp_cop
    return {
        "geo_energy_mwh": geo_energy,
        "heat_energy_mwh": heat_energy,
        "geo_coverage": geo_energy / heat_energy if heat_energy else float("nan"),
        "geo_fleq_h": geo_energy / cfg.geo_capacity_mwth if cfg.geo_capacity_mwth else float("nan"),
        "hp_elec_mwh": float(hp_elec.sum()),
        "backup_energy_mwh": float(backup.sum()),
        "hp_peak_mwe": float(hp_elec.max()),
        "hours_geo_capped": int((heat_mwth > cfg.geo_capacity_mwth).sum()),
    }


def dispatch_cooling(cool_mwth: np.ndarray, cfg: DispatchConfig) -> dict:
    """ATES discharge (sized to peak cooling) then electric-chiller trim."""
    peak = float(cool_mwth.max())
    ates_pairs = int(np.ceil(peak / cfg.ates_throughput_mwth_per_pair)) if peak > 0 else 0
    ates_power = ates_pairs * cfg.ates_throughput_mwth_per_pair
    ates = np.minimum(cool_mwth, ates_power)
    chiller = cool_mwth - ates
    cool_energy = float(cool_mwth.sum())
    chiller_elec = chiller / cfg.chiller_cop
    return {
        "cool_energy_mwh": cool_energy,
        "cool_peak_mwth": peak,
        "cool_fleq_h": cool_energy / peak if peak else float("nan"),
        "ates_pairs": ates_pairs,
        "ates_energy_mwh": float(ates.sum()),
        "ates_supply_fraction": float(ates.sum()) / cool_energy if cool_energy else float("nan"),
        "chiller_elec_mwh": float(chiller_elec.sum()),
        "chiller_peak_mwe": float(chiller_elec.max()),
    }


def simulate_dispatch(cfg: DispatchConfig | None = None) -> dict:
    """Full hourly dispatch -> derived load-hours, ATES sizing, peak electricity."""
    cfg = cfg or DispatchConfig()
    d = demand_profiles(cfg)
    h = dispatch_heating(d["heat_mwth"], cfg)
    c = dispatch_cooling(d["cool_mwth"], cfg)
    return {
        "geo_capacity_mwth": cfg.geo_capacity_mwth,
        "heat_peak_mwth": float(d["heat_mwth"].max()),
        **h, **c,
        "total_elec_mwh": h["hp_elec_mwh"] + c["chiller_elec_mwh"],
        "peak_elec_mwe": h["hp_peak_mwe"] + c["chiller_peak_mwe"],
    }


def sizing_table(capacities=(5.06, 7.5, 10.0), cfg: DispatchConfig | None = None) -> pd.DataFrame:
    """Geothermal baseload sizing trade: capacity -> coverage, FLEQ, peak backup.

    The core geothermal economics lesson — utilisation rises (FLEQ up) as you size
    the doublet down toward baseload, while the share of demand it covers falls and
    more peak load shifts to the heat pump / boiler.
    """
    from dataclasses import replace
    base = cfg or DispatchConfig()
    rows = []
    for g in capacities:
        s = simulate_dispatch(replace(base, geo_capacity_mwth=g))
        rows.append({
            "geo_capacity_mwth": round(g, 2),
            "geo_coverage_pct": round(100 * s["geo_coverage"], 1),
            "geo_fleq_h": round(s["geo_fleq_h"], 0),
            "hp_elec_mwh": round(s["hp_elec_mwh"], 0),
            "backup_mwh": round(s["backup_energy_mwh"], 0),
            "peak_elec_mwe": round(s["peak_elec_mwe"], 2),
        })
    return pd.DataFrame(rows)


def lcoe_at_simulated_loadhours(cfg: DispatchConfig | None = None) -> dict:
    """Re-price heat at the simulation-derived FLEQ, against the assumed 6000 h."""
    from src.lcoe import heat_economics
    from src.surface import SchemeConfig
    cfg = cfg or DispatchConfig()
    s = simulate_dispatch(cfg)
    sc = SchemeConfig()
    assumed = heat_economics(sc.heat_case(), heat_mwth=sc.heat_delivered_mwth)
    derived_case = sc.heat_case()
    from dataclasses import replace
    derived_case = replace(derived_case, heat_loadhours=s["geo_fleq_h"])
    derived = heat_economics(derived_case, heat_mwth=sc.heat_delivered_mwth)
    return {
        "fleq_assumed_h": sc.heat_case().heat_loadhours,
        "fleq_simulated_h": round(s["geo_fleq_h"], 0),
        "lcoe_heat_assumed": round(assumed["lcoe_eur_gj"], 2),
        "lcoe_heat_simulated": round(derived["lcoe_eur_gj"], 2),
        "geo_coverage_pct": round(100 * s["geo_coverage"], 1),
    }


def plot_dispatch(cfg: DispatchConfig | None = None, save_path=None):
    """Heat load-duration curve (with geothermal baseload band) + FLEQ-vs-sizing."""
    import matplotlib.pyplot as plt
    cfg = cfg or DispatchConfig()
    d = demand_profiles(cfg)
    ldc = np.sort(d["heat_mwth"])[::-1]
    x = np.arange(HOURS) / HOURS * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax1.fill_between(x, 0, ldc, color="#e6b8a2", label="heat demand")
    base = np.minimum(ldc, 5.06)
    ax1.fill_between(x, 0, base, color="#c1432b", alpha=0.85, label="1 doublet baseload (~5 MWth)")
    ax1.axhline(5.06, color="#1F4E5F", lw=1, ls="--")
    ax1.axhline(10.0, color="#3b7dab", lw=1, ls="--", label="2 doublets (peak-sized)")
    ax1.set_xlabel("% of year (load-duration)")
    ax1.set_ylabel("MWth")
    ax1.set_title("Heat load-duration — geothermal baseload vs peak")
    ax1.legend(fontsize=8, loc="upper right")

    st = sizing_table(capacities=(5.06, 6.0, 7.5, 8.5, 10.0), cfg=cfg)
    ax2.plot(st["geo_capacity_mwth"], st["geo_fleq_h"], "o-", color="#1F4E5F")
    ax2.axhline(6000, color="#c1432b", ls="--", lw=1, label="assumed 6000 h")
    ax2.set_xlabel("geothermal baseload capacity (MWth)")
    ax2.set_ylabel("geothermal FLEQ hours")
    ax2.set_title("Utilisation rises as geothermal is sized to baseload")
    for _, r in st.iterrows():
        ax2.annotate(f"{r['geo_coverage_pct']:.0f}%", (r["geo_capacity_mwth"], r["geo_fleq_h"]),
                     textcoords="offset points", xytext=(4, 6), fontsize=8)
    ax2.legend(fontsize=8)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


if __name__ == "__main__":
    import pandas as pd
    pd.set_option("display.width", 140)
    print("=== dispatch summary (geo = 10.0 MWth) ===")
    for k, v in simulate_dispatch().items():
        print(f"  {k:24} = {v:.2f}" if isinstance(v, float) else f"  {k:24} = {v}")
    print("\n=== geothermal baseload sizing trade ===")
    print(sizing_table().to_string(index=False))
    print("\n=== LCOE at simulated vs assumed load-hours ===")
    for k, v in lcoe_at_simulated_loadhours().items():
        print(f"  {k:24} = {v}")
