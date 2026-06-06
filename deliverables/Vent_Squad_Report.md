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

*Version 1 — 2026-06-06. All numbers in this report are produced by the team's
code (`src/`), unit-tested, and reproducible end-to-end from a fresh clone via
`pip install -r requirements.txt` then `python -m src.build_all`.*

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
heating demand I therefore size a **two-doublet (four-well) scheme**. Modelling the
two doublets as *independent* reservoir realisations — two separate well pairs in
the same fairway sample the resource independently — and bounding each draw at a
300 m³/h pump/sand-control ceiling so the optimistic tail stays physical, the
scheme reaches a P50 of **13.2 MWth** with a **62 % probability of clearing
10 MWth**. That is comfortably resource-adequate with headroom, not a number I have
massaged: the single doublet still falls well short, so two doublets remain the
honest minimum.

For the surface system I recommend **Design A: geothermal doublets → plate heat
exchangers → district hot loop, with cooling from seasonal ATES (aquifer thermal
energy storage) trimmed by electric heat pumps.** It wins on three counts, in order
of strength: it does **not** divert ~7 MWth of saleable heat to make cold (Design B
does); a LiBr/H₂O absorption chiller wants 85–95 °C drive heat, above our 77 °C
resource; and even after sizing ATES robustly to clear the cooling demand at the
low-throughput end, its cooling LCOE (**23.0 €/GJ**) is on par with — marginally
below — the absorption route (**23.4 €/GJ**). I do not claim a large cost win on
cooling; the case for Design A is that it keeps the heat we are in business to sell
and works at our actual reservoir temperature.

The economics are benchmarked and honest. My LCOE engine reproduces the TNO
reference workbook to **5.769 €/GJ** before I trust any of my own numbers. On that
footing, the hybrid scheme delivers **heat at 11.8 €/GJ, cooling at 23.0 €/GJ, a
blended 13.4 €/GJ**, for **≈ €21.3 M** of capital. That heat price is ~2× the Dutch
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

| Well | Gross (m) | Net (m) | **My NTG** | φ_net | ThermoGIS NTG | ThermoGIS φ / k / kh / T |
|------|-----------|---------|------------|-------|---------------|--------------------------|
| **BLT-01** | 122.4 | 113.8 | **0.93** | **0.150** | 0.98 | 17 % / 82 mD / 9.3 Dm / 77 °C |
| EVD-01 | 76.8 | 42.1 | 0.55 | 0.109 | 0.99 | 9 % / 6 mD / 0.4 Dm / 72 °C |
| JUT-01 | 133.0 | 42.3 | 0.32 | 0.099 | 0.99 | 11 % / 40 mD / 4.8 Dm / 72 °C |
| PKP-01 | 64.4 | 6.6 | 0.10 | 0.091 | 0.95 | 9 % / 1 mD / 0.1 Dm / 88 °C |

**A deliberate disagreement on NTG, declared not hidden.** At the anchor well my
log-based net-to-gross (**0.93**) closely matches the ThermoGIS regional figure
(0.98), which is what gives me confidence in the BLT-01 numbers I build the design
on. At the three weaker wells my NTG is markedly *lower* than ThermoGIS's
0.95–0.99. That is not an error: ThermoGIS publishes a play-average net-to-gross,
whereas I apply explicit sample-by-sample cut-offs (**V_sh ≤ 0.40 AND φ ≥ 0.08**) to
the actual logs, which strips the shalier, tighter intervals that a regional average
smooths over — PKP-01's 0.10, for instance, reflects log character consistent with
its ThermoGIS permeability of just 1 mD. I trust the well-specific logs over the
play-average where they disagree, which makes my estimate the **more conservative**
of the two. Crucially, this does not distort Challenge 1: my resource MWth is
anchored on ThermoGIS's *own* published flow-rate distribution (§3.4), not on my
NTG, so the disagreement changes none of the deliverability numbers — it only makes
my characterisation of the non-anchor wells stricter. (See *Appendix B* for the
BLT-01 petrophysical track and MD→TVD QC plots.)

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

