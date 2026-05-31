"""Day-2 figures: Monte-Carlo MWth distribution + ThermoGIS reconciliation.

Run:  python scripts/make_deliverability_figures.py
Writes figures/mc_mwth_blt.png and figures/deliverability_reconciliation.png
(both git-ignored, regenerable).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.constants import DEMAND_HEATING_MWTH
from src.deliverability import deliverability_table
from src.montecarlo import simulate_all
from src.paths import FIGURES
from src.thermogis import load_thermogis


def fig_mc_distribution(mc, out: Path) -> None:
    blt = mc[mc["well"] == "BLT-01"]["mwth"].to_numpy()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for nd, c in [(1, "#4c72b0"), (2, "#dd8452"), (3, "#55a868")]:
        scheme = blt * nd
        ax.hist(np.clip(scheme, 0, 40), bins=60, alpha=0.55, color=c,
                label=f"{nd} doublet{'s' if nd > 1 else ''} "
                      f"(P50 {np.median(scheme):.1f} MWth)")
    ax.axvline(DEMAND_HEATING_MWTH, color="k", ls="--", lw=1.6,
               label=f"heating demand {DEMAND_HEATING_MWTH:.0f} MWth")
    ax.set_xlabel("Thermal power (MWth)")
    ax.set_ylabel("Monte-Carlo realisations (10k draws)")
    ax.set_title("BLT-01 doublet deliverability — Monte-Carlo MWth")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def fig_reconciliation(deliver, out: Path) -> None:
    wells = deliver["well"].tolist()
    x = np.arange(len(wells))
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(x - 0.2, deliver["flow_tg_p50"], 0.4, label="ThermoGIS Flow P50", color="#8c8c8c")
    ax.bar(x + 0.2, deliver["flow_model_p50"], 0.4, label="Darcy model P50", color="#4c72b0")
    ax.set_xticks(x)
    ax.set_xticklabels(wells)
    ax.set_ylabel("Flow rate (m$^3$/h)")
    ax.set_title("Darcy doublet model vs ThermoGIS — P50 flow reconciliation")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    tg = load_thermogis()
    mc = simulate_all(tg, n=10_000, anchor="flow")
    deliver = deliverability_table(tg)
    fig_mc_distribution(mc, FIGURES / "mc_mwth_blt.png")
    fig_reconciliation(deliver, FIGURES / "deliverability_reconciliation.png")
    print("wrote figures/mc_mwth_blt.png, figures/deliverability_reconciliation.png")


if __name__ == "__main__":
    main()
