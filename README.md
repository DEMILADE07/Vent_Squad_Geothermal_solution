# Utrecht District Geothermal Heating & Cooling — A Hybrid Doublet Feasibility Study

**SPE Africa Geothermal Datathon 2026**

**Team Vent Squad**

| Member | Role | SPE membership |
|--------|------|----------------|
| Demilade Kolawole-Jacobs (Team Lead) | Geoscience & integration | `SPE #: ____` |
| Fikayo | ML workflow | `SPE #: ____` |
| Ashinze | Simulation & economics | `SPE #: ____` |
| Ayomide | Geoscience QA | `SPE #: ____` |
| Sodiq | Benchmarks & economic inputs | `SPE #: ____` |

> SPE membership numbers are filled in on the deck title slide and report title
> page before submission.

## Problem statement

We were asked whether a **Rotliegend (Slochteren sandstone) geothermal scheme** can
supply a mixed urban district in the **Utrecht region** with **≥ 10 MWth of
heating and ≥ 5 MWth of cooling**, and what it would cost. We answer it end to end:
we characterise the resource from four wells, decide whether it meets the demand
(Challenge 1), design the surface system that delivers both heating and cooling
(Challenge 2), and re-derive the levelised cost of energy for the hybrid scheme.

## What we conclude (headline)

- **BLT-01 is the anchor well** — the thickest, most porous and most permeable of
  the four; our own petrophysics, computed independently from the logs, agrees with
  ThermoGIS at the anchor (NTG 0.93 vs 0.98) and is deliberately stricter at the
  weaker wells.
- The resource is **real but modest at 77 °C**. As a probabilistic distribution
  (split-lognormal fit, optimistic tail bounded at a 300 m³/h pump ceiling), one
  doublet is **P50 5.05 MWth (29 % chance of clearing 10)**, so we size a
  **two-doublet (four-well) scheme** — two *independent* doublets reach **P50
  13.2 MWth with a 62 % probability of clearing 10 MWth**. Thermal breakthrough at
  1.3 km spacing is **~177 yr away** (Gringarten-Sauty), so the deliverability holds
  over field life.
- **Cooling** is delivered by **seasonal ATES + an electric heat pump**, sized
  probabilistically (**6 well pairs → 99.8 % chance of meeting 5 MWth**), and shown
  to beat an absorption-chiller alternative on keeping saleable heat and on the
  physics of 77 °C driving heat.
- The economics are **benchmarked to the TNO LCOE workbook** (reproduced to
  5.769 €/GJ): heat **11.8 / cooling 23.0 / blended 13.4 €/GJ**, **≈ €21.3 M** capex.
  Reported as a **distribution** (heat P10/P50/P90 ≈ 10.8 / 12.6 / 26.7 €/GJ) and
  taken through to a **Dutch SDE++ value case** — ~13 kt CO₂/yr abated, ~€63/tCO₂
  subsidy, **equity IRR ≈ 21 %**. An 8,760-hour dispatch simulation *derives* the
  load-hours rather than assuming them.

All headline numbers come from the code in `src/` and are reproducible from a
fresh clone — see below. The full argument, assumptions and citations are in
[`deliverables/Vent_Squad_Report.md`](deliverables/Vent_Squad_Report.md).

## How to run

```bash
# 1. Create the environment (Python 3.9–3.12)
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (PowerShell / cmd)
pip install -r requirements.txt

# 2. Prove it works (the bonus-ML tests self-skip if libomp is absent)
pytest -q

# 3. Regenerate EVERYTHING the report and deck use, in one command
#    (processed data + figures + LCOE workbook + executed notebooks)
python -m src.build_all

# --- or run the pieces individually ---
python -m src.pipeline all          # ingest → petro → predict → dispatch → ml → lcoe (CLI)
python -m src.pipeline dispatch     # 8760-h dispatch → derived load-hours, sizing
python -m src.pipeline lcoe         # LCOE workbook + probabilistic LCOE + SDE++ value case
python -m src.build_processed       # just the processed data
python -m src.build_lcoe_workbook   # just data/processed/LCOE_hybrid.xlsx
python -m src.tornado               # just figures/lcoe_tornado.png
jupyter lab notebooks/              # explore the analysis notebooks
```

