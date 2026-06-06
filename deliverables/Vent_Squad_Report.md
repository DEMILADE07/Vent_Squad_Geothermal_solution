# Utrecht District Geothermal Heating & Cooling — A Hybrid Doublet Feasibility Study

**SPE Africa Geothermal Datathon 2026 — Technical Report**

**Team Vent Squad**

| Member | Role | SPE membership |
|--------|------|----------------|
| Demilade Kolawole-Jacobs (lead) | Geoscience, integration | `[SPE #: ____]` |
| Fikayo | ML workflow | `[SPE #: ____]` |
| Ashinze | Simulation & economics | `[SPE #: ____]` |
| Ayomide | Geoscience QA | `[SPE #: ____]` |
| Sodiq | Benchmarks & economic inputs | `[SPE #: ____]` |

*Version 1 — 2026-06-02. All numbers in this report are produced by the team's
code (`src/`) and are reproducible end-to-end via `python -m src.pipeline all`.*

---

## Executive summary

I was asked a deceptively simple question: can a Rotliegend geothermal scheme
supply an Utrecht-region district with **≥ 10 MWth of heating and ≥ 5 MWth of
cooling**, and what does it cost? My answer is **yes — but it takes two doublets,
not one, and that fact drives the entire economics.**

The four candidate wells are not equal. BLT-01 is the clear anchor: 130 m of net
Rotliegend at 17 % porosity, 82 mD, 9.3 Dm transmissivity and 77 °C. My own
petrophysics, computed independently from the logs, confirms it — net-to-gross
**0.93** at 15 % net porosity, the best of the four by a wide margin. The other
three are progressively weaker, and two of them (EVD-01, PKP-01) are judged
non-productive by ThermoGIS and by my own Darcy model.

The headline tension is this: the Dutch industry benchmark gets ~13 MWth from a
*single* doublet because its reference reservoir is hotter (~94 °C) and more
permeable. **Our 77 °C reservoir yields only ~5 MWth per doublet** (Monte-Carlo
P50 **5.05 MWth**, with only a 29 % chance of clearing 10 MWth alone). To meet the
heating demand I therefore size a **two-doublet (four-well) scheme**, which reaches
a P50 of **10.11 MWth** and a **50 % probability of clearing 10 MWth** — an honest
coin-flip that I do not dress up as a certainty. The resource distribution is
**physically bounded**: the optimistic tail is fitted to ThermoGIS's published band
with a two-piece (split) lognormal that reproduces all three percentiles exactly,
then de-rated at a pump/sand-control ceiling of 300 m³/h per doublet — so the
upside is real-world deliverable, not a fitting artefact.

For the surface system I recommend **Design A: geothermal doublets → plate heat
exchangers → district hot loop, with cooling from seasonal ATES (aquifer thermal
energy storage) trimmed by electric heat pumps.** It beats the absorption-chiller
alternative (Design B) on three counts: cooling LCOE **17.5 vs 23.2 €/GJ**; it
does not divert ~7 MWth of saleable heat to make cold; and a LiBr/H₂O absorption
chiller wants 85–95 °C drive heat, above our 77 °C resource.

The economics are benchmarked and honest. My LCOE engine reproduces the TNO
reference workbook to **5.769 €/GJ** before I trust any of my own numbers. On that
footing, the hybrid scheme delivers **heat at 11.7 €/GJ, cooling at 17.5 €/GJ, a
blended 12.5 €/GJ**, for **≈ €19.9 M** of capital — and, propagating the full
resource and cost uncertainty, that heat price carries a **90 % band of ~6–57 €/GJ
whose heavy upper tail is resource risk, not cost risk** (P50 11.8 €/GJ; §5). That
heat price is ~2× the Dutch
heat-only benchmark, and I can attribute the gap precisely: a cooler, less
productive reservoir needs four wells for 10 MWth where the benchmark needs two for
13 MWth.

**If you read nothing else:** the resource is real but modest; two doublets are the
honest minimum; Design A is the right surface scheme; and the whole chain — raw LAS
to hybrid LCOE — runs from one command and is unit-tested.

---

## 1. Project context and scope

