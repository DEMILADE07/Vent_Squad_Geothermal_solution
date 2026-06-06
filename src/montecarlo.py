"""Monte-Carlo MWth: propagate ThermoGIS transmissivity uncertainty.

Transmissivity (kh) is the dominant uncertain input and the one ThermoGIS
publishes as a P90/P50/P10 band. We fit a lognormal to that band (P50 = median;
P90/P10 = 10th/90th percentiles in ThermoGIS's low-to-high convention), draw kh,
push it through the calibrated Darcy doublet model to a flow rate, and convert to
thermal power at the well's production-injection dT.

The resulting flow distribution is validated against ThermoGIS's own published
Flow P90/P50/P10 (it should match, since Darcy is linear in kh and the drawdown
is calibrated to the P50). Output: one row per (well, draw).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.constants import DRAWDOWN_THERMOGIS_PA, INJECTION_TEMP_C, WELLS
from src.deliverability import darcy_flow_m3h, delta_t_c, thermal_power_mw
from src.thermogis import load_thermogis, thermogis_property

_Z90 = 1.2815515594  # z-score for the 90th percentile
_KH_FLOOR_DM = 0.01  # guard against rounded-to-zero P90 (PKP-01)

# Physical ceiling on sustained production from a single doublet. ThermoGIS's own
# published flow P10 (high) for BLT-01 is 469 m3/h, and a symmetric lognormal fit
# overshoots even that (-> ~550 m3/h). Neither is bankable: NL Rotliegend doublets
# run ~100-300 m3/h, pump- and sand-control-limited. We therefore de-rate any
# realisation above this rate to the rate itself (the surface choke, not the
# reservoir, sets the cap). Only the dishonest upper tail is touched; P50 << cap.
MAX_SUSTAINABLE_FLOW_M3H = 300.0


def fit_lognormal(p90, p50, p10):
    """(mu, sigma) of ln(X) from a low/median/high percentile triple.

    ThermoGIS convention: p90 is the LOW value, p10 the HIGH value. The single
    sigma is set from the full P90->P10 span, so the fit is symmetric in log space
    and reproduces the median exactly but only the P90/P10 *average* spread.
    """
    lo, mid, hi = (max(v, _KH_FLOOR_DM) for v in (p90, p50, p10))
    mu = np.log(mid)
    sigma = (np.log(hi) - np.log(lo)) / (2.0 * _Z90)
    return mu, sigma


def fit_split_lognormal(p90, p50, p10):
    """(mu, sigma_lo, sigma_hi) of a two-piece lognormal honouring all three points.

    ThermoGIS bands are log-asymmetric (BLT-01 flow 17/105/469: the median sits
    closer to the high value than the low). A single-sigma lognormal cannot hit
    both P90 and P10, and on that well it overshoots the published P10 by ~17 %
    (551 vs 469 m3/h), inflating the optimistic resource tail. The split fit keeps
    mu = ln(P50) and uses a separate sigma below and above the median, so the
    sampled P90 and P10 reproduce ThermoGIS's published values *exactly*.
    """
    lo, mid, hi = (max(v, _KH_FLOOR_DM) for v in (p90, p50, p10))
    mu = np.log(mid)
    sigma_lo = (np.log(mid) - np.log(lo)) / _Z90
    sigma_hi = (np.log(hi) - np.log(mid)) / _Z90
    return mu, sigma_lo, sigma_hi


def _sample_split_lognormal(rng, mu, sigma_lo, sigma_hi, n):
    """Draw n samples from the two-piece lognormal of ``fit_split_lognormal``.

    A single standard normal z selects the side (z<0 below the median, z>0 above)
    and supplies the magnitude; the per-draw sigma switches at the median. P(z<0)
    = 0.5 keeps exp(mu) the exact median, and the |z|=z90 points map to the
    published P90/P10 by construction.
    """
    z = rng.standard_normal(n)
    sigma = np.where(z < 0.0, sigma_lo, sigma_hi)
    return np.exp(mu + sigma * z)


def simulate_well(df_tg, well, n=10_000, drawdown_pa=DRAWDOWN_THERMOGIS_PA,
                  seed=0, anchor="flow",
                  q_max_m3h=MAX_SUSTAINABLE_FLOW_M3H) -> pd.DataFrame:
    """Draw n MWth realisations for a single-doublet at ``well``.

    anchor="flow" (headline): sample a split-lognormal fit to ThermoGIS's
    published Flow Rate P90/P50/P10. The two-piece fit reproduces all three
    published points exactly (the old single-sigma fit overshot the P10), and the
    draw is de-rated at ``q_max_m3h`` — the pump/sand-control ceiling on a single
    doublet — so the optimistic tail stays physical. ``kh_dm`` is then back-
    implied from flow.

    anchor="kh": sample the transmissivity band and push through the Darcy
    doublet model. The mechanistic propagation; matches ThermoGIS at P50, fatter
    upper tail. Retained as the physical cross-check.

    q_max_m3h: per-doublet flow ceiling; None disables it. Default
        ``MAX_SUSTAINABLE_FLOW_M3H`` (300 m3/h). Only the flow anchor is capped.
    """
    t = thermogis_property(df_tg, well, "Temperature")
    dt = delta_t_c(t["p50"], INJECTION_TEMP_C)
    rng = np.random.default_rng(seed)

    if anchor == "flow":
        fr = thermogis_property(df_tg, well, "Flow Rate")
        if max(fr["p90"], fr["p50"], fr["p10"]) <= 0.0:
            flow = np.zeros(n)  # ThermoGIS judges this well uneconomic
        else:
            mu, sigma_lo, sigma_hi = fit_split_lognormal(
                fr["p90"], fr["p50"], fr["p10"])
            flow = _sample_split_lognormal(rng, mu, sigma_lo, sigma_hi, n)
            if q_max_m3h is not None:
                flow = np.minimum(flow, q_max_m3h)
        kh_draws = np.full(n, thermogis_property(df_tg, well, "Transmissivity")["p50"])
    elif anchor == "kh":
        kh = thermogis_property(df_tg, well, "Transmissivity")
        mu, sigma = fit_lognormal(kh["p90"], kh["p50"], kh["p10"])
        kh_draws = rng.lognormal(mean=mu, sigma=sigma, size=n)
        flow = darcy_flow_m3h(kh_draws, drawdown_pa)
    else:
        raise ValueError(f"anchor must be 'flow' or 'kh', got {anchor!r}")

    mwth = thermal_power_mw(flow, dt)
    return pd.DataFrame({
        "well": well, "draw": np.arange(n), "anchor": anchor,
        "kh_dm": kh_draws, "flow_m3h": flow, "mwth": mwth,
    })


def simulate_all(df_tg=None, n=10_000, drawdown_pa=DRAWDOWN_THERMOGIS_PA,
                 seed=0, anchor="flow",
                 q_max_m3h=MAX_SUSTAINABLE_FLOW_M3H) -> pd.DataFrame:
    """Monte-Carlo all four wells; distinct per-well seed for independence."""
    if df_tg is None:
        df_tg = load_thermogis()
    frames = [simulate_well(df_tg, w, n, drawdown_pa, seed + i, anchor, q_max_m3h)
              for i, w in enumerate(WELLS)]
    return pd.concat(frames, ignore_index=True)


def summarise(mc: pd.DataFrame, demand_mwth=10.0, n_doublets=1) -> pd.DataFrame:
    """Per-well P10/P50/P90 MWth and P(scheme >= demand) for n_doublets.

    With independent identical doublets, scheme power is n * single-doublet draw
    (a conservative shorthand: identical reservoir realisation per doublet).
    """
    rows = []
    for well, g in mc.groupby("well", sort=False):
        scheme = g["mwth"].to_numpy() * n_doublets
        rows.append({
            "well": well,
            "n_doublets": n_doublets,
            "mwth_p90": round(float(np.percentile(scheme, 10)), 2),
            "mwth_p50": round(float(np.percentile(scheme, 50)), 2),
            "mwth_p10": round(float(np.percentile(scheme, 90)), 2),
            "mwth_mean": round(float(scheme.mean()), 2),
            f"p_ge_{demand_mwth:g}MWth": round(float((scheme >= demand_mwth).mean()), 3),
        })
    return pd.DataFrame(rows)
