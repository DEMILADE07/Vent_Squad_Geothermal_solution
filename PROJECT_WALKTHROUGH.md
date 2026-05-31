# Vent Squad — Project Walkthrough & Team Tasks

**SPE Africa Geothermal Datathon 2026**
**Author / team lead:** Demilade
**Last updated:** 2026-05-31 (end of Day 3)

---

## How to read this document

I wrote this for the whole team. Nobody needs a geothermal background to follow
it — I start from the absolute basics and build up. If you already know a
section, skip it. The structure is:

- **Part A — The problem**, explained from zero.
- **Part B — The data** we were handed, and what each file actually is.
- **Part C — What I've built so far**, step by step, with the *concept first* and
  the *code second*, plus the key number that came out of each step.
- **Part D — The story we'll tell the judges** (the headline findings).
- **Part E — What's left to do.**
- **Part F — Your tasks**, split by person. At minimum everyone QAs (quality-
  checks) the part that matches their background.
- **Part G — A plain-English glossary** of every bit of jargon in the project.

Wherever I write a term in **bold the first time**, it's defined in the glossary
(Part G). The code all lives in the `src/` folder; the analysis you can run lives
in `notebooks/`; the tests that prove the code is correct live in `tests/`.

> **First thing to try:** clone the repo, then from the project folder run
> `.venv\Scripts\python.exe -m pytest -q`. If it says ~39 passed, your setup
> works and every number in this document is reproducible on your machine. (Full
> setup steps are at the very end, Part H.)

---

# Part A — The problem, from zero

## A.1 What is geothermal energy?

The ground gets hotter the deeper you go — roughly **30 °C per kilometre** in the
Netherlands. If you drill down ~2 km, the rock and the water trapped in it sit at
70–90 °C. **Geothermal energy** simply means pumping that hot water up, taking
the heat out of it at the surface, and pumping the now-cooler water back down so
the underground "battery" doesn't run dry. It's a heat source, not (in our case)
an electricity source — the water isn't hot enough to make power efficiently, but
it's perfect for heating buildings.

## A.2 What does our "customer" need?

We're designing a heat-and-cooling supply for a **district** (a neighbourhood /
cluster of buildings) in the **Utrecht region of the Netherlands**. The brief
gives us a demand to meet:

- **At least 10 MWth of heating** (in winter), and
- **At least 5 MWth of cooling** (in summer).

**MWth** = "megawatts thermal" = millions of joules of heat per second. Think of
10 MWth as roughly the heating need of a few thousand Dutch homes at once. The
"th" is there to distinguish heat power from electrical power (MWe).

So the job has two halves:
- **Challenge 1 (worth 60% of the score):** Is there enough hot water down there
  to deliver the heat? (A subsurface / geoscience question.)
- **Challenge 2 (worth 40%):** Design the surface plant — the pipes, pumps, heat
  exchangers and machines — that turns that hot water into both heating *and*
  cooling for the district, and work out what it costs. (An engineering +
  economics question.)
- **Bonus track:** Build an AI/automation tool that does part of this workflow by
  itself. (We haven't done this part yet — it's Day 4 work.)

## A.3 How do you get heat out of the ground? The "doublet".

You don't drill one hole — you drill **two**, working as a pair. This pair is
called a **doublet**:

1. The **producer** well brings hot water *up* from the deep sandstone layer.
2. At the surface, a **heat exchanger** takes the heat out of that water (like a
   car radiator) and hands it to a separate clean-water loop that runs to the
   district.
3. The **injector** well pumps the now-cooled water *back down* into the same
   layer, a safe distance away (~1.3 km), so the pressure underground stays up
   and we don't waste the water.

It's a closed loop underground: take water out hot, put it back cool, let the
rock reheat it over time. The two wells are ~1.3 km apart so the cold injected
water doesn't reach the producer too quickly (if it did, the producer would cool
down — that's called **thermal breakthrough**).

## A.4 Where exactly is the hot water? The "Rotliegend" reservoir.

Hot water alone isn't enough — it has to be in rock that can give it up fast
enough. The target rock layer is the **Rotliegend sandstone** (specifically a
unit called the **Slochteren Formation**), a ~290-million-year-old sandstone that
sits ~1.8–2.3 km deep under this area. It's the same rock that holds the famous
Groningen gas field, so it's well understood in the Netherlands.

