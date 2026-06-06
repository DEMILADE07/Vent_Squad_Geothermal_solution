# CHECKPOINT — 2026-06-06 (LCOE + simulation hardening, branch `shinzii`)

> World-class pass on the resource Monte-Carlo and the LCOE engine. The TNO
> `5.769049 €/GJ` reference gate stays green throughout; all 58 tests pass.

**What changed**
1. **Bounded resource tails** (`src/montecarlo.py`). New `fit_split_lognormal`
   (two-piece) reproduces ThermoGIS's published P90/P50/P10 *exactly* — the old
   single-sigma fit overshot BLT-01's published flow P10 (551 vs 469 m³/h),
   inflating the optimistic resource. A `MAX_SUSTAINABLE_FLOW_M3H = 300` pump/sand
   ceiling then de-rates the tail. Effect: single-doublet optimistic P10
   26.9 → 14.6 MWth, mean 11.7 → 6.6; **P50 and P(≥10)=50 % unchanged**.
2. **Thermal breakthrough** (`src/reservoir_thermal.py`, new). Gringarten-Sauty
   doublet breakthrough + produced-temperature decline. At 1.3 km spacing
   t_bt ≈ 155 yr ≫ 30-yr life → breakthrough-safe, constant-MWth *validated*. The
   "thermal breakthrough" risk is now a number, not a footnote.
3. **Time-varying + longer-life LCOE** (`src/lcoe.py`). `financed_lcoe` /
   `heat_economics` accept a per-year MWth profile and a `lifetime_yr` override; a
   flat profile still reproduces 5.769. A 30-yr economic life (loan still 15 yr)
   lowers heat LCOE 11.7 → 10.6 €/GJ.
4. **Probabilistic LCOE** (`src/lcoe_montecarlo.py`, new). Propagates the bounded
   2-doublet resource MC *and* cost/market uncertainty (drilling, load-hours,
   electricity, ATES — triangular, anchored to the tornado bounds) through the
   financed model to an LCOE distribution: heat **P10/P50/P90 = 6.3 / 11.8 / 56.7
   €/GJ**, P(≤15)=0.59. The P50 matches the deterministic point estimate; the heavy
   upper tail is resource downside (not cost), the quantified case for staged
   appraisal. Wired into `pipeline.py lcoe` (writes `lcoe_mc_summary.csv`,
   `lcoe_mc_by_hurdle.csv`, `figures/lcoe_*_distribution.png`).
5. Docs updated (README, technical report §3.4/§5/§6). Tests: **64 pass** (+12 this
   branch); TNO `5.769049` gate green throughout.

**Next (planned):** 8760-hr hourly dispatch sim (derive load-hours / ATES sizing /
peak electricity instead of assuming them) and the SDE++ subsidy + value case
(NPV/IRR at a heat tariff, €/tCO₂ abated).

---

# CHECKPOINT — 2026-05-30 (Day 1 complete)

> Resume by re-reading this file plus `PLAN.md`. Skip `CONTEXT.md` only
> if you already remember the raw-data facts. The data foundation is now
> code, not notes — trust `src/` + the tests over older prose.

---

## Where we are

**Day 0 + Day 1 complete.** Repo is now its own git repo (`git init` done,
local only, no remote). Internal deadline **Tue 2026-06-02 17:00 EAT**;
hard deadline **Thu 2026-06-04 23:59 EAT**. Day-1 gate passed: we have a
defensible BLT-01 Rotliegend table.

## Environment

- `.venv/` (gitignored) holds the pinned `requirements.txt` deps for
  Python 3.12. Activate or call `.venv/Scripts/python.exe` directly.
- Run tests: `.venv/Scripts/python.exe -m pytest` (26 passing).
- Rebuild processed data: `.venv/Scripts/python.exe -m src.build_processed`.
- Rebuild EDA notebook: `python scripts/make_eda_notebook.py` then
  `jupyter nbconvert --execute --inplace notebooks/01_eda.ipynb`.
- Commits are authored **solely by the user** — no Claude co-author trailer.

## What got done (Day 1)

Modules (all tested):
- `src/units.py` — idempotent ft→m (`ensure_metres`); guards double-conversion.
- `src/mdtvd.py` — minimum-curvature MD→TVD; matches the workbook TVD to
  <0.01 m on all 4 wells; interpolant with terminal-inclination extrapolation.
