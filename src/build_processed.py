"""Write the Day-1 processed artefacts from raw data.

Outputs (all under data/processed/, git-ignored and regenerable):
  * well_logs.parquet              tidy, unit-harmonised, TVD-referenced logs
  * target_lithologies_tvd.csv     flag cleared, depth_tvd_m recovered

Run:  python -m src.build_processed
"""

from __future__ import annotations

import logging

import pandas as pd

from src.lithostrat import rotliegend_pick
from src.paths import (
    DATA_PROCESSED,
    ROTLIEGEND_SUMMARY_CSV,
    WELL_LOGS_PARQUET,
)
from src.petrophysics import add_petrophysics, rotliegend_summary
from src.targets import build_target_tvd
from src.wells_io import WELLS, coverage_table, load_all

log = logging.getLogger(__name__)

TARGET_TVD_CSV = DATA_PROCESSED / "target_lithologies_tvd.csv"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    logs = add_petrophysics(load_all())
    logs.to_parquet(WELL_LOGS_PARQUET, index=False)
    log.info("wrote %s (%d rows, +vsh/phi_d)", WELL_LOGS_PARQUET.name, len(logs))
    print(coverage_table(logs).to_string(index=False))

    targets = build_target_tvd()
    targets.to_csv(TARGET_TVD_CSV, index=False)
    log.info("wrote %s (%d rows, flag cleared)", TARGET_TVD_CSV.name, len(targets))

    summary = pd.DataFrame(
        [rotliegend_summary(logs, rotliegend_pick(w)) for w in WELLS]
    )
    summary.to_csv(ROTLIEGEND_SUMMARY_CSV, index=False)
    log.info("wrote %s", ROTLIEGEND_SUMMARY_CSV.name)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