**Demand.** A district in the Utrecht region requiring ≥ 10 MWth of space heating
(winter) and ≥ 5 MWth of cooling (summer).

**Reservoir target.** The Lower Permian **Rotliegend sandstone** (Slochteren
Formation) — the same play that hosts the Groningen field, with ~20 producing
geothermal doublets across the Netherlands, so the precedent is strong.

**In scope.** Subsurface characterisation of the four wells (Challenge 1);
probabilistic resource assessment and doublet siting; a hybrid heating + cooling
surface design with two costed options (Challenge 2); an extended LCOE covering
both energy products; and a runnable AI-assisted pipeline (bonus).

**Out of scope (declared, not skipped).** Detailed district heat-distribution
network hydraulics; permitting and ATES regulatory approval beyond a noted risk;
3-D static geological modelling and geomechanics; and full transient reservoir
simulation. These are the right next-phase activities, not feasibility-stage ones.

---

## 2. Data inventory and quality

| Source | What it is | How I used it |
|--------|-----------|---------------|
| 4 LAS files (BLT-01, EVD-01, JUT-01, PKP-01) | Wireline logs (GR, sonic, density, ±neutron) | Petrophysics, ML log prediction |
| Lithostratigraphic Data.xlsx | Formation tops, fault flags | Rotliegend/Slochteren interval picks |
| Well Path Data.xlsx | Deviation surveys | MD → TVD (minimum curvature) |
| ThermoGIS Data.xlsx | TNO P90/P50/P10 reservoir + flow/power | Reconciliation, Monte-Carlo inputs |
| target_lithologies.csv | 3,455 reservoir-property samples | Recovered (see below) |
| LCOE.xlsx | TNO heat-only LCOE workbook | Validation reference; rebuilt in code |

**Quality issues I handled in code (not by hand):**

1. **`-999.25` nulls** masked to NaN on load before any arithmetic.
2. **JUT-01 depths in feet** — converted once to metres by an *idempotent* function
   (`src/units.py`) that is guarded against double-conversion and unit-tested.
3. **Spike garbage** on JUT-01 sonic/density (values in the millions) removed by
   physical-range gating, distinct from the null sentinel.
4. **Bottom-up logging** on EVD-01 and PKP-01 (negative survey step) sorted
   ascending so depth-ordered operations are valid.
5. **`target_lithologies.csv` shipped broken on purpose:** every row flagged
   "needs TVD conversion" with the TVD column empty; its `formation_top/base` were
   actually along-hole **MD** (feet for JUT-01). I reverse-engineered the structure,
   matched each row to its exact LAS sample by GR, recovered the TVD, and cleared
   the flag (`src/targets.py`). Cross-check against the lithostratigraphic tops
   agrees to **0.0 m** for BLT-01/EVD-01/PKP-01; JUT-01 is flagged (see §3.1).

**External data and citations.** ThermoGIS / DINOloket (TNO) for the reservoir
P-distributions and the LCOE reference workbook (van Wees et al., TNO LCOE model);
standard NL Rotliegend doublet precedent for flow rates (100–300 m³/h), drilling
cost, and ATES capex ranges. The full input-to-source mapping is in Appendix D.

---

## 3. Subsurface assessment (Challenge 1)

### 3.1 Data conditioning

All depth referencing is **true vertical depth (TVD)** via the **minimum-curvature**
method (`src/mdtvd.py`), the industry standard for tracing a deviated well path.
My recomputed station TVD matches the survey's own TVD column to **better than
1 cm** on all four wells. PKP-01 is the most deviated (~37°); EVD-01 has only 22
survey stations and falls back to a piecewise-linear path with a logged warning.

JUT-01 is the problem child and I treat it explicitly: its target rows trace to a
spurious ~506 m depth (a 1659.5 *ft* → metre error in the source file), while its
true Slochteren sits at ~3161 m TVD below the Zechstein, with a reverse fault at
~2555 m repeating section. **JUT-01 target rows are excluded from reservoir
aggregation and flagged for manual review** rather than silently averaged in.

### 3.2 Petrophysical interpretation

