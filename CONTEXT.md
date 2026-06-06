# SPE Africa Geothermal Datathon 2026 — Project Context

> **Data inventory and challenge brief.** This file records the raw-data facts and
> the brief as we received them; it is background, not the solution. The completed
> solution and all final numbers are in [the technical report](deliverables/Vent_Squad_Report.md)
> and the judge-facing [project walkthrough](PROJECT_WALKTHROUGH.md). Last updated 2026-06-06.

## 1. The challenge in one paragraph

Design a **geothermal-based heating and cooling system** for a mixed urban
district in the Netherlands (Utrecht region), targeting the **Rotliegend
sandstone** as the reservoir. The district has an estimated peak demand of
**≥ 10 MWth heating** and **≥ 5 MWth cooling**. The competition has two
graded challenges and one bonus track.

| Track       | Weight | What it asks |
|-------------|--------|--------------|
| Challenge 1 | 60%    | Assess geothermal potential from the well data; decide if the resource can supply the district demand. |
| Challenge 2 | 40%    | Design an integrated surface system (heat pumps, chillers, thermal storage, hybrid renewables) that delivers the demand. |
| Bonus       | —      | Build an AI-assisted workflow that automates part of the geothermal design process. |

## 2. Key dates

| Date          | Event                                                |
|---------------|------------------------------------------------------|
| 2026-05-11    | Kick-off, data + challenge released                  |
| **2026-06-07 23:59 EAT** | **Final submission deadline (hard; extended from 4 June)** |
| Early July    | Finalists notified                                   |
| 2026-07-22..24| SAASC 2026 at Kenyatta University, Nairobi — finalist presentations |

> Deadline 2026-06-07 (extended from 4 June). The analysis is complete; this file is
> retained as the data-inventory record behind the final solution.

## 3. Deliverables (must submit all three via Google Form)

| ID | Artefact | Naming | Notes |
|----|----------|--------|-------|
| D1 | Code repo `.zip` | `Team_<TeamName>_Code_V1` | README.md with project title, team, problem statement, methodology, repro instructions. `.ipynb`/`.py` must run top-to-bottom. `requirements.txt` or `environment.yml`. |
| D2 | Slide deck | `Team_<TeamName>_PPT_V1` | 10–15 slides max. PDF preferred. Cover: problem framing, EDA, methodology, insights, limitations, recommendations. Title slide must list members + SPE numbers. |
| D3 | Explainer video | `Team_<TeamName>_Vid_V1` | 3–5 min, ≥720p, narrated (no silent screen recordings). Upload to Google Drive (login-free shareable link). |

Up to 3 resubmissions allowed (`_V1`, `_V2`, `_V3`). Latest before deadline wins.

The challenge brief itself also asks for a **technical report** summarising
the assessment, design, assumptions, external data use, economics, and the
final LCOE. Treat this as a 4th deliverable alongside D1–D3.

## 4. Data inventory

All data lives in [data/](data/). The original `data_AGD_2026.zip` was
extracted in-place — ignore the zip; the folder is the source of truth.

### 4.1 Raw well logs — [data/raw/](data/raw/)

Four LAS 2.0 files, one per well. **Curve coverage is very uneven** and
**unit handling needs care**.

| Well     | File size | Step      | Curves available | Notes |
|----------|-----------|-----------|------------------|-------|
| BLT-01   | 6.4 MB    | 0.0762 m  | MD, BITSIZE, CALI, casing flag, DRHO, DTC, DTS, DTST, GR, GRKT, GRTO, NPHI, PE, POTA, RD, RHOB, RM, RS, THOR, URAN (20) | Field: Utrecht-Oost. BHT 167 °F. Deepest log to ~2124 m. Best curve coverage by far — anchor well for any model. |
| EVD-01   | 1.5 MB    | (m)       | DEPT, GR, DT, RHOB, DRHO (5) | Sparse log suite. |
| JUT-01   | 1.4 MB    | 0.5 ft    | DEPT, GR, DT, RHOB (4) | ⚠ **Depths in FEET** (STRT/STOP/STEP units are `F`). Convert before merging with the rest. |
| PKP-01   | 2.3 MB    | (m)       | DEPT, GR, DT, RHOB, DRHO, NPHI (6) | |

