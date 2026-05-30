"""Lithostratigraphic picks per well, TVD-referenced.

Tops/bases in the workbook are along-hole MD in metres (JUT-01's deepest pick
~3409 m matches its LAS MD range, confirming metres even though its LAS is in
feet). We convert each pick to TVD via minimum curvature and flag the
zero-thickness "Fault" / "Reverse fault" rows so they don't masquerade as
intervals.

The Rotliegend reservoir is the **Slochteren Formation**. JUT-01 carries two
Slochteren picks (a shallow anomalous one at ~1659 m and the true reservoir at
3240-3378 m below the Zechstein); ``rotliegend_pick`` returns the deepest, which
is the genuine reservoir.
"""

from __future__ import annotations

import logging

import pandas as pd

from src.mdtvd import md_to_tvd
from src.paths import LITHOSTRAT_XLSX

log = logging.getLogger(__name__)

ROTLIEGEND_UNIT = "Slochteren Formation"
_FAULT_TOKENS = ("fault",)


def load_lithostrat(well: str) -> pd.DataFrame:
    """Return picks with MD and TVD tops/bases and an ``is_fault`` flag."""
    raw = pd.read_excel(LITHOSTRAT_XLSX, sheet_name=well).iloc[:, [0, 2, 3, 4]]
    raw.columns = ["unit", "top_md", "base_md", "anomaly"]
    raw = raw.dropna(subset=["top_md"]).reset_index(drop=True)
    raw["unit"] = raw["unit"].astype(str).str.strip()

    raw["is_fault"] = raw["unit"].str.lower().str.contains("|".join(_FAULT_TOKENS))
    raw["top_tvd"] = md_to_tvd(well, raw["top_md"].to_numpy())
    raw["base_tvd"] = md_to_tvd(well, raw["base_md"].to_numpy())
    raw["thickness_tvd_m"] = raw["base_tvd"] - raw["top_tvd"]
    return raw


def rotliegend_pick(well: str) -> dict:
    """Deepest Slochteren (Rotliegend) interval for ``well``, in MD and TVD."""
    lith = load_lithostrat(well)
    rot = lith[lith["unit"].str.contains("Slochteren", case=False)]
    if rot.empty:
        raise RuntimeError(f"{well}: no Slochteren (Rotliegend) pick found.")
    pick = rot.sort_values("top_md").iloc[-1]  # deepest = true reservoir
    if len(rot) > 1:
        log.warning("%s: %d Slochteren picks; using deepest (top_md=%.1f m).",
                    well, len(rot), pick["top_md"])
    return {
        "well": well,
        "top_md": float(pick["top_md"]),
        "base_md": float(pick["base_md"]),
        "top_tvd": float(pick["top_tvd"]),
        "base_tvd": float(pick["base_tvd"]),
        "thickness_tvd_m": float(pick["thickness_tvd_m"]),
        "n_slochteren_picks": int(len(rot)),
    }