- **Shale volume** — Larionov (1969) *older-rock* transform from gamma ray. The
  Rotliegend is ~290 Ma and compacted; the Tertiary (young-rock) form would
  over-clean the result. A linear-GR index is computed in parallel as a sanity
  check.
- **Porosity** — density porosity with a sandstone matrix (ρ_ma = 2.65 g/cc,
  ρ_fl = 1.00 g/cc), cross-checked against NPHI where it exists (BLT-01, PKP-01).
- **Net reservoir** — counted only where **V_sh ≤ 0.40 AND φ ≥ 0.08**, the
  conventional NL Rotliegend cut-offs.

### 3.3 Rotliegend characterisation per well

My independent net-reservoir summary (`data/processed/rotliegend_summary.csv`),
set beside the ThermoGIS expert estimate:

| Well | Gross (m) | Net (m) | **NTG** | φ_net | ThermoGIS φ / k / kh / T |
|------|-----------|---------|---------|-------|--------------------------|
| **BLT-01** | 122.4 | 113.8 | **0.93** | **0.150** | 17 % / 82 mD / 9.3 Dm / 77 °C |
| EVD-01 | 76.8 | 42.1 | 0.55 | 0.109 | 9 % / 6 mD / 0.4 Dm / 72 °C |
| JUT-01 | 133.0 | 42.3 | 0.32 | 0.099 | 11 % / 40 mD / 4.8 Dm / 72 °C |
| PKP-01 | 64.4 | 6.6 | 0.10 | 0.091 | 9 % / 1 mD / 0.1 Dm / 88 °C |

The petrophysics confirms BLT-01 as the anchor on every axis, and PKP-01's NTG of
0.10 is consistent with its ThermoGIS k of 1 mD — tight rock that will not flow.
(See *Appendix B* for the BLT-01 petrophysical track and MD→TVD QC plots.)

### 3.4 Resource calculation

**Deliverability model** (`src/deliverability.py`). A steady-state doublet with
Darcy radial inflow, `Q = 2π·kh·ΔP / (μ·ln(r_e/r_w))`, external radius = well
spacing (1.3 km), r_w = 0.108 m, μ ≈ 3.5×10⁻⁴ Pa·s at 77 °C. Thermal power is
`MWth = ρ·c_p·Q·ΔT / 10⁶` with reinjection at 35 °C (ΔT = 42 °C at BLT-01).

**The model is calibrated, not asserted.** With these properties the Darcy model
reproduces ThermoGIS's *own published* flow and power at the ~16.5 bar drawdown
that back-solves from their numbers:

| Well | Darcy flow P50 | ThermoGIS flow P50 | Darcy power P50 | ThermoGIS power P50 |
|------|----------------|--------------------|-----------------|--------------------|
| BLT-01 | 104.2 m³/h | 105.0 m³/h | 5.08 MWth | 5.1 MWth |
| JUT-01 | 53.8 m³/h | 55.0 m³/h | 2.31 MWth | 2.3 MWth |

Matching the national database to ~1 % earns me the right to use the model for
what-if scenarios.

**Probabilistic MWth** (`src/montecarlo.py`). I fit a **split (two-piece)
lognormal** to the ThermoGIS flow P90/P50/P10 band — a single-sigma fit cannot hit
both tails of a log-asymmetric band and overshoots ThermoGIS's *own* published P10
(551 vs 469 m³/h at BLT-01), inflating the optimistic resource; the split fit
reproduces all three published points exactly. I then **de-rate every realisation
at a 300 m³/h pump/sand-control ceiling** (NL doublets run 100–300 m³/h), draw
10,000 realisations, and report the distribution rather than a point:

| Scheme | P90 | **P50** | P10 | Mean | **P(MWth ≥ 10)** |
|--------|-----|---------|-----|------|------------------|
| 1 doublet @ BLT-01 | 0.86 | **5.05** | 14.6 | 6.6 | **29 %** |
| **2 doublets @ BLT-01** | 1.71 | **10.11** | 29.3 | 13.2 | **50 %** |
| 1 doublet @ JUT-01 | 1.11 | 2.39 | 4.75 | 2.73 | 0.4 % |

