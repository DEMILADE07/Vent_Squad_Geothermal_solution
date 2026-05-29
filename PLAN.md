# SPE Africa Geothermal Datathon 2026 — Execution Plan

**Author's stance.** This plan is written the way I would scope a real
subsurface-to-surface feasibility study at a junior client engagement: tight
hypothesis, defensible numbers, uncertainty propagated rather than waved
away, and an honest split between what we will deliver and what we will
flag as out of scope. The competition rewards a complete, internally
consistent story over isolated brilliance; the plan is engineered for that.

**Last updated:** 2026-05-28 (T-7 days to the hard deadline).
**Cross-references:** see [CONTEXT.md](CONTEXT.md) for raw-data inventory
and the original challenge brief.

---

## 1. Executive framing

We are designing a **doublet-based geothermal heating-and-cooling supply**
for a Utrecht-region district demanding **≥ 10 MWth heating** and
**≥ 5 MWth cooling**, using the **Lower Permian Rotliegend sandstone** as
the reservoir. Four wells are on the table; the petrophysical picture from
ThermoGIS already tells us which one to anchor on:

| Well   | Net (m) | φ (%) | k_P50 (mD) | T (°C) | kh (Dm) | Verdict |
|--------|---------|-------|------------|--------|---------|---------|
| **BLT-01** | **130** | **17** | **82** | **77** | **9.3** | **Sweet spot — anchor well.** |
| JUT-01 | 125 | 11 | 40 | 72 | 4.8 | Viable second pick. |
| PKP-01 |  60 |  9 |  1 | 88 | 0.1 | Hot but tight — uneconomic doublet. |
| EVD-01 |  76 |  9 |  6 | 72 | 0.4 | Weakest on every axis. |

The headline geothermal hypothesis is set before we run a line of code:
**a 2-well doublet placed near BLT-01, producing ~150–200 m³/h at 77 °C with
~35 °C surface ΔT, will land in the 10–13 MWth heat-only band.** Cooling
will come from a hybrid layout (ATES + electric heat pumps in chiller mode,
optionally supplemented by a LiBr/H₂O absorption chiller driven by the
return-line heat). This is consistent with the ~20 producing Rotliegend
doublets across the Netherlands and with the TNO LCOE workbook's reference
case (50 L/s, 13.4 MWth, ≈ 5.8 €/GJ).

Where this plan adds value over a "load the data, plot the logs, copy the
LCOE sheet" baseline:

1. **Uncertainty is propagated.** Every reservoir property carries a
   P10/P50/P90, and the headline MWth is reported as a distribution, not
   a single point.
2. **Cooling is sized in real numbers**, not hand-waved. Most teams will
   skim past this; it is 5 MWth of demand and 40 % of the surface scope.
3. **The bonus AI track is a runnable pipeline**, not a notebook. End-to-end
   CLI from LAS files to a hybrid LCOE.
4. **The leave-one-well-out validation is honest.** With only one
   fully-logged well, we will report cross-well R² and degrade gracefully
   to ThermoGIS deterministic values when it is poor.

---

## 2. Timeline and gating

Today is **2026-05-28**. The hard deadline is **2026-06-04 23:59 EAT**.
We will operate to an **internal deadline of Tuesday 2026-06-02 17:00 EAT**,
leaving Wednesday and Thursday as pure buffer. The plan is paced for a
single operator; tasks marked **[T]** are team-stretch upgrades and should
be dropped first if collaborators do not engage.

| Day | Date         | Block         | Gate at end of day |
|-----|--------------|---------------|--------------------|
| D0  | Thu 28 May   | Scaffold + outline | Repo, requirements, deck skeleton, doublet hypothesis locked. |
| D1  | Fri 29 May   | Data foundation + petrophysics MVP | LAS loaded with units harmonised, MD→TVD applied, Rotliegend interval picked at all four wells, first Vsh/φ/k pass on BLT-01. |
| D2  | Sat 30 May   | Resource + surface MVP | Deterministic MWth per well, doublet location picked with a 5-criterion matrix, Design A (geothermal + ATES + HP) sized to demand, single-point LCOE produced. |
| D3  | Sun 31 May   | Deepening | Monte-Carlo MWth from P10/P50/P90, LCOE tornado, Design B (absorption-chiller contrast) sized, ML log-prediction with leave-one-well-out, pipeline.py wired end-to-end. |
| D4  | Mon 1 Jun    | Polish | Report draft, deck v1, README, requirements pinned, smoke test from a clean venv. Analysis frozen by 12:00. |
| D5  | Tue 2 Jun    | **Submit** | Video recorded AM, zip + PPT + drive link uploaded by 17:00, submission form confirmed. |
| D6  | Wed 3 Jun    | Buffer | Resubmit only if a real defect is found. |
| D7  | Thu 4 Jun    | Buffer / hard deadline | No new work. |

