"""Doublet thermal breakthrough and produced-temperature decline over field life.

The TNO cash flow assumes the produced temperature — and therefore MWth — is flat
for the whole economic life.  That is only true if the injected cold front has not
reached the producer.  This module makes that assumption *checkable* rather than
asserted: it computes when thermal breakthrough occurs and how the produced
temperature (hence delivered MWth) declines afterwards, so the economics can
ingest a time-varying energy profile.

Method.
- **Breakthrough time** — Gringarten & Sauty (1975) doublet result.  The thermal
  front along the direct inter-well streamline arrives at

      t_bt = (pi * H * L^2) / (3 * Q) * (rhoc_bulk / rhoc_water)

  with H the (flowing) reservoir thickness, L the producer-injector spacing, Q the
  volumetric flow, and the heat-capacity ratio rhoc_bulk/rhoc_water the thermal
  retardation (the front lags the tracer because it must also cool the matrix).
  Conduction from the over/under-burden is neglected, which makes the estimate
  *conservative* (earliest possible breakthrough); real conduction reheats the
  produced water and pushes breakthrough later.

- **Produced-temperature decline** — before t_bt the produced temperature holds at
  the reservoir value (conduction keeps it there); after t_bt different streamlines
  break through in turn, so the flow-weighted produced temperature relaxes from
  T_res toward T_inj.  We model that relaxation as a transparent linear envelope
  over a recovery timescale (default = t_bt, the same swept-volume scale); it
  approximates the Gringarten-Sauty production-temperature curve without its full
  streamline integral, which is the right altitude for a feasibility study.

For the recommended 1.3 km doublet on this reservoir, t_bt lands far beyond the
economic life, so the profile is ~flat and the constant-MWth assumption is
*validated, not assumed*.  The value of the model is that it (a) proves that, and
(b) shows — via the spacing sensitivity — where breakthrough would start to bite.
"""

from __future__ import annotations

import numpy as np

from src.constants import (
    DOUBLET_SPACING_M,
    INJECTION_TEMP_C,
    ROCK_DENSITY_KG_M3,
    ROCK_HEAT_CAPACITY_J_KGK,
    SECONDS_PER_YEAR,
    WATER_DENSITY_KG_M3,
    WATER_HEAT_CAPACITY_J_KGK,
)
from src.deliverability import thermal_power_mw

# In-situ fluid properties (1000 kg/m3, 4180 J/kgK) drive this reservoir heat balance;
# the LCOE engine (src/lcoe.py) deliberately keeps TNO's workbook brine (1078, 4250)
# so it reproduces the published 5.769 reference. The two contexts are distinct
# (in-situ thermal front vs workbook cash flow) and the ~8 % difference does not cross
# between them.
_RHOC_WATER = WATER_DENSITY_KG_M3 * WATER_HEAT_CAPACITY_J_KGK   # J/(m^3.K)
_RHOC_ROCK = ROCK_DENSITY_KG_M3 * ROCK_HEAT_CAPACITY_J_KGK      # J/(m^3.K)


def bulk_volumetric_heat_capacity(porosity: float) -> float:
    """Saturated-rock bulk volumetric heat capacity, J/(m^3.K)."""
    return porosity * _RHOC_WATER + (1.0 - porosity) * _RHOC_ROCK


def breakthrough_time_yr(flow_m3h: float, thickness_m: float, porosity: float,
                         spacing_m: float = DOUBLET_SPACING_M) -> float:
    """Gringarten-Sauty thermal breakthrough time for a doublet, in years.

    t_bt = (pi * H * L^2 / (3 Q)) * (rhoc_bulk / rhoc_water).  Note porosity enters
    only through rhoc_bulk — it cancels against the pore volume in the tracer time.
    Returns +inf for non-producing wells (Q <= 0).
    """
    q_m3s = float(flow_m3h) / 3600.0
    if q_m3s <= 0.0:
        return float("inf")
    retardation = bulk_volumetric_heat_capacity(porosity) / _RHOC_WATER
    t_s = np.pi * thickness_m * spacing_m ** 2 / (3.0 * q_m3s) * retardation
    return t_s / SECONDS_PER_YEAR


def produced_temperature_profile(years, t_res_c: float, t_bt_yr: float,
                                 t_inj_c: float = INJECTION_TEMP_C,
                                 recovery_yr: float | None = None) -> np.ndarray:
    """Produced temperature (degC) per year: flat at T_res until breakthrough,
    then a linear relaxation toward T_inj over ``recovery_yr`` (default t_bt)."""
    years = np.asarray(years, dtype=float)
    if recovery_yr is None:
        recovery_yr = t_bt_yr
    if not np.isfinite(t_bt_yr) or recovery_yr <= 0.0:
        return np.full(years.shape, float(t_res_c))
    frac = np.clip((years - t_bt_yr) / recovery_yr, 0.0, 1.0)
    return t_res_c - frac * (t_res_c - t_inj_c)


def mwth_profile(years, flow_m3h: float, thickness_m: float, porosity: float,
                 t_res_c: float, t_inj_c: float = INJECTION_TEMP_C,
                 spacing_m: float = DOUBLET_SPACING_M,
                 recovery_yr: float | None = None) -> np.ndarray:
    """Delivered thermal power (MWth) per year, declining after breakthrough.

    Convenience wrapper: compute t_bt, the produced-temperature profile, and the
    corresponding MWth = rho*cp*Q*(T_prod - T_inj).
    """
    t_bt = breakthrough_time_yr(flow_m3h, thickness_m, porosity, spacing_m)
    t_prod = produced_temperature_profile(years, t_res_c, t_bt, t_inj_c, recovery_yr)
    return thermal_power_mw(flow_m3h, t_prod - t_inj_c)


def decline_summary(flow_m3h: float, thickness_m: float, porosity: float,
                    t_res_c: float, lifetime_yr: int,
                    t_inj_c: float = INJECTION_TEMP_C,
                    spacing_m: float = DOUBLET_SPACING_M,
                    recovery_yr: float | None = None) -> dict:
    """Headline breakthrough metrics over an ``lifetime_yr`` economic life."""
    years = np.arange(1, lifetime_yr + 1)
    t_bt = breakthrough_time_yr(flow_m3h, thickness_m, porosity, spacing_m)
    t_prod = produced_temperature_profile(years, t_res_c, t_bt, t_inj_c, recovery_yr)
    mw = thermal_power_mw(flow_m3h, t_prod - t_inj_c)
    mw0 = float(mw[0])
    return {
        "breakthrough_yr": t_bt,
        "breakthrough_within_life": bool(t_bt <= lifetime_yr),
        "t_prod_start_c": float(t_prod[0]),
        "t_prod_end_c": float(t_prod[-1]),
        "temp_decline_c": float(t_prod[0] - t_prod[-1]),
        "mwth_start": mw0,
        "mwth_end": float(mw[-1]),
        "mwth_mean_over_life": float(mw.mean()),
        "energy_retention": float(mw.mean() / mw0) if mw0 else float("nan"),
        "mwth_profile": mw,
    }