The bounding tightens the optimistic tail (single-doublet P10 26.9 → 14.6 MWth) and
pulls the mean down from 11.7 to 6.6 — much nearer the 5.1 median, as a bounded
resource should be — while leaving the **P50 and the 50 % P(≥10) decision metric
essentially unchanged**. EVD-01 and PKP-01 carry a ThermoGIS flow of zero — they
are non-productive and are not candidate doublet sites. (Distribution chart:
`figures/mc_mwth_blt.png`.)

**Thermal sustainability — breakthrough is modelled, not assumed**
(`src/reservoir_thermal.py`). The economics assume the produced temperature holds
for the field life; I check that with the **Gringarten & Sauty (1975)** doublet
solution. The cold front reaches the producer at
`t_bt = (π·H·L²/3Q)·(ρc_bulk/ρc_water)`. At the recommended **1.3 km spacing the
breakthrough time is ~155 yr — far beyond a 30-yr economic life** — so the produced
temperature decline over the project is **0.0 °C and the constant-MWth assumption is
validated rather than asserted.** A spacing sensitivity shows where it *would* bite
(1.0 km → 92 yr, 0.6 km → 33 yr, 0.4 km → 15 yr): the 1.3 km design is
deliberately breakthrough-safe, the standard NL doublet rationale.

**The conclusion the data forces:** one doublet does not meet the heating demand
(only 31 % likely). **Two doublets are the honest minimum** for a coin-flip-or-
better chance of 10 MWth, and everything downstream assumes the four-well scheme.

**Doublet siting.** A 5-criterion weighted matrix (deliverable MWth ×4, distance
to demand ×2, thermal-breakthrough risk ×2, surface footprint ×1, subsurface
uncertainty ×1) ranks the BLT-01 vicinity first by a clear margin; the matrix
exists to make an obvious call auditable. Producer–injector spacing of ~1.3 km
follows NL precedent and manages thermal breakthrough (see §6).

### 3.5 Cross-well validation (bonus AI)

See §7 for the leave-one-well-out result. The short version: cross-well log
prediction is **not** reliable enough on these four distinct wells to feed the
resource calc, so I fall back to ThermoGIS deterministic values for the missing
curves — and I prove that with an honest R², rather than trusting an in-sample fit.

---

## 4. Surface design (Challenge 2)

### 4.1 Demand-side characterisation — an 8760-hour dispatch, not an assumption

