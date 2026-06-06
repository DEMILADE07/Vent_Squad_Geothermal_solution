# Vent Squad — Slide Deck (content, 13 slides)

> Board-memo structure: **problem → recommendation → evidence → risks → ask.**
> One `##` per slide. Each slide has bullets, a **Speaker note**, and the **Figure**
> to drop in. A ready-to-present version lives in `deliverables/slides/` (open the
> HTML, present in-browser, export to PDF as `Team_VentSquad_PPT_V1.pdf`). Numbers
> are final (from the committed code, `python -m src.build_all`); only the SPE IDs
> remain to add to the title slide.

---

## Slide 1 — Title

- **Utrecht District Geothermal Heating & Cooling — A Hybrid Doublet Solution**
- **Team Vent Squad** — Demilade Kolawole-Jacobs (lead), Fikayo, Ashinze, Ayomide, Sodiq
- **SPE membership numbers:** `____` (one per member — mandatory per brief)
- SPE Africa Geothermal Datathon 2026 · 2026-06-06 · v1

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
  - Heating P50: **13.2 MWth** (P90 3.8 / P10 23.1) · **P(≥10 MWth) = 62 %**
  - Cooling delivered: **5 MWth** (6 ATES pairs, 99.8 % adequacy)
  - LCOE heat **11.8 €/GJ** · cool **23.0 €/GJ** · blended **13.4 €/GJ**
  - Total capex **≈ €21.3 M** · equity **IRR ≈ 21 %** with SDE++

**Speaker note:** Lead with the answer, board-memo style. The honest catch: it's
*two* doublets, not one. Two independent doublets clear 10 MWth 62 % of the time
with real headroom — we put a number on the uncertainty instead of hiding it, and
we size the plant to the 10 MWth demand, not the 13 MWth resource surplus.

---

## Slide 4 — Why BLT-01: four wells, one sweet spot

- ThermoGIS side-by-side (thickness · φ · k · T · kh):
  - **BLT-01 — 130 m / 17 % / 82 mD / 77 °C / 9.3 Dm — anchor**
  - JUT-01 — 125 / 11 / 40 / 72 / 4.8 — viable backup
  - PKP-01 — 60 / 9 / 1 / 88 / 0.1 — hot but **too tight to flow**
  - EVD-01 — 76 / 9 / 6 / 72 / 0.4 — weakest all round
- Our independent petrophysics agrees at the anchor: BLT-01 **NTG 0.93** vs
  ThermoGIS 0.98 — the best by far (we apply stricter log cut-offs at the weaker
  wells, so our estimate is the more conservative; details in the report)

**Speaker note:** BLT-01 dominates on k·h, the make-or-break flow term. PKP is hot
but tight; EVD weak; JUT structurally complex. One well is the obvious anchor. Our
log-based NTG matches ThermoGIS at BLT and is deliberately stricter elsewhere — we
flag that honestly rather than claim a false "consistent."

**Figure:** ThermoGIS comparison table (from Section 3.3 of the report).

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

## Slide 6 — Resource: probabilistic MWth

- Monte-Carlo from ThermoGIS P90/P50/P10 — **10,000 draws**, split-lognormal fit
  (hits all 3 points), tail **bounded at a 300 m³/h pump ceiling**
- 1 doublet: P50 **5.05 MWth**, only **29 %** chance of clearing 10 MWth
- **2 independent doublets: P50 13.2 MWth, 62 % chance** → the design basis
- Darcy reconciled to ThermoGIS flow/power to **~1 %**; thermal breakthrough **~177 yr ≫ life**

**Speaker note:** This is our differentiator — a *distribution*, not a single
number, and an honest one: we bound the optimistic tail at a physical pump ceiling
(no 77 °C doublet beats the ~13 MWth Dutch benchmark) and treat the two doublets as
independent. 62 % chance of clearing 10 MWth with headroom; one doublet falls short.

**Figure:** `figures/mc_mwth_blt.png` + inset `figures/deliverability_reconciliation.png`.

---

## Slide 7 — Surface Design A: geothermal + ATES + heat pumps

- Doublets → plate-and-frame HX → district hot loop → heat pump (COP 4.2) trim
- Cooling from seasonal **ATES** — cold banked in winter, spent in summer
- **6 ATES well pairs** for 5 MWth — per-pair capacity is uncertain (0.5–2 MWth),
  so we size off the *low* end: **P(supply ≥ 5 MWth) = 99.8 %**, P90 supply 6.0 MWth
- Load-hours **derived from an 8,760-h dispatch sim**, not assumed: geothermal must
  run **baseload** (~6,000 FLEQ h) — peak-sizing it wastes the doublet (~3,170 h)
- Cooling ~2,000 h/yr (summer-peaky → sized off August peak)

**Speaker note:** ATES is the clever bit — a seasonal "cold battery." We size off
the peak *and* the low-throughput end: 4 pairs would meet demand only 29 % of the
time once you honour the uncertainty, so we carry 6. And our 6,000 load-hours aren't
assumed — an hourly dispatch sim shows they only hold if the geothermal runs
baseload with heat-pump trim, which is exactly our design.

**Figure:** `figures/design_a_schematic.png` — doublet → HX → hot loop → HP + ATES.

---

## Slide 8 — Surface Design B: absorption-chiller contrast

