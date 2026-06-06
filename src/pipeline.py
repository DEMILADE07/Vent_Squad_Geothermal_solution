"""Bonus AI track (WS5.2): the end-to-end feasibility pipeline as one CLI.

This is the part that makes the bonus a *runnable workflow* rather than a
notebook with ``model.fit()`` in it.  Raw LAS in, hybrid LCOE out, in five
deterministic stages that each persist a processed artefact the next stage
consumes:

    python -m src.pipeline ingest     # raw LAS  -> well_logs.parquet (+ targets)
    python -m src.pipeline petro      #           -> rotliegend_summary.csv (+ deliverability)
    python -m src.pipeline predict    #           -> mc_mwth.parquet (Monte-Carlo MWth)
    python -m src.pipeline dispatch   #           -> dispatch_summary.csv (8760-h load-hours)
    python -m src.pipeline ml         #           -> ml_loo_cv.csv + ml_log_predictions.parquet
    python -m src.pipeline lcoe       #           -> LCOE_hybrid.xlsx + lcoe_mc_summary.csv (P10/P50/P90)
    python -m src.pipeline all        # run every stage in order

Every stage is a plain function returning the paths it wrote, so the steps are
unit-testable without the CLI.  The CLI layer (typer + rich) only adds argument
parsing and a readable summary table.  Reproducible from a clean
``pip install -r requirements.txt``.
"""

import logging
import warnings

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from src.build_processed import DELIVERABILITY_CSV, MC_SUMMARY_CSV, TARGET_TVD_CSV
from src.deliverability import deliverability_table
from src.lithostrat import rotliegend_pick
from src.montecarlo import simulate_all, summarise
from src.paths import (
    DATA_PROCESSED,
    DISPATCH_SIZING_CSV,
    DISPATCH_SUMMARY_CSV,
    FIGURES,
    LCOE_HYBRID,
    LCOE_MC_HURDLE_CSV,
    LCOE_MC_SUMMARY_CSV,
    MC_MWTH_PARQUET,
    ML_LOO_CV_CSV,
    ML_PREDICTIONS_PARQUET,
    ROTLIEGEND_SUMMARY_CSV,
    WELL_LOGS_PARQUET,
)
from src.petrophysics import add_petrophysics, rotliegend_summary
from src.targets import build_target_tvd
from src.thermogis import load_thermogis
from src.wells_io import WELLS, coverage_table, load_all

app = typer.Typer(add_completion=False, help=__doc__)
console = Console(width=120)  # stable layout when output is redirected (non-TTY)
log = logging.getLogger("pipeline")


def _rule(title: str) -> None:
    console.rule(f"[bold cyan]{title}")


def _df_table(df: pd.DataFrame, title: str, max_rows: int = 12) -> None:
    """Render a DataFrame as a rich table (truncated for very long frames)."""
    t = Table(title=title, header_style="bold magenta", show_lines=False)
    for col in df.columns:
        t.add_column(str(col), overflow="fold")
    for _, row in df.head(max_rows).iterrows():
        t.add_row(*[f"{v:.3g}" if isinstance(v, float) else str(v) for v in row])
    console.print(t)


def _ensure_out() -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


def _load_logs() -> pd.DataFrame:
    """Load the petrophysics-augmented logs from parquet, rebuilding if absent."""
    if WELL_LOGS_PARQUET.exists():
        return pd.read_parquet(WELL_LOGS_PARQUET)
    log.warning("%s missing; rebuilding from raw", WELL_LOGS_PARQUET.name)
    return add_petrophysics(load_all())


# ---------------------------------------------------------------------------
# Stage functions (importable, return the paths written)
# ---------------------------------------------------------------------------

def stage_ingest() -> dict:
    """Raw LAS -> tidy, unit-harmonised, TVD-referenced logs + recovered targets."""
    _ensure_out()
    logs = add_petrophysics(load_all())
    logs.to_parquet(WELL_LOGS_PARQUET, index=False)
    targets = build_target_tvd()
    targets.to_csv(TARGET_TVD_CSV, index=False)
    cov = coverage_table(logs)[["well", "n_samples", "GR", "DTC", "RHOB", "NPHI", "DTS"]]
    _df_table(cov, "Curve coverage by well (non-null sample counts)")
    console.print(f"[green]wrote[/] {WELL_LOGS_PARQUET.name} ({len(logs):,} rows) "
                  f"and {TARGET_TVD_CSV.name} ({len(targets):,} rows)")
    return {"well_logs": WELL_LOGS_PARQUET, "targets": TARGET_TVD_CSV}


