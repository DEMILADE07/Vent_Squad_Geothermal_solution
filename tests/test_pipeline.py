"""End-to-end pipeline CLI: command surface + a light stage smoke test."""

import warnings

import typer

from src import pipeline
from src.build_processed import MC_SUMMARY_CSV
from src.paths import MC_MWTH_PARQUET

warnings.filterwarnings("ignore")

EXPECTED_COMMANDS = {"ingest", "petro", "predict", "dispatch", "ml", "lcoe", "all"}


def test_cli_exposes_all_stages():
    cmd = typer.main.get_command(pipeline.app)
    assert set(cmd.commands) == EXPECTED_COMMANDS


def test_stage_functions_are_importable():
    for name in ("stage_ingest", "stage_petro", "stage_predict", "stage_dispatch",
                 "stage_ml", "stage_lcoe"):
        assert callable(getattr(pipeline, name))


def test_predict_stage_writes_montecarlo():
    """A small Monte-Carlo run must persist both the draws and the scheme summary."""
    out = pipeline.stage_predict(n=500)
    assert out["mc"] == MC_MWTH_PARQUET and MC_MWTH_PARQUET.exists()
    assert out["mc_summary"] == MC_SUMMARY_CSV and MC_SUMMARY_CSV.exists()
