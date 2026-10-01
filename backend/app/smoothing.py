"""
One-Euro filter (Casiez et al., 2012): heavy smoothing when still, low lag when moving.
"""

import math


class _LowPass:
    def __init__(self) -> None:
        self.value: float | None = None

    def __call__(self, x: float, alpha: float) -> float:
        self.value = x if self.value is None else alpha * x + (1 - alpha) * self.value
        return self.value


def _alpha(cutoff: float, dt: float) -> float:
    tau = 1.0 / (2 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / dt)


class OneEuroFilter:
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.05, d_cutoff: float = 1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._x = _LowPass()
        self._dx = _LowPass()
        self._prev: float | None = None

    def reset(self) -> None:
        self.__init__(self.min_cutoff, self.beta, self.d_cutoff)

    def __call__(self, x: float, dt: float) -> float:
        dt = max(dt, 1e-3)
        dx = 0.0 if self._prev is None else (x - self._prev) / dt
        self._prev = x
        edx = self._dx(dx, _alpha(self.d_cutoff, dt))
        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self._x(x, _alpha(cutoff, dt))