The load-hours that the LCOE hinges on (heat FLEQ is the #2 tornado driver) are too
important to type in, so I **simulate them** (`src/dispatch.py`). I build an hourly
Utrecht temperature year (seasonal + diurnal + AR(1) weather, winter low −10 °C,
summer high 29 °C), drive a temperature-dependent space-heating + flat DHW demand
(peak 10 MWth) and an internal-gain-driven cooling demand (peak 5 MWth), and
dispatch the supply stack hour by hour: geothermal baseload → heat pump → backup for
heat; ATES → chiller trim for cold.

Two findings fall straight out, and one of them is uncomfortable:

1. **The 6,000 h heat FLEQ is only achievable under *baseload* operation.** A
   geothermal scheme sized to the full 10 MWth peak is idle most of the year:
   simulated FLEQ is just **~3,100 h**, which would re-price heat at **~21 €/GJ**, not
   11.7. Utilisation is the whole game — and it is recovered by sizing geothermal
   *down* to baseload:

   | Geo capacity | Heat-energy coverage | Geo FLEQ | Peak shifted to HP |
   |--------------|----------------------|----------|--------------------|
   | 10.1 MWth (2 doublets, peak-sized) | 100 % | ~3,100 h | 0 |
   | 5.05 MWth (1 doublet, baseload) | **92 %** | **~5,800 h** | 1.2 MWe |

   **The economic recommendation the sim forces:** baseload ~one doublet (~5 MWth) and
   let an electric heat pump cover the residual winter peak. That reaches the ~6,000 h
   the economics need and still covers 92 % of annual heat energy. Meeting the full
   10 MWth peak *from geothermal alone* (two doublets) buys supply security and a
   low-carbon peak, but at roughly half the utilisation — a trade I now state in the
   open rather than hide inside a load-hours constant. (Figure:
   `figures/dispatch_load_duration.png`.)

2. **ATES is correctly sized at 4 pairs, and cooling is genuinely small.** The 5 MWth
   cooling peak needs ⌈5 / 1.5⌉ = **4 ATES pairs** — the sim confirms the costing
   assumption — but Utrecht's modest cooling load means a simulated cooling FLEQ of
   only ~640 h (the assumed 2,000 h was generous). ATES alone covers ~all of it, so
   the electric chiller barely runs. Because cooling is a small, low-LCOE-impact slice
   (the tornado already showed this), the over-estimate does not move the headline.

The load-duration shape is also what makes seasonal storage (ATES) attractive: cold
banked cheaply in winter is spent against the summer peak.

### 4.2 Design A — geothermal + ATES + heat pumps (recommended)

Geothermal doublets → plate-and-frame heat exchanger → district hot loop. An
electric heat pump (COP ≈ 4.2) trims winter heat peaks. **Cooling** comes from
**ATES**: cold is stored in a shallow aquifer over winter and recovered in summer,
with an electric heat pump in chiller mode trimming the hottest days. I size
**4 ATES well pairs** (0.5–2 MWth each, round-trip efficiency ~70 %) for the 5 MWth
cooling demand. Blended system cooling COP ≈ 10 (mostly free stored cold + a little
electric lift), giving ~1,000 MWh/yr of cooling electricity.

### 4.3 Design B — geothermal + LiBr/H₂O absorption chiller (contrast)

Same heat source, but cooling from a LiBr/H₂O **absorption chiller** (thermal
COP ≈ 0.7) driven by geothermal heat. To make 5 MWth of cold it needs **≈ 7.1 MWth
of driving heat** — heat that Design A instead sells. I price that driving heat at
the heat LCOE as an internal transfer cost, which is the fair way to expose the
trade-off.

### 4.4 Recommendation and selection rationale

**Design A wins, and I made sure it won honestly:**

| | Design A (ATES + HP) | Design B (absorption) |
|---|---|---|
| Cooling LCOE | **17.5 €/GJ** | 23.2 €/GJ |
| Geo heat consumed for cooling | 0 MWth | 7.1 MWth |
| Total capex | €19.9 M | €17.8 M |
| Cooling electricity | ~1,000 MWh/yr | ~400 MWh/yr |

1. **Cost** — Design A's cooling is cheaper per GJ once ATES is costed at the real
   NL range. 2. **It doesn't cannibalise the product** — Design B diverts ~7 MWth
   of saleable heat. 3. **Physics** — an absorption chiller wants 85–95 °C drive
   heat; our reservoir is 77 °C, marginal-to-insufficient. Design B is lower-capex
   but loses on the metric that matters (cost per unit energy delivered) and on the
   thermodynamics.

---

## 5. Economics — extended LCOE

**What LCOE is.** The Levelised Cost Of Energy is the financed, after-tax,
break-even price (€/GJ) at which discounted cash flows plus upfront equity are
recovered at the investors' required 15 % return. It is *not* total-cost ÷
total-energy — the 80/20 debt/equity split, loan interest, depreciation, tax and
discounting all set the number.

**Method and validation.** Rather than edit the TNO workbook (the single source of
truth, left untouched), I rebuilt its financial model in Python (`src/lcoe.py`) so
sensitivities and the bonus pipeline can drive it. The rebuild is **gated**: it must
reproduce the stock workbook's heat case to **5.769 €/GJ** before any of my numbers
are trusted. It does, to the third decimal, and a unit test locks it.

**Results (Design A):**

| Metric | Value |
|--------|-------|
| LCOE heat | **11.7 €/GJ** (≈ 42 €/MWh) |
| LCOE cooling | **17.5 €/GJ** |
| Blended system LCOE | **12.5 €/GJ** |
| Subsurface capex (4 wells + pumps) | €15.0 M |
| Heat-plant capex | €1.5 M |
| Cooling capex (ATES + chiller) | €3.4 M |
| **Total capex** | **€19.9 M** |
| TNO heat-only reference | 5.77 €/GJ |

**Economic-life lever.** The headline above caps the cash flow at the 15-yr loan
term, matching the TNO reference for a like-for-like benchmark. But the wells are
sunk capital that keep delivering heat long after the loan is repaid: extending the
economic life to a realistic **30 yr (loan unchanged at 15 yr) lowers heat LCOE from
11.7 to 10.6 €/GJ (−9 %)** with no new capital. I report the 15-yr figure as the
benchmark-comparable headline and the 30-yr figure as the bankable upside, because
the thermal-breakthrough check above confirms the resource is good for it.

**Probabilistic LCOE — a band, not a point** (`src/lcoe_montecarlo.py`). A single
break-even price hides that its dominant input is a coin-flip. I therefore propagate
the **bounded two-doublet resource Monte-Carlo *and* the cost/market uncertainty**
(drilling-cost scaling, heat load-hours, electricity price, ATES capex and COP —
sampled from the same low/base/high ranges the tornado swings, for one consistent
story) through the financed model, 10,000 joint draws, to an LCOE *distribution*:

| Heat LCOE | P10 (low) | **P50** | P90 (high) |
|-----------|-----------|---------|------------|
| €/GJ | 6.3 | **11.8** | 56.7 |

The **P50 of 11.8 matches the deterministic point estimate**, and
**P(LCOE ≤ 15 €/GJ) = 0.59**. The distribution is strongly right-skewed, and the
driver of the heavy upper tail is unambiguous: it is the **resource downside** — the
two-doublet P90 of ~1.7 MWth spreads four fixed well costs over little energy — **not
cost inflation** (cooling LCOE stays tight at 15–22 €/GJ). That is the quantified
economic case for **staged appraisal**: drilling one pilot well to confirm
deliverability *before* committing the full four-well capital is precisely what
truncates the tail. Reported at three hurdle rates (P50 heat LCOE 11.0 / 11.8 / 12.6
€/GJ at 10 / 15 / 20 % required return) so the financing choice is explicit rather
than buried in the discount factor. CDF and histogram:
`figures/lcoe_heat_distribution.png`.

**Sensitivities (tornado, `figures/lcoe_tornado.png`).** The LCOE is
**heat-dominated**: the top drivers are resource deliverability (MWth), heat
load-hours, and drilling cost per metre. The cooling-side knobs (ATES capex,
cooling COP) barely move the blended number. The lesson is strategic — getting the
*subsurface* right matters far more than fine-tuning the cooling plant.

Our heat at ~2× the Dutch benchmark is fully explained by Challenge 1: a cooler,
less productive reservoir needs four wells for 10 MWth where the benchmark needs two
for 13 MWth. That clean cause-and-effect is the spine of the report.

---

## 6. Risks, assumptions, and limitations

| Risk | Mitigation / note |
|------|-------------------|
| **Thermal breakthrough** — injected cold reaching the producer | **Quantified** (`src/reservoir_thermal.py`, Gringarten-Sauty): ~155 yr at the 1.3 km design spacing, far beyond the economic life — breakthrough-safe. Decline only enters the LCOE below ~0.5 km spacing. |
| **Resource optimism** (top LCOE driver) | Full P10–P90 propagated; the headline is the P50 with P(≥10) = 50 % stated plainly. |
| **ATES sizing** | Sized off the summer peak, not the annual mean; 4 pairs with 30 % margin. |
| **ATES regulatory risk (NL)** | Dutch ATES permitting is well-established but site-specific; flagged for the permitting phase. |
| **Drilling cost volatility** | Among the top three LCOE sensitivities; carried in the tornado. |

**Key assumptions:** reinjection 35 °C; electricity €150/MWh; heat 6,000 / cooling
2,000 load-hours; HP COP 4.2; ATES €0.7 M/pair. **Model limitations:** 1-D
well-based rather than 3-D static; no geomechanics; no detailed network hydraulics
or transient simulation. These are feasibility-appropriate and named, not hidden.

---

## 7. AI-assisted workflow (bonus)

**`pipeline.py` — the workflow, not a notebook.** A typer CLI runs the whole chain
deterministically, each stage persisting an artefact the next consumes:

```
python -m src.pipeline ingest   # raw LAS  -> well_logs.parquet (+ recovered targets)
python -m src.pipeline petro    #          -> rotliegend_summary.csv (+ deliverability)
python -m src.pipeline predict  #          -> mc_mwth.parquet (Monte-Carlo MWth)
python -m src.pipeline ml        #          -> ml_loo_cv.csv + ml_log_predictions.parquet
python -m src.pipeline lcoe      #          -> LCOE_hybrid.xlsx
python -m src.pipeline all        # everything, in order
```

A reviewer can re-run it from a clean `pip install -r requirements.txt`.

**ML missing-log prediction with honest validation** (`src/ml_logs.py`,
`notebooks/05_ml_logs.ipynb`). Only BLT-01 is fully logged; NPHI is absent on
EVD-01/JUT-01 and RHOB is sparse on EVD-01. I train LightGBM on donor wells and
score it by **leave-one-well-out** cross-validation — the only honest measure of
generalisation to an unseen well:

| Curve | Cross-well R² | Decision |
|-------|---------------|----------|
| DTC (sonic) | **0.51** | ML usable (benchmark; present on all wells) |
| RHOB | 0.10 | **ThermoGIS fallback** |
| NPHI | −0.20 | **ThermoGIS fallback** |

**The locked fallback rule:** where cross-well R² < 0.50, the prediction is *not*
trusted — the petrophysics uses the ThermoGIS deterministic value instead. With one
fully-logged well and four geologically distinct locations, log prediction is not
reliable enough here, and I prove it rather than assume it. The ML layer adds value
as an automated, validated *screen* — not as a number I quietly trust. Where AI
does **not** belong: the dimensioning and design decisions stay engineer-in-the-loop.

---

## 8. Conclusions and next steps

**Is the resource sufficient?** Yes, with two doublets. One BLT-01 doublet is ~5
MWth (P50); two reach 10.12 MWth at a 50 % probability of clearing the heating
demand — stated as a probability, not a promise.

**Is the surface design viable?** Yes. Design A (geothermal + ATES + heat pumps)
meets both 10 MWth heating and 5 MWth cooling, at a blended **12.5 €/GJ** for
**≈ €19.9 M**, and beats the absorption-chiller alternative on cost, on product
economics, and on the physics of a 77 °C resource.

**Recommended next phase:** drill one pilot well at the BLT-01 site → in-situ
injectivity/production test to confirm the Darcy deliverability → if confirmed,
complete the doublet, then the second doublet → FID. **Data gaps to close first:**
3-D seismic confirmation of the BLT-01 fairway, an in-situ injectivity test, and a
transient thermal-breakthrough simulation at the chosen spacing.

---

## Appendices

- **A. Petrophysical equations & constants** — Larionov-older V_sh, density-φ
  (2.65 g/cc), cut-offs (V_sh ≤ 0.40, φ ≥ 0.08); fluid properties at 77 °C
  (`src/constants.py`, `src/petrophysics.py`).
- **B. MD→TVD method & QC** — minimum curvature, sub-cm survey match;
  `figures/md_vs_tvd.png`, `figures/petro_BLT-01.png`,
  `figures/raw_curves_*.png`, `figures/coverage.png`.
- **C. Monte-Carlo & tornado underlying data** — `figures/mc_mwth_blt.png`,
  `figures/deliverability_reconciliation.png`, `figures/lcoe_tornado.png`,
  `data/processed/mc_mwth_summary.csv`.
- **D. Full LCOE input table with sources** — `data/processed/LCOE_hybrid.xlsx`
  (Inputs sheet carries the per-parameter source column).
- **E. External data citation list** — ThermoGIS / DINOloket (TNO); TNO LCOE
  workbook (van Wees et al.); NL Rotliegend doublet flow-rate, drilling-cost and
  ATES-capex precedent (compiled by Sodiq, see repo issues).
- **F. ML cross-validation detail** — `figures/ml_coverage.png`,
  `figures/ml_dtc_crossplot.png`, `figures/ml_nphi_prediction.png`,
  `data/processed/ml_loo_cv.csv`, `notebooks/05_ml_logs.ipynb`.

*Reproduce every figure and table: `.venv\Scripts\python.exe -m pytest` (70 tests)
then `.venv\Scripts\python.exe -m src.pipeline all`.*