**Probabilistic MWth** (`src/montecarlo.py`). I fit a **split (two-piece) lognormal**
to the ThermoGIS flow P90/P50/P10 band so the sampled distribution reproduces all
three published points *exactly* — a single-sigma fit overshoots BLT-01's published
flow P10 (≈551 vs 469 m³/h) and inflates the optimistic resource. I then **cap each
draw at a 300 m³/h pump/sand-control ceiling** (NL Rotliegend doublets run
~100–300 m³/h; the surface choke, not the reservoir, sets the limit), which de-rates
only the unphysical upper tail and leaves the P50 untouched. A *k*-doublet scheme is
the **sum of *k* independent** single-doublet realisations — two well pairs sample
the play independently, so I do not collapse them to one shared realisation
(rescaling a single draw by *k* would impose perfect correlation and force
P(2× ≥ 10) = P(× ≥ 5), understating the genuine two-site result):

| Scheme | P90 | **P50** | P10 | Mean | **P(MWth ≥ 10)** |
|--------|-----|---------|-----|------|------------------|
| 1 doublet @ BLT-01 | 0.86 | **5.05** | 14.6 | 6.6 | **29 %** |
| **2 doublets @ BLT-01** | 3.76 | **13.2** | 23.1 | 13.2 | **62 %** |
| 3 doublets @ BLT-01 | 8.06 | 19.2 | 31.8 | 19.8 | 85 % |
| 1 doublet @ JUT-01 | — | 2.39 | — | — | 0.5 % |

The bounded single-doublet P10 (**14.6 MWth**, mean 6.6) is the honest replacement
for the unbounded model's implausible 27 MWth tail; no 77 °C doublet outproduces the
~13 MWth Dutch benchmark. EVD-01 and PKP-01 carry a ThermoGIS flow of zero — they
are non-productive and are not candidate doublet sites. (Distribution chart:
`figures/mc_mwth_blt.png`.)

**Independence is a labelled assumption, and I bracket it.** Two doublets 1.3 km apart
share the regional geology (positive correlation) but sample local heterogeneity
separately (independence), so the truth lies between two bounds I can both compute:
the **fully-correlated** case (one shared draw, the most conservative) gives a
two-doublet P50 of **≈ 10.1 MWth with P(≥10) ≈ 50 %**, while the **independent** case
(my central estimate) gives **13.2 MWth / 62 %**. The design decision is robust across
the whole range — the scheme clears 10 MWth at P50 *either way* — so the
correlation assumption changes the comfort margin, not the conclusion. I report the
independent case as the headline and the correlated case as the conservative floor.

**The conclusion the data forces:** one doublet does not meet the heating demand
(only 29 % likely). **Two doublets are the honest minimum** — they lift the P50 to
13.2 MWth and the probability of clearing 10 MWth to 62 %, better than even with
real headroom above the demand — and everything downstream assumes the four-well
scheme. I size the surface plant and LCOE to the 10 MWth *delivered* demand, not to
the 13.2 MWth resource P50, so the resource surplus de-risks delivery rather than
inflating the economics.

**Doublet siting.** A 5-criterion weighted matrix (deliverable MWth ×4, distance
to demand ×2, thermal-breakthrough risk ×2, surface footprint ×1, subsurface
uncertainty ×1) ranks the BLT-01 vicinity first by a clear margin; the matrix
exists to make an obvious call auditable. Producer–injector spacing of ~1.3 km
follows NL precedent and manages thermal breakthrough.

**Thermal breakthrough — quantified, not deferred** (`src/reservoir_thermal.py`).
Using the Gringarten-Sauty doublet result with the reservoir's bulk volumetric heat
capacity (the thermal front lags the tracer because it must also cool the rock
matrix), the injected cold front reaches the producer at **t_bt ≈ 177 years** for the
1.3 km spacing — far beyond the 30-year economic life, so the cash flow's constant-MWth
assumption is supported by a very large margin. Two caveats pull in opposite
directions and do *not* cleanly cancel: neglecting conduction from the over/under-burden
is **conservative** (it pushes breakthrough later), but the closed form assumes a
**homogeneous** reservoir, whereas real heterogeneity and preferential flow would bring
it earlier. So this is **breakthrough-safe on a homogeneous estimate** with a
177-yr-to-30-yr margin to absorb that optimism — comfortable, but to be confirmed with
the transient heterogeneous simulation flagged in next steps. Breakthrough only becomes
a near-term design constraint at spacings well below 1 km.

### 3.5 Cross-well validation (bonus AI)

See §7 for the leave-one-well-out result. The short version: cross-well log
prediction is **not** reliable enough on these four distinct wells to feed the
resource calc, so I fall back to ThermoGIS deterministic values for the missing
curves — and I prove that with an honest R², rather than trusting an in-sample fit.

