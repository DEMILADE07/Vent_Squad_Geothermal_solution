# SPE Africa Geothermal Datathon 2026 — Utrecht District Geothermal Heating & Cooling

> Placeholder README — to be finalised Day 4 (Mon 1 Jun 2026). The
> current contents document the structure of the working repo; final
> language for the submission lives in `deliverables/Team_<X>_Report_V1.pdf`.

**Team:** _TBD_
**Members + SPE numbers:** _TBD — to be locked end of Day 1_
**Date:** 2026-05-28 → submission 2026-06-04

## What this is

A feasibility study for a **doublet-based geothermal heating-and-cooling
supply** for a Utrecht-region urban district, sized to **≥ 10 MWth
heating** and **≥ 5 MWth cooling**, using the **Lower Permian Rotliegend
sandstone** as the reservoir. Submitted to the SPE Africa Geothermal
Datathon 2026.

The work spans:

- **Challenge 1 (60 %)** — subsurface assessment from four wells (BLT-01,
  EVD-01, JUT-01, PKP-01) plus ThermoGIS P10/P50/P90 envelopes. The resource
  Monte-Carlo uses a **split-lognormal** fit (reproduces ThermoGIS's published
  P90/P50/P10 exactly) with a **physical 300 m³/h pump ceiling** on the
  optimistic tail, and a **Gringarten–Sauty thermal-breakthrough** check
  (`src/reservoir_thermal.py`) that proves the 1.3 km doublet is breakthrough-safe
  over a 30-yr life.
- **Challenge 2 (40 %)** — hybrid surface system (geothermal + ATES +
  electric heat pumps; absorption-chiller contrast) and re-derived LCOE, with an
  **8760-hour dispatch simulation** (`src/dispatch.py`) that derives the load-hours,
  ATES sizing and the geothermal baseload-vs-peak trade instead of assuming them.
- **Economics** — a faithful Python rebuild of the TNO LCOE workbook (gated to
  reproduce the reference to **5.769 €/GJ**), extended to a **time-varying
  (thermal-decline) energy profile** and a **configurable economic life** (the
  asset outlives the 15-yr loan: a 30-yr life lowers heat LCOE ~9 %), plus a
  **probabilistic LCOE** (`src/lcoe_montecarlo.py`) that propagates the bounded
  resource + cost uncertainty to a **P10/P50/P90 distribution and CDF** (heat P50
  11.8 €/GJ; the heavy upper tail is resource risk, the case for staged appraisal),
  and a **value case** (`src/value_case.py`): CO₂ abated (~13 kt/yr), the **SDE++
  subsidy** (~61 €/tCO₂) and equity **NPV/IRR** at a heat tariff — the Dutch
  investment view, not just the cost.
- **Bonus** — runnable AI-assisted pipeline (LAS → Rotliegend summary →
  Monte-Carlo MWth → hybrid LCOE).

The headline hypothesis, locked Day 0: **a 2-well doublet near BLT-01
landing ~150–200 m³/h at 77 °C with ~35 °C ΔT** delivers the 10–13 MWth
heat-only band; cooling comes from ATES + heat pumps.

## How to run

```bash
# 1. clone, create env
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# 2. end-to-end pipeline (CLI, available once WS5.2 lands on Day 3)
python -m src.pipeline ingest  --las-dir data/raw
python -m src.pipeline petro   --in data/processed/well_logs.parquet
python -m src.pipeline predict --in data/processed/rotliegend_summary.csv
python -m src.pipeline lcoe    --in data/processed/mc_mwth.parquet

# 3. or run notebooks top-to-bottom
jupyter lab notebooks/
```

## Repo map

```
.
├── PLAN.md                      # execution plan (Day 0–7)
├── CONTEXT.md                   # raw-data inventory + challenge brief notes
├── README.md
├── requirements.txt
├── data/
│   ├── raw/                     # 4 LAS files (BLT, EVD, JUT, PKP)
│   ├── Lithostratigraphic Data.xlsx
│   ├── Well Path Data.xlsx
│   ├── ThermoGIS Data.xlsx
│   ├── target_lithologies.csv
│   └── processed/               # regenerable: parquets, summaries
├── notebooks/                   # 01_eda → 05_ml_logs
├── src/                         # pipeline.py + library modules
├── tests/                       # pytest for unit conversion + MD→TVD
├── deliverables/                # final PPT, report, video link
├── figures/                     # plots referenced by deck + report
└── LCOE.xlsx                    # original TNO workbook (untouched)
```

## External data

Permitted by the brief; documented per row in
`deliverables/Team_<X>_Report_V1.pdf`. Anticipated sources: ThermoGIS,
DINOloket / NLOG, published NL Rotliegend doublet data (Honselersdijk,
Den Haag, Heemskerk).

## Reproducibility

- All notebooks are required to run **top-to-bottom from a fresh clone**.
- Pipeline regenerates every artefact under `data/processed/` from
  `data/raw/` and `data/*.xlsx`.
- `requirements.txt` pins exact versions; tested on Python 3.12.0,
  Windows 11.
