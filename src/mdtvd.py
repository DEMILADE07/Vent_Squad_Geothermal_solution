"""Measured-depth -> true-vertical-depth conversion via minimum curvature.

The well-path workbook already carries a ``TVD (m)`` column at every survey
station, so this module does two things:

1. Recompute station TVD (and N/E offsets) from inclination/azimuth with the
   minimum-curvature method, and *validate* it against the supplied TVD. A
   large mismatch means either our maths or the source data is wrong, and we
   want to know before building anything on top of it.
2. Expose ``md_to_tvd(well, md)`` — a monotonic interpolator that maps arbitrary
   log/pick measured depths onto the minimum-curvature TVD profile. Between
   stations this is piecewise-linear in TVD vs MD, which is exact for the
   straight-segment idealisation and more than adequate given station spacing.
   Beyond the deepest station we extrapolate along the terminal inclination.

EVD-01 has only ~21 stations and is near-vertical; the interpolation degrades
gracefully to essentially linear there, and we log a note when a well is sparse.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.paths import WELLPATH_XLSX

log = logging.getLogger(__name__)

# Below this station count we flag the survey as sparse (interpolation coarse).
SPARSE_SURVEY_THRESHOLD = 25
# TVD validation tolerance: recomputed vs supplied station TVD (metres).
TVD_VALIDATION_TOL_M = 1.0


@dataclass(frozen=True)
class Survey:
    well: str
    md: np.ndarray          # measured depth along hole (m), ascending
    incl_deg: np.ndarray
    azi_deg: np.ndarray
    tvd_provided: np.ndarray
    x_off: np.ndarray
    y_off: np.ndarray

    @property
    def is_sparse(self) -> bool:
        return len(self.md) < SPARSE_SURVEY_THRESHOLD


def load_survey(well: str) -> Survey:
    """Load one well's deviation survey, columns indexed positionally to dodge
    the mangled degree-symbol headers in the source workbook.

    Column order: Depth(m), Inclination(deg), Azimuth(deg), TVD(m),
    X-offset(m), Y-offset(m).
    """
    df = pd.read_excel(WELLPATH_XLSX, sheet_name=well)
    df = df.iloc[:, :6]
    df.columns = ["md", "incl_deg", "azi_deg", "tvd", "x_off", "y_off"]
    df = df.dropna(subset=["md"]).sort_values("md").reset_index(drop=True)
    return Survey(
        well=well,
        md=df["md"].to_numpy(float),
        incl_deg=df["incl_deg"].to_numpy(float),
        azi_deg=df["azi_deg"].to_numpy(float),
        tvd_provided=df["tvd"].to_numpy(float),
        x_off=df["x_off"].to_numpy(float),
        y_off=df["y_off"].to_numpy(float),
    )


def minimum_curvature(
    md: np.ndarray, incl_deg: np.ndarray, azi_deg: np.ndarray
) -> dict[str, np.ndarray]:
    """Minimum-curvature integration of a survey.

    Returns cumulative ``tvd``, ``north`` and ``east`` (m) at each station,
    referenced so the first station sits at (tvd=md[0], north=0, east=0).
    """
    md = np.asarray(md, float)
    inc = np.radians(np.asarray(incl_deg, float))
    azi = np.radians(np.asarray(azi_deg, float))

    d_md = np.diff(md)
    i1, i2 = inc[:-1], inc[1:]
    a1, a2 = azi[:-1], azi[1:]

    # Dogleg angle between successive stations.
    cos_beta = np.cos(i2 - i1) - np.sin(i1) * np.sin(i2) * (1.0 - np.cos(a2 - a1))
    cos_beta = np.clip(cos_beta, -1.0, 1.0)
    beta = np.arccos(cos_beta)

    # Ratio factor (2/beta)*tan(beta/2), -> 1 as beta -> 0. Guard small angles.
    with np.errstate(divide="ignore", invalid="ignore"):
        rf = np.where(beta > 1e-9, (2.0 / beta) * np.tan(beta / 2.0), 1.0)

    d_tvd = 0.5 * d_md * (np.cos(i1) + np.cos(i2)) * rf
    d_north = 0.5 * d_md * (np.sin(i1) * np.cos(a1) + np.sin(i2) * np.cos(a2)) * rf
    d_east = 0.5 * d_md * (np.sin(i1) * np.sin(a1) + np.sin(i2) * np.sin(a2)) * rf

    tvd = np.concatenate([[md[0]], md[0] + np.cumsum(d_tvd)])
    north = np.concatenate([[0.0], np.cumsum(d_north)])
    east = np.concatenate([[0.0], np.cumsum(d_east)])
    return {"tvd": tvd, "north": north, "east": east}


def validate_survey(well: str) -> dict[str, float]:
    """Compare recomputed minimum-curvature TVD against the workbook's TVD.

    Returns a small report; logs a warning if the mismatch exceeds tolerance.
    """
    s = load_survey(well)
    mc = minimum_curvature(s.md, s.incl_deg, s.azi_deg)
    resid = mc["tvd"] - s.tvd_provided
    max_abs = float(np.nanmax(np.abs(resid)))
    report = {
        "well": well,
        "n_stations": len(s.md),
        "max_abs_resid_m": max_abs,
        "rms_resid_m": float(np.sqrt(np.nanmean(resid**2))),
        "max_inclination_deg": float(np.nanmax(s.incl_deg)),
        "md_max_m": float(s.md.max()),
        "tvd_max_m": float(mc["tvd"].max()),
    }
    if max_abs > TVD_VALIDATION_TOL_M:
        log.warning(
            "%s: minimum-curvature TVD differs from workbook TVD by up to "
            "%.2f m (tol %.1f m).", well, max_abs, TVD_VALIDATION_TOL_M
        )
    if s.is_sparse:
        log.warning(
            "%s: sparse survey (%d stations); MD->TVD interpolation is coarse, "
            "falling back to effectively piecewise-linear.", well, len(s.md)
        )
    return report


def md_to_tvd(well: str, md_query) -> np.ndarray:
    """Map measured depths to TVD along ``well``'s minimum-curvature profile.

    Piecewise-linear in TVD-vs-MD between stations; beyond the deepest station
    we extrapolate along the terminal inclination (so deep log tails that run
    past the last survey point stay physical rather than clamping flat).
    """
    s = load_survey(well)
    mc = minimum_curvature(s.md, s.incl_deg, s.azi_deg)
    md_q = np.asarray(md_query, float)

    tvd = np.interp(md_q, s.md, mc["tvd"])  # clamps outside range

    # Linear extrapolation past the deepest station using terminal inclination.
    deepest = s.md[-1]
    beyond = md_q > deepest
    if np.any(beyond):
        cos_i_term = np.cos(np.radians(s.incl_deg[-1]))
        tvd = tvd.copy()
        tvd[beyond] = mc["tvd"][-1] + (md_q[beyond] - deepest) * cos_i_term
    return tvd