---

## 4. Surface design (Challenge 2)

### 4.1 Demand-side characterisation

Heating is winter-baseload; cooling is summer-peaky, so cooling is sized off the
**August peak**, not the annual mean. The load-duration shape is what makes seasonal
storage (ATES) attractive: cold banked cheaply in winter is spent against the summer
peak.

**Load-hours derived, not assumed** (`src/dispatch.py`). Rather than typing in the
6,000 FLEQ hours the LCOE leans on, I build an **8,760-hour** demand year from a
synthetic-but-realistic Utrecht temperature profile (space heat + DHW baseload;
temperature-driven cooling) and dispatch the supply stack against it (geothermal →
heat-pump trim → backup; ATES → chiller). The result is a sharp, defensible finding:
geothermal sized to the *full 10 MWth peak* runs at only **~3,170 FLEQ hours** (heat
LCOE ≈ 21 €/GJ — peaky demand wastes a peak-sized doublet), whereas **baseloading
~one doublet (~5 MWth) reaches ~6,000 FLEQ at >90 % annual-energy coverage**, with
the heat pump picking up the peak. So the 6,000-hour assumption is only valid under
**baseload operation** — which is exactly how the recommended scheme runs the
geothermal and trims with heat pumps. The same simulation confirms the cooling peak
of 5 MWth and, at the conservative 1 MWth/pair throughput, a deterministic-peak ATES
need of 5 pairs — below the 6 the probabilistic sizing (§4.2) carries for confidence.

### 4.2 Design A — geothermal + ATES + heat pumps (recommended)

Geothermal doublets → plate-and-frame heat exchanger → district hot loop. An
electric heat pump (COP ≈ 4.2, IEA HPT range) trims winter heat peaks. **Cooling**
comes from **ATES**: cold is stored in a shallow aquifer over winter and recovered
in summer, with an electric heat pump in chiller mode trimming the hottest days.

**ATES is sized probabilistically, not to a comfortable midpoint.** A single
warm/cold pair delivers an uncertain 0.5–2.0 MWth of cooling (Fleuchaus et al.,
2018; Bloemendal & Hartog, 2018), so I treat the per-pair throughput as a triangular
distribution (mode 1.0 MWth) and size the pair count off the *low* end. At
**6 pairs** the Monte-Carlo probability of meeting the 5 MWth demand is **99.8 %**,
and even the conservative P90 supply (6.0 MWth) clears it — whereas the 4 pairs a
midpoint estimate would suggest meet the demand only 29 % of the time once the
throughput uncertainty is honoured. Round-trip efficiency ~70 %; blended system
cooling COP ≈ 10 (ATES circulation at COP ~20–30 plus a heat-pump trim at COP ~4.5,
a ~70/30 split), giving ~1,000 MWh/yr of cooling electricity. The full surface
schematic is in `figures/design_a_schematic.png`.

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
| Cooling LCOE | **23.0 €/GJ** | 23.4 €/GJ |
| Geo heat consumed for cooling | **0 MWth** | 7.1 MWth |
| Total capex | €21.3 M | €17.8 M |
| Cooling electricity | ~1,000 MWh/yr | ~400 MWh/yr |

1. **It doesn't cannibalise the product** — Design B diverts ~7.1 MWth of saleable
   heat to drive the chiller, on a project where heat is already our expensive,
   revenue-generating output. 2. **Physics** — a single-effect LiBr/H₂O absorption
   chiller wants 85–95 °C drive heat (ASHRAE); our reservoir is 77 °C,
   marginal-to-insufficient. 3. **Cost** — once ATES is sized *robustly* (6 pairs,
   §4.2) rather than to an optimistic midpoint, Design A's cooling LCOE is on par
   with Design B, marginally below it. I deliberately do **not** lean the
   recommendation on a large cost advantage that the honest sizing does not support;
   Design A wins on keeping the heat and on the thermodynamics, with cost a wash.
   Design B is lower-capex but loses on both.

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
| LCOE heat | **11.8 €/GJ** (≈ 42 €/MWh) |
| LCOE cooling | **23.0 €/GJ** |
| Blended system LCOE | **13.4 €/GJ** |
| Subsurface capex (4 wells + pumps) | €15.0 M |
| Heat-plant capex | €1.5 M |
| Cooling capex (6 ATES pairs + chiller) | €4.8 M |
| **Total capex** | **€21.3 M** |
| TNO heat-only reference | 5.77 €/GJ |

