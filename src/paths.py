"""Project paths, derived from this file's location so they survive any CWD."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
DATA_RAW = DATA / "raw"
DATA_PROCESSED = DATA / "processed"

NOTEBOOKS = ROOT / "notebooks"
DELIVERABLES = ROOT / "deliverables"
FIGURES = ROOT / "figures"
TESTS = ROOT / "tests"

LITHOSTRAT_XLSX = DATA / "Lithostratigraphic Data.xlsx"
WELLPATH_XLSX = DATA / "Well Path Data.xlsx"
THERMOGIS_XLSX = DATA / "ThermoGIS Data.xlsx"
TARGET_LITHOLOGIES_CSV = DATA / "target_lithologies.csv"

LCOE_ORIGINAL = ROOT / "LCOE.xlsx"
LCOE_HYBRID = DATA_PROCESSED / "LCOE_hybrid.xlsx"

WELL_LOGS_PARQUET = DATA_PROCESSED / "well_logs.parquet"
ROTLIEGEND_SUMMARY_CSV = DATA_PROCESSED / "rotliegend_summary.csv"
MC_MWTH_PARQUET = DATA_PROCESSED / "mc_mwth.parquet"