Two properties decide whether a rock is a good geothermal **reservoir**:

- **Porosity** (symbol φ, "phi"): what fraction of the rock is empty pore space
  that can hold water. Think of a sponge vs. a brick. 17% porosity (our best
  well) means 17% of the rock volume is fluid-filled holes. Higher = more water
  stored.
- **Permeability** (symbol k, measured in **millidarcies, mD**): how easily water
  can *flow through* those connected pores. A sponge with big connected holes
  flows easily (high k); one with tiny isolated holes doesn't (low k). This is
  the single most important number for "can we pump water fast enough?".

A rock can be porous but not permeable (lots of storage, no flow). We need both.

## A.5 The honest tension in this project

Here's the punchline I want everyone to internalise, because it's the spine of
our whole story:

> The Dutch industry benchmark gets ~13 MWth of heat out of **one** doublet,
> because their reference reservoir is ~94 °C and very permeable. **Our** best
> reservoir is only **77 °C** and less permeable, so **one** doublet only gives
> us about **5 MWth — half the heating demand.** That means we need **two**
> doublets (four wells) to clear 10 MWth, which roughly doubles the drilling
> cost. We don't hide this — we prove it with the data and let it drive the
> design and the economics. Judges reward an honest, internally consistent story
> far more than a number that's been quietly massaged to look good.

---

# Part B — The data we were given

Everything lives in the `data/` folder. Here's what each item is, in plain terms.

## B.1 The four wells (LAS files) — `data/raw/*.las`

A **well log** is a record of measurements taken by instruments lowered down a
borehole, sampled every few centimetres of depth. A **LAS file** is the standard
text format these come in. We have four wells: **BLT-01, EVD-01, JUT-01,
PKP-01** (those are well names).

Each log curve measures something physical about the rock at each depth:

| Curve | What it measures | Why we care |
|-------|------------------|-------------|
| **GR** (gamma ray) | natural radioactivity | clays/shales are radioactive, clean sandstone isn't → tells us how "clean" the rock is |
| **RHOB** (bulk density) | density of the rock | lets us calculate porosity (more pore space = lower density) |
| **NPHI** (neutron porosity) | hydrogen content ≈ porosity | a second, independent porosity estimate |
| **DT / DTC** (sonic) | how fast sound travels through rock | a third porosity estimate, and rock strength |

The catch: **only BLT-01 has the full set of curves.** The other three are
sparse (some only have GR, density and sonic). That unevenness is exactly why the
**bonus AI track** makes sense — train a model on the well that has everything
(BLT-01) to *predict* the missing curves on the others.

Two data traps the brief warns about, both of which I handled in code:
- The number **-999.25** in a LAS file is not a measurement — it's the code for
  "no data here". It must be replaced with a blank before doing any maths, or it
  poisons every average.
- **JUT-01's depths are recorded in feet**, while the other three are in metres.
  Mixing them silently would wreck every depth-based comparison.

## B.2 Lithostratigraphy — `data/Lithostratigraphic Data.xlsx`

**Lithostratigraphy** = the named layers of rock, top to bottom, like a stack of
geological pancakes. This file says, for each well, "from depth X to depth Y the
rock is formation Z". We use it to find exactly where the Rotliegend / Slochteren
layer starts and stops in each well, so we only analyse the reservoir interval
and not the rock above it. It also marks **faults** (cracks where the rock layers
are offset) — these need careful handling because they can repeat or cut out
layers.

## B.3 Well-path / deviation surveys — `data/Well Path Data.xlsx`

Wells aren't drilled straight down — they slant. So there are two different
"depths":

- **MD (measured depth):** distance *along the borehole* (like the length of a
  bent straw).
- **TVD (true vertical depth):** the actual *straight-down* depth (how far below
  the surface you really are).

For a slanted well these differ a lot. The deviation survey lists, every so
often, the well's angle and direction, which lets us convert MD → TVD. **This
matters enormously:** porosity, temperature, and which layer you're in all depend
on *true vertical* depth. Comparing wells using MD would be comparing apples to
slanted oranges.

## B.4 ThermoGIS reservoir summary — `data/ThermoGIS Data.xlsx`