def stage_petro() -> dict:
    """Logs -> per-well Rotliegend net-reservoir summary + Darcy/ThermoGIS reconciliation."""
    _ensure_out()
    logs = _load_logs()
    summary = pd.DataFrame([rotliegend_summary(logs, rotliegend_pick(w)) for w in WELLS])
    summary.to_csv(ROTLIEGEND_SUMMARY_CSV, index=False)
    deliver = deliverability_table(load_thermogis())
    deliver.to_csv(DELIVERABILITY_CSV, index=False)
    _df_table(summary[["well", "gross_tvd_m", "net_tvd_m", "ntg", "phi_mean_net"]],
              "Rotliegend net-reservoir summary")
    console.print(f"[green]wrote[/] {ROTLIEGEND_SUMMARY_CSV.name} and "
                  f"{DELIVERABILITY_CSV.name}")
    return {"summary": ROTLIEGEND_SUMMARY_CSV, "deliverability": DELIVERABILITY_CSV}


def stage_predict(n: int = 10_000) -> dict:
    """ThermoGIS P90/P50/P10 -> Monte-Carlo MWth distribution + scheme summary."""
    _ensure_out()
    tg = load_thermogis()
    mc = simulate_all(tg, n=n, anchor="flow")
    mc.to_parquet(MC_MWTH_PARQUET, index=False)
    mc_sum = pd.concat([
        summarise(mc, 10.0, n_doublets=1),
        summarise(mc[mc["well"] == "BLT-01"], 10.0, n_doublets=2),
    ], ignore_index=True)
    mc_sum.to_csv(MC_SUMMARY_CSV, index=False)
    _df_table(mc_sum, "Monte-Carlo MWth (P(scheme >= 10 MWth))")
    console.print(f"[green]wrote[/] {MC_MWTH_PARQUET.name} ({len(mc):,} draws) and "
                  f"{MC_SUMMARY_CSV.name}")
    return {"mc": MC_MWTH_PARQUET, "mc_summary": MC_SUMMARY_CSV}


def stage_ml() -> dict:
    """Missing-log prediction with leave-one-well-out cross-validation."""
    _ensure_out()
    from src.ml_logs import run_all  # local import; heavy (lightgbm)

    out = run_all(_load_logs())
    out["summary"].to_csv(ML_LOO_CV_CSV, index=False)
    out["predictions"].to_parquet(ML_PREDICTIONS_PARQUET, index=False)
    _df_table(out["summary"][["target", "donor_wells", "recipient_wells",
                              "cross_well_r2", "decision"]],
              "Cross-well log prediction (leave-one-well-out)")
    console.print(f"[green]wrote[/] {ML_LOO_CV_CSV.name} and "
                  f"{ML_PREDICTIONS_PARQUET.name} ({len(out['predictions']):,} filled samples)")
    console.print("[dim]Fallback rule: curves with cross-well R^2 < 0.50 use the "
                  "ThermoGIS deterministic value downstream.[/]")
    return {"cv": ML_LOO_CV_CSV, "predictions": ML_PREDICTIONS_PARQUET}


def stage_dispatch() -> dict:
    """8760-h hourly dispatch -> derived load-hours, ATES sizing, baseload trade."""
    _ensure_out()
    from src.dispatch import (
        lcoe_at_simulated_loadhours,
        plot_dispatch,
        simulate_dispatch,
        sizing_table,
    )

    summary = simulate_dispatch()
    sizing = sizing_table(capacities=(5.05, 6.0, 7.5, 8.5, 10.12))
    lc = lcoe_at_simulated_loadhours()
    pd.DataFrame([{**summary, **lc}]).to_csv(DISPATCH_SUMMARY_CSV, index=False)
    sizing.to_csv(DISPATCH_SIZING_CSV, index=False)
    FIGURES.mkdir(parents=True, exist_ok=True)
    plot_dispatch(save_path=FIGURES / "dispatch_load_duration.png")
    _df_table(sizing, "Geothermal baseload sizing trade (FLEQ rises toward baseload)")
    console.print(f"[green]wrote[/] {DISPATCH_SUMMARY_CSV.name}, {DISPATCH_SIZING_CSV.name}, "
                  "dispatch_load_duration.png")
    console.print(f"[dim]Simulated geo FLEQ {lc['fleq_simulated_h']:.0f} h (peak-sized) vs "
                  f"assumed {lc['fleq_assumed_h']:.0f} h -> heat LCOE "
                  f"{lc['lcoe_heat_simulated']} vs {lc['lcoe_heat_assumed']} EUR/GJ.[/]")
    return {"dispatch": DISPATCH_SUMMARY_CSV, "sizing": DISPATCH_SIZING_CSV}


