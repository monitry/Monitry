import random


class AdaptiveInterval:
    """Tracks the check interval used by the monitor loop.

    The base interval starts at ``min_interval`` and ramps up by ``step``
    seconds after every check, capping at ``max_interval``. Detecting an
    off-task moment snaps the base back down to ``min_interval`` so the
    next few checks run more often. Each wait is jittered by a random
    factor in ``[jitter_lo, jitter_hi]`` and floored at ``min_interval``.
    """

    def __init__(
        self,
        min_interval: float = 10,
        max_interval: float = 120,
        step: float = 10,
        jitter_lo: float = 0.4,
        jitter_hi: float = 1.6,
        rng: random.Random | None = None,
    ):
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.step = step
        self.jitter_lo = jitter_lo
        self.jitter_hi = jitter_hi
        self._rng = rng or random
        self.base = min_interval

    def snap_down(self) -> None:
        """Call when off-task is detected — resets the ramp to the minimum."""
        self.base = self.min_interval

    def step_up(self) -> None:
        """Call after each check to ramp the base interval back toward the max."""
        self.base = min(self.base + self.step, self.max_interval)

    def sample_wait(self, elapsed: float = 0.0) -> tuple[float, float]:
        """Return (sleep_seconds, effective_seconds) for the next wait.

        ``effective_seconds`` is the jittered interval; ``sleep_seconds``
        subtracts time already spent this cycle (e.g. on the API call).
        """
        effective = max(self.min_interval, self.base * self._rng.uniform(self.jitter_lo, self.jitter_hi))
        sleep_seconds = max(0.0, effective - elapsed)
        return sleep_seconds, effective