> **Bonus ML note:** the missing-log prediction (`src/ml_logs.py`, notebook
> `05_ml_logs.ipynb`) uses LightGBM, whose compiled backend needs the OpenMP
> runtime. On a fresh machine install it once — macOS `brew install libomp`,
> Debian/Ubuntu `sudo apt-get install libgomp1`. Everything else runs without it.

## Repo map

```
.
├── README.md                    # this file
├── PROJECT_WALKTHROUGH.md       # plain-English companion to the report, for evaluators
├── requirements.txt             # pinned, cross-platform dependencies
├── LCOE.xlsx                    # original TNO workbook (reference, untouched)
├── data/
│   ├── raw/                     # 4 LAS well logs (BLT, EVD, JUT, PKP)
│   ├── *.xlsx                   # lithostratigraphy, well paths, ThermoGIS
│   ├── target_lithologies.csv
│   └── processed/               # regenerable: parquet, csv, LCOE_hybrid.xlsx
├── notebooks/                   # 01_eda · 03_resource_montecarlo · 04_lcoe · 05_ml_logs
├── src/                         # library modules + pipeline.py + build_all.py
│                                #   (incl. dispatch, lcoe_montecarlo, reservoir_thermal, value_case)
├── scripts/                     # figure generator (make_deliverability_figures)
├── tests/                       # pytest (units, MD→TVD, deliverability, LCOE, dispatch, value case, ML)
├── figures/                     # rendered figures the report and deck embed (tracked)
└── deliverables/                # technical report + slide deck
```

## Methodology summary

1. **Data foundation** — load LAS, harmonise units (JUT-01 is in feet), convert
   measured depth → true vertical depth with minimum curvature (matched to the
   survey to < 1 cm), recover the mis-shipped `target_lithologies.csv` depths.
2. **Petrophysics** — Larionov (older-rock) shale volume, density porosity, net
   reservoir at the standard NL Rotliegend cut-offs; per-well Rotliegend summary.
3. **Resource** — Darcy radial-inflow doublet deliverability reconciled to the
   ThermoGIS published flow/power, then a Monte-Carlo MWth distribution (split-lognormal
   fit, pump-capped tail, independent doublets) reported against the 10 MWth demand,
   with a Gringarten-Sauty **thermal-breakthrough** check (`src/reservoir_thermal.py`).
4. **Surface design** — two designs (ATES + heat pump vs absorption chiller) sized to
   the heating *and* cooling demand; an **8,760-hour dispatch** simulation
   (`src/dispatch.py`) derives the load-hours and ATES sizing instead of assuming them.
5. **Economics** — a faithful Python rebuild of the TNO LCOE workbook (validated to its
   published reference), extended to the hybrid case, with a sensitivity tornado, a
   **probabilistic LCOE** distribution (`src/lcoe_montecarlo.py`), and a Dutch **SDE++
   value case** — CO₂ abatement, subsidy-per-tonne and equity NPV/IRR (`src/value_case.py`).
6. **Bonus AI workflow** — an end-to-end CLI pipeline (`src/pipeline.py`) plus an honest
   leave-one-well-out ML log-prediction with a documented fallback rule.

## Reproducibility

- The four LAS files, three Excel sheets and the target CSV are committed, so every
  processed artefact regenerates from `data/raw/` via `python -m src.build_all`.
- `requirements.txt` pins exact versions and installs on Windows, macOS (Apple
  Silicon) and Linux.
- `pytest -q` runs the full suite from a clean clone; the figures the report and
  deck embed are tracked under `figures/`.

## Use of AI tools & references

Per the datathon guidelines, we disclose that AI assistants were used as a tool — to
brainstorm, refine ideas, and speed up specified engineering directives. All analysis,
assumptions, and design decisions were made and validated by the team, and every
number is reproducible from our code (`python -m src.build_all`).

External sources are attributed in full in the report (Section 10). Key references: ThermoGIS /
DINOloket / NLOG (TNO); the TNO LCOE workbook (van Wees et al., 2012); Larionov (1969)
and Wyllie et al. (1956) for petrophysics; Gringarten & Sauty (1975) for thermal
breakthrough; Fleuchaus et al. (2018) and Bloemendal & Hartog (2018) for ATES; ASHRAE
and IEA HPT for surface-equipment performance.
