# Technical Report — Outline

> Required by the challenge brief in addition to D1–D3. Target length:
> **15–25 pages** including figures. Tone: client-facing feasibility
> report, not academic write-up. Written final on Day 4; this outline
> drives the analysis on Days 1–3.

---

## Executive summary (1 page)

- Problem, recommendation, headline numbers (MWth P10/P50/P90, LCOE heat & cool, key risks).
- The "if you read nothing else" page.

## 1. Project context and scope

- Demand: 10 MWth heating, 5 MWth cooling, Utrecht region.
- Reservoir target: Lower Permian Rotliegend sandstone.
- What the report covers and what it does not (e.g. permitting, district HX network design — out of scope).

## 2. Data inventory and quality

- Source data: 4 LAS files, lithostrat picks, well-path surveys, ThermoGIS reservoir summary, target_lithologies.csv, TNO LCOE workbook.
- Quality notes: JUT-01 in feet; sparse curves at EVD/JUT; -999.25 nulls; deviation gaps requiring MD→TVD.
- External data used and citation list (per brief, mandatory).

## 3. Subsurface assessment (Challenge 1, 60 %)

### 3.1 Data conditioning

- Unit harmonisation (JUT ft → m), null masking, depth referencing.
- MD → TVD via minimum-curvature (piecewise-linear fallback at EVD-01).

### 3.2 Petrophysical interpretation

- Vshale: Larionov older-rock formula; linear GR sanity check.
- Porosity: density-φ (ρ_ma 2.65 g/cc); NPHI cross-check; sonic-φ (Wyllie) tertiary.
- Permeability: k–φ transform calibrated to ThermoGIS at BLT-01.
- Net reservoir: Vsh ≤ 0.40 AND φ ≥ 0.08.

### 3.3 Rotliegend characterisation per well

- Table of net thickness, φ, k, T per well with ThermoGIS P10/P50/P90 cross-reference.

### 3.4 Resource calculation

- Darcy radial inflow → flow rate per well.
- Thermal power MWth = ρ·c·Q·ΔT.
- **Monte-Carlo MWth** at chosen doublet location: 10 000 draws, P10/P50/P90, P(MWth ≥ 10).
- Doublet siting: 5-criterion weighted decision matrix.

### 3.5 Cross-well validation (bonus AI)

- LightGBM log prediction trained on BLT-01.
- **Leave-one-well-out R²** table per curve.
- Honest fallback: where R² < 0.5, downstream uses ThermoGIS deterministic.

## 4. Surface design (Challenge 2, 40 %)

### 4.1 Demand-side characterisation

- Annual heating load profile (assumed shape — NL residential district).
- Cooling load profile, August peak.
- Load-duration curve drives ATES sizing.

### 4.2 Design A — geothermal + ATES + heat pumps (recommended)

- Process flow diagram.
- Doublet flow rate, surface HX duty, HP COP and electricity load.
- ATES sizing (well-pair count, throughput, round-trip efficiency).
- Component capex/opex assumptions table with sources.

### 4.3 Design B — geothermal + LiBr/H₂O absorption chiller (contrast)

- Process flow diagram.
- COP_th, parasitic electricity, capex/opex.
- Side-by-side comparison vs. Design A.

### 4.4 Recommendation and selection rationale

- Why Design A given this geology, demand mix, and economics.

## 5. Economics — extended LCOE

- TNO workbook starting point and how we extended it.
- LCOE per GJ heat and per GJ cool, derivation.
- **Tornado** on top 8 sensitivities.
- Comparison to TNO heat-only reference (5.77 €/GJ).

## 6. Risks, assumptions, and limitations

- Subsurface uncertainty (k, h, T propagation already in §3.4).
- Thermal breakthrough estimate (analytic Lauwerier/Gringarten time-to-BT).
- Drilling cost volatility.
- ATES regulatory risk in NL (briefly note Dutch ATES permitting framework).
- Model limitations: 1D well-based vs. 3D static model; no geomechanics; no detailed network hydraulics.

## 7. AI-assisted workflow (bonus)

- `pipeline.py` architecture diagram.
- CLI commands and outputs.
- Where AI/ML actually helps (log prediction + Monte-Carlo orchestration) and where it does not (dimensioning decisions stay engineer-in-the-loop).

## 8. Conclusions and next steps

- Headline answer to "is the resource sufficient?" and "is the surface design viable?".
- Recommended next phase: pilot well + injectivity test → FID.
- Data gaps to close.

## Appendices

- A. Detailed petrophysical equations and constants.
- B. MD→TVD method and QC plots per well.
- C. Monte-Carlo distributions and tornado underlying data.
- D. Full LCOE input table with sources.
- E. External data citation list.
