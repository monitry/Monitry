import unittest

from core.interval import AdaptiveInterval


class FixedRandom:
    """Stub for random.Random — .uniform() always returns a fixed value."""

    def __init__(self, value: float):
        self.value = value

    def uniform(self, lo, hi):
        return self.value


class TestAdaptiveInterval(unittest.TestCase):
    def test_starts_at_min(self):
        interval = AdaptiveInterval(min_interval=10, max_interval=120, step=10)
        self.assertEqual(interval.base, 10)

    def test_step_up_increases_by_step(self):
        interval = AdaptiveInterval(min_interval=10, max_interval=120, step=10)
        interval.step_up()
        self.assertEqual(interval.base, 20)
        interval.step_up()
        self.assertEqual(interval.base, 30)

    def test_step_up_caps_at_max(self):
        interval = AdaptiveInterval(min_interval=10, max_interval=25, step=10)
        interval.step_up()  # 20
        interval.step_up()  # would be 30, capped at 25
        self.assertEqual(interval.base, 25)
        interval.step_up()  # stays capped
        self.assertEqual(interval.base, 25)

    def test_snap_down_resets_to_min_from_any_point(self):
        interval = AdaptiveInterval(min_interval=10, max_interval=120, step=10)
        for _ in range(5):
            interval.step_up()
        self.assertGreater(interval.base, 10)
        interval.snap_down()
        self.assertEqual(interval.base, 10)

    def test_sample_wait_applies_jitter(self):
        interval = AdaptiveInterval(
            min_interval=10, max_interval=120, step=10,
            jitter_lo=0.4, jitter_hi=1.6, rng=FixedRandom(0.5),
        )
        interval.base = 20
        sleep_seconds, effective = interval.sample_wait(elapsed=0.0)
        self.assertEqual(effective, 10.0)  # 20 * 0.5
        self.assertEqual(sleep_seconds, 10.0)

    def test_sample_wait_floors_at_min_interval(self):
        # base * jitter can dip below min_interval — must be floored.
        interval = AdaptiveInterval(
            min_interval=10, max_interval=120, step=10,
            jitter_lo=0.4, jitter_hi=1.6, rng=FixedRandom(0.1),
        )
        interval.base = 10
        _, effective = interval.sample_wait(elapsed=0.0)
        self.assertEqual(effective, 10.0)  # 10 * 0.1 = 1.0, floored to 10

    def test_sample_wait_subtracts_elapsed(self):
        interval = AdaptiveInterval(
            min_interval=10, max_interval=120, step=10,
            jitter_lo=1.0, jitter_hi=1.0, rng=FixedRandom(1.0),
        )
        interval.base = 20
        sleep_seconds, effective = interval.sample_wait(elapsed=5.0)
        self.assertEqual(effective, 20.0)
        self.assertEqual(sleep_seconds, 15.0)

    def test_sample_wait_never_goes_negative(self):
        interval = AdaptiveInterval(
            min_interval=10, max_interval=120, step=10,
            jitter_lo=1.0, jitter_hi=1.0, rng=FixedRandom(1.0),
        )
        interval.base = 10
        sleep_seconds, _ = interval.sample_wait(elapsed=50.0)  # API call took way longer than the interval
        self.assertEqual(sleep_seconds, 0.0)

    def test_off_task_then_ramp_sequence(self):
        # Mirrors the real monitor loop: snap on off-task, step up after every check.
        interval = AdaptiveInterval(min_interval=10, max_interval=30, step=10)
        interval.step_up()  # 20 after first on-task check
        interval.step_up()  # 30 after second
        self.assertEqual(interval.base, 30)

        interval.snap_down()  # off-task detected
        self.assertEqual(interval.base, 10)

        interval.step_up()  # ramping back up
        self.assertEqual(interval.base, 20)


if __name__ == "__main__":
    unittest.main()
