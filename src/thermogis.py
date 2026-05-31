"""Loader for the ThermoGIS workbook (one sheet per well).

Each sheet carries a small fixed table: surface (x, Y) and a property block with
P90/P50/P10 columns. The value-column *header* in some sheets is mislabelled
(e.g. the BLT-01 sheet header reads "PKP-01"), so we key strictly off the sheet
name and the (x, Y) row — never the header cell.

Returns a tidy frame: one row per (well, property) with unit + P90/P50/P10.
ThermoGIS already publishes Flow Rate and Power as a P-distribution; those rows
are the authoritative deliverability baseline that src/deliverability.py
reconciles its Darcy model against.
"""

from __future__ import annotations

import pandas as pd

from src.paths import THERMOGIS_XLSX

# Property labels as they appear in column 0 of each sheet's property block.
_PROPERTY_ROW = "Property"


def load_thermogis(path=THERMOGIS_XLSX) -> pd.DataFrame:
    """Parse every well sheet into a tidy P10/P50/P90 frame.

    Columns: ``well, property, unit, p90, p50, p10`` (plus ``x``, ``y`` repeated
    per row for convenience). Numeric columns are floats.
    """
    xl = pd.ExcelFile(path)
    frames = []
    for sheet in xl.sheet_names:
        raw = xl.parse(sheet, header=None)
        frames.append(_parse_sheet(sheet, raw))
    return pd.concat(frames, ignore_index=True)


def _parse_sheet(well: str, raw: pd.DataFrame) -> pd.DataFrame:
    col0 = raw[0].astype("string").str.strip()

    x = float(raw.loc[col0 == "x", 1].iloc[0])
    y = float(raw.loc[col0.isin(["Y", "y"]), 1].iloc[0])

    hdr = raw.index[col0 == _PROPERTY_ROW]
    if len(hdr) == 0:
        raise ValueError(f"{well}: no 'Property' header row found")
    body = raw.loc[hdr[0] + 1:].copy()

    out = pd.DataFrame({
        "well": well,
        "property": body[0].astype("string").str.strip(),
        "unit": body[1].astype("string").str.strip(),
        "p90": pd.to_numeric(body[2], errors="coerce"),
        "p50": pd.to_numeric(body[3], errors="coerce"),
        "p10": pd.to_numeric(body[4], errors="coerce"),
        "x": x,
        "y": y,
    })
    return out.dropna(subset=["property"]).reset_index(drop=True)


def thermogis_property(df: pd.DataFrame, well: str, prop: str) -> dict:
    """Return {'unit','p90','p50','p10'} for one (well, property)."""
    row = df[(df["well"] == well) & (df["property"] == prop)]
    if row.empty:
        raise KeyError(f"{well}/{prop} not in ThermoGIS frame")
    r = row.iloc[0]
    return {"unit": r["unit"], "p90": r["p90"], "p50": r["p50"], "p10": r["p10"]}