- `src/wells_io.py` — LAS loader: null-mask + physical-range gating (kills
  JUT-01 spike garbage), ft→m, ascending sort (EVD/PKP logged bottom-up),
  per-sample TVD, `coverage_table`.
- `src/lithostrat.py` — TVD-referenced picks, fault flagging, `rotliegend_pick`
  (Slochteren; deepest pick handles JUT-01's fault-repeat).
- `src/petrophysics.py` — Larionov-older Vsh, density φ, `rotliegend_summary`.
- `src/targets.py` — recovers `target_lithologies.csv` depths (see below).
- `src/build_processed.py` — writes the processed artefacts.
- `scripts/make_eda_notebook.py` — regenerates `notebooks/01_eda.ipynb`.

Processed outputs (in `data/processed/`, gitignored, regenerable):
- `well_logs.parquet` (99,379 rows, tidy, TVD-referenced, +vsh/phi_d)
- `target_lithologies_tvd.csv` (3,455 rows, **flag cleared**, depth_tvd_m filled)
- `rotliegend_summary.csv`
- `figures/*.png` (coverage, raw curves ×4, md_vs_tvd, petro_BLT-01)

## Key data facts discovered (carry forward)

1. **Reservoir = "Slochteren Formation"** in the lithostrat sheets.
2. **`target_lithologies.csv` structure was disguised:** `formation_top_tvd` /
   `formation_base_tvd` are along-hole **MD** (in **feet** for JUT-01),
   mislabelled as TVD; `depth_tvd_m` shipped empty. Each row is an exact LAS
   sample, matched by GR — **BLT-01/JUT-01 top→base, EVD-01/PKP-01 reversed**.
3. **JUT-01 is the problem child:** target GR traces uniquely to ~506 m
   (1659.5 *ft* → metres) — a feet/metre bug in the source file. True
   Slochteren is at ~3161 m TVD (3240–3378 m MD) below the Zechstein; a
   reverse fault at 2555 m repeats section. **Exclude JUT-01 target rows from
   reservoir aggregation; flagged for manual review.**
4. **Net-reservoir summary (TVD):** BLT-01 NTG 0.93 / φ_net 15% (anchor) ·
   EVD-01 NTG 0.55 / φ 11% · JUT-01 NTG 0.32 (deep pick) · PKP-01 NTG 0.10
   (tight — matches ThermoGIS k_P50 = 1 mD).
5. Formation-top cross-check (target vs lithostrat) = **0.0 m** for
   BLT/EVD/PKP; JUT flagged.
6. PKP-01 is the most deviated well (~37°), not BLT-01 as CONTEXT.md guessed.
7. NPHI is a fraction (v/v) on BLT-01 and PKP-01; EVD-01/JUT-01 have no NPHI.

## Open decisions still pending

- **Team name + SPE membership numbers** — still to be added by the user.
  Touches README, deck slide 1, report title page, submission filenames
  `Team_<TeamName>_(Code|PPT|Vid)_V1`.

## Day 2 plan (when we resume) — Reservoir deliverability + Challenge 2 start

1. **Deliverability model** — from Rotliegend k·h, φ, T per well + ThermoGIS
   P10/P50/P90, estimate doublet flow rate and **MWth** at the USP. Use
   `src/constants.py` doublet defaults. Reconcile gross k·h vs ThermoGIS
   transmissivity (BLT gross 10.66 Dm vs effective 9.3 Dm — NTG now 0.93
   explains most of the gap).
2. **Monte Carlo MWth** — propagate P10/P50/P90 thickness/φ/k to a MWth
   distribution; write `data/processed/mc_mwth.parquet`.
3. **Confirm `distance_to_usp_km`** semantics during this step.
4. **Begin Challenge 2** — doublet layout, flow rate, surface heat
   exchangers, heat pump (COP 4.2) for heating + cooling, optional ATES.
5. **Bonus AI track** — scope ML missing-curve prediction (train on BLT-01
   full suite → predict NPHI/DTC/RHOB at EVD/JUT/PKP). The loader + parquet
   are ready feedstock.

**Day 2 gate:** "Do we have a P50 MWth number for a BLT-01-anchored doublet
that clears the 10 MWth heating demand?"

## Exact prompt to restart with

> "Pick up from `CHECKPOINT.md`. Start Day 2: reservoir deliverability /
> MWth from the Rotliegend summary + ThermoGIS P10/P50/P90, then begin
> Challenge 2 doublet design. Team name + SPE numbers I'll add later."
