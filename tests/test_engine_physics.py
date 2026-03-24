from __future__ import annotations

import unittest

from smalloldgames.engine.physics import apply_gravity, bounce_x, clamp, integrate_velocity, wrap_x


class IntegrateVelocityTests(unittest.TestCase):
    def test_basic(self) -> None:
        x, y = integrate_velocity(0.0, 0.0, 10.0, 20.0, 0.5)
        self.assertAlmostEqual(x, 5.0)
        self.assertAlmostEqual(y, 10.0)

    def test_zero_dt(self) -> None:
        x, y = integrate_velocity(5.0, 10.0, 100.0, 200.0, 0.0)
        self.assertAlmostEqual(x, 5.0)
        self.assertAlmostEqual(y, 10.0)


class ApplyGravityTests(unittest.TestCase):
    def test_negative_gravity(self) -> None:
        vy = apply_gravity(0.0, -980.0, 1.0)
        self.assertAlmostEqual(vy, -980.0)

    def test_accumulates(self) -> None:
        vy = apply_gravity(100.0, -980.0, 0.5)
        self.assertAlmostEqual(vy, -390.0)


class ClampTests(unittest.TestCase):
    def test_in_range(self) -> None:
        self.assertAlmostEqual(clamp(5.0, 0.0, 10.0), 5.0)

    def test_below(self) -> None:
        self.assertAlmostEqual(clamp(-1.0, 0.0, 10.0), 0.0)

    def test_above(self) -> None:
        self.assertAlmostEqual(clamp(15.0, 0.0, 10.0), 10.0)


class WrapXTests(unittest.TestCase):
    def test_in_range(self) -> None:
        self.assertAlmostEqual(wrap_x(100.0, 540.0), 100.0)

    def test_wraps_positive(self) -> None:
        self.assertAlmostEqual(wrap_x(550.0, 540.0), 10.0)

    def test_wraps_negative(self) -> None:
        result = wrap_x(-10.0, 540.0)
        self.assertAlmostEqual(result, 530.0)


class BounceXTests(unittest.TestCase):
    def test_no_change_in_bounds(self) -> None:
        x, vx = bounce_x(50.0, 10.0, 20.0, 0.0, 540.0)
        self.assertAlmostEqual(x, 50.0)
        self.assertAlmostEqual(vx, 10.0)

    def test_bounce_at_min(self) -> None:
        x, vx = bounce_x(-5.0, -10.0, 20.0, 0.0, 540.0)
        self.assertAlmostEqual(x, 0.0)
        self.assertGreater(vx, 0.0)

    def test_bounce_at_max(self) -> None:
        x, vx = bounce_x(525.0, 10.0, 20.0, 0.0, 540.0)
        self.assertAlmostEqual(x, 520.0)
        self.assertLess(vx, 0.0)

    def test_preserves_speed(self) -> None:
        _, vx = bounce_x(-1.0, -15.0, 10.0, 0.0, 100.0)
        self.assertAlmostEqual(abs(vx), 15.0)


if __name__ == "__main__":
    unittest.main()
