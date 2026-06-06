"""One command to regenerate EVERY artefact the report, deck and notebooks embed.

    python -m src.build_all

Runs, in order:
  1. build_processed      -> data/processed/*.parquet, *.csv (logs, targets,
                             Rotliegend summary, deliverability, Monte-Carlo MWth)
  2. build_lcoe_workbook  -> data/processed/LCOE_hybrid.xlsx
  3. tornado              -> figures/lcoe_tornado.png
  4. deliverability figs  -> figures/mc_mwth_blt.png, deliverability_reconciliation.png
  5. notebooks (executed) -> notebooks/*.ipynb with fresh outputs + their figures
                             (figures/coverage.png, md_vs_tvd.png, petro_BLT-01.png,
                              ml_*.png, ...)

It is idempotent and reproducible from a fresh clone after
``pip install -r requirements.txt``.  The bonus ML notebook (05) needs LightGBM's
OpenMP backend (libomp); if that is unavailable the notebook step is skipped with a
clear message and the command still completes — every non-ML artefact is produced.

Each generator is run as a module (``runpy``, exactly like ``python -m <mod>``) so
this stays decoupled from the individual modules' function names.
"""

from __future__ import annotations

import runpy
import subprocess
import sys

from src.paths import DATA_PROCESSED, FIGURES, NOTEBOOKS

# (module, human label) run as `python -m <module>` in order.
_GENERATORS = (
    ("src.build_processed", "processed data (logs, targets, summary, deliverability, MC)"),
    ("src.build_lcoe_workbook", "hybrid LCOE workbook"),
    ("src.tornado", "LCOE tornado figure"),
    ("scripts.make_deliverability_figures", "deliverability + Monte-Carlo figures"),
)

# Executed in this order; 05 (ML) is attempted last and skipped cleanly if libomp
# is missing.  03 is the resource/Monte-Carlo notebook (the Challenge-1 verdict).
_NOTEBOOKS = ("01_eda.ipynb", "03_resource_montecarlo.ipynb",
              "04_lcoe.ipynb", "05_ml_logs.ipynb")


def _execute_notebook(name: str) -> bool:
    """Execute one notebook in place (fresh outputs + figures). Returns success."""
    nb = NOTEBOOKS / name
    if not nb.exists():
        print(f"  - {name}: not present, skipping")
        return False
    cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook",
           "--execute", "--inplace", "--ExecutePreprocessor.timeout=900", str(nb)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"  - {name}: executed OK")
        return True
    err = (proc.stderr or "") + (proc.stdout or "")
    if "libomp" in err or "lightgbm" in err.lower():
        print(f"  - {name}: SKIPPED (LightGBM/libomp unavailable — bonus ML only)")
    else:
        tail = err.strip().splitlines()[-1:] or [""]
        print(f"  - {name}: FAILED — {tail[0]}")
    return False


def main() -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    for i, (module, label) in enumerate(_GENERATORS, start=1):
        print(f"\n=== [{i}/5] {label} ===", flush=True)
        runpy.run_module(module, run_name="__main__")

    print("\n=== [5/5] execute notebooks (fresh outputs + figures) ===", flush=True)
    for nb in _NOTEBOOKS:
        _execute_notebook(nb)

    print(f"\nDone. Processed data in {DATA_PROCESSED}, figures in {FIGURES}.")


if __name__ == "__main__":
    main()