def stage_lcoe(draws: int = 10_000) -> dict:
    """Resource + design -> hybrid LCOE workbook + probabilistic LCOE distribution.

    Two products: the deterministic extended workbook (LCOE_hybrid.xlsx) and a
    Monte-Carlo LCOE that propagates the bounded resource + cost uncertainty to a
    P10/P50/P90 band (lcoe_mc_summary.csv) and a hurdle-rate scenario table.
    """
    _ensure_out()
    from src.build_lcoe_workbook import build  # local import; heavy (openpyxl styling)
    from src.lcoe_montecarlo import (
        lcoe_scenarios_by_hurdle,
        plot_lcoe_distribution,
        simulate_lcoe,
        summarise_lcoe,
    )

    path = build()
    console.print(f"[green]wrote[/] {LCOE_HYBRID.name}")

    mc = simulate_lcoe(n=draws)
    summary = summarise_lcoe(mc)
    summary.to_csv(LCOE_MC_SUMMARY_CSV, index=False)
    hurdle = lcoe_scenarios_by_hurdle(n=max(draws // 2, 2_000))
    hurdle.to_csv(LCOE_MC_HURDLE_CSV, index=False)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for col in ("lcoe_heat", "lcoe_blended"):
        plot_lcoe_distribution(mc, col, save_path=FIGURES / f"{col}_distribution.png")
    _df_table(summary, "Probabilistic LCOE — P10/P50/P90 (EUR/GJ)")
    console.print(f"[green]wrote[/] {LCOE_MC_SUMMARY_CSV.name}, "
                  f"{LCOE_MC_HURDLE_CSV.name} and lcoe_*_distribution.png")
    return {"lcoe": path, "lcoe_mc": LCOE_MC_SUMMARY_CSV,
            "lcoe_hurdle": LCOE_MC_HURDLE_CSV}


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

@app.command()
def ingest() -> None:
    """Ingest raw LAS files -> well_logs.parquet (+ recovered target lithologies)."""
    _rule("ingest")
    stage_ingest()


@app.command()
def petro() -> None:
    """Petrophysics -> Rotliegend summary (+ Darcy/ThermoGIS deliverability)."""
    _rule("petro")
    stage_petro()


@app.command()
def predict(draws: int = typer.Option(10_000, help="Monte-Carlo draws per well")) -> None:
    """Monte-Carlo MWth from the ThermoGIS P90/P50/P10 deliverability band."""
    _rule("predict (Monte-Carlo MWth)")
    stage_predict(n=draws)


@app.command()
def ml() -> None:
    """Bonus: ML missing-log prediction with honest leave-one-well-out CV."""
    _rule("ml (missing-log prediction)")
    stage_ml()


@app.command()
def dispatch() -> None:
    """8760-h dispatch: derive heat/cool load-hours, ATES sizing, baseload trade."""
    _rule("dispatch (8760-h hourly)")
    stage_dispatch()


@app.command()
def lcoe(draws: int = typer.Option(10_000, help="Probabilistic-LCOE Monte-Carlo draws")) -> None:
    """Hybrid LCOE workbook + probabilistic LCOE (P10/P50/P90, CDF, hurdle scenarios)."""
    _rule("lcoe")
    stage_lcoe(draws=draws)


@app.command()
def all(draws: int = typer.Option(10_000, help="Monte-Carlo draws per well")) -> None:
    """Run the whole pipeline end to end: ingest -> petro -> predict -> ml -> lcoe."""
    _rule("full pipeline")
    stage_ingest()
    stage_petro()
    stage_predict(n=draws)
    stage_dispatch()
    stage_ml()
    stage_lcoe(draws=draws)
    console.print("\n[bold green]Pipeline complete.[/] All artefacts in "
                  f"{DATA_PROCESSED}")


def main() -> None:
    warnings.filterwarnings("ignore")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    app()


if __name__ == "__main__":
    main()
