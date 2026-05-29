"""Unit harmonisation — depth conversions.

Only JUT-01 is logged in feet; every other well and all coordinates are in
metres. We convert *once*, centrally, and guard against accidental double
application: ``ensure_metres`` is idempotent because it keys off the declared
unit string and rewrites it to ``"m"`` after converting.

The raw multiply (``feet_to_metres``) is intentionally *not* idempotent — that
is the bug we are protecting against, and ``tests/test_units.py`` pins it.
"""

from __future__ import annotations

import numpy as np

# 1 international foot = 0.3048 m exactly. constants.FEET_PER_METRE is the
# reciprocal (3.280839895); we keep the exact factor here to avoid rounding.
FOOT_IN_METRES = 0.3048

_METRE_UNITS = {"m", "metre", "metres", "meter", "meters"}
_FEET_UNITS = {"f", "ft", "feet", "foot"}


def feet_to_metres(values):
    """Convert a scalar or array of feet to metres. Pure multiply — calling
    this twice double-converts and is wrong by design (see ensure_metres)."""
    return np.asarray(values, dtype=float) * FOOT_IN_METRES


def ensure_metres(values, unit: str) -> tuple[np.ndarray, str]:
    """Idempotently return ``values`` in metres alongside the unit ``"m"``.

    Safe to call repeatedly: once the unit is metric it is a no-op, so a
    pipeline that re-runs cannot silently double-convert.

    Raises on an unrecognised unit rather than guessing.
    """
    u = unit.strip().lower()
    arr = np.asarray(values, dtype=float)
    if u in _METRE_UNITS:
        return arr, "m"
    if u in _FEET_UNITS:
        return feet_to_metres(arr), "m"
    raise ValueError(f"Unrecognised depth unit {unit!r}; expected feet or metres.")