**ThermoGIS** is the Dutch national geothermal database (run by TNO, the Dutch
research institute). For each of our four wells it gives an expert estimate of
the reservoir's thickness, porosity, permeability, **transmissivity** (k×h — see
glossary), temperature, and even an expected flow rate and power — each as a
**P90 / P50 / P10** range (explained next). Think of this as a partial "answer
key" from the national experts. We don't blindly copy it; we compute our own
numbers from the raw logs and then **reconcile** (cross-check) against ThermoGIS.
When our independent calculation lands on their numbers, that's strong evidence
we did it right.

**P90 / P50 / P10 — what percentiles mean.** Geology is uncertain, so estimates
come as a range, not a single number:
- **P50** = the middle / most-likely value (50% chance the truth is higher, 50%
  lower).
- **P90** = a *pessimistic* value (90% chance the truth is *at least* this — so
  it's a low number).
- **P10** = an *optimistic* value (only 10% chance the truth is this good or
  better — a high number).

So "P90 < P50 < P10" in the resource sense (low / middle / high).

Here is the ThermoGIS table — read it and you already know why BLT-01 is our hero:

| Well | Thickness P50 (m) | Porosity (%) | Permeability P50 (mD) | Transmissivity (Dm) | Temp (°C) | Verdict |
|------|------|------|------|------|------|---------|
| **BLT-01** | **130** | **17** | **82** | **9.3** | **77** | **Sweet spot — our anchor well** |
| JUT-01 | 125 | 11 | 40 | 4.8 | 72 | Decent backup |
| PKP-01 | 60 | 9 | 1 | 0.1 | 88 | Hot but too tight (won't flow) |
| EVD-01 | 76 | 9 | 6 | 0.4 | 72 | Weakest all round |

## B.5 Target lithologies — `data/target_lithologies.csv`

A 3,455-row table of reservoir-property samples, one per well location. It shipped
**broken on purpose**: every row was flagged "needs TVD conversion", and the TVD
column was empty. Part of Day-1 work was reverse-engineering and fixing it (see
C.1). I found the file had its measured-depths mislabelled as vertical depths,
and JUT-01's were in feet — a trap. We fixed it in code and cleared the flags.

## B.6 The economics template — `LCOE.xlsx`

A spreadsheet from TNO that calculates the **LCOE** (Levelised Cost Of Energy) of
a geothermal heat project. LCOE is *the* headline economic number — see C.6 for a
full plain-English explanation. The stock spreadsheet only handles *heating*.
Challenge 2 asks us to extend it to *heating + cooling*, which is a big part of
what I built on Day 3. **I never edit the original file** — it's our reference
"answer key", so I rebuilt its logic in Python and validated against it instead.

---

# Part C — What I've built so far, step by step

The work is organised into **workstreams (WS)**. Days 0–3 are done. For each
workstream I give you the *idea*, then *what the code does*, then *the result*.

## C.1 WS1 — Data foundation (`src/units.py`, `src/mdtvd.py`, `src/wells_io.py`, `src/lithostrat.py`, `src/targets.py`)

**The idea.** Before any clever analysis, get all the data into one clean,
consistent, trustworthy table. Garbage in = garbage out, and a quiet bug here
would poison everything downstream.

**What the code does.**
- `units.py` converts JUT-01's feet to metres — and is built so that running it
  twice by accident won't double-convert (a real risk).
- `wells_io.py` loads all four LAS files, replaces every `-999.25` with "no
  data", throws out obviously broken spike values, and sorts the depths properly
  (two wells were logged bottom-to-top).
- `mdtvd.py` converts measured depth → true vertical depth using the **minimum-
  curvature method** (the industry-standard way to trace a curved borehole's true
  path; in plain terms, it fits the smoothest possible curve through the survey
  points). I checked our TVD against the values in the provided survey and they
  match to **better than 1 centimetre** on all four wells.
- `lithostrat.py` finds the Rotliegend/Slochteren layer in each well and handles
  the faults.
- `targets.py` fixes the broken `target_lithologies.csv` described in B.5.

**The result.** A single tidy table `well_logs.parquet` (~99,000 rows), every
sample tagged with its true vertical depth and clean. This is the bedrock
everything else stands on.

## C.2 WS2 — Petrophysics (`src/petrophysics.py`)

**Petrophysics** = turning raw log measurements into rock properties we can
reason about.

**The idea + what the code does.**
- **How clean is the rock? (Vshale)** From the gamma-ray curve we compute
  **Vshale** — the fraction of the rock that is shale/clay rather than clean
  sand. We use the **Larionov (older-rocks) formula** because the Rotliegend is
  ancient (~290 Ma); using the formula meant for young rocks would over-clean the
  answer. Shaly rock = bad reservoir, so this matters.
- **How much space? (Porosity, φ)** From the density curve, using the standard
  sandstone assumption (rock-grain density 2.65 g/cc, water 1.00 g/cc). Where a
  second porosity curve (NPHI) exists, we cross-check.
- **Net reservoir.** We only count rock that is actually good: Vshale ≤ 40% **and**
  porosity ≥ 8% (standard Dutch Rotliegend cut-offs). The fraction of the layer
  that passes is the **Net-to-Gross (NTG)**.

**The result** — our independent per-well table (`rotliegend_summary.csv`):

| Well | Net-to-Gross | Net porosity | Read as |
|------|------|------|---------|
| BLT-01 | **0.93** | **15%** | excellent — 93% of the layer is good reservoir |
| EVD-01 | 0.55 | 11% | moderate |
| JUT-01 | 0.32 | ~10% | poor (and structurally complicated by a fault) |
| PKP-01 | 0.10 | ~9% | very tight — matches ThermoGIS's k = 1 mD |

This independently confirms BLT-01 as the well to build around.

## C.3 WS3 — Resource: how much heat can we actually deliver? (`src/deliverability.py`)

**The idea.** Two physics equations turn rock properties into delivered heat.

1. **Flow rate — how fast can we pump? (Darcy's law)** There's a 150-year-old
   equation (**Darcy's law**) for how fast fluid flows through rock given the
   permeability, the thickness of the layer, and how hard we push (the pressure
   difference, called **drawdown**). More permeable + thicker + harder push =
   more flow. We express the rock's flow capacity as **transmissivity = k × h**
   (permeability times thickness).

2. **Heat power — how much heat is in that flow? (the thermal power equation)**
   `Power (MWth) = water flow × water heat capacity × temperature drop`. The
   "temperature drop" (**ΔT**, "delta-T") is how much we cool the water at the
   surface before reinjecting it — from 77 °C down to 35 °C, a ΔT of 42 °C for
   BLT-01.

**The reconciliation (why you can trust our numbers).** I calibrated our Darcy
model so that it **reproduces ThermoGIS's own published flow and power numbers**
(it matches to ~1% on the two good wells when we assume a realistic ~16.5-bar
drawdown and a 35 °C reinjection temperature). Because our independent physics
lands on the national database's numbers, we've earned the right to use the model
to explore "what-if" scenarios.

**The result.** A single BLT-01 doublet delivers about **5 MWth** (P50) — which
is *half* the heating demand. This is the key finding that forces a two-doublet
design.

## C.4 Monte-Carlo uncertainty (`src/montecarlo.py`)

**The idea.** "5 MWth" is the middle estimate, but geology is uncertain. Rather
than pretend we know the answer exactly, we run a **Monte-Carlo simulation**:
basically, roll the dice 10,000 times. Each "roll" draws a plausible value of the
reservoir's transmissivity (from the ThermoGIS P90/P50/P10 range), pushes it
through the flow + power equations, and records the resulting MWth. After 10,000
rolls you get a *distribution* of possible outcomes, not a single guess.

**What the code does.** Fits a statistical distribution to the ThermoGIS range,
draws 10,000 samples per well, computes MWth for each, and reports the P10/P50/P90
of the result plus **the probability of beating the 10 MWth demand**.

**The result:**

| Scheme | P50 heat | Chance of clearing 10 MWth |
|--------|------|------|
| 1 doublet at BLT-01 | 5.1 MWth | 31% |
| **2 doublets at BLT-01** | **10.1 MWth** | **50%** |

So two doublets is the honest minimum to have a coin-flip-or-better chance of
meeting demand — and it's why everything downstream assumes a 4-well scheme.

## C.5 WS4 — Surface design: Design A vs Design B (`src/surface.py`)

Now Challenge 2. The hot water arrives at the surface; how do we make **both**
heating and cooling from it? I sized two competing designs against the same
2-doublet heat source.

- **Design A (my recommendation): geothermal + ATES + heat pumps.**
  - Heating comes straight from the geothermal loop via heat exchangers, with an
    electric **heat pump** (a machine that moves heat, like a fridge run in
    reverse; very efficient — gives ~4 units of heat per 1 unit of electricity)
    to top up winter peaks.
  - Cooling comes from **ATES — Aquifer Thermal Energy Storage.** This is clever:
    in winter you store *cold* water in a shallow aquifer (a separate, shallow
    set of wells), then in summer you pull that cold back up to cool the
    district. It's like charging a "cold battery" in winter to spend in summer.
    An electric heat pump in chiller mode trims the hottest summer days.

- **Design B (the contrast): geothermal + absorption chiller.**
  - An **absorption chiller** is a machine that makes *cold* by *burning heat*
    (counter-intuitive, but real — it uses a lithium-bromide/water chemistry
    cycle). To make 5 MWth of cooling it needs about **7 MWth of driving heat**.

**Why Design A wins — and I made sure it won honestly, not by rigging it:**
1. **Cost:** once ATES is costed at the real Dutch range, Design A's cooling is
   *cheaper* per unit (17.5 vs 23.2 €/GJ — see C.6).
2. **It doesn't cannibalise our product:** Design B would divert ~7 MWth of heat
   — heat we're trying to *sell* — just to make cold. On a project where heat is
   already expensive, that's the wrong trade.
3. **Physics:** an absorption chiller really wants ~85–95 °C driving heat. Our
   reservoir is only **77 °C** — marginal-to-insufficient. That's a hard
   engineering knock against Design B regardless of cost.

## C.6 WS4 — Economics: the LCOE (`src/lcoe.py`, `src/build_lcoe_workbook.py`)

**What is LCOE?** **Levelised Cost Of Energy** is the single most important number
in energy economics. It answers: *"Over the whole life of the project, what is the
break-even price we'd have to charge per unit of energy to pay back every cost —
the drilling, the equipment, the maintenance, the loan interest, the tax — at the
investors' required rate of return?"* It's quoted in **euros per gigajoule
(€/GJ)** of heat or cold delivered. Lower = more competitive.

Crucially, LCOE is **not** "total cost ÷ total energy". It's a *financed* number:
the wells are paid for ~80% with a loan and ~20% with the investors' own money,
the loan accrues interest, the kit is depreciated for tax, and future euros are
discounted because money now is worth more than money later (we discount at the
investors' 15% required return). All of that is baked in. That financing
structure — not just the physics — is what sets the price.

**What I built.**
- I **rebuilt the TNO spreadsheet's entire financial model in Python**
  (`src/lcoe.py`). Rebuilding it (instead of editing the spreadsheet) lets us run
  hundreds of scenarios automatically and lets the bonus AI pipeline call it.
- I **gated it against the original**: my code must reproduce the spreadsheet's
  published answer of **5.769 €/GJ** to the third decimal before I trust it. It
  does, exactly. A test (`tests/test_lcoe.py`) locks this so we can never break it
  unnoticed.
- I then **extended it to cooling** (ATES wells, chillers, the cooling
  electricity) — the part the original spreadsheet can't do.
- `build_lcoe_workbook.py` writes our deliverable spreadsheet
  `data/processed/LCOE_hybrid.xlsx` with everything laid out (inputs, outputs,
  Design A vs B, and year-by-year cash flows). The original `LCOE.xlsx` is never
  touched.

**The result (our headline economics):**

| Quantity | Value |
|----------|-------|
| LCOE of **heat** | **11.7 €/GJ** (≈ 42 €/MWh) |
| LCOE of **cooling** (Design A) | **17.5 €/GJ** |
| Blended system LCOE | **12.5 €/GJ** |
| Total capital cost | **~€19.9 million** (4 deep wells + surface kit) |
| TNO heat-only benchmark | 5.77 €/GJ |

Our heat costs ~2× the Dutch benchmark — and we can explain *exactly* why: a
cooler, less productive reservoir needs four wells for 10 MWth instead of two for
13 MWth. That clean cause-and-effect from Challenge 1 → Challenge 2 is our edge.

## C.7 WS4 — Sensitivity tornado (`src/tornado.py`)

**The idea.** Which assumptions actually matter? A **tornado chart** takes each
input, swings it to a low and a high value, and draws how far the LCOE moves. The
biggest bars (drawn at the top, making a tornado shape) are the things worth
worrying about.

**The result** (`figures/lcoe_tornado.png`): the LCOE is **heat-dominated**. The
top drivers are **resource deliverability (MWth), heat load-hours, and drilling
cost.** The cooling-side knobs (ATES cost, cooling efficiency) barely move the
needle. Lesson for the team: getting the *subsurface* right matters far more than
fine-tuning the cooling plant.

## C.8 How it all connects

```
 raw LAS logs ─► WS1 clean+TVD ─► WS2 petrophysics ─► rock properties (φ, k, NTG)
                                                              │
                              ThermoGIS P90/P50/P10 ──────────┤
                                                              ▼
                                          WS3 Darcy flow + thermal power
                                                              │
                                                    WS4 Monte-Carlo MWth
                                                              │
                                  ┌───────────────────────────┤
                                  ▼                           ▼
                       WS4 Surface design A/B        WS4 LCOE (heat + cool)
                                  └───────────┬───────────────┘
                                              ▼
                                        Tornado + LCOE_hybrid.xlsx
```

---

# Part D — The story we'll tell the judges

1. **Four wells, one clear winner.** BLT-01 is thick, porous, permeable and warm
   enough; the data says so three independent ways (ThermoGIS, our logs, our
   flow model).
2. **The resource is real but modest.** One doublet ≈ 5 MWth, so we honestly
   need **two doublets** to meet the 10 MWth heating demand — and we put a
   probability on it (≈50% chance of clearing 10 MWth, with the full P10–P90
   range shown).
3. **Cooling is sized in real numbers**, not waved away: ATES + heat pumps
   (Design A), shown to beat the absorption-chiller alternative (Design B) on
   cost, on not cannibalising heat sales, and on the physics of our 77 °C water.
4. **Economics are benchmarked and honest:** blended LCOE ≈ 12.5 €/GJ, ~2× the
   Dutch heat benchmark, and we explain precisely why (cooler reservoir → more
   wells).
5. **Everything is reproducible:** clean code, 39 passing tests, notebooks that
   run top to bottom, and (soon) a one-command pipeline.

---

# Part E — What's still left to do (Days 4–5)

| # | Task | Status |
|---|------|--------|
| WS5.1 | **ML missing-log prediction** — train LightGBM on BLT-01 to predict the missing NPHI/DTC/RHOB curves on the other wells, with honest leave-one-well-out validation | not started |
| WS5.2 | **`pipeline.py`** — one command-line tool that runs the whole flow end to end (ingest → petrophysics → resource → LCOE) | not started |
| D2 | **Slide deck** (10–15 slides; outline already in `deliverables/deck_outline.md`) | outline only |
| D4 | **Technical report** (outline in `deliverables/report_outline.md`) | outline only |
| D3 | **3–5 min narrated video** | not started |
| — | **Team name slot is "Vent Squad"; still need each member's full name + SPE membership number** for the title slide | **needed from you all** |
| — | (Stretch) **Thermal-breakthrough check** — analytic estimate of how long until the injected cold water reaches the producer | optional |

---

# Part F — Your tasks

I've matched tasks to backgrounds. **Everyone's baseline job is to QA (quality-
check) the part that matches their expertise** — read the code/notebook, re-run
it, and challenge my assumptions. Finding a wrong assumption now is worth more
than any new feature. Put findings as GitHub issues or comments so we have a
trail. Replace "[name]" with yourself.

### F.1 — ML engineer, insurance background → **own the ML workflow** `[name]`

You're the lead on the bonus AI track (WS5.1), the part that needs real ML craft.
1. **Build the missing-log model.** Train a **LightGBM** regressor on BLT-01
   (the only well with all curves) to predict the curves the other wells are
   missing (NPHI, DTC, RHOB) from the curves they *do* have (GR, density, etc.).
   The clean training table is already sitting in `data/processed/well_logs.parquet`.
2. **Do the validation honestly — leave-one-well-out (LOO).** Train on three
   wells, test on the fourth, rotate. Report the **cross-well R²** (how well it
   predicts a well it never saw). This is the number judges trust; in-sample R²
   is vanity.
3. **Hyperparameter tuning.** This is your wheelhouse — tune learning rate, tree
   depth, number of leaves, regularisation, etc. Document what you tried and why.
4. **Define the fallback rule.** Where cross-well R² < 0.5 for a curve, we *don't*
   trust the prediction — we fall back to the ThermoGIS deterministic value. Make
   that rule explicit and write it into the report.
5. Deliverable: `notebooks/05_ml_logs.ipynb` with the LOO-CV table, plus a short
   write-up. (I'll wire your model into the pipeline.)

### F.2 — ML engineer, chemical engineering background → **simulation + LCOE deep-review** `[name]`

Your process-engineering background is perfect for the physics and economics.
1. **QA the deliverability physics** (`src/deliverability.py`): check my Darcy-law
   flow model, the fluid properties (viscosity, density, heat capacity at 77 °C),
   and the thermal-power equation. Are my brine properties right? Is 16.5 bar a
   defensible drawdown?
2. **Deep-review the LCOE model** (`src/lcoe.py`): I rebuilt the TNO financial
   model from scratch — sanity-check the cash-flow logic (depreciation, loan
   amortisation, tax, the 15% discount). The validation gate (reproduces 5.769
   €/GJ) is your friend here.
3. **Pressure-test the surface-design assumptions** (`src/surface.py`,
   `src/lcoe.py`): heat-pump COP (4.2), ATES cost (€0.7M/pair), cooling COP (10),
   absorption-chiller behaviour at 77 °C. Tell me which are too optimistic.
4. **(Stretch) Thermal-breakthrough check:** an analytic estimate
   (Gringarten/Lauwerier) of how many years until the injected cold reaches the
   producer at 1.3 km spacing. This strengthens the risk section a lot.

### F.3 — Data scientist / Geophysics (early-stage), with me → **geoscience QA lead** `[name]`

You and I share the geoscience background, so we co-own the credibility of
Challenge 1. We'll pair on this.
1. **QA the petrophysics** (`src/petrophysics.py`): is the Larionov-older Vshale
   the right choice? Are the porosity calc (density, 2.65 g/cc matrix) and the
   net cut-offs (Vsh ≤ 0.4, φ ≥ 0.08) defensible for the Rotliegend?
2. **QA the layer picks** (`src/lithostrat.py`): did we pick the
   Rotliegend/Slochteren interval correctly in each well, especially the messy
   JUT-01 (fault repeat + the feet/metre bug)?
3. **QA the MD→TVD conversion** (`src/mdtvd.py`) and the `target_lithologies.csv`
   fix — these underpin every depth in the project.
4. **Cross-check against literature:** do our per-well numbers look like real
   Dutch Rotliegend wells? Pull a couple of public ThermoGIS/DINOloket examples.
5. Work with me on the **geoscience narrative** for the report and deck — this is
   great practice and it's 60% of the marks.

### F.4 — Petroleum & gas engineering student → **support: benchmarks + economic inputs** `[name]`

A focused support role — pick these up when you can; they make the others'
work more defensible.
1. **Find real-world benchmarks** for our key assumptions and tell me if we're in
   range: Dutch Rotliegend doublet **flow rates** (typically 100–300 m³/h),
   **drilling cost per metre**, **ATES system costs**, heat-pump COPs. Cite
   sources — the brief *requires* us to document external data.
2. **QA the economic inputs** in `LCOE_hybrid.xlsx` against industry figures:
   well cost, surface-plant cost, electricity price, load-hours.
3. **Sanity-check the doublet design** (1.3 km spacing, well depth ~2 km, 8.5"
   hole) against standard practice.
4. Coordinate with F.2 (chemical-eng) — you're both on simulation + LCOE.

### F.5 — Me (Demilade), team lead → coordination + assembly

I'll keep building (WS5 ML + pipeline next), pair with F.3 on geoscience, then
assemble the deck, report and video, and integrate everyone's QA findings. I'll
also collect everyone's **full name + SPE membership number** for the title slide
— please send these to me ASAP, they block the deck.

### F.6 — How to give feedback / contribute

- Clone the repo (Part H), run the tests, run the notebooks.
- Found a problem or a better assumption? Open a **GitHub issue** describing it,
  or message me. If you can code the fix, branch off `main`, keep commits small
  and clearly described, and open a pull request.
- **Authorship note:** all commits and written work are attributed to us as a
  team — please don't add any AI/tool co-author tags to commits.

---

# Part G — Plain-English glossary

- **Aquifer:** an underground layer of rock that holds and transmits water.
- **ATES (Aquifer Thermal Energy Storage):** storing heat or cold in a shallow
  aquifer between seasons — "charge a cold battery in winter, use it in summer".
- **Absorption chiller:** a machine that makes cooling by consuming heat (via a
  lithium-bromide/water cycle) instead of much electricity.
- **Capex / Opex:** capital expenditure (one-off build cost) / operating
  expenditure (ongoing running cost).
- **COP (Coefficient of Performance):** for a heat pump, units of heat (or cold)
  moved per unit of electricity used. COP 4 = 4× as efficient as a resistance
  heater.
- **Darcy's law:** the equation for how fast fluid flows through porous rock under
  a pressure difference.
- **Deviation survey / well path:** the record of a well's angle and direction
  with depth, used to convert MD to TVD.
- **Doublet:** a producer + injector well pair forming the geothermal loop.
- **Drawdown:** the pressure difference we apply to pull water from the rock
  (measured in bar).
- **ΔT (delta-T):** the temperature drop we extract from the water at the surface
  (production temp − reinjection temp).
- **Heat exchanger:** a device that transfers heat between two fluids without
  mixing them (like a car radiator).
- **Heat pump:** a machine that moves heat from one place to another using
  electricity; run forwards it heats, reversed it cools.
- **LAS file:** the standard text file format for well-log data.
- **LCOE (Levelised Cost Of Energy):** the lifetime break-even price per unit of
  energy delivered, after financing, tax and discounting; €/GJ here.
- **Lithostratigraphy:** the named sequence of rock layers with depth.
- **MD (Measured Depth):** distance measured *along* the (curved) borehole.
- **Minimum-curvature method:** the standard maths for tracing a well's true 3-D
  path from the deviation survey.
- **Monte-Carlo simulation:** estimating an uncertain result by random sampling
  many times and looking at the distribution of outcomes.
- **MWth / MWe:** megawatts of *thermal* power (heat) / *electric* power.
- **Net-to-Gross (NTG):** the fraction of a rock layer that is good-quality
  reservoir.
- **P90 / P50 / P10:** pessimistic / most-likely / optimistic estimates from an
  uncertainty range.
- **Permeability (k, millidarcies mD):** how easily fluid flows *through* the
  rock. The make-or-break property.
- **Petrophysics:** converting well-log measurements into rock properties.
- **Porosity (φ):** the fraction of the rock that is empty, fluid-fillable pore
  space.
- **Reservoir:** a rock body that can store and yield fluids (here, hot water).
- **Rotliegend / Slochteren Formation:** our target ~290-million-year-old
  sandstone reservoir.
- **Thermal breakthrough:** when injected cold water reaches the producer well and
  starts cooling it — a long-term risk to manage via well spacing.
- **ThermoGIS:** the Dutch national geothermal resource database (TNO).
- **Transmissivity (k·h, Darcy-metres Dm):** permeability × layer thickness — the
  rock's overall flow capacity.
- **TVD (True Vertical Depth):** straight-down depth below surface.
- **Vshale (Vsh):** the fraction of the rock that is shale/clay (computed from
  gamma ray); high Vshale = poor reservoir.

---

# Part H — How to set up and run the project

```bash
# 1. Get the code
git clone https://github.com/DEMILADE07/Vent_Squad_Geothermal_solution.git
cd Vent_Squad_Geothermal_solution

# 2. Create the Python environment (Python 3.12) and install pinned deps
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 3. Prove everything works (should be ~39 passing)
python -m pytest -q

# 4. Rebuild the processed data from raw (optional; outputs are gitignored)
python -m src.build_processed

# 5. Run the analysis notebooks (top to bottom)
jupyter lab                     # then open notebooks/01_eda.ipynb and 04_lcoe.ipynb

# 6. Regenerate the hybrid LCOE workbook and the tornado figure
python -m src.build_lcoe_workbook        # -> data/processed/LCOE_hybrid.xlsx
python -m src.tornado                     # -> figures/lcoe_tornado.png
```

If `git clone` asks for a login you don't have, ping me — I'll add you as a
collaborator on the repo.

---

*Questions about any of this? Ask me. Nothing here is too basic to ask about —
this document exists precisely so we're all on the same page.*
— Demilade
