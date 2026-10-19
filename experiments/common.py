"""Shared experiment plumbing: configs, seeds, problem construction, parallel execution."""
from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from langfal import bo  # noqa: E402
from langfal.falsification import FalsificationProblem  # noqa: E402
from langfal.language import compile_negated_language  # noqa: E402
from langfal.monitors import RtamtMonitor, ensure_typing_io  # noqa: E402
from langfal.specs import cc_specs  # noqa: E402
from langfal.systems.chasing_cars import CCConfig, ChasingCars  # noqa: E402

ensure_typing_io()
SPEC_CODES = {f"phi{i}": i for i in range(1, 9)}
# PROF and PROF-all share a code on purpose: identical random streams make Table 4's S_min equal
# Table 2's PROF iteration count for the same trial (as observed in the paper).
METHOD_CODES = {"PROF": 1, "PROF-all": 1, "PBO-RTAMT": 2, "SMuRF": 3, "SBO-RTAMT": 4, "SEQ-BO": 5,
                "LCW": 6, "LCP": 7, "BO-CTRL": 8}


def utf8_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load_config(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def single_threaded_env():
    """Avoid BLAS oversubscription when running many worker processes."""
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(var, "1")


def trial_seed(cfg: dict, trial: int) -> int:
    return int(cfg["seed_base"]) + int(trial)


def initial_design(seed: int, n_init: int, dim: int) -> np.ndarray:
    """D7: the n_init starting points of a trial, shared by every method (paired design)."""
    return np.random.default_rng(np.random.SeedSequence([seed, 0])).uniform(size=(n_init, dim))


def method_rng(seed: int, method: str, spec: str) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([seed, METHOD_CODES[method], SPEC_CODES[spec]]))


def cc_config(cfg: dict) -> CCConfig:
    return CCConfig(**cfg.get("cc", {}))


def bo_config(cfg: dict) -> bo.BOConfig:
    d = dict(cfg.get("bo", {}))
    if "local_scales" in d:
        d["local_scales"] = tuple(d["local_scales"])
    return bo.BOConfig(**d)


_PROBLEMS = {}


def language_boxes(cfg: dict, spec_name: str, sp):
    """Boxes of L(not phi) from the configured source: the exact compiler (default) or a FindBox run
    (config: language: {source: findbox, run: <run-id>, variant: <variant>})."""
    lang = cfg.get("language", {"source": "exact"})
    if lang.get("source", "exact") == "exact":
        return compile_negated_language(sp.formula, sp.n_samples)
    if lang["source"] == "findbox":
        from langfal.language import BoxUnion
        path = ROOT / "results" / "raw" / "findbox" / lang["run"] / f"{lang['variant']}_{spec_name}.json"
        return BoxUnion.load(path)
    raise ValueError(f"unknown language source {lang}")


def cc_problem(cfg: dict, spec_name: str) -> FalsificationProblem:
    key = (spec_name, repr(sorted(cfg.get("cc", {}).items())), repr(cfg.get("language")))
    if key not in _PROBLEMS:
        ccfg = cc_config(cfg)
        sp = cc_specs(dt=ccfg.sample_dt, n_samples=ccfg.n_samples)[spec_name]
        sim = ChasingCars(ccfg)
        _PROBLEMS[key] = FalsificationProblem(
            name=spec_name, simulate=sim, neg_boxes=language_boxes(cfg, spec_name, sp),
            rtamt=RtamtMonitor(sp.formula), dim=ccfg.dim)
    return _PROBLEMS[key]


def run_parallel(fn, tasks, workers: int, on_result):
    """Run fn(task) for each task; call on_result(task, result) in the parent as results arrive."""
    if workers <= 1:
        for t in tasks:
            on_result(t, fn(t))
        return
    single_threaded_env()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, t): t for t in tasks}
        for fut in as_completed(futs):
            on_result(futs[fut], fut.result())
