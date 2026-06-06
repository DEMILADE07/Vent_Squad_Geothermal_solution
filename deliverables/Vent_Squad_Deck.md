# Vent Squad — Slide Deck (content draft, 14 slides)

> Board-memo structure: **problem → recommendation → evidence → risks → ask.**
> One `##` per slide. Each slide has bullets, a **Speaker note**, and the **Figure**
> to drop in. Convert to PowerPoint / Google Slides; add the title-page SPE numbers
> and paste the named figures from `figures/`. Numbers are final (from the committed
> code, 79 tests, TNO gate green); only the SPE IDs are outstanding.

---

## Slide 1 — Title

- **Utrecht District Geothermal Heating & Cooling — A Hybrid Doublet Solution**
- **Team Vent Squad** — Demilade Kolawole-Jacobs (lead), Fikayo, Ashinze, Ayomide, Sodiq
- **SPE membership numbers:** `____` (one per member — mandatory per brief)
- SPE Africa Geothermal Datathon 2026 · v2

**Speaker note:** "We're Vent Squad. Our question was simple — can a Rotliegend
geothermal scheme heat *and* cool an Utrecht district? — and our answer is yes,
with one honest catch we'll get to in 90 seconds."

---

## Slide 2 — The problem in one slide

- District demand: **10 MWth heating** (winter) + **5 MWth cooling** (summer)
- Reservoir target: **Rotliegend sandstone** (Lower Permian, ~2 km deep)
- Four wells on the table: **BLT-01, EVD-01, JUT-01, PKP-01**
- Why now: the Netherlands already runs ~20 producing Rotliegend doublets

**Speaker note:** Frame heating + cooling as two halves: 60 % subsurface, 40 %
surface. The precedent is real — we're not inventing a play, we're siting one.

---

## Slide 3 — Our recommendation (lead with the answer)

- **Site a 2-doublet (4-well) scheme near BLT-01**
- **Design A: geothermal + ATES + electric heat pumps**
- Headline numbers:
  - Heating P50 **~10.1 MWth** (P90 2.1 / P10 ~29) · **P(≥10 MWth) ≈ 50 %**
  - Cooling delivered: **5 MWth**
  - LCOE heat **11.7 €/GJ** · cool **17.5 €/GJ** · blended **12.5 €/GJ**
  - Probabilistic heat LCOE **P50 11.8 (90 % band ~6–57)** — tail = *resource* risk
  - Funded as Dutch low-carbon heat: **~13 kt CO₂/yr, SDE++ ~61 €/tCO₂, equity IRR ~21 %**
  - Total capex **≈ €19.9 M**

**Speaker note:** Lead with the answer, board-memo style. The honest catch: it's
*two* doublets and a 50 % probability — we put a number on the uncertainty instead
of hiding it, and we show it's fundable as a subsidised low-carbon asset.

---

## Slide 4 — Why BLT-01: four wells, one sweet spot

- ThermoGIS side-by-side (thickness · φ · k · T · kh):
  - **BLT-01 — 130 m / 17 % / 82 mD / 77 °C / 9.3 Dm — anchor**
  - JUT-01 — 125 / 11 / 40 / 72 / 4.8 — viable backup
  - PKP-01 — 60 / 9 / 1 / 88 / 0.1 — hot but **too tight to flow**
  - EVD-01 — 76 / 9 / 6 / 72 / 0.4 — weakest all round
- Our independent petrophysics agrees: BLT-01 **NTG 0.93**, the best by far

**Speaker note:** BLT-01 dominates on k·h, the make-or-break flow term. PKP is hot
but tight; EVD weak; JUT structurally complex. One well is the obvious anchor.

**Figure:** ThermoGIS comparison table (from §3.3 of the report).

---

## Slide 5 — Subsurface workflow (methodology, one slide)

- LAS load → unit harmonisation (JUT-01 ft → m) → **MD→TVD (minimum curvature,
  sub-cm match)**
- Petrophysics: **Larionov-older** V_sh · density-φ (ρ_ma 2.65) · NPHI cross-check
- Net cut-off: **V_sh ≤ 0.40 AND φ ≥ 0.08**
- Honest validation: **leave-one-well-out** cross-validation (R² reported, not hidden)

