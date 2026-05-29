"""target_lithologies TVD recovery: alignment must be exact and physical."""

import numpy as np
import pytest

from src.targets import build_target_tvd, recover_well_depths
from src.wells_io import WELLS

EXPECTED = {  # (n_rows, reversed) established during EDA
    "BLT-01": (1689, False),
    "EVD-01": (780, True),
    "JUT-01": (256, False),
    "PKP-01": (730, True),
}


@pytest.mark.parametrize("well", WELLS)
def test_alignment_recovers_all_rows(well):
    sub = recover_well_depths(well)
    n, rev = EXPECTED[well]
    assert len(sub) == n
    assert sub.attrs["aligned_reversed"] is rev
    assert sub["depth_tvd_m"].notna().all()


def test_build_clears_flag_and_fills_tvd():
    df = build_target_tvd()
    assert (df["flag"] == "ok").all()
    assert df["depth_tvd_m"].notna().all()
    # TVD must never exceed MD, and rows sit within their formation TVD window.
    assert (df["depth_tvd_m"] <= df["md_m"] + 1e-6).all()
    within = (
        (df["depth_tvd_m"] >= df["formation_top_tvd"] - 1.0)
        & (df["depth_tvd_m"] <= df["formation_base_tvd"] + 1.0)
    )
    assert within.all()


def test_gr_matches_source_exactly():
    """Recovered rows must carry the same GR as the CSV (sanity on the join)."""
    import pandas as pd
    from src.paths import TARGET_LITHOLOGIES_CSV
    tl = pd.read_csv(TARGET_LITHOLOGIES_CSV)
    for well in WELLS:
        sub = recover_well_depths(well)
        src = tl[tl.well_id == well].reset_index(drop=True)
        np.testing.assert_allclose(sub["gamma_ray_api"], src["gamma_ray_api"])
