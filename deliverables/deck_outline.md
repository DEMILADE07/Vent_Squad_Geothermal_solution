# Slide Deck Outline — 12 slides

> Board-memo structure: **problem → recommendation → evidence → risks → ask.**
> Locked Day 0; the analysis is built to fill these slides, not the other
> way round. Cap is 15 (per brief); we are deliberately leaving 3 in
> reserve in case we need a backup-data slide or a second economics view.

---

## 1. Title

- Project: **Utrecht District Geothermal Heating & Cooling — A Hybrid Doublet Solution**
- Team name + member names + **SPE membership numbers** (mandatory per brief)
- Datathon name, date, version

## 2. The problem in one slide

- Utrecht-region district: **10 MWth heating, 5 MWth cooling**
- Reservoir target: **Rotliegend sandstone** (Lower Permian)
- Four wells available — BLT-01, EVD-01, JUT-01, PKP-01
- Why now: NL has ~20 producing Rotliegend doublets; the precedent is there

## 3. Our recommendation (lead with the answer)

- **Site a 2-well doublet near BLT-01**
- **Design A: geothermal + ATES + electric heat pumps**
- Headline numbers (filled Day 3):
  - MWth heating P50: **__ MWth** (P10 __ / P90 __)
  - MWth cooling delivered: **__ MWth**
  - LCOE heat: **__ €/GJ**  |  LCOE cool: **__ €/GJ**
  - P(MWth ≥ 10) = **__ %**

## 4. Why BLT-01 — four wells, one sweet spot

- Side-by-side ThermoGIS table (thickness, φ, k, T, kh)
- BLT-01 dominates on k·h (9.3 Dm); PKP hot but tight; EVD weakest
- One short sentence each on why the other three are not the doublet site

## 5. Subsurface workflow (one slide of methodology)

- LAS load → unit harmonisation (JUT ft → m) → **MD → TVD via minimum-curvature**
- Petrophysics: Larionov-older Vshale; density-φ (ρ_ma=2.65); k–φ transform calibrated to ThermoGIS at BLT-01
- Net cutoff Vsh ≤ 0.4 **and** φ ≥ 0.08
- Cross-validation: leave-one-well-out (R² reported honestly)

## 6. Resource — probabilistic MWth

- Monte-Carlo MWth from ThermoGIS P10/P50/P90 (10 000 draws)
- Distribution plot at chosen doublet location
- Darcy radial-inflow Q; thermal-power equation; ΔT sensitivity (30/35/40 °C)
- Doublet siting decision matrix (5 criteria)

## 7. Surface Design A — geothermal + ATES + heat pumps

- Process flow diagram (one figure)
- Doublet → plate-and-frame HX → district hot loop → HP (COP 4.2) → ATES
- ATES sizing: **3–4 well pairs** for 5 MWth cooling (0.5–2 MWth per pair)
- Capacity factors heating / cooling; load-duration profile inset

## 8. Surface Design B — absorption-chiller contrast

- LiBr/H₂O absorption chiller driven by return-line heat (COP_th 0.7)
- Single side-by-side capex/opex/LCOE comparison with Design A
- Why Design A wins on this geology and demand mix

## 9. Economics — extended LCOE

- LCOE per GJ heat **and** per GJ cool (re-derived from TNO workbook)
- **Tornado chart** — top 8 sensitivities (drilling €/m, Q, CF_heat, CF_cool, e-price, HP COP, ATES capex, discount rate)
- Comparison vs. TNO heat-only reference case (5.77 €/GJ)

## 10. Bonus — AI-assisted workflow

- `pipeline.py` end-to-end demo (one screenshot of the CLI)
- LightGBM log-prediction with **leave-one-well-out R²** table
- Where the model degrades to ThermoGIS deterministic and why

## 11. Risks, assumptions, what we did **not** do

- Three top risks from the register (thermal breakthrough, ATES sizing, drilling cost volatility)
- Key assumptions (return T = 42 °C, e-price, capacity factors)
- Out of scope: surface heat distribution network design, permitting, detailed FEM thermal modelling

## 12. Ask / next steps

- What a pilot phase looks like (one well first, then doublet)
- Data gaps to close before FID: 3D seismic confirmation, in-situ injectivity test
- Contact / acknowledgements / data sources
