"""Domain constants — wells, fluid properties, reservoir cutoffs.

Sources:
- Well surface coordinates (RD New EPSG:28992) and ThermoGIS P10/P50/P90 from
  data/ThermoGIS Data.xlsx (per-sheet headers).
- BHT from BLT-01 LAS header (167 degF at TD ~2124 m).
- Fluid properties from standard NL Rotliegend doublet literature.
- Petrophysical cutoffs are conventional NL Rotliegend reservoir limits.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Well metadata
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Well:
    name: str
    x_rd: float  # easting,  RD New EPSG:28992 (m)
    y_rd: float  # northing, RD New EPSG:28992 (m)
    top_rotliegend_m: float
    thickness_p10_m: float
    thickness_p50_m: float
    thickness_p90_m: float
    porosity_pct_p50: float
    permeability_md_p50: float
    transmissivity_dm_p50: float
    temperature_c_p50: float
    las_unit: str  # "M" or "F" — JUT-01 is feet


WELLS: dict[str, Well] = {
    "BLT-01": Well("BLT-01", 141_577, 456_881, 1837, 110, 130, 150, 17.0, 82.0, 9.3, 77.0, "M"),
    "EVD-01": Well("EVD-01", 136_997, 441_189, 1723,  60,  76,  92,  9.0,  6.0, 0.4, 72.0, "M"),
    "JUT-01": Well("JUT-01", 134_098, 451_726, 1776, 105, 125, 145, 11.0, 40.0, 4.8, 72.0, "F"),
    "PKP-01": Well("PKP-01", 118_503, 453_402, 2255,  45,  60,  75,  9.0,  1.0, 0.1, 88.0, "M"),
}


# ---------------------------------------------------------------------------
# Petrophysical cutoffs (NL Rotliegend convention)
# ---------------------------------------------------------------------------

VSHALE_CUTOFF = 0.40
POROSITY_CUTOFF = 0.08

RHO_MATRIX_SANDSTONE = 2.65  # g/cc
RHO_FLUID = 1.00             # g/cc
DT_MATRIX_SANDSTONE = 55.5   # us/ft (Wyllie sandstone)
DT_FLUID = 189.0             # us/ft

LAS_NULL = -999.25
FEET_PER_METRE = 3.280839895


# ---------------------------------------------------------------------------
# Fluid / thermal properties at reservoir conditions (~77 degC, brine)
# ---------------------------------------------------------------------------

WATER_DENSITY_KG_M3 = 1000.0     # close enough at this T and salinity
WATER_HEAT_CAPACITY_J_KGK = 4180.0
WATER_VISCOSITY_PA_S = 3.5e-4    # ~77 degC, fresh-ish brine

# Rock matrix thermal properties (TNO Input_Output!K7,K8 — Rho_rock, Cp_rock).
# Used for the bulk volumetric heat capacity that retards the thermal front.
ROCK_DENSITY_KG_M3 = 2700.0
ROCK_HEAT_CAPACITY_J_KGK = 1000.0
SECONDS_PER_YEAR = 31_557_600.0  # 365.25 d, matches TNO Input_Output!K20


# ---------------------------------------------------------------------------
# Doublet design defaults (NL Rotliegend precedent)
# ---------------------------------------------------------------------------

DOUBLET_SPACING_M = 1300.0
WELLBORE_RADIUS_M = 0.108         # 8.5" hole approx
DRAWDOWN_PA = 5.0e6               # 50 bar nominal (aggressive sensitivity case)

# Calibrated against ThermoGIS: their published Flow Rate P50 is reproduced by
# the Darcy doublet model (this file's mu, spacing, rw) at ~16.5 bar drawdown,
# consistent across BLT-01 and JUT-01. We adopt this as the reconciled baseline.
DRAWDOWN_THERMOGIS_PA = 1.65e6    # ~16.5 bar — ThermoGIS-equivalent doublet

# ThermoGIS Power = rho*cp*Q*dT back-solves to an injection temperature of ~35 C
# (dT 42 C at BLT-01 T=77; ~37 C at the T=72 wells). This is the ThermoGIS
# standard reinjection temperature; we adopt it for the headline thermal calc.
INJECTION_TEMP_C = 35.0
DELTA_T_DEFAULTS_C = (30.0, 35.0, 40.0)
RETURN_TEMP_DEFAULT_C = 42.0      # legacy DT=35 sensitivity anchor


# ---------------------------------------------------------------------------
# Surface design defaults
# ---------------------------------------------------------------------------

# Surface-equipment performance. Sources are cited in the report's external-data
# appendix; values are the conservative end of each published range, not the best case.
HEAT_PUMP_COP = 4.2                  # electric HP, ~70 C delivery (IEA HPT Annex 47)
ABSORPTION_CHILLER_COP_TH = 0.7      # single-effect LiBr/H2O thermal COP (ASHRAE)
ABSORPTION_DRIVE_TEMP_MIN_C = 85.0   # single-effect needs ~85-95 C drive heat;
ABSORPTION_DRIVE_TEMP_MAX_C = 95.0   # our 77 C resource is below this -> Design B knock
ATES_ROUND_TRIP_EFFICIENCY = 0.70    # seasonal recovery efficiency (Fleuchaus 2018)

# ATES cooling capacity per warm/cold well pair (MWth). NL field range ~0.5-2.0;
# we model it triangular(min, mode, max) and size the pair count off the low end
# rather than the midpoint (Bloemendal & Hartog 2018; Fleuchaus et al. 2018).
ATES_THROUGHPUT_MIN_MWTH_PER_PAIR = 0.5
ATES_THROUGHPUT_MODE_MWTH_PER_PAIR = 1.0
ATES_THROUGHPUT_MAX_MWTH_PER_PAIR = 2.0
ATES_THROUGHPUT_MWTH_PER_PAIR = ATES_THROUGHPUT_MODE_MWTH_PER_PAIR  # conservative central

DEMAND_HEATING_MWTH = 10.0
DEMAND_COOLING_MWTH = 5.0