**Speaker note:** One slide of method to earn credibility, then move on. Emphasise
"sub-cm TVD match" and "we recovered the deliberately-broken target file in code."

**Figure:** `figures/petro_BLT-01.png` (or `figures/md_vs_tvd.png`).

---

## Slide 6 — Resource: a *bounded, correlated* probabilistic MWth

- Monte-Carlo from ThermoGIS P90/P50/P10 — **10,000 draws**
- **Split-lognormal** reproduces ThermoGIS's published band *exactly*; **300 m³/h pump
  cap** removes the unphysical tail (single-doublet P10 26.9 → 14.6 MWth)
- 1 doublet: P50 **5.05 MWth**, only **29 %** chance of clearing 10 MWth
- **2 doublets: P50 ~10.1 MWth, ≈ 50 %** → the design basis
- **Joint scheme model:** doublet correlation ρ≈0.6 + ±4 °C T + ~10 % interference →
  the 50 % is **robust**, and the downside P90 *improves* (1.7 → ~2.1 MWth)

**Speaker note:** This is our differentiator — a *distribution*, physically bounded,
with correlated doublets — not a single number. The 50 % survives a harder model.

**Figure:** `figures/mc_mwth_blt.png` + inset `figures/deliverability_reconciliation.png`.

---

## Slide 7 — Surface Design A: geothermal + ATES + heat pumps

- Doublets → plate-and-frame HX → district hot loop → heat pump (COP 4.2) trim
- Cooling from seasonal **ATES** — cold banked in winter, spent in summer
- **4 ATES well pairs** for 5 MWth — *confirmed by the hourly sim's 5 MWth peak*
- Recommended operation: **baseload the geothermal, peak with the heat pump** (next slide)

**Speaker note:** ATES is the clever bit — a seasonal "cold battery." We size off
the peak, not the average, which is where most cooling designs go wrong.

**Figure:** process-flow diagram (to draw) — doublet → HX → hot loop → HP + ATES.

---

## Slide 8 — Surface Design B: absorption-chiller contrast

- LiBr/H₂O absorption chiller driven by geothermal heat (thermal COP ≈ 0.7)
- Needs **≈ 7.1 MWth of drive heat** to make 5 MWth cold — heat we'd rather sell
- Cooling LCOE **23.2 €/GJ** vs Design A's **17.5 €/GJ**
- Wants 85–95 °C drive heat; our reservoir is **77 °C** → marginal

**Speaker note:** We carry Design B as a real contrast, not a strawman. It's
lower-capex but loses on cost-per-GJ, cannibalises heat sales, and fights the
thermodynamics of a 77 °C resource. That's why A wins.

**Figure:** Design A vs B comparison table (from §4.4).

---

## Slide 9 — Operating strategy: an 8760-hour dispatch, not an assumption

- We **simulate** the year (Utrecht temperature → hourly demand → merit-order dispatch)
  rather than assume the load-hours
- **Key finding:** geothermal sized to the full 10 MWth peak runs at only ~3,100 FLEQ
  (→ heat ~21 €/GJ). **Baseloading ~1 doublet (~5 MWth) → ~5,800 FLEQ at 92 % coverage**,
  heat pump covers the winter peak → the ~6,000 h the economics assume
- **Thermal breakthrough modelled** (Gringarten–Sauty): ~155 yr at 1.3 km ≫ life →
  **breakthrough-safe**, decline only bites below ~0.5 km spacing
- ATES covers ~all of a modest cooling load; chiller barely runs

**Speaker note:** This is the rigor slide — most teams *assume* load-hours; we ran
8,760 hours and it changed the operating recommendation to baseload + HP-peak. And
breakthrough is a number (155 yr), not a worry.

**Figure:** `figures/dispatch_load_duration.png`.

---

## Slide 10 — Economics: validated, probabilistic LCOE