**Sensitivities (tornado, `figures/lcoe_tornado.png`).** The LCOE is
**heat-dominated**: the top drivers are heat delivered (MWth), heat load-hours, and
drilling cost per metre. The cooling-side knobs (ATES capex, cooling COP) barely
move the blended number — even though robust ATES sizing pushed cooling capex up,
cooling is only ~12 % of delivered GJ, so it cannot drive the blend. The lesson is
strategic: getting the *subsurface* right matters far more than fine-tuning the
cooling plant.

Our heat at ~2× the Dutch benchmark is fully explained by Challenge 1: a cooler,
less productive reservoir needs four wells for 10 MWth where the benchmark needs two
for 13 MWth. That clean cause-and-effect is the spine of the report.

**Reconciling the load factor — the honest caveat behind 11.8 €/GJ.** This number is
priced at **6,000 full-load-equivalent (FLEQ) hours** — the utilisation that
direct-use geothermal *needs* to be economic, and that NL schemes routinely reach by
baseloading high-load-factor heat customers. My own 8,760-hour dispatch (§4.1) is
deliberately explicit about the consequence: a doublet *peak-sized to this district's
comfort heat demand and run comfort-only* sees just **~3,170 FLEQ → ~21 €/GJ**,
because space-heat demand is peaky. That is exactly why the design runs the
geothermal as **baseload** (its cheapest MWh) and meets the winter peak with heat
pumps, and why a viable scheme must serve a heat load with ~6,000-FLEQ utilisation
(district space heat + year-round DHW + ATES warm-side regeneration, with the
13.2 MWth resource P50 giving headroom to serve adjacent demand). So **11.8 €/GJ is a
*baseload* number and ~21 €/GJ a *comfort-peak-only* one** — not a contradiction but
the same physics seen two ways, and load factor is the single largest heat-LCOE lever
in the tornado. **Cooling carries the identical caveat:** at the 2,000 served-hours
typical when geothermal-assisted cooling also serves process or longer-season loads
it is **23.0 €/GJ**, but at the **~640 comfort-only hours** the dispatch derives for
this district the same plant prices at **~63 €/GJ**. I therefore lead on the
**blended** system LCOE (13.4 €/GJ), which is robust to both because heat is
~86–95 % of delivered energy, and treat load factor as a headline sensitivity rather
than a settled input.

**The LCOE is a *distribution*, not a point** (`src/lcoe_montecarlo.py`). The
headline number's dominant input is the resource — itself a probability — so I
propagate the bounded resource Monte-Carlo *and* the cost/market uncertainty
(drilling cost, load-hours, electricity price, ATES capex/COP — triangular ranges
anchored to the tornado swing points) through the financed model. The heat LCOE
comes out at **P10/P50/P90 ≈ 10.8 / 12.6 / 26.7 €/GJ** (blended 12.5 / 14.4 / 25.8).
The P50 sits just above the deterministic point because delivery is demand-capped —
resource *upside* cannot cheapen the unit cost, while resource *shortfall* lifts it,
so the heavy upper tail is precisely the quantified cost of the resource
under-delivering. That tail is deliberately **unconditional** — it prices building
the full four-well scheme even into a resource one would in practice abandon at the
pilot, so the conditional-on-developable distribution is tighter — and that is exactly
the financial case for **staged appraisal** (drill and test one well before committing
the scheme), which truncates the worst outcomes. The result is reported per hurdle
rate (10 / 15 / 20 %) rather than blurred into one cloud, since the required return is
a financing choice, not a geological draw.

**Asset life.** The TNO reference depreciates and prices over the 15-year loan, but a
geothermal doublet delivers heat well beyond it. Running the same scheme to a 30-year
economic life (loan unchanged) lowers the heat LCOE to **≈ 10.7 €/GJ** — a legitimate
improvement I flag but do not bank in the headline, which stays on the conservative
15-year basis.