**Gating rule.** At each end-of-day gate, we ask: *"If we had to submit
tonight, would we have a defensible answer on Challenge 1, Challenge 2,
and the bonus?"* If the answer is no on any track, the next day's first
slot patches that track before deepening anywhere.

---

## 3. Technical workstreams

### WS1 — Data foundation and well-path correction

**Objective.** Produce a single, unit-consistent, TVD-referenced parquet
file (`data/processed/well_logs.parquet`) that every downstream step
consumes. This is the load-bearing artefact of the whole project; a quiet
bug here propagates into Challenge 1, Challenge 2, and the bonus AI track.

**Tasks.**

1. Load all four LAS files with `lasio`. Replace `-999.25` with `NaN`.
2. **JUT-01 unit conversion** — `STRT/STOP/STEP` are in feet
   (LAS header confirms unit `F`). Convert depth column and any
   depth-derived curves to metres in a single, well-commented function;
   write a unit test that fails if the function is run twice.
3. **MD → TVD** via **minimum-curvature** on the well-path tables in
   `Well Path Data.xlsx`. PKP-01 (111 stations) and BLT-01 (103) have
   enough density for clean min-curvature; EVD-01 (22 stations) falls
   back to piecewise-linear with a warning logged.
4. Project log depths from MD to TVD with the resulting MD↔TVD lookup;
   write a QC plot per well overlaying MD, TVD, and the lithostrat picks.
5. Apply the same MD→TVD transform to the **flagged `depth_tvd_m`**
   column of `target_lithologies.csv` and clear the flag.
6. **Cross-check** TVD-converted formation tops against the lithostrat
   picks at each well. Discrepancy > 10 m → manual review.

**Deliverable.** `data/processed/well_logs.parquet` (one row per depth
sample, columns including `well_id`, `md_m`, `tvd_m`, `gr`, `rhob`,
`nphi`, `dt`, `pe`, plus a sparse-curve flag).

### WS2 — Petrophysical interpretation and Rotliegend characterisation

**Objective.** Per well, produce a Rotliegend summary (thickness, φ, k,
T) with explicit error bars, that the resource calc and the LCOE will
consume.

**Tasks.**

1. **Vshale** — Larionov (1969) older-rock formula (Rotliegend is Lower
   Permian, ~290 Ma; the Tertiary form would over-clean the result).
   Linear-GR Vshale is computed in parallel as a sanity check.
2. **Porosity** — density-porosity with sandstone matrix
   ρ_ma = 2.65 g/cc and fluid ρ_f = 1.00 g/cc; NPHI cross-check where
   available (BLT-01, PKP-01); sonic-porosity (Wyllie) as a tertiary
   estimate. Report the **min(φ_D, φ_N) shale-corrected** value as the
   headline.
3. **Permeability** — published Rotliegend k–φ transform of the form
   log10(k) = a·φ + b, with coefficients calibrated against the
   ThermoGIS P50 k at BLT-01 (anchors the curve to the only well with
   reliable inputs). Predict at the other three wells, then sanity-check
   against ThermoGIS P50 — if the wells fall outside their own P10–P90
   band, ThermoGIS values are used directly and the prediction is
   reported as "indicative".
4. **Net reservoir** — gross Rotliegend interval from lithostrat picks,
   net cutoff at Vsh ≤ 0.40 **and** φ ≥ 0.08 (standard NL Rotliegend
   cutoffs). Report N/G.
5. **Temperature** — accept the ThermoGIS P50 T at each well; gradient
   QC against the BLT-01 BHT (167 °F at TD ≈ 75 °C; aligns with 77 °C
   reservoir temp).

**Deliverable.** `data/processed/rotliegend_summary.csv` with one row per
well: `net_m, phi_pct, k_md, t_c, thickness_p10, thickness_p50,
thickness_p90` (with P10/P90 imported from ThermoGIS).

### WS3 — Resource assessment and doublet siting

**Objective.** Convert the per-well reservoir summary into a **probabilistic
MWth deliverable** at the chosen doublet location and justify the
siting decision.

**Tasks.**

1. **Doublet productivity index** by Darcy radial inflow,

   `Q = (2π · k · h · ΔP) / (μ · ln(r_e / r_w))`

   with k·h from WS2, μ at reservoir T (≈ 3.5 · 10⁻⁴ Pa·s at 77 °C),
   r_e taken as half the producer–injector spacing (typical 1.2–1.5 km
   for NL doublets), r_w = 0.108 m. Convert to volumetric flow per well.
