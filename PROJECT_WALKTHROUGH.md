# Vent Squad — Project Walkthrough (a plain-English companion for the evaluator)

**SPE Africa Geothermal Datathon 2026**
**Team Vent Squad** — Demilade Kolawole-Jacobs (lead), Fikayo, Ashinze, Ayomide, Sodiq
**Last updated:** 2026-06-06

---

## How to read this document

This is a plain-English companion to our [technical report](deliverables/Vent_Squad_Report.md),
written for you, the evaluator. The report is the formal submission; this document
exists so that anyone — including a reviewer without a geothermal background — can
follow *what* we did, *why*, and *how to check it*, building from the basics. Every
number here is produced by the code in `src/`, is unit-tested, and reproduces from a
fresh clone (Part H). Where we use a technical term for the first time it is **bold**
and defined in the glossary (Part G).

The structure:
- **Part A — The problem**, from zero.
- **Part B — The data** we were given.
- **Part C — What we built and found**, step by step, concept first, then the number.
- **Part D — The story in five sentences.**
- **Part E — Why you can trust the numbers** (validation gates and honesty checks).
- **Part F — Applicability to African geothermal.**
- **Part G — Glossary.**
- **Part H — How to reproduce everything.**

---

# Part A — The problem, from zero

## A.1 What geothermal is

The ground gets hotter with depth — about **30 °C per kilometre** in the
Netherlands. Drill ~2 km and the water in the rock sits at 70–90 °C. **Geothermal
direct-use** means pumping that hot water up, taking the heat out at the surface,
and pumping the cooled water back down so the underground reservoir does not run dry.
At these temperatures it is a *heat* source, not an efficient electricity source —
ideal for heating (and, as we show, cooling) buildings.

## A.2 What the district needs

We design a heat-and-cooling supply for a mixed urban **district** in the **Utrecht
region**, with a stated demand of **≥ 10 MWth of heating** (winter) and **≥ 5 MWth
of cooling** (summer). *MWth* = megawatts of thermal power. The brief splits the
marks: **Challenge 1 (60 %)** — is there enough hot water? **Challenge 2 (40 %)** —
design the surface plant that delivers both heating and cooling, and cost it. Plus a
**bonus** AI-workflow track.

## A.3 How you get heat out: the doublet

You drill a pair of wells — a **doublet**. The **producer** lifts hot water up; a
surface **heat exchanger** strips the heat into a clean district loop; the
**injector** returns the cooled water to the same layer ~1.3 km away, keeping
pressure up. The 1.3 km spacing is chosen so the injected cold does not reach the
producer too soon (**thermal breakthrough**).

## A.4 Where the hot water is: the Rotliegend

The target is the **Rotliegend sandstone** (the **Slochteren Formation**), a
~290-million-year-old sandstone ~1.8–2.3 km deep — the same rock as the Groningen gas
field, so it is well understood. Two rock properties decide whether it is a good
reservoir: **porosity** (φ — the fraction that is fluid-filled pore space) and
**permeability** (k — how easily fluid flows through it, in millidarcies). We need
both: storage *and* flow.

## A.5 The honest tension at the heart of our answer

> The Dutch benchmark gets ~13 MWth from **one** doublet because its reference
> reservoir is ~94 °C and very permeable. **Our** best reservoir is only **77 °C**
> and less permeable, so **one** doublet delivers only ~5 MWth — half the heating
> demand. We therefore need **two** doublets (four wells), which roughly doubles the
> drilling cost. We do not hide this; we prove it from the data and let it drive the
> design and the economics. That clean cause-and-effect — a cooler reservoir → more
> wells → a higher unit cost — is the spine of our submission.

---

# Part B — The data we were given

Everything lives in `data/`.

## B.1 Four wells (LAS logs) — `data/raw/*.las`
A **well log** records instrument measurements every few centimetres down a
borehole. We have four wells — **BLT-01, EVD-01, JUT-01, PKP-01** — measuring gamma
ray (**GR**, clay content), bulk density (**RHOB**, → porosity), neutron porosity
(**NPHI**) and sonic (**DT/DTC**). Only **BLT-01 carries the full suite**; the others
are sparse — which is exactly why the bonus AI track (predict missing curves) makes
sense. Two traps we handle in code: the value **-999.25** means "no data" (not a
measurement), and **JUT-01's depths are in feet** while the others are in metres.

