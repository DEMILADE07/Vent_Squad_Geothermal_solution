"""Unit-conversion guards. The key risk is double-converting JUT-01's feet."""

import numpy as np
import pytest

from src.units import FOOT_IN_METRES, ensure_metres, feet_to_metres


def test_feet_to_metres_known_value():
    # 11220 ft (JUT-01 STOP) -> ~3419.9 m
    assert feet_to_metres(11220.0) == pytest.approx(11220.0 * 0.3048)


def test_double_application_is_wrong():
    """feet_to_metres is deliberately not idempotent: applying it twice must
    NOT equal the correct single conversion. This pins the bug ensure_metres
    exists to prevent."""
    once = feet_to_metres(1000.0)
    twice = feet_to_metres(feet_to_metres(1000.0))
    assert once == pytest.approx(304.8)
    assert twice != pytest.approx(once)
    assert twice == pytest.approx(304.8 * FOOT_IN_METRES)  # 92.9 m — clearly wrong


def test_ensure_metres_is_idempotent():
    """ensure_metres keyed on unit must be safe to re-run on its own output."""
    vals, unit = ensure_metres([7.0, 11220.0], "F")
    assert unit == "m"
    np.testing.assert_allclose(vals, np.array([7.0, 11220.0]) * 0.3048)

    # Feeding the already-metric output back in changes nothing.
    vals2, unit2 = ensure_metres(vals, unit)
    assert unit2 == "m"
    np.testing.assert_allclose(vals2, vals)


def test_ensure_metres_passthrough_metres():
    vals, unit = ensure_metres([100.0, 200.0], "M")
    np.testing.assert_allclose(vals, [100.0, 200.0])
    assert unit == "m"


def test_ensure_metres_rejects_unknown_unit():
    with pytest.raises(ValueError):
        ensure_metres([1.0], "fathoms")