2. **Thermal power** by

   `MWth = ρ · c_p · Q · ΔT / 10⁶`

   with ρ ≈ 1000 kg/m³, c_p ≈ 4 180 J/kg·K, ΔT = T_res − T_return.
   Sensitivity on ΔT = 30, 35, 40 °C (return temperatures of 47, 42, 37 °C).
3. **Monte-Carlo MWth** — sample k, φ, h independently from
   ThermoGIS P10/P50/P90 fit to a log-normal (k, φ) / normal (h) family;
   10 000 draws; report P10/P50/P90 MWth and the probability of
   exceeding 10 MWth.
4. **Doublet siting** — score four candidate locations on a 5-criterion
   weighted matrix: deliverable MWth (×4), distance to USP (×2),
   thermal-breakthrough risk (×2), surface footprint / planning (×1),
   subsurface uncertainty (×1). Headline pick is almost certainly the
   BLT-01 vicinity; the matrix exists to make the case auditable.
5. **[T] Thermal breakthrough check** — simple analytic estimate of
   time-to-breakthrough at chosen spacing and flow rate (Gringarten /
   Lauwerier closed-form). Drop if time-pressed.

**Deliverables.** A map figure of the four wells + USP + chosen doublet; a
Monte-Carlo MWth distribution chart; a decision-matrix table.

### WS4 — Hybrid surface design and extended LCOE

**Objective.** Specify a surface scheme that supplies ≥ 10 MWth heating
**and** ≥ 5 MWth cooling, and produce a re-derived LCOE that covers both
energy products. Two designs are sized; the recommended one is the
headline.

**Design A (recommended).** Geothermal doublet → plate-and-frame heat
exchanger to a district hot loop → electric heat pumps (COP ≈ 4.2 at
delivery T ≈ 70 °C) for peak-load shaving in winter and chiller-mode
operation in summer, backed by **ATES** (aquifer thermal energy storage)
for seasonal load shifting. ATES round-trip efficiency ≈ 70 %; typical
per-doublet ATES throughput 0.5–2 MWth per warm/cold well pair. For
5 MWth cooling demand we provisionally size **3–4 ATES well pairs**, to
be refined with the load-duration profile.

**Design B (contrast).** Geothermal doublet → heat exchanger → district
hot loop → **LiBr/H₂O absorption chiller** driven by the return line
(COP_th ≈ 0.7). Simpler thermally, weaker electrically; included to give
the deck a real comparison rather than a strawman.

**LCOE.**

1. Work on a copy: `data/processed/LCOE_hybrid.xlsx`. Leave the original
   `LCOE.xlsx` untouched.
2. Extend the workbook with a **cooling-energy block** (annual GJ_cool,
   chiller electricity opex), a **surface-equipment capex block**
   (HP, chiller, ATES wells, surface HX, controls), and a re-derived
   **LCOE per GJ heat** and **LCOE per GJ cool**.
3. Reproduce the workbook's logic in `notebooks/04_lcoe.ipynb` so that
   we can drive sensitivities programmatically.
4. **Tornado chart** on the top 8 LCOE drivers: drilling cost per metre,
   doublet flow rate, capacity factor heating, capacity factor cooling,
   electricity price, HP COP, ATES capex, discount rate.

**Deliverables.** `data/processed/LCOE_hybrid.xlsx`, `notebooks/04_lcoe.ipynb`,
the tornado figure, and a one-page surface-flow diagram.

### WS5 — Bonus: AI-assisted workflow

**Objective.** A short, runnable workflow that automates a real part of
the geothermal feasibility loop, not a notebook with `model.fit()` in it.

**WS5.1 — ML log prediction (LightGBM).** Train on BLT-01's full curve
suite to predict NPHI, DTC, and RHOB where missing; **leave-one-well-out
CV** as the honest evaluation. Report cross-well R² explicitly. **If
cross-well R² < 0.5 on a curve, that curve falls back to ThermoGIS
deterministic** in the downstream calc and the report says so.

**WS5.2 — End-to-end pipeline (`pipeline.py`).** A typer / click CLI:

```
pipeline.py ingest  --las-dir data/raw          # → well_logs.parquet
pipeline.py petro   --in well_logs.parquet      # → rotliegend_summary.csv
pipeline.py predict --in rotliegend_summary.csv # → mc_mwth.parquet
pipeline.py lcoe    --in mc_mwth.parquet        # → LCOE_hybrid.xlsx
```

