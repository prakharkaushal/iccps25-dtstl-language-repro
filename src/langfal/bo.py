"""Gaussian-process Bayesian optimisation pieces shared by all falsification methods.

The paper specifies a GP surrogate with Expected Improvement (Eq. 5) and, for SMuRF, the MinBO
variant with a global incumbent (Eq. 7, ref. [34]). Everything else is our decision (D6), applied
identically to the proposed methods and to the RTAMT baselines:
  * scikit-learn GaussianProcessRegressor, kernel C * Matern(nu=2.5, isotropic) + White noise,
    normalize_y=True; hyperparameters re-optimised every iteration with a warm start from the
    previous fit (one random restart on the first fit). Isotropic rather than ARD because ARD fits
    cost 10-30x more (measured) and PROF fits one GP per box per round.
  * EI for MAXIMISATION of the objective (Eq. 5 is written in the minimisation form while Eq. 4
    maximises the distance; we use the standard maximisation form, xi = 0).
  * Acquisition maximised over random candidates: uniform samples in [0, 1]^d plus Gaussian
    perturbations around the best observed inputs (no gradient polishing).
"""
from __future__ import annotations

import time
import warnings
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", message=".*lbfgs failed to converge.*")


@dataclass(frozen=True)
class BOConfig:
    n_init: int = 5                    # paper: "same set of five starting points"
    max_iter: int = 200                # paper: terminate after 200 iterations
    n_uniform: int = 1000              # random acquisition candidates (D6)
    n_local: int = 1000                # local candidates around incumbents (D6)
    local_scales: tuple = (0.02, 0.1)  # std of local perturbations (D6)
    top_k: int = 5                     # incumbents used for local candidates (D6)
    xi: float = 0.0                    # EI exploration parameter (D6)
    length_scale_bounds: tuple = (1e-2, 1e2)
    noise_bounds: tuple = (1e-10, 1e-2)


def make_kernel(cfg: BOConfig):
    return (ConstantKernel(1.0, (1e-3, 1e3))
            * Matern(length_scale=0.5, length_scale_bounds=cfg.length_scale_bounds, nu=2.5)
            + WhiteKernel(1e-6, cfg.noise_bounds))


class Surrogate:
    """GP surrogate with warm-started hyperparameters; records fitting time."""

    def __init__(self, cfg: BOConfig, rng: np.random.Generator):
        self.cfg = cfg
        self.rng = rng
        self.kernel = make_kernel(cfg)
        self.gp = None
        self.fit_ms = 0.0
        self.n_fits = 0

    def fit(self, X, y):
        t0 = time.perf_counter_ns()
        restarts = 1 if self.gp is None else 0
        gp = GaussianProcessRegressor(self.kernel, normalize_y=True, n_restarts_optimizer=restarts,
                                      random_state=int(self.rng.integers(2**31 - 1)))
        y = np.asarray(y, dtype=float)
        if np.ptp(y) == 0.0:           # constant data: avoid a degenerate normalisation
            y = y + 1e-9 * self.rng.standard_normal(y.shape)
        gp.fit(np.asarray(X, dtype=float), y)
        self.gp, self.kernel = gp, gp.kernel_
        self.fit_ms += (time.perf_counter_ns() - t0) / 1e6
        self.n_fits += 1
        return self

    def predict(self, Xc):
        mu, sd = self.gp.predict(Xc, return_std=True)
        return mu, np.maximum(sd, 1e-12)


def expected_improvement(mu, sd, best, xi=0.0):
    """EI for maximisation: E[max(f - best - xi, 0)] under N(mu, sd^2)."""
    imp = mu - best - xi
    z = imp / sd
    return imp * norm.cdf(z) + sd * norm.pdf(z)


def candidates(rng, X, y, dim, cfg: BOConfig):
    """Uniform candidates plus Gaussian perturbations of the top-k observed inputs."""
    parts = [rng.uniform(size=(cfg.n_uniform, dim))]
    if cfg.n_local > 0 and len(X):
        top = np.asarray(X)[np.argsort(np.asarray(y))[::-1][: cfg.top_k]]
        per = max(1, cfg.n_local // (len(top) * len(cfg.local_scales)))
        for s in cfg.local_scales:
            for x0 in top:
                parts.append(np.clip(x0 + s * rng.standard_normal((per, dim)), 0.0, 1.0))
    return np.vstack(parts)


def propose(sur: Surrogate, X, y, dim, cfg: BOConfig, rng, best=None):
    """Next input maximising EI (best = incumbent; defaults to max(y)). Returns (u, ei)."""
    best = float(np.max(y)) if best is None else float(best)
    Xc = candidates(rng, X, y, dim, cfg)
    mu, sd = sur.predict(Xc)
    ei = expected_improvement(mu, sd, best, cfg.xi)
    k = int(np.argmax(ei))
    return Xc[k], float(ei[k])
