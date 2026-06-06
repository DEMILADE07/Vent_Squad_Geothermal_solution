"""Generate notebooks/01_eda.ipynb (the EDA / data-foundation deliverable).

Run from repo root:  python scripts/make_eda_notebook.py
The notebook imports everything from `src/`, so it stays in sync with the
tested pipeline. Re-run this after changing the analysis modules.
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code = lambda s: cells.append(nbf.v4.new_code_cell(s))

md(r"""# 01 - Exploratory Data Analysis & Data Foundation
**SPE Africa Geothermal Datathon 2026 - Challenge 1 - Team Vent Squad**

This notebook establishes the clean, unit-consistent, depth-referenced data
foundation that every later result is built on, for the four Utrecht-region wells
(BLT-01, EVD-01, JUT-01, PKP-01) targeting the **Rotliegend / Slochteren Formation**
sandstone. It runs top-to-bottom from a fresh clone; all logic lives in `src/` and is
unit-tested, so each figure and table below is reproducible rather than asserted.

**What this notebook establishes**
1. Curve inventory and coverage per well (BLT-01 is the anchor).
2. Unit harmonisation (JUT-01 in feet) and null/spike cleaning.
3. Minimum-curvature **MD->TVD**, validated against the survey TVD column.
4. Recovery of the flagged `target_lithologies.csv` depths.
5. First-pass petrophysics (V_shale, density porosity) + Rotliegend summary.""")

code(r"""import logging, warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

import sys
from pathlib import Path
ROOT = Path.cwd()
if (ROOT / "src").exists():
    sys.path.insert(0, str(ROOT))
elif (ROOT.parent / "src").exists():
    sys.path.insert(0, str(ROOT.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.paths import FIGURES
from src.wells_io import WELLS, STANDARD_CURVES, load_all, coverage_table
from src.petrophysics import add_petrophysics, rotliegend_summary
from src.lithostrat import rotliegend_pick
from src.mdtvd import load_survey, md_to_tvd, validate_survey
from src.targets import build_target_tvd
from src.constants import WELLS as META

FIGURES.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3})
WELLS""")

md(r"""## 1. Load, clean, unit-harmonise, TVD-reference

`load_all()` reads every LAS, masks the `-999.25` null, applies physical-range
gates (JUT-01 carries spike values in the millions on DT/RHOB), converts JUT-01
feet->metres once, sorts the bottom-up-logged EVD-01/PKP-01 ascending, and
attaches a per-sample TVD. We then add `vsh`/`phi_d`.""")

code(r"""logs = add_petrophysics(load_all())
cov = coverage_table(logs)
cov""")

md(r"""**Coverage read-out.** BLT-01 has the full petrophysical suite and is the
modelling anchor. The others are sonic+GR-led with sparse density/neutron - the
natural place for the bonus ML log-prediction track.""")

code(r"""frac = cov.set_index("well")[STANDARD_CURVES].div(cov.set_index("well")["n_samples"], axis=0)
fig, ax = plt.subplots(figsize=(9, 3))
im = ax.imshow(frac.values, aspect="auto", cmap="viridis", vmin=0, vmax=1)
ax.set_xticks(range(len(STANDARD_CURVES))); ax.set_xticklabels(STANDARD_CURVES, rotation=45, ha="right")
ax.set_yticks(range(len(frac))); ax.set_yticklabels(frac.index)
for (i, j), v in np.ndenumerate(frac.values):
    ax.text(j, i, f"{v:.2f}", ha="center", va="center",
            color="white" if v < 0.6 else "black", fontsize=8)
fig.colorbar(im, ax=ax, label="non-null fraction"); ax.set_title("Curve coverage by well")
fig.tight_layout(); fig.savefig(FIGURES / "coverage.png"); plt.show()""")

md(r"""## 2. Raw curves per well