- LiBr/H₂O absorption chiller driven by geothermal heat (thermal COP ≈ 0.7)
- Needs **≈ 7.1 MWth of drive heat** to make 5 MWth cold — heat we'd rather sell
- Cooling LCOE **23.4 €/GJ** vs Design A's **23.0 €/GJ** — essentially a wash on cost
- Wants 85–95 °C drive heat; our reservoir is **77 °C** → marginal-to-insufficient

**Speaker note:** We carry Design B as a real contrast, not a strawman. On cost
it's a tie once ATES is sized honestly — so A wins on the two things that aren't
close: it keeps the ~7 MWth of heat we're in business to sell, and it actually
works at 77 °C, where an absorption chiller is starved of drive heat.

**Figure:** Design A vs B comparison table (from Section 4.4).

---

## Slide 9 — Economics: extended LCOE

- LCOE **heat 11.8 / cool 23.0 / blended 13.4 €/GJ** — re-derived from the TNO workbook
- Engine **validated to 5.769 €/GJ** against the stock TNO reference before we trust it
- **As a distribution, not a point:** heat LCOE **P10/P50/P90 = 10.8 / 12.6 / 26.7 €/GJ** —
  the upper tail is the quantified cost of the resource under-delivering (→ stage the appraisal)
- **Fundable:** SDE++ subsidy **≈ 3.8 €/GJ (~€63/tCO₂**, ~13 kt CO₂/yr abated) → **equity IRR ≈ 21 %**
- **Tornado:** heat-dominated — top drivers are heat delivered (MWth), load-hours, drilling €/m
- ~2× the Dutch heat-only benchmark (5.77 €/GJ) — and we explain exactly why

**Speaker note:** The 2× gap is the punchline: a cooler, less productive reservoir
needs 4 wells for 10 MWth where the benchmark needs 2 for 13. And we go past the
point estimate — a probabilistic LCOE band and an SDE++ value case that clears the
hurdle at €63/tCO₂. Cause and effect, Challenge 1 → Challenge 2 → bankability.

**Figure:** `figures/lcoe_tornado.png`.

---

## Slide 10 — Bonus: AI-assisted workflow

- `pipeline.py` — one CLI, raw LAS → hybrid LCOE, reproducible end-to-end
- LightGBM missing-log prediction, validated by **leave-one-well-out**
- Cross-well R²: DTC 0.51 (usable) · RHOB 0.10 · NPHI −0.20
- **Fallback rule:** R² < 0.50 → use ThermoGIS deterministic. We prove it, not assume it.

**Speaker note:** The honesty is the point — log prediction *doesn't* generalise
well across these four wells, so we fall back. AI as a validated screen, not a
number we quietly trust. The pipeline is the runnable artefact reviewers can re-run.

**Figure:** CLI screenshot + `figures/ml_dtc_crossplot.png`.

---

## Slide 11 — Does this travel? Applicability to African geothermal

- **The method transfers, the numbers don't.** Our probabilistic resource workflow,
  database-reconciliation discipline, financed LCOE engine and one-command AI
  pipeline are geology-agnostic — they slot onto any geothermal project.
- **Not a template for the Rift:** East African geothermal (Kenya Olkaria/Menengai,
  Ethiopia Aluto/Corbetti) is **high-enthalpy volcanic → power**, a different model.
- **Where *this* fits in Africa:** North African / intracratonic **sedimentary**
  basins (Algeria, Tunisia, Egypt — direct-use heat) and, more relevantly, the
  **hybrid-cooling** half of our design for cooling-dominated African cities.

**Speaker note:** We're honest that a 77 °C Dutch sandstone doublet isn't a Rift
template. But the transferable asset is the workflow — and the cooling design is
arguably *more* relevant in a hot, cooling-hungry continent than the heating is.

**Figure:** none needed — or a small "method vs. setting" two-column graphic.

---

## Slide 12 — Risks, assumptions, what we did **not** do

- **Thermal breakthrough quantified** (Gringarten-Sauty): t_bt **≈ 177 yr ≫ 30-yr life**
  on a homogeneous estimate (heterogeneous transient sim is next-step) → wide margin
- Other top risks: **ATES throughput** (probabilised 0.5–2 MWth/pair; 6 pairs →
  99.8 % adequacy), **drilling-cost volatility**; resource downside carried in the LCOE tail
- Key assumptions: reinjection 35 °C (ΔT 42 °C), e-price €150/MWh, 6,000/2,000 load-hours
- Out of scope (declared): heat-distribution network, permitting, 3-D/FEM thermal modelling

**Speaker note:** Naming what we didn't do builds trust. Each is a next-phase item,
not a gap we missed.

---

## Slide 13 — Ask / next steps

- **Pilot first:** one well → in-situ injectivity/production test → confirm Darcy → complete doublet → second doublet → FID
- Data gaps to close before FID: 3-D seismic, in-situ injectivity test, transient breakthrough sim
- **The resource is real but modest; two doublets are the honest minimum; Design A is the right scheme.**
- Acknowledgements & sources: ThermoGIS/DINOloket (TNO), TNO LCOE workbook

**Speaker note:** Close on the ask — a staged, de-risked path to FID — and repeat
the one-line thesis. End confident, not hedged.

---

*Reserve slides (cap is 15): a backup ThermoGIS-data slide and a second economics
view (cash-flow / capex breakdown) are available if Q&A needs them.*