**From cost to fundability — the SDE++ value case** (`src/value_case.py`). LCOE says
what a GJ costs to make; a Dutch investment board asks what subsidy it needs and
whether it clears the hurdle. The scheme abates **≈ 13 kt CO₂/yr** (displaced
gas-fired heat, net of its own grid electricity). Under **SDE++** — which pays the
gap between the cost price (our LCOE) and the gas-linked market reference — it needs
**≈ 3.8 €/GJ** of support, i.e. **≈ €63 per tonne CO₂ avoided**, comfortably inside
the fundable range (well under the ~€300/t SDE++ ceiling) and the metric the auction
actually ranks on. With that top-up the equity **IRR is ≈ 21 %** against a 15 %
hurdle; without it the project is under water at a gas-linked tariff — which is
exactly the gap SDE++ exists to bridge. (As an internal check, a flat tariff equal to
the LCOE returns the 15 % hurdle exactly — the value model *is* the LCOE model,
extended.)

---

## 6. Risks, assumptions, and limitations

| Risk | Mitigation / note |
|------|-------------------|
| **Thermal breakthrough** — injected cold reaching the producer | **Quantified** (`src/reservoir_thermal.py`): Gringarten-Sauty t_bt ≈ 177 yr at 1.3 km spacing ≫ 30-yr life, so produced temperature holds flat — the constant-MWth assumption is validated, not assumed. |
| **Resource optimism** (top LCOE driver) | Full P10–P90 propagated, with the optimistic tail bounded by a 300 m³/h pump ceiling; the headline is the two-doublet P50 (13.2 MWth) with P(≥10) = 62 % stated plainly, the LCOE sized on the 10 MWth *delivered* demand, and the resource downside carried explicitly in the probabilistic LCOE tail (§5). |
| **ATES sizing** | Per-pair throughput probabilised (0.5–2.0 MWth, triangular); sized to clear 5 MWth at the low end — 6 pairs give P(supply ≥ 5 MWth) = 99.8 % and a conservative P90 supply of 6.0 MWth. |
| **ATES regulatory risk (NL)** | Dutch ATES permitting is well-established but site-specific; flagged for the permitting phase. |
| **Drilling cost volatility** | Among the top three LCOE sensitivities; carried in the tornado. |

**Key assumptions (all sourced — see Appendix E):** reinjection 35 °C; drawdown
~16.5 bar (back-solved from ThermoGIS flow); producer–injector spacing 1.3 km;
electricity €150/MWh; heat 6,000 / cooling 2,000 load-hours; HP COP 4.2 (IEA HPT);
absorption COP_th 0.7 needing 85–95 °C drive heat (ASHRAE); ATES €0.7 M/pair
(NL 0.5–0.8) at 0.5–2.0 MWth/pair (Fleuchaus 2018). **Model limitations:** 1-D
well-based rather than 3-D static; no geomechanics; no detailed network hydraulics
or transient simulation. These are feasibility-appropriate and named, not hidden.

---

## 7. AI-assisted workflow (bonus)

**`pipeline.py` — the workflow, not a notebook.** A typer CLI runs the whole chain
deterministically, each stage persisting an artefact the next consumes:

