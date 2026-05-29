"""Load, clean, unit-harmonise and TVD-reference the four LAS files.

Cleaning is two-stage:

1. ``-999.25`` nulls (lasio already maps the declared NULL to NaN on read).
2. Physical-range gating — JUT-01 in particular carries spike values in the
   millions on DT/RHOB that are not the null sentinel; anything outside a
   plausible petrophysical range is set to NaN and counted.

Depths are converted to metres once (JUT-01 is in feet) via ``units.ensure_metres``
and every sample is given a true-vertical depth from ``mdtvd.md_to_tvd``. EVD-01
and PKP-01 are logged bottom-up (negative STEP); we sort ascending on MD.
"""

from __future__ import annotations

import logging

import lasio
import numpy as np
import pandas as pd

from src.mdtvd import md_to_tvd
from src.paths import DATA_RAW
from src.units import ensure_metres

log = logging.getLogger(__name__)

WELLS = ["BLT-01", "EVD-01", "JUT-01", "PKP-01"]

# Standard output columns (missing curves stay NaN per well).
STANDARD_CURVES = ["GR", "DTC", "DTS", "RHOB", "NPHI", "DRHO", "PE", "RD", "RM", "RS", "CALI"]

# Map each well's raw mnemonics to the standard names above.
_RENAME = {
    "DT": "DTC",      # compressional sonic on EVD/JUT/PKP is named DT
    "DTC": "DTC",
}

# Physically plausible ranges; values outside -> NaN. Wide enough to keep real
# washout/unconsolidated readings, tight enough to kill JUT-01's spike garbage.
PHYSICAL_RANGES = {
    "GR": (0.0, 400.0),
    "DTC": (30.0, 500.0),
    "DTS": (50.0, 800.0),
    "RHOB": (1.0, 3.5),
    "NPHI": (-0.15, 1.0),
    "DRHO": (-1.0, 1.0),
    "PE": (0.0, 30.0),
    "RD": (0.01, 1e5),
    "RM": (0.01, 1e5),
    "RS": (0.01, 1e5),
    "CALI": (0.0, 40.0),
}


def _depth_unit(las: lasio.LASFile) -> str:
    """Unit string of the depth index curve."""
    return las.curves[0].unit or las.well.STRT.unit or "m"


def load_well(well: str, gate_ranges: bool = True) -> pd.DataFrame:
    """Return one well's logs as a tidy, ascending, TVD-referenced frame.

    Columns: ``well, md_m, tvd_m`` + the STANDARD_CURVES present (others NaN).
    Also returns sentinel-free physical curves and a per-curve gate count via
    the ``.attrs['gated']`` dict for QC reporting.
    """
    las = lasio.read(DATA_RAW / f"{well}.las")
    raw = las.df()  # indexed by the depth curve, NULLs already NaN

    # Depth index -> metres (JUT-01 is feet). Index name varies (MD/DEPT/DEPT:1).
    md_m, _ = ensure_metres(raw.index.to_numpy(float), _depth_unit(las))
    out = pd.DataFrame({"md_m": md_m})

    # Pull standard curves where the raw mnemonic (after rename) matches.
    for mnem in raw.columns:
        std = _RENAME.get(mnem, mnem)
        if std in STANDARD_CURVES and std not in out:
            out[std] = raw[mnem].to_numpy(float)

    out = out.sort_values("md_m").reset_index(drop=True)

    # Physical-range gating.
    gated: dict[str, int] = {}
    if gate_ranges:
        for col, (lo, hi) in PHYSICAL_RANGES.items():
            if col in out:
                mask = (out[col] < lo) | (out[col] > hi)
                n = int(mask.sum())
                if n:
                    out.loc[mask, col] = np.nan
                    gated[col] = n

    out.insert(0, "well", well)
    out.insert(2, "tvd_m", md_to_tvd(well, out["md_m"].to_numpy()))

    # Ensure all standard columns exist (NaN if the well lacks the curve).
    for c in STANDARD_CURVES:
        if c not in out:
            out[c] = np.nan
    out = out[["well", "md_m", "tvd_m", *STANDARD_CURVES]]

    out.attrs["gated"] = gated
    if gated:
        log.info("%s: range-gated samples -> NaN: %s", well, gated)
    return out


def load_all(gate_ranges: bool = True) -> pd.DataFrame:
    """Concatenate all four wells into one tidy frame."""
    return pd.concat(
        [load_well(w, gate_ranges=gate_ranges) for w in WELLS], ignore_index=True
    )


def coverage_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-well non-null sample counts for each standard curve, plus depth span."""
    rows = []
    for well, g in df.groupby("well", sort=False):
        row = {"well": well, "n_samples": len(g),
               "md_min_m": g["md_m"].min(), "md_max_m": g["md_m"].max(),
               "tvd_max_m": g["tvd_m"].max()}
        for c in STANDARD_CURVES:
            row[c] = int(g[c].notna().sum())
        rows.append(row)
    return pd.DataFrame(rows)
