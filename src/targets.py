"""Recover true vertical depths for ``target_lithologies.csv``.

The shipped file flags every row "AH depth - deviated well needs TVD conversion"
and leaves ``depth_tvd_m`` empty. Investigation (see notebooks/01_eda) shows:

* ``formation_top_tvd`` / ``formation_base_tvd`` actually hold *along-hole MD*
  in each well's native LAS unit (feet for JUT-01, metres otherwise), not TVD.
* Each row is an exact LAS sample inside that MD window, identifiable by its
  ``gamma_ray_api`` matching the LAS GR curve.
* Row order is top->base for BLT-01 / JUT-01 but base->top for EVD-01 / PKP-01
  (those two are logged bottom-up).

So we align each well's CSV GR sequence to its LAS GR (forward or reversed),
recover the exact per-row MD, and convert to TVD with the validated
minimum-curvature model. We then rewrite the depth columns to true TVD, keep
the original MD in explicit ``*_md`` columns, and clear the flag.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.constants import WELLS as WELL_META
from src.mdtvd import md_to_tvd
from src.paths import TARGET_LITHOLOGIES_CSV
from src.units import ensure_metres
from src.wells_io import WELLS, load_well

log = logging.getLogger(__name__)

_MATCH_ATOL = 0.05  # GR units; LAS and CSV agree to better than this.
_HEAD = 8           # samples used for the cheap pre-check before full compare.


def _find_alignment(las_gr: np.ndarray, csv_gr: np.ndarray):
    """Return (start_index, reversed) aligning csv_gr to a slice of las_gr.

    Tries forward order then reversed (bottom-up logged wells). Confirms with a
    full-sequence comparison so repeated GR values cannot cause a false hit.
    """
    n = len(csv_gr)
    for seq, is_rev in ((csv_gr, False), (csv_gr[::-1], True)):
        head = seq[:_HEAD]
        for i in range(len(las_gr) - n + 1):
            if np.allclose(las_gr[i:i + _HEAD], head, atol=_MATCH_ATOL, equal_nan=True):
                if np.allclose(las_gr[i:i + n], seq, atol=_MATCH_ATOL, equal_nan=True):
                    return i, is_rev
    return None, None


def recover_well_depths(well: str) -> pd.DataFrame:
    """Return this well's target rows with recovered ``md_m`` and ``depth_tvd_m``."""
    tl = pd.read_csv(TARGET_LITHOLOGIES_CSV)
    sub = tl[tl.well_id == well].reset_index(drop=True).copy()
    las = load_well(well)

    start, is_rev = _find_alignment(las.GR.to_numpy(float), sub.gamma_ray_api.to_numpy(float))
    if start is None:
        raise RuntimeError(f"{well}: could not align target GR to LAS GR.")

    n = len(sub)
    md_slice = las["md_m"].to_numpy()[start:start + n]
    tvd_slice = las["tvd_m"].to_numpy()[start:start + n]
    if is_rev:  # CSV rows run base->top; flip LAS slice to match CSV order
        md_slice = md_slice[::-1]
        tvd_slice = tvd_slice[::-1]

    sub["md_m"] = md_slice
    sub["depth_tvd_m"] = tvd_slice
    sub.attrs["aligned_reversed"] = bool(is_rev)
    sub.attrs["las_start_index"] = int(start)
    log.info("%s: aligned %d rows to LAS (reversed=%s) at index %d.",
             well, n, is_rev, start)
    return sub


def build_target_tvd() -> pd.DataFrame:
    """Recover depths for all wells, recompute true formation tops, clear flag.

    Output columns of note:
      * ``md_m``                 per-row along-hole depth (m)
      * ``depth_tvd_m``          per-row true vertical depth (m), now populated
      * ``formation_top_md`` / ``formation_base_md``   original AH window (m)
      * ``formation_top_tvd`` / ``formation_base_tvd`` corrected to true TVD
      * ``formation_thickness_m`` recomputed as true vertical thickness
      * ``flag`` / ``flag_reason`` cleared to ``ok`` / resolution note
    """
    out = []
    for well in WELLS:
        sub = recover_well_depths(well)
        unit = WELL_META[well].las_unit
        top_md_m, _ = ensure_metres([sub["formation_top_tvd"].iloc[0]], unit)
        base_md_m, _ = ensure_metres([sub["formation_base_tvd"].iloc[0]], unit)

        sub["formation_top_md"] = top_md_m[0]
        sub["formation_base_md"] = base_md_m[0]
        top_tvd = float(md_to_tvd(well, top_md_m)[0])
        base_tvd = float(md_to_tvd(well, base_md_m)[0])
        sub["formation_top_tvd"] = top_tvd
        sub["formation_base_tvd"] = base_tvd
        sub["formation_thickness_m"] = base_tvd - top_tvd

        sub["flag"] = "ok"
        sub["flag_reason"] = (
            f"TVD recovered via minimum-curvature MD->TVD "
            f"(AH window {top_md_m[0]:.1f}-{base_md_m[0]:.1f} m)"
        )
        out.append(sub)

    df = pd.concat(out, ignore_index=True)
    cols = ["well_id", "easting", "northing", "md_m", "depth_tvd_m",
            "porosity_pct", "gamma_ray_api", "bulk_density_gcc",
            "formation_top_md", "formation_base_md",
            "formation_top_tvd", "formation_base_tvd", "formation_thickness_m",
            "distance_to_usp_km", "flag", "flag_reason"]
    return df[cols]
