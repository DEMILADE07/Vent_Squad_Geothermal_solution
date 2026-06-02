# Vent Squad — Slide Deck (content draft, 12 slides)

> Board-memo structure: **problem → recommendation → evidence → risks → ask.**
> One `##` per slide. Each slide has bullets, a **Speaker note**, and the **Figure**
> to drop in. Convert to PowerPoint / Google Slides; add the title-page SPE numbers
> and paste the named figures from `figures/`. Numbers are final (from the committed
> code); only the SPE IDs are outstanding.

---

## Slide 1 — Title

- **Utrecht District Geothermal Heating & Cooling — A Hybrid Doublet Solution**
- **Team Vent Squad** — Demilade Kolawole-Jacobs (lead), Fikayo, Ashinze, Ayomide, Sodiq
- **SPE membership numbers:** `____` (one per member — mandatory per brief)
- SPE Africa Geothermal Datathon 2026 · 2026-06-02 · v1

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
  - Heating P50: **10.12 MWth** (P90 2.0 / P10 53.9) · **P(≥10 MWth) = 50 %**
  - Cooling delivered: **5 MWth**
  - LCOE heat **11.7 €/GJ** · cool **17.5 €/GJ** · blended **12.5 €/GJ**
  - Total capex **≈ €19.9 M**

**Speaker note:** Lead with the answer, board-memo style. The honest catch: it's
*two* doublets, not one, and a 50 % probability — we put a number on the
uncertainty instead of hiding it.

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

## Slide 6 — Resource: probabilistic MWth

- Monte-Carlo from ThermoGIS P90/P50/P10 — **10,000 draws**
- 1 doublet: P50 **5.06 MWth**, only **31 %** chance of clearing 10 MWth
- **2 doublets: P50 10.12 MWth, 50 % chance** → the design basis
- Darcy model reconciled to ThermoGIS flow/power to **~1 %** (16.5 bar, 35 °C reinjection)

**Speaker note:** This is our differentiator — a *distribution*, not a single
number. The 50 % is deliberately honest; most teams will quote a point estimate.

**Figure:** `figures/mc_mwth_blt.png` + inset `figures/deliverability_reconciliation.png`.

---

## Slide 7 — Surface Design A: geothermal + ATES + heat pumps

- Doublets → plate-and-frame HX → district hot loop → heat pump (COP 4.2) trim
- Cooling from seasonal **ATES** — cold banked in winter, spent in summer
- **4 ATES well pairs** for 5 MWth (0.5–2 MWth each, ~70 % round-trip)
- Heating ~6,000 h/yr · cooling ~2,000 h/yr (summer-peaky → sized off August peak)

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

## Slide 9 — Economics: extended LCOE

- LCOE **heat 11.7 / cool 17.5 / blended 12.5 €/GJ** — re-derived from the TNO workbook
- Engine **validated to 5.769 €/GJ** against the stock TNO reference before we trust it
- **Tornado:** LCOE is heat-dominated — top drivers are MWth, heat load-hours, drilling €/m
- ~2× the Dutch heat-only benchmark (5.77 €/GJ) — and we explain exactly why

**Speaker note:** The 2× gap is the punchline of the whole story: a cooler, less
productive reservoir needs 4 wells for 10 MWth where the benchmark needs 2 for 13.
Cause and effect, Challenge 1 → Challenge 2.

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

## Slide 11 — Risks, assumptions, what we did **not** do

- Top risks: **thermal breakthrough** (1.3 km spacing), **ATES sizing** (peak-based),
  **drilling-cost volatility** (top-3 LCOE driver)
- Key assumptions: reinjection 35 °C (ΔT 42 °C), e-price €150/MWh, 6,000/2,000 load-hours
- Out of scope (declared): heat-distribution network, permitting, 3-D/FEM thermal modelling

**Speaker note:** Naming what we didn't do builds trust. Each is a next-phase item,
not a gap we missed.

---

## Slide 12 — Ask / next steps

- **Pilot first:** one well → in-situ injectivity/production test → confirm Darcy → complete doublet → second doublet → FID
- Data gaps to close before FID: 3-D seismic, in-situ injectivity test, transient breakthrough sim
- **The resource is real but modest; two doublets are the honest minimum; Design A is the right scheme.**
- Acknowledgements & sources: ThermoGIS/DINOloket (TNO), TNO LCOE workbook

**Speaker note:** Close on the ask — a staged, de-risked path to FID — and repeat
the one-line thesis. End confident, not hedged.

---

*Reserve slides (cap is 15): a backup ThermoGIS-data slide and a second economics
view (cash-flow / capex breakdown) are available if Q&A needs them.*