## B.2 Lithostratigraphy — `data/Lithostratigraphic Data.xlsx`
The named rock layers top-to-bottom per well, so we analyse only the Slochteren
reservoir interval. It also marks **faults**, which we handle specially.

## B.3 Well paths — `data/Well Path Data.xlsx`
Wells slant, so there are two depths: **MD** (measured along the bent borehole) and
**TVD** (true vertical). Porosity, temperature and which layer you are in all depend
on TVD, so we convert MD→TVD with the industry-standard **minimum-curvature** method.

## B.4 ThermoGIS — `data/ThermoGIS Data.xlsx`
The Dutch national geothermal database (TNO). For each well it gives expert
estimates of thickness, porosity, permeability, **transmissivity** (k×h), net-to-gross,
temperature, and an expected flow rate and power — each as a **P90/P50/P10** range
(pessimistic / most-likely / optimistic). We compute our own numbers from the raw
logs and **reconcile** against ThermoGIS; landing on the national database is strong
evidence we did it right.

## B.5 Target lithologies — `data/target_lithologies.csv`
A 3,455-row property table that shipped **deliberately broken**: every row flagged
"needs TVD conversion" with the TVD column empty, depths mislabelled (and in feet for
JUT-01). We reverse-engineered it, matched each row to its exact log sample by GR,
recovered the true depths, and cleared the flags (see C.1).

## B.6 The economics template — `LCOE.xlsx`
A TNO spreadsheet that computes the **LCOE** (levelised cost of energy) of a
heat-only project. We never edit it — it is our reference "answer key" — we rebuilt
its logic in Python and validate against it (C.6).

---

# Part C — What we built and found

The work is organised into workstreams (WS). For each: the idea, what the code does,
then the result.

## C.1 WS1 — Data foundation (`units`, `mdtvd`, `wells_io`, `lithostrat`, `targets`)
Get all the data into one clean, consistent, TVD-referenced table before any
analysis. We harmonise units (JUT-01 feet→metres, guarded against double-conversion),
mask the -999.25 nulls and physical-spike garbage, sort the two bottom-up-logged
wells, convert MD→TVD by minimum curvature (matched to the survey's own TVD column to
**better than 1 cm** on all four wells), pick the Slochteren interval, and repair the
broken target file. **Result:** a tidy ~99,000-row `well_logs.parquet`, the bedrock
everything stands on.

## C.2 WS2 — Petrophysics (`petrophysics.py`)
From the logs we compute **Vshale** (clay fraction, Larionov *older-rock* form — the
Rotliegend is ancient, so the young-rock formula would over-clean it), **porosity**
(from density, sandstone matrix 2.65 g/cc), and **net reservoir** (rock that passes
Vsh ≤ 0.40 **and** φ ≥ 0.08 — the standard NL cut-offs). **Result** — our independent
**net-to-gross (NTG)** per well:

| Well | Our NTG | ThermoGIS NTG | Read as |
|------|---------|---------------|---------|
| **BLT-01** | **0.93** | 0.98 | excellent — the anchor |
| EVD-01 | 0.55 | 0.99 | moderate |
| JUT-01 | 0.32 | 0.99 | poor (fault-complicated) |
| PKP-01 | 0.10 | 0.95 | very tight (matches k = 1 mD) |

**An honesty point we flag, not bury:** at the anchor our NTG (0.93) matches
ThermoGIS (0.98) — which is why we trust the BLT-01 numbers we build on. At the
weaker wells our log-based cut-offs are *stricter* than ThermoGIS's play-average, so
our NTG is lower; we trust the actual logs there, which makes our estimate the more
conservative. Crucially, our resource MWth is anchored on ThermoGIS's *own published
flow*, not on our NTG, so this disagreement sharpens the characterisation without
changing the Challenge-1 numbers.

## C.3 WS3 — How much heat can we deliver? (`deliverability.py`)
Two physics equations turn rock properties into delivered heat: **Darcy's law** (flow
rate from permeability, thickness and the pressure we apply) and the **thermal-power
equation** (Power = flow × heat capacity × temperature drop). We *calibrate* the
Darcy model so it reproduces ThermoGIS's own published flow and power — it matches to
**~1 %** on both productive wells at a single ~16.5-bar drawdown and 35 °C
reinjection. **Result:** a single BLT-01 doublet delivers about **5 MWth (P50)** —
half the heating demand. This is the finding that forces a two-doublet design.

