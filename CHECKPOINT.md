# CHECKPOINT — 2026-05-28 (Day 0 complete)

> Resume by re-reading this file plus `PLAN.md`. Skip `CONTEXT.md` only
> if you already remember the raw-data facts.

---

## Where we are

**Day 0 complete.** Day 1 (data foundation + petrophysics MVP) **not yet
started.** Internal deadline still **Tue 2026-06-02 17:00 EAT**; hard
deadline **Thu 2026-06-04 23:59 EAT**. We have 5 working days left to
the internal deadline.

## What got done today (Day 0)

Repo scaffold and skeletons written and verified:

- `PLAN.md` — senior-voice execution plan (Day 0–7, 7 sections, risk register)
- `README.md` — placeholder (team name + SPE numbers to be filled later)
- `requirements.txt` — pinned for Python 3.12 on Windows 11
- `.gitignore` — Python, Jupyter, processed-data, venv, IDE, secrets
- `deliverables/deck_outline.md` — 12-slide board-memo skeleton
- `deliverables/report_outline.md` — 8-section technical report outline
- `src/__init__.py`, `src/paths.py`, `src/constants.py` — project paths and
  the `WELLS` dataclass dict (all 4 wells' RD-New coords, ThermoGIS
  P10/P50/P90, petrophysical cutoffs, doublet design defaults)
- Directories created: `data/processed/`, `notebooks/`, `figures/`,
  `tests/`, `deliverables/`

Sanity check that passed: `python -c "from src import paths, constants"`
imports cleanly. BLT-01 gross k·h computes to 10.66 Dm vs ThermoGIS
effective 9.3 Dm — the ~13 % gap is the net-to-gross effect, which the
Day 1 Vsh/φ cutoffs will reconcile. Constants are correctly pasted.

## Open decisions still to make (asked before interrupt)

1. **Git setup** — the hackathon folder currently lives inside the
   Desktop-wide NAPE git repo, which is the wrong root for submission.
   Recommended: `git init` here as its own repo on resume.
2. **Team name + SPE membership numbers** — the user wants to add these
   later. Touches: `README.md`, deck slide 1, report title page,
   submission filenames `Team_<TeamName>_(Code|PPT|Vid)_V1`.

## What Day 1 will do (when we resume)

**Workstreams:** WS1 (data foundation) + start of WS2 (petrophysics).

**Concrete tasks, in order:**

1. Notebook `notebooks/01_eda.ipynb` — load all 4 LAS with `lasio`,
   replace `-999.25` with NaN, plot raw curves per well, log a
   curve-coverage table.
2. Notebook / module `src/units.py` — JUT-01 ft→m conversion with a
   unit test that fails on double-application.
3. Module `src/mdtvd.py` — minimum-curvature MD→TVD from
   `Well Path Data.xlsx`. Piecewise-linear fallback for EVD-01
   (only 22 stations) with a warning logged.
4. Apply MD→TVD to LAS depths and to the flagged `depth_tvd_m` column
   in `target_lithologies.csv`; clear the flag.
5. QC plot per well: MD vs TVD overlaid with lithostrat picks.
6. Cross-check formation tops vs lithostrat picks — > 10 m discrepancy
   triggers manual review.
7. First petrophysics pass on BLT-01 only: Larionov-older Vshale,
   density-φ (ρ_ma 2.65), pick the Rotliegend interval.
8. Write `data/processed/well_logs.parquet` (one row per depth sample,
   tvd-referenced, with sparse-curve flag).

**Day 1 gate (end-of-day question):** "If we had to submit tonight,
would we have a defensible Rotliegend table for BLT-01?" If yes → Day 2.

## Disk-space watch

`C:\` had 4.18 GB free at last check (was 0 earlier today). Keep ≥ 2 GB
free through Tue 2 Jun. `data/processed/` artefacts should stay
under 500 MB total.

## Exact prompt to restart with

> "Pick up from `CHECKPOINT.md`. Decisions: git init here as its own
> repo (yes / no), and start Day 1 now (yes / no). Team name and SPE
> numbers I'll add later."