Reproducible from a fresh `python -m venv && pip install -r requirements.txt`.

**WS5.3 — [T] LLM summarisation.** A small wrapper that takes the
`rotliegend_summary.csv` and the LCOE outputs and emits a one-page
exec-summary draft (Anthropic Claude API, with prompt caching of the
system prompt so reruns are cheap). Time-boxed to Day 4 PM only;
dropped if anything else is behind.

**Deliverables.** `src/pipeline.py`, `notebooks/05_ml_logs.ipynb` with the
LOO-CV table, and a README block on how to run the CLI.

---

## 4. Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R1 | TVD conversion silently wrong in one well | M | High — every downstream number shifts | Cross-check converted TVD vs. lithostrat picks; >10 m off triggers manual review. |
| R2 | ML log prediction overfits BLT-01 | H | Medium | Leave-one-well-out CV is the gate; degrade to ThermoGIS P50 if cross-well R² < 0.5 and report the fallback. |
| R3 | LCOE workbook corrupted by edits | L | High — single source of truth | Work on a copy; original stays untouched; both files in git. |
| R4 | Cooling design under-sized (ATES well count too low) | M | Medium | Build the load-duration profile on Day 2; size ATES off the August peak, not the annual mean. |
| R5 | Doublet flow rate optimistic vs. NL precedent | M | Medium | Sanity-check the Darcy Q against published NL Rotliegend doublets (typical 100–300 m³/h); if outside that band by >25 %, revise. |
| R6 | Team flake — solo operator carries [T] tasks | H | Low | Plan is built so every [S] task alone delivers a complete submission; [T] tasks upgrade, not enable. |
| R7 | Deadline drift on report writing | M | High | Internal deadline 2 days before the hard deadline; analysis frozen at Day 4 noon. |
| R8 | Disk-space exhaustion on C: (already hit once) | M | High — blocks all writes | Keep ≥ 2 GB free; processed artefacts under 500 MB total; clean `.las` interpretation caches at end of WS1. |

---

## 5. Open decisions to lock by end of Day 1

1. **Team name and SPE member numbers** — needed for filenames and the
   title slide.
2. **Doublet location** — pre-analysis recommendation: BLT-01 vicinity,
   ~1.3 km producer–injector spacing along the strike of the Rotliegend
   fairway. Confirm or revise after the WS3 decision matrix runs.
3. **Headline design** — Design A (geothermal + ATES + HP) as the
   recommendation, Design B as the contrast. If reviewing the load-duration
   profile flips this, decide before Day 3 deepening starts.
4. **WS5.3 (LLM summarisation) in or out** — go/no-go at Day 4 16:00.

---

## 6. Submission map (what we hand in, where it lives)

| Deliverable | Path in repo | Required by |
|-------------|--------------|-------------|
| D1 — code zip | `/` (zipped from a clean clone) | Submission Form |
| D2 — slide deck (PDF) | `deliverables/Team_<X>_PPT_V1.pdf` | Submission Form |
| D3 — explainer video | Google Drive link (login-free) | Submission Form |
| D4 — technical report | `deliverables/Team_<X>_Report_V1.pdf` | Challenge brief |
| README | `README.md` | D1 requirement |
| Reproducibility | `requirements.txt` (pinned) | D1 requirement |
| LCOE artefact | `data/processed/LCOE_hybrid.xlsx` | Challenge 2 |
| Pipeline | `src/pipeline.py` | Bonus track |

---

## 7. What "extraordinary" looks like on this submission

The competition will receive a long tail of submissions that load the LAS,
plot the logs, compute a single MWth, copy the LCOE workbook, and call the
notebook the "AI workflow". Five things will separate this entry from
that tail:

1. **Probabilistic MWth**, not a single number. Most teams will not
   propagate the P10/P50/P90 — we will.
2. **Cooling sized in real numbers.** ATES well count, COP-driven
   electricity load, summer-peak load-duration. Most decks will treat
   cooling in one sentence; ours treats it as 40 % of the surface scope
   because that is what the demand says.
3. **End-to-end runnable pipeline** as the bonus. A CLI that takes raw
   LAS in and a hybrid LCOE out. Reviewers can re-run it.
4. **Honest cross-well validation.** Leave-one-well-out reported, fallback
   path documented. No vanity in-sample R².
5. **Deck reads as a board memo**: problem → recommendation → evidence →
   risks → ask. Not a 14-slide methods walkthrough.

If we hold the gates, deliver Design A end-to-end with a probabilistic
MWth and a hybrid LCOE, and submit the runnable pipeline, this is a
finalist-grade entry.