```
python -m src.pipeline ingest    # raw LAS  -> well_logs.parquet (+ recovered targets)
python -m src.pipeline petro     #          -> rotliegend_summary.csv (+ deliverability)
python -m src.pipeline predict   #          -> mc_mwth.parquet (Monte-Carlo MWth)
python -m src.pipeline dispatch  #          -> dispatch_summary.csv (8760-h load-hours)
python -m src.pipeline ml         #          -> ml_loo_cv.csv + ml_log_predictions.parquet
python -m src.pipeline lcoe      #          -> LCOE_hybrid.xlsx + lcoe_mc_summary.csv + value_case.csv
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
MWth (P50, only 29 % likely to clear 10); two independent doublets reach a P50 of
**13.2 MWth** with a **62 %** probability of clearing the heating demand — stated as
a probability, not a promise, with the plant sized to the 10 MWth delivered demand
and the optimistic tail bounded to a physical pump ceiling. Thermal breakthrough at
the chosen 1.3 km spacing is ~177 yr away on a homogeneous estimate (to be confirmed
with a heterogeneous transient sim), so that deliverability holds over the field life
with a wide margin.

**Is the surface design viable?** Yes. Design A (geothermal + ATES + heat pumps)
meets both 10 MWth heating and 5 MWth cooling (the latter at 99.8 % confidence on
6 robustly-sized ATES pairs), at a blended **13.4 €/GJ** for **≈ €21.3 M**, and
beats the absorption-chiller alternative on product economics (it keeps the heat we
sell) and on the physics of a 77 °C resource, with cooling cost a wash.

**Recommended next phase:** drill one pilot well at the BLT-01 site → in-situ
injectivity/production test to confirm the Darcy deliverability → if confirmed,
complete the doublet, then the second doublet → FID. **Data gaps to close first:**
3-D seismic confirmation of the BLT-01 fairway, an in-situ injectivity test, and a
transient thermal-breakthrough simulation at the chosen spacing.

---

## 9. Applicability to African geothermal contexts

This is a Dutch case study, but the competition is an African one, so I want to be
explicit about what carries across and what does not — because pretending a 77 °C
sedimentary Rotliegend doublet is a template for African geothermal would be the
kind of over-claim I have avoided everywhere else.

**The transferable asset is the *method*, not the numbers.** Four things I built
here are geology-agnostic and would slot directly onto an African project:

1. **The probabilistic resource workflow** — taking a P90/P50/P10 reservoir
   envelope, propagating it through a calibrated deliverability model by Monte
   Carlo, and reporting *P(meets demand)* rather than a single number. This is how
   you make an honest go/no-go call under subsurface uncertainty anywhere.
2. **The database-reconciliation discipline** — calibrating a first-principles
   model against a published reference (here ThermoGIS) before trusting it for
   what-if scenarios. The African analogue is calibrating against well-test or
   published field data from the relevant play.
3. **The financed LCOE engine** — a transparent, validated cash-flow model that any
   project can re-parameterise with local drilling costs, tariffs and cost of
   capital (which, in much of Africa, is the dominant LCOE driver — exactly the kind
   of sensitivity our tornado is built to expose).
4. **The AI-assisted pipeline** — one command from raw logs to economics, valuable
   precisely where subsurface data is sparse and teams are small.

**What does *not* transfer directly.** Most African geothermal is **high-enthalpy
volcanic/magmatic**, concentrated along the **East African Rift** — Kenya
(Olkaria, Menengai), Ethiopia (Aluto-Langano, Corbetti), Tanzania, Djibouti. Those
resources are 200–350 °C and are developed for **electricity**, with flash/binary
plants and very different well, reservoir-physics and cost models. Our low-enthalpy
**direct-use** scheme — Darcy-flow sandstone deliverability, ATES seasonal
cold-banking, a heat-led district loop — is not the right tool there, and I would
not pretend otherwise.

**Where the Dutch model genuinely fits in Africa.** The sedimentary, direct-use
template *does* transfer to **North African and intracratonic sedimentary basins**
— Algeria, Tunisia and Egypt already use low-enthalpy aquifers (e.g. the Continental
Intercalaire) for direct heat and agriculture — and, more interestingly for a
cooling-heavy continent, the **hybrid cooling** half of this design is the
transferable innovation: many African cities are cooling-dominated year-round, and a
geothermal- or aquifer-assisted cooling scheme (ATES-style storage, absorption or
heat-pump chilling) is a more relevant contribution there than the heating that
dominates the Dutch case. In short: **the rift gets power; the sedimentary basins
and the hot, cooling-hungry cities get a version of *this* — and the workflow we
built is what makes either bankable.**

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
- **E. External data citation list** — ThermoGIS / DINOloket (TNO) for the reservoir
  P-distributions; TNO LCOE workbook (van Wees et al., 2012) as the LCOE reference;
  NL Rotliegend doublet flow-rate (100–300 m³/h), drilling-cost and ATES-capex
  precedent; ATES per-pair throughput and round-trip efficiency (Fleuchaus et al.,
  *Renew. Sustain. Energy Rev.*, 2018; Bloemendal & Hartog, 2018); heat-pump COP
  (IEA HPT); absorption-chiller COP_th and 85–95 °C drive-temperature window
  (ASHRAE). Per-parameter source mapping in `LCOE_hybrid.xlsx` (Inputs sheet).
- **F. ML cross-validation detail** — `figures/ml_coverage.png`,
  `figures/ml_dtc_crossplot.png`, `figures/ml_nphi_prediction.png`,
  `data/processed/ml_loo_cv.csv`, `notebooks/05_ml_logs.ipynb`.

*Reproduce every figure and table from a fresh clone (any OS):*
`pip install -r requirements.txt` *→* `python -m pytest` *→* `python -m src.build_all`*.
The bonus ML stage additionally needs the OpenMP runtime (`brew install libomp` on
macOS); every other number reproduces without it.*
