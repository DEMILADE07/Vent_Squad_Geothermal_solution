"""Doublet deliverability: Darcy radial inflow + thermal power.

The model is a steady-state doublet: a producer and an injector ``spacing`` apart,
with the external radius taken as the well spacing. Flow follows Darcy radial
inflow; thermal power is the produced enthalpy drop to the (re)injection
temperature.

Calibration. ThermoGIS publishes Flow Rate and Power as a P90/P50/P10
distribution. With this module's fluid properties, spacing and well radius, the
ThermoGIS Flow P50 is reproduced at ~16.5 bar drawdown (DRAWDOWN_THERMOGIS_PA),
and the ThermoGIS Power back-solves to a 35 C injection temperature
(INJECTION_TEMP_C). We therefore treat ThermoGIS Flow/Power as the authoritative
baseline and use this Darcy model as the engine for Monte-Carlo propagation and
for the higher-drawdown sensitivity case.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.constants import (
    DOUBLET_SPACING_M,
    DRAWDOWN_THERMOGIS_PA,
    INJECTION_TEMP_C,
    WATER_DENSITY_KG_M3,
    WATER_HEAT_CAPACITY_J_KGK,
    WATER_VISCOSITY_PA_S,
    WELLBORE_RADIUS_M,
    WELLS,
)
from src.thermogis import load_thermogis, thermogis_property

DARCY_M2 = 9.869233e-13  # 1 Darcy in m^2
_RHO_CP = WATER_DENSITY_KG_M3 * WATER_HEAT_CAPACITY_J_KGK  # J/(m^3.K)


def darcy_flow_m3h(kh_dm, drawdown_pa=DRAWDOWN_THERMOGIS_PA,
                   spacing_m=DOUBLET_SPACING_M, rw_m=WELLBORE_RADIUS_M,
                   mu_pa_s=WATER_VISCOSITY_PA_S):
    """Doublet volumetric flow (m^3/h) from transmissivity kh in Darcy-metres.

    Q = 2*pi*kh*dP / (mu * ln(spacing / rw)), converted s->h.
    """
    kh = np.asarray(kh_dm, float) * DARCY_M2  # Dm -> m^3 (m^2.m)
    q_m3s = 2.0 * np.pi * kh * drawdown_pa / (mu_pa_s * np.log(spacing_m / rw_m))
    return q_m3s * 3600.0


def thermal_power_mw(flow_m3h, delta_t_c):
    """Thermal power (MW) for a produced flow and production-injection dT."""
    q_m3s = np.asarray(flow_m3h, float) / 3600.0
    return _RHO_CP * q_m3s * np.asarray(delta_t_c, float) / 1e6


def delta_t_c(t_res_c, t_inj_c=INJECTION_TEMP_C):
    """Production-injection temperature difference."""
    return float(t_res_c) - float(t_inj_c)


def well_deliverability(df_tg: pd.DataFrame, well: str,
                        drawdown_pa=DRAWDOWN_THERMOGIS_PA) -> dict:
    """Per-well deliverability at P90/P50/P10, our Darcy model vs ThermoGIS.

    Uses ThermoGIS transmissivity (kh) and temperature; returns both our modelled
    flow/power and ThermoGIS's published flow/power for side-by-side reconciliation.
    """
    kh = thermogis_property(df_tg, well, "Transmissivity")
    t = thermogis_property(df_tg, well, "Temperature")
    tg_q = thermogis_property(df_tg, well, "Flow Rate")
    tg_p = thermogis_property(df_tg, well, "Power")

    dt = delta_t_c(t["p50"])
    out = {"well": well, "t_res_c": t["p50"], "t_inj_c": INJECTION_TEMP_C,
           "delta_t_c": round(dt, 1), "drawdown_bar": round(drawdown_pa / 1e5, 1)}
    for p in ("p90", "p50", "p10"):
        q_model = float(darcy_flow_m3h(kh[p], drawdown_pa))
        out[f"kh_dm_{p}"] = kh[p]
        out[f"flow_model_{p}"] = round(q_model, 1)
        out[f"flow_tg_{p}"] = tg_q[p]
        out[f"power_model_{p}"] = round(float(thermal_power_mw(q_model, dt)), 2)
        out[f"power_tg_{p}"] = tg_p[p]
    return out


def deliverability_table(df_tg: pd.DataFrame | None = None,
                         drawdown_pa=DRAWDOWN_THERMOGIS_PA) -> pd.DataFrame:
    """Deliverability + ThermoGIS reconciliation for all four wells."""
    if df_tg is None:
        df_tg = load_thermogis()
    return pd.DataFrame([well_deliverability(df_tg, w, drawdown_pa) for w in WELLS])