- LCOE **heat 11.7 / cool 17.5 / blended 12.5 €/GJ** — re-derived from the TNO workbook
- Engine **validated to 5.769 €/GJ** against the stock TNO reference before we trust it
- **Probabilistic:** heat P50 **11.8**, 90 % band **~6–57 €/GJ** — heavy tail is the
  *resource* downside (the case for staged appraisal), not cost inflation
- **Tornado:** heat-dominated (MWth, load-hours, drilling €/m); **30-yr life → 10.6 €/GJ**
- ~2× the Dutch heat-only benchmark (5.77) — and we explain exactly why

**Speaker note:** The 2× gap is the punchline: a cooler, less productive reservoir
needs 4 wells for 10 MWth where the benchmark needs 2 for 13. The band, not the
point, is the honest headline — and its tail is resource risk we de-risk by piloting.

**Figure:** `figures/lcoe_tornado.png` + inset `figures/lcoe_heat_distribution.png`.

---

## Slide 11 — Investment case: CO₂, SDE++, returns

- **Carbon:** displaces gas-fired heat → **~13,100 t CO₂/yr** abated (~196 kt / 15 yr)
- **SDE++:** pays cost-price minus gas-linked market value → **~3.7 €/GJ subsidy**,
  ranked at **~61 €/tCO₂** — comfortably fundable (ceiling ~300 €/t)
- **Returns:** at a ~9 €/GJ tariff the market alone is under water, but **with SDE++ the
  equity IRR is ~21 %** (clears the 15 % hurdle); 30-yr life → 44 €/tCO₂
- The honest framing: a **subsidised, low-carbon heat asset** — exactly how every Dutch
  geothermal doublet is financed — not a merchant project at today's gas price

**Speaker note:** This converts "what does it cost" into "should you build it." The
answer is yes, through SDE++, and it's competitive on the metric the auction uses.

**Figure:** value-case table (from `data/processed/value_case.csv`).

---

## Slide 12 — Bonus: AI-assisted workflow

- `pipeline.py` — one CLI, raw LAS → hybrid LCOE, reproducible end-to-end
  (ingest → petro → predict → dispatch → ml → lcoe)
- LightGBM missing-log prediction, validated by **leave-one-well-out**
- Cross-well R²: DTC 0.51 (usable) · RHOB 0.10 · NPHI −0.20
- **Fallback rule:** R² < 0.50 → use ThermoGIS deterministic. We prove it, not assume it.

**Speaker note:** The honesty is the point — log prediction *doesn't* generalise
well across these four wells, so we fall back. AI as a validated screen, not a
number we quietly trust. The pipeline is the runnable artefact reviewers can re-run.

**Figure:** CLI screenshot + `figures/ml_dtc_crossplot.png`.

---

## Slide 13 — Risks, assumptions, what we did **not** do

- Top risks: **resource optimism** (top LCOE driver — fully propagated as a band),
  **drilling-cost volatility** (top-3 driver), **ATES regulatory** (NL permitting)
- **Thermal breakthrough: quantified** at ~155 yr (1.3 km) — *not* a binding risk
- Key assumptions: reinjection 35 °C (ΔT 42 °C), e-price €150/MWh; load-hours now
  *simulated*, not assumed
- Out of scope (declared): heat-distribution network, permitting, 3-D/FEM thermal modelling

**Speaker note:** Naming what we didn't do builds trust. Note that two former
assumptions (load-hours, breakthrough) are now simulated numbers — we closed our own gaps.

---

## Slide 14 — Ask / next steps

- **Pilot first:** one well → in-situ injectivity/production test → confirm Darcy →
  complete doublet → second doublet → FID
- Data gaps to close before FID: 3-D seismic, in-situ injectivity test, transient breakthrough sim
- **The resource is real but modest; two doublets are the honest minimum; Design A is the
  right scheme; SDE++ makes it fundable.**
- Acknowledgements & sources: ThermoGIS/DINOloket (TNO), TNO LCOE workbook

**Speaker note:** Close on the ask — a staged, de-risked path to FID — and repeat
the one-line thesis. End confident, not hedged.

---

*Reserve slide (cap is 15): a cash-flow / capex breakdown view is available if Q&A
needs it.*