## C.4 Uncertainty done honestly (`montecarlo.py`)
"5 MWth" is the middle estimate; geology is uncertain, so we report a **distribution**
from 10,000 Monte-Carlo draws. Three deliberate choices make it honest:
1. A **split (two-piece) lognormal** fit reproduces ThermoGIS's P90/P50/P10 *exactly*
   (a single-sigma fit overshoots BLT-01's published flow P10 and inflates the upside).
2. A **300 m³/h pump/sand-control cap** de-rates the unphysical optimistic tail (NL
   doublets run 100–300 m³/h; the surface choke, not the reservoir, sets the limit).
3. Two doublets are the **sum of two *independent* draws**, not one draw doubled —
   doubling one realisation would impose perfect correlation and *understate* the
   real two-site result.

**Result:**

| Scheme | P50 heat | Chance of clearing 10 MWth |
|--------|----------|----------------------------|
| 1 doublet @ BLT-01 | **5.05 MWth** | **29 %** |
| **2 doublets @ BLT-01** | **13.2 MWth** | **62 %** |
| 3 doublets @ BLT-01 | 19.2 MWth | 85 % |

The bounded single-doublet P10 is **14.6 MWth** (not the unbounded model's implausible
27) — no 77 °C doublet beats the ~13 MWth Dutch benchmark. **Two doublets are the
honest minimum**: better-than-even, with real headroom above the demand, and we size
the plant to the 10 MWth *delivered* demand so the surplus de-risks delivery rather
than flattering the economics. We treat independence as a labelled assumption and
bracket it: a fully-correlated pair (the conservative bound) gives ~10.1 MWth P50 /
~50 %, the independent case 13.2 / 62 %, and reality sits between — the scheme clears
10 MWth at P50 either way, so the conclusion is robust to it.

## C.5 Will it last? Thermal breakthrough (`reservoir_thermal.py`)
The cash flow assumes the produced temperature stays flat for the field life — true
only if the injected cold front has not reached the producer. Using the
**Gringarten-Sauty** doublet result (with the rock's heat capacity retarding the
front), breakthrough at 1.3 km spacing is **~177 years away** — far beyond the 30-year
life. This is a *homogeneous-reservoir* estimate (real heterogeneity would bring it
somewhat earlier; neglecting conduction pushes it later), so it is breakthrough-safe
with a large margin rather than a precise date, to be confirmed with a heterogeneous
transient simulation. Breakthrough only bites at spacings well below 1 km.

## C.6 WS4 — Surface design: A vs B (`surface.py`, `dispatch.py`)
The hot water arrives at the surface; how do we make **both** heating and cooling?
- **Design A (recommended): geothermal + ATES + heat pumps.** Heating from the
  geothermal loop with an electric **heat pump** (COP ≈ 4.2) trimming winter peaks.
  Cooling from **ATES** — cold banked in a shallow aquifer in winter, spent in summer
  — a seasonal "cold battery," with a heat pump trimming the hottest days.
- **Design B (contrast): absorption chiller.** Makes cold by *burning heat* (~7 MWth
  of geothermal heat to make 5 MWth of cold).

We do not just assume the load-hours: an **8,760-hour dispatch simulation** builds an
hourly Utrecht demand year and dispatches the supply stack. It shows that geothermal
sized to the full 10 MWth peak runs at only ~3,170 full-load hours (poor utilisation),
while **baseloading ~one doublet (~5 MWth) reaches ~6,000 hours at >90 % coverage** —
so the 6,000-hour assumption holds *only* under baseload operation, which is exactly
how Design A runs the geothermal and trims with heat pumps.

**Cooling is sized probabilistically.** A single ATES well pair delivers an uncertain
0.5–2.0 MWth, so we size off the *low* end: **6 pairs give a 99.8 % chance of meeting
the 5 MWth demand** (4 pairs would meet it only 29 % of the time once you honour the
uncertainty).

**Why Design A wins — honestly:** (1) it does not divert ~7 MWth of *saleable* heat to
make cold; (2) an absorption chiller wants 85–95 °C drive heat and our reservoir is
77 °C — marginal; (3) on cost the two are a *wash* (cooling LCOE 23.0 vs 23.4 €/GJ
once ATES is sized robustly). We deliberately do not claim a cost win the honest
sizing does not support.

## C.7 WS4 — Economics: the LCOE and beyond (`lcoe.py`, `lcoe_montecarlo.py`, `value_case.py`)
**LCOE** is the financed, after-tax break-even price per unit of energy — not
total-cost ÷ total-energy, but a number set by the 80/20 debt/equity split, loan
interest, depreciation, tax and a 15 % required return. We **rebuilt the TNO
spreadsheet's model in Python** and **gate** it: it must reproduce the workbook's
**5.769 €/GJ** reference before we trust a single number of our own (a unit test locks
this). We then extend it to cooling.

**Result (headline):**

| Quantity | Value |
|----------|-------|
| LCOE heat | **11.8 €/GJ** |
| LCOE cooling (Design A) | **23.0 €/GJ** |
| **Blended system LCOE** | **13.4 €/GJ** |
| Total capital cost | **≈ €21.3 M** (4 deep wells + surface kit) |
| TNO heat-only benchmark | 5.77 €/GJ |

**An honest caveat we make explicit (load factor).** The 11.8 €/GJ is the
*baseload* heat number — priced at 6,000 FLEQ, the utilisation geothermal needs to be
economic. Our own dispatch (C.6) shows a comfort-only, peak-sized doublet sees just
~3,170 FLEQ → ~21 €/GJ, which is exactly why we baseload the geothermal and trim peaks
with heat pumps. Cooling is the same: 23.0 €/GJ at 2,000 served-hours, but ~63 €/GJ at
the ~640 comfort-only hours. So we lead on the **blended** 13.4 €/GJ (robust — heat is
~86–95 % of delivered energy) and treat load factor as the headline sensitivity, not a
settled input.

We go past the point estimate in two ways most entries will not:
- **A probabilistic LCOE** (`lcoe_montecarlo.py`): propagating the bounded resource
  *and* cost/market uncertainty gives heat **P10/P50/P90 ≈ 10.8 / 12.6 / 26.7 €/GJ**.
  The heavy upper tail is the quantified cost of the resource under-delivering — the
  financial case for **staged appraisal**.
- **A Dutch SDE++ value case** (`value_case.py`): the scheme abates **~13 kt CO₂/yr**,
  needs **~3.8 €/GJ** of SDE++ support (**~€63 per tonne CO₂** — the metric the
  auction actually ranks on, well inside the fundable range), and clears the hurdle at
  an **equity IRR ≈ 21 %** with the subsidy. Run the asset to a 30-year life and the
  heat LCOE falls to ~10.7 €/GJ.

## C.8 WS5 — Bonus AI workflow (`pipeline.py`, `ml_logs.py`)
- **A one-command pipeline** (`python -m src.pipeline all`): raw LAS → cleaned logs →
  petrophysics → Monte-Carlo MWth → dispatch → ML → hybrid LCOE + probabilistic LCOE
  + value case. Reproducible from a clean install; reviewers can re-run it.
- **Honest ML log-prediction:** we train LightGBM to predict the missing curves and
  validate by **leave-one-well-out** cross-validation (the only honest measure of
  generalisation to an unseen well). Cross-well R²: DTC **0.51** (usable), RHOB
  **0.10**, NPHI **−0.20**. Our locked rule: where R² < 0.50 we **do not** trust the
  prediction and fall back to the ThermoGIS value — so with one fully-logged well and
  four distinct locations, we *prove* log-prediction is unreliable here rather than
  quietly trusting it. The AI value is the validated screen and the runnable pipeline,
  not a number we massage.

## C.9 How it all connects

```
 raw LAS ─► WS1 clean+TVD ─► WS2 petrophysics ─► rock properties (φ, k, NTG)
                                                          │
                          ThermoGIS P90/P50/P10 ──────────┤
                                                          ▼
                            WS3 Darcy flow + WS4 Monte-Carlo MWth (bounded, independent)
                                                          │
                            thermal breakthrough check ───┤
                                                          ▼
            ┌────────────────────────────────────────────┤
            ▼                          ▼                  ▼
  WS4 surface A/B + 8760-h     WS4 LCOE (heat+cool)   probabilistic LCOE + SDE++
       dispatch sizing               │                     value case
            └───────────────┬────────┴─────────────────────┘
                            ▼
                  tornado + LCOE_hybrid.xlsx + figures
```

---

# Part D — The story in five sentences

1. **Four wells, one clear winner.** BLT-01 is thick, porous, permeable and warm
   enough; the data says so three independent ways (ThermoGIS, our logs, our flow model).
2. **The resource is real but modest.** One doublet ≈ 5 MWth, so two doublets are the
   honest minimum — P50 13.2 MWth with a 62 % chance of clearing 10 MWth, the
   optimistic tail bounded to a physical pump limit, and breakthrough ~177 years away.
3. **Cooling is sized in real numbers** — 6 ATES well pairs for 99.8 % confidence —
   and Design A beats the absorption alternative on keeping saleable heat and on the
   physics of a 77 °C resource, with cost a wash.
4. **The economics are benchmarked, honest, and bankable:** blended ≈ 13.4 €/GJ
   (~2× the Dutch benchmark, explained precisely), reported as a distribution, and
   fundable under SDE++ at ~€63/tCO₂ for a ~21 % equity IRR.
5. **Everything is reproducible:** clean code, a green test suite, notebooks that run
   top-to-bottom, and a one-command pipeline from raw LAS to hybrid LCOE.

---

# Part E — Why you can trust the numbers

We built explicit checks so the work is verifiable rather than asserted:
- **TNO LCOE gate:** our engine reproduces the published 5.769 €/GJ to six decimals
  before any of our economics is trusted; a unit test fails if it ever drifts.
- **ThermoGIS reconciliation:** our independent Darcy model reproduces the national
  database's flow/power to ~1 %, and our petrophysics matches ThermoGIS at the anchor.
- **Honest uncertainty:** split-lognormal that hits all three published points, a
  physical pump cap on the optimistic tail, independent doublets, and a probabilistic
  LCOE that carries the resource downside instead of quoting a single comfortable number.
- **No vanity ML:** leave-one-well-out cross-validation with a documented fallback —
  we report the model failing and fall back, rather than trusting an in-sample fit.
- **A green, behaviour-specific test suite** locks every headline (the 5 MWth single
  doublet, the independent two-doublet result, the bounded tail, the cooling adequacy,
  the SDE++ consistency check). Run `python -m pytest` to see it pass.

---

# Part F — Applicability to African geothermal

This is a Dutch case study, but the **method** is the transferable asset, not the
numbers. The probabilistic resource workflow, the database-reconciliation discipline,
the financed LCOE engine and the one-command AI pipeline are geology-agnostic. What
does *not* transfer directly: most African geothermal is **high-enthalpy volcanic**
along the East African Rift (Kenya Olkaria/Menengai, Ethiopia Aluto/Corbetti),
developed for *power* — a different model from our low-enthalpy direct-use scheme.
Where *this* template genuinely fits: **North African / intracratonic sedimentary
basins** (Algeria, Tunisia, Egypt — direct-use heat) and, more relevantly for a
cooling-hungry continent, the **hybrid-cooling** half of our design for
cooling-dominated African cities. (Full discussion in Section 9 of the report.)

---

# Part G — Plain-English glossary

- **ATES (Aquifer Thermal Energy Storage):** storing heat/cold in a shallow aquifer
  between seasons — "charge a cold battery in winter, use it in summer."
- **Absorption chiller:** a machine that makes cooling by consuming heat (LiBr/H₂O
  cycle) rather than much electricity; wants ~85–95 °C drive heat.
- **Capex / Opex:** one-off build cost / ongoing running cost.
- **COP (Coefficient of Performance):** units of heat (or cold) moved per unit of
  electricity used; COP 4 = 4× a resistance heater.
- **Darcy's law:** the equation for fluid flow through porous rock under a pressure
  difference.
- **Dispatch simulation:** an hour-by-hour (8,760 h) match of supply to demand, used
  here to *derive* the load-hours instead of assuming them.
- **Doublet:** a producer + injector well pair forming the geothermal loop.
- **Drawdown:** the pressure difference applied to pull water from the rock (bar).
- **ΔT (delta-T):** the temperature drop extracted at the surface (production −
  reinjection temperature).
- **FLEQ (full-load-equivalent) hours:** annual energy ÷ peak capacity — how many
  hours per year the plant effectively runs flat-out.
- **Gringarten-Sauty:** the standard analytic result for doublet thermal breakthrough.
- **LCOE (Levelised Cost Of Energy):** the financed, after-tax break-even price per
  unit of energy delivered, after financing, tax and discounting; €/GJ here.
- **MD / TVD:** measured depth along the borehole / true vertical depth below surface.
- **Minimum curvature:** the standard maths for tracing a well's 3-D path from the
  deviation survey.
- **Monte-Carlo simulation:** estimating an uncertain result by random sampling many
  times and reading the distribution of outcomes.
- **Net-to-Gross (NTG):** the fraction of a rock layer that is good-quality reservoir.
- **P90 / P50 / P10:** pessimistic / most-likely / optimistic estimates from an
  uncertainty range.
- **Permeability (k, millidarcies):** how easily fluid flows *through* the rock — the
  make-or-break property.
- **Porosity (φ):** the fraction of the rock that is empty, fluid-fillable pore space.
- **Probabilistic LCOE:** the LCOE reported as a P10/P50/P90 distribution rather than a
  single number, by propagating resource and cost uncertainty.
- **Rotliegend / Slochteren Formation:** our target ~290-Ma sandstone reservoir.
- **SDE++:** the Dutch subsidy scheme that pays the gap between a project's cost price
  and the market value of the energy, ranked by subsidy per tonne of CO₂ avoided.
- **Split-lognormal:** a two-piece lognormal that reproduces all three of a P90/P50/P10
  band exactly (a single-sigma fit cannot).
- **Thermal breakthrough:** when injected cold reaches the producer and starts cooling
  it — a long-term risk managed by well spacing.
- **ThermoGIS:** the Dutch national geothermal resource database (TNO).
- **Transmissivity (k·h, Darcy-metres):** permeability × layer thickness — the rock's
  overall flow capacity.
- **Vshale (Vsh):** the shale/clay fraction (from gamma ray); high Vsh = poor reservoir.

---

# Part H — How to reproduce everything

```bash
# 1. Get the code and create the environment (Python 3.9–3.12)
git clone https://github.com/DEMILADE07/Vent_Squad_Geothermal_solution.git
cd Vent_Squad_Geothermal_solution
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (PowerShell / cmd)
pip install -r requirements.txt

# 2. Prove it works — the full test suite (bonus-ML tests self-skip if libomp is absent)
python -m pytest -q

# 3. Regenerate EVERYTHING the report and deck use, in one command
#    (processed data + all figures + LCOE workbook + executed notebooks)
python -m src.build_all

# 4. Or run the analysis end to end as a pipeline
python -m src.pipeline all          # ingest → petro → predict → dispatch → ml → lcoe

# 5. Explore the narrative notebooks
jupyter lab notebooks/              # 01_eda · 03_resource_montecarlo · 04_lcoe · 05_ml_logs
```

**Bonus-ML note:** the missing-log prediction uses LightGBM, whose compiled backend
needs the OpenMP runtime. Install it once if you want to run the ML stage — macOS
`brew install libomp`, Debian/Ubuntu `sudo apt-get install libgomp1`. Everything else
(every headline resource and economics number) reproduces without it.

---

# Use of AI tools & references

**Use of AI tools.** Per the datathon guidelines, we disclose that AI assistants were
used as a tool — to brainstorm, refine ideas, and speed up specified engineering
directives. All analysis, assumptions, and design decisions were made and validated by
the team, and every number is reproducible from our code (`python -m src.build_all`).

**References.** External data and methods are attributed in full in the report (Section 10).
In brief: ThermoGIS / DINOloket / NLOG (TNO) for reservoir and well data; the TNO LCOE
workbook (van Wees et al., 2012) for the economics reference; Larionov (1969) and
Wyllie et al. (1956) for petrophysics; Gringarten & Sauty (1975) for thermal
breakthrough; Fleuchaus et al. (2018) and Bloemendal & Hartog (2018) for ATES; and
ASHRAE and IEA HPT for surface-equipment performance.

---

*Questions about any of this are welcome — this document exists precisely so the
reasoning behind every number is open and checkable.*
— Team Vent Squad