Cleaned curves vs measured depth - note the uneven suites and the character
change entering the Slochteren sand at the base of each well.""")

code(r"""def plot_raw_curves(well):
    g = logs[logs.well == well]
    tracks = [("GR", "GR (gAPI)", "tab:green", None),
              ("RHOB", "RHOB (g/cc)", "tab:red", (1.8, 3.0)),
              ("DTC", "DTC (us/ft)", "tab:blue", None),
              ("NPHI", "NPHI (v/v)", "tab:purple", None)]
    fig, axes = plt.subplots(1, len(tracks), figsize=(11, 7), sharey=True)
    for ax, (c, lab, col, xlim) in zip(axes, tracks):
        if g[c].notna().any():
            ax.plot(g[c], g.md_m, col, lw=0.5)
            if xlim: ax.set_xlim(*xlim)
        else:
            ax.text(0.5, 0.5, "not logged", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlabel(lab)
    axes[0].set_ylabel("MD (m)"); axes[0].invert_yaxis()
    fig.suptitle(f"{well} - raw curves"); fig.tight_layout()
    fig.savefig(FIGURES / f"raw_curves_{well}.png"); plt.show()

for w in WELLS:
    plot_raw_curves(w)""")

md(r"""## 3. MD->TVD validation

Recomputed minimum-curvature station TVD vs the workbook TVD column - agreement
is sub-centimetre on all four wells. PKP-01 is the most deviated (~37 deg).""")

code(r"""val = pd.DataFrame([validate_survey(w) for w in WELLS])
val[["well","n_stations","max_abs_resid_m","rms_resid_m","max_inclination_deg","md_max_m","tvd_max_m"]].round(4)""")

code(r"""fig, axes = plt.subplots(1, 4, figsize=(13, 5), sharey=True)
for ax, w in zip(axes, WELLS):
    s = load_survey(w)
    ax.plot(s.md, md_to_tvd(w, s.md), "k-", lw=1)
    ax.plot([0, s.md.max()], [0, s.md.max()], "--", color="grey", lw=0.8, label="MD=TVD")
    pick = rotliegend_pick(w)
    ax.axhspan(pick["top_tvd"], pick["base_tvd"], color="orange", alpha=0.3, label="Slochteren")
    ax.set_title(f"{w} (max {s.incl_deg.max():.0f} deg)"); ax.set_xlabel("MD (m)")
axes[0].set_ylabel("TVD (m)"); axes[0].invert_yaxis(); axes[0].legend(fontsize=7)
fig.suptitle("MD vs TVD (minimum curvature) with Rotliegend interval")
fig.tight_layout(); fig.savefig(FIGURES / "md_vs_tvd.png"); plt.show()""")

md(r"""## 4. Recovering `target_lithologies.csv`

The shipped file flags every row "AH depth - deviated well needs TVD conversion"
and leaves `depth_tvd_m` empty. `formation_top/base` are actually along-hole MD
(feet for JUT-01), and each row is an exact LAS sample identifiable by its GR -
top->base for BLT-01/JUT-01, reversed for the bottom-up-logged EVD-01/PKP-01.""")

code(r"""tgt = build_target_tvd()
chk = tgt.groupby("well_id").agg(
    n=("md_m","size"), tvd_min=("depth_tvd_m","min"), tvd_max=("depth_tvd_m","max"),
    top_tvd=("formation_top_tvd","first"), base_tvd=("formation_base_tvd","first")).round(1)
chk["lithostrat_top_tvd"] = [round(rotliegend_pick(w)["top_tvd"],1) for w in chk.index]
chk["top_diff_m"] = (chk.top_tvd - chk.lithostrat_top_tvd).abs().round(1)
chk["review"] = np.where(chk.top_diff_m > 10, "REVIEW", "ok")
chk""")

md(r"""**Cross-check.** Target tops match the lithostrat Slochteren tops to 0.0 m
for BLT-01/EVD-01/PKP-01. **JUT-01 is flagged**: its target GR traces uniquely to
~506 m (1659.5 *ft* - a feet/metre error in the source file), whereas its true
Slochteren sits at ~3161 m TVD below the Zechstein. JUT-01 target rows are
excluded from reservoir aggregation pending manual review.""")

md(r"""## 5. Petrophysics - BLT-01 anchor

Larionov-older V_shale and density porosity over BLT-01, Slochteren reservoir
shaded, net-reservoir flag where V_sh < 0.40 and phi > 0.08.""")

code(r"""def plot_petro(well):
    g = logs[logs.well == well].sort_values("tvd_m")
    pick = rotliegend_pick(well)
    net = (g.vsh < 0.40) & (g.phi_d > 0.08)
    fig, axes = plt.subplots(1, 3, figsize=(9, 8), sharey=True)
    axes[0].plot(g.GR, g.tvd_m, "g", lw=0.5); axes[0].set_xlabel("GR (gAPI)")
    ax0b = axes[0].twiny(); ax0b.plot(g.vsh, g.tvd_m, "brown", lw=0.6); ax0b.set_xlabel("Vsh"); ax0b.set_xlim(0,1)
    axes[1].plot(g.RHOB, g.tvd_m, "r", lw=0.5); axes[1].set_xlabel("RHOB (g/cc)"); axes[1].set_xlim(1.9,2.9)
    axes[2].plot(g.phi_d, g.tvd_m, "b", lw=0.5); axes[2].set_xlabel("phi_d (v/v)"); axes[2].set_xlim(0,0.3)
    axes[2].fill_betweenx(g.tvd_m, 0, g.phi_d.where(net), color="gold", alpha=0.6, label="net")
    for ax in axes:
        ax.axhspan(pick["top_tvd"], pick["base_tvd"], color="orange", alpha=0.15)
    axes[0].set_ylabel("TVD (m)"); axes[0].set_ylim(pick["base_tvd"]+40, pick["top_tvd"]-40)
    axes[2].legend(fontsize=7); fig.suptitle(f"{well} - Slochteren petrophysics")
    fig.tight_layout(); fig.savefig(FIGURES / f"petro_{well}.png"); plt.show()

plot_petro("BLT-01")""")

md(r"""## 6. Rotliegend net-reservoir summary (all wells)""")

code(r"""summary = pd.DataFrame([rotliegend_summary(logs, rotliegend_pick(w)) for w in WELLS])
summary["thermoGIS_top_m"] = [META[w].top_rotliegend_m for w in WELLS]
summary["thermoGIS_phi"]   = [META[w].porosity_pct_p50/100 for w in WELLS]
summary""")

md(r"""### What the data foundation tells us

* **BLT-01 is the development anchor** - gross ~122 m of Slochteren, **net-to-gross
  0.93**, net porosity ~15% (ThermoGIS 17%): the thickest, cleanest, most porous of
  the four, and the well every downstream calculation is anchored on.
* **EVD-01** - NTG ~0.55, phi ~11%: moderate.
* **PKP-01** - **NTG 0.10**, very tight (consistent with its low ThermoGIS
  permeability of ~1 mD).
* **JUT-01** - structurally complex (a reverse fault repeats the Slochteren section)
  with a deliberately corrupted target interval; we isolate and flag it rather than
  let it contaminate the aggregate.

A note on net-to-gross we make openly: our log-based NTG matches ThermoGIS at the
anchor well (0.93 vs 0.98) but is deliberately *stricter* at the three weaker wells,
where ThermoGIS publishes a regional play-average of 0.95-0.99. We trust the
well-specific logs there, which makes our characterisation the more conservative; and
because the resource estimate (notebook 03) is anchored on ThermoGIS's own published
flow rate, this disagreement sharpens the picture without changing the headline
deliverability. With a trustworthy data foundation in hand, notebook 03 turns these
rock properties into a probabilistic resource estimate and the doublet design.""")

nb["cells"] = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata["language_info"] = {"name": "python"}
with open("notebooks/01_eda.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print("wrote notebooks/01_eda.ipynb with", len(cells), "cells")
