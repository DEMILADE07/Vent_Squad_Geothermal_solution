"""Petrophysics: shale volume, porosity, and a Rotliegend net-reservoir summary.

Conventions for the Permian Rotliegend (consolidated, pre-Tertiary):
  * Larionov (older rocks) for V_shale from gamma ray.
  * Density porosity with a sandstone matrix (rho_ma = 2.65 g/cc, rho_fl = 1.0).
  * Net-reservoir cutoffs V_sh < 0.40 and phi > 0.08 (NL Rotliegend convention,
    see constants).
GR baselines are robust per-well percentiles (clean-sand vs shale) unless given.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.constants import (
    POROSITY_CUTOFF,
    RHO_FLUID,
    RHO_MATRIX_SANDSTONE,
    VSHALE_CUTOFF,
)


def vshale_larionov_older(gr, gr_clean, gr_shale):
    """V_shale via Larionov (1969) for older/consolidated rocks.

    IGR is the linear gamma-ray index; the Larionov-older transform reduces the
    linear estimate, appropriate for compacted Permian sandstones.
    """
    gr = np.asarray(gr, float)
    igr = np.clip((gr - gr_clean) / (gr_shale - gr_clean), 0.0, 1.0)
    return 0.33 * (np.power(2.0, 2.0 * igr) - 1.0)


def density_porosity(rhob, rho_ma=RHO_MATRIX_SANDSTONE, rho_fl=RHO_FLUID):
    """Density porosity (fraction); clipped to [0, 1]."""
    rhob = np.asarray(rhob, float)
    phi = (rho_ma - rhob) / (rho_ma - rho_fl)
    return np.clip(phi, 0.0, 1.0)


def gr_baselines(gr, p_clean=5.0, p_shale=95.0):
    """Robust (clean, shale) GR endpoints from percentiles, ignoring NaN."""
    gr = np.asarray(gr, float)
    return float(np.nanpercentile(gr, p_clean)), float(np.nanpercentile(gr, p_shale))


def add_petrophysics(logs: pd.DataFrame) -> pd.DataFrame:
    """Add ``vsh`` and ``phi_d`` columns to a tidy multi-well logs frame.

    Baselines are derived per well from that well's full GR range.
    """
    out = logs.copy()
    out["vsh"] = np.nan
    out["phi_d"] = np.nan
    for well, idx in out.groupby("well", sort=False).groups.items():
        g = out.loc[idx]
        clean, shale = gr_baselines(g["GR"])
        out.loc[idx, "vsh"] = vshale_larionov_older(g["GR"], clean, shale)
        if g["RHOB"].notna().any():
            out.loc[idx, "phi_d"] = density_porosity(g["RHOB"])
    return out


def rotliegend_summary(logs: pd.DataFrame, pick: dict,
                       vsh_cut=VSHALE_CUTOFF, phi_cut=POROSITY_CUTOFF) -> dict:
    """Net-reservoir summary over a well's Rotliegend (Slochteren) TVD window.

    ``logs`` must already carry ``vsh``/``phi_d`` (see add_petrophysics) and a
    ``tvd_m`` column. ``pick`` is a rotliegend_pick() dict. Net is the cumulative
    TVD thickness of samples passing both cutoffs; sample spacing is inferred
    from the median TVD step.
    """
    well = pick["well"]
    g = logs[(logs["well"] == well)
             & (logs["tvd_m"] >= pick["top_tvd"])
             & (logs["tvd_m"] <= pick["base_tvd"])].sort_values("tvd_m")
    if g.empty:
        return {"well": well, "n_samples": 0, "note": "no logs in Rotliegend window"}

    step = float(np.nanmedian(np.diff(g["tvd_m"].to_numpy())))
    reservoir = (g["vsh"] < vsh_cut) & (g["phi_d"] > phi_cut)
    have_phi = g["phi_d"].notna()

    gross = pick["thickness_tvd_m"]
    net = float(reservoir.sum()) * step
    return {
        "well": well,
        "top_tvd_m": round(pick["top_tvd"], 1),
        "base_tvd_m": round(pick["base_tvd"], 1),
        "gross_tvd_m": round(gross, 1),
        "n_samples": int(len(g)),
        "n_with_phi": int(have_phi.sum()),
        "net_tvd_m": round(net, 1),
        "ntg": round(net / gross, 3) if gross else float("nan"),
        "phi_mean_net": round(float(g.loc[reservoir, "phi_d"].mean()), 4),
        "phi_mean_all": round(float(g["phi_d"].mean()), 4),
        "vsh_mean": round(float(g["vsh"].mean()), 3),
        "tvd_step_m": round(step, 4),
    }