Missing-value sentinel: `-999.25` (declared in each LAS header).

### 4.2 Lithostratigraphy — [data/Lithostratigraphic Data.xlsx](data/Lithostratigraphic%20Data.xlsx)

One sheet per well. Columns: `Stratigrafical unit`, blank, `Top (m)`,
`Bottom (m)`, `Anomaly code`. Includes explicit **"Fault" intervals**
(zero-thickness picks marking fault planes) — handle these specially.

Stratigraphy ranges from the Upper North Sea Group down to the
**Rotliegend** (the target reservoir) at the base of each well.

### 4.3 Well-path / deviation surveys — [data/Well Path Data.xlsx](data/Well%20Path%20Data.xlsx)

One sheet per well. Columns: `Depth (m)`, `Inclination (°)`, `Azimuth (°)`,
`TVD (m)`, `X-offset (m)`, `Y-offset (m)`.

| Well   | Stations | Deviation character |
|--------|----------|---------------------|
| BLT-01 | 103      | Heavily deviated (inclinations climb past 30°) — significant MD↔TVD gap. |
| EVD-01 | 22       | Near-vertical at shallow depth. |
| JUT-01 | 34       | Moderately deviated. |
| PKP-01 | 111      | Most stations, deviation builds early. |

> **Used to convert measured-depth (along-hole) values in
> `target_lithologies.csv` to TVD** — see §4.5.

### 4.4 ThermoGIS reservoir summary — [data/ThermoGIS Data.xlsx](data/ThermoGIS%20Data.xlsx)

One sheet per well. P90 / P50 / P10 estimates for the Rotliegend interval at
each well location (the wells' surface X/Y coordinates are in sheet headers
— RD New / EPSG:28992).

| Well   | X        | Y        | Top depth (m) | Thickness P50 (m) | Porosity (%) | Permeability P50 (mD) | Transmissivity P50 (Dm) | Temp (°C) |
|--------|----------|----------|---------------|-------------------|--------------|------------------------|--------------------------|-----------|
| BLT-01 | 141 577  | 456 881  | 1837          | 130               | 17           | 82                     | 9.3                      | 77        |
| EVD-01 | 136 997  | 441 189  | 1723          | 76                | 9            | 6                      | 0.4                      | 72        |
| JUT-01 | 134 098  | 451 726  | 1776          | 125               | 11           | 40                     | 4.8                      | 72        |
| PKP-01 | 118 503  | 453 402  | 2255          | 60                | 9            | 1                      | 0.1                      | 88        |

Read this off straight away: **BLT-01 is the sweet spot** (thick, porous,
permeable, warm enough); **PKP-01 is hotter but ~tight**; **EVD-01 is the
weakest**.

### 4.5 Target lithologies — [data/target_lithologies.csv](data/target_lithologies.csv)

3,455 rows. Schema: `well_id, easting, northing, depth_tvd_m, porosity_pct,
gamma_ray_api, bulk_density_gcc, formation_top_tvd, formation_base_tvd,
formation_thickness_m, distance_to_usp_km, flag, flag_reason`.

| Well   | Rows |
|--------|------|
| BLT-01 | 1689 |
| EVD-01 |  780 |
| PKP-01 |  730 |
| JUT-01 |  256 |

**Every row is flagged** `check` with reason
`"AH depth — deviated well needs TVD conversion before use"`. The
`depth_tvd_m` column is currently empty for the flagged rows — you must
back out true vertical depths using the well-path surveys (§4.3) before
this CSV is usable.

`distance_to_usp_km` looks like the great-circle / projected distance from
each row to the planned **Urban Supply Point (USP)** — the district being
heated. Worth confirming during EDA.

### 4.6 Economics template — [LCOE.xlsx](LCOE.xlsx)

TNO Dutch LCOE workbook (Jan-Diederik van Wees et al., 2011, v2012.1). Four
sheets:

| Sheet         | Purpose |
|---------------|---------|
| `Colofon`     | Authors / version / colour-coding legend. |
| `Input_Output`| All input parameters + the headline LCOE outputs. Currently configured for **heat-only** mode: 50 L/s, AH 1800 m, Tx 93.7 °C, 2 wells, 15-yr lifetime → ~13.4 MWth, LCOE ≈ **5.77 €/GJ** (≈ 20.8 €/MWhth). Power-plant block exists but is toggled off. |
| `CFpower`     | Cash-flow model for power-producing variant (not currently active). |
| `CFheat`      | Cash-flow model for the heat-only variant. |

**Challenge 2 requires you to modify this sheet** to model the *hybrid
heating + cooling* design (the stock workbook handles heat only, and
power as an alternative — not heating + cooling combined). At minimum
you'll need: a cooling-load block, surface-side equipment costs (heat
pump COP, chiller COP, BTES/ATES storage), and a re-derived LCOE that
covers both energy products.

## 5. Key data constraints and how we handle them

1. **Unit harmonisation.** JUT-01 LAS is in feet; the others in metres.
   Coordinates are RD New (EPSG:28992) in metres. Convert once, centrally.
2. **MD → TVD everywhere.** Both the LAS depths (along-hole) and
   `target_lithologies.csv` (flagged) need to be referenced to the same
   TVD frame before cross-well comparison or any reservoir-property map.
3. **Faults in the strat column** are zero-thickness picks — don't let
   them collapse the interval logic.
4. **Sparse curve coverage** at EVD-01 and JUT-01 means any porosity /
   sonic / NPHI prediction has to be transfer-learned from BLT-01 (the
   only well with the full petrophysical suite). This is a natural place
   for the **bonus AI workflow** — e.g. ML log prediction filling missing
   curves.
5. **`-999.25` = null** in every LAS. Drop or mask before stats.
6. **Public data is allowed** — you may pull additional ThermoGIS / DINOloket
   wells to enlarge the dataset. Document any external data clearly in the
   report (mandatory per the brief).
7. **Reservoir cooling design** is non-trivial: at ~72–88 °C the resource
   is direct-use heat. Cooling has to come from heat pumps, absorption
   chillers driven by the geothermal heat, or hybrid (ATES) configurations
   — call this out explicitly in Challenge 2.
8. **No silent screen-recordings** in D3; **strict 10–15 slide cap** in D2;
   late submissions are not accepted.

## 6. Suggested high-level workflow

A defensible order of operations, not a prescription:

1. **EDA + cleanup** — load LAS with `lasio`, normalise units, handle
   nulls, plot raw curves per well.
2. **MD→TVD conversion** — minimum-curvature or piecewise-linear
   interpolation from the well-path tables; apply to LAS depths and to
   the flagged rows in `target_lithologies.csv`.
3. **Petrophysics** — compute porosity (density / sonic), Vshale (GR
   normalisation), saturation if feasible; pick the Rotliegend interval
   per well using the lithostrat picks.
4. **Missing-curve prediction** (bonus AI track) — train on BLT-01's full
   suite, predict NPHI / DTC / RHOB at the other wells.
5. **Reservoir property mapping** — combine well-level Rotliegend
   properties (thickness, φ, k, T) with the ThermoGIS P10/P50/P90
   ranges and the USP location to estimate deliverable MWth.
6. **Design Challenge 2** — pick a doublet layout (1 producer + 1
   injector or larger), specify flow rate, surface heat exchangers, heat
   pumps for both heating *and* cooling, optional ATES.
7. **Economics** — extend LCOE.xlsx to the hybrid case; compute updated
   LCOE per GJ heat *and* per GJ cooling delivered.
8. **Bonus AI workflow** — package the missing-log model + the
   property-extraction + LCOE-update steps into a runnable pipeline
   (Python script or notebook with documented entry points).

## 7. Useful references

- TNO ThermoGIS — https://www.thermogis.nl/
- NLOG / DINOloket — Dutch well-data portal.
- `lasio` (Python LAS reader), `welly` (well-log workflows).
- SPE OnePetro for geothermal direct-use case studies.
