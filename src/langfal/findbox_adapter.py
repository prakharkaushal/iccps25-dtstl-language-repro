"""Run FindBox (the language-approximation code of the paper's ref. [5]) and convert its boxes.

FindBox lives in external/FindBox (github.com/Chris-amV/FindBox, commit bf19736). It has NO license;
it is used locally at the user's explicit request (2026-10-18) and is not redistributed (external/ is
git-ignored). Nothing in the repository is modified:
  * LanguageBoxGeneral.py runs a 50-dimensional FindBox at import time and imports its oracle from
    model.py (which needs PSY-TaLiRo). We parse the file, keep only its imports, function/class
    definitions and the ``Ocount`` counter, and execute that unchanged code with our own ``model``
    module providing the oracle ``d2``.
  * The oracle is what FindBox's model.py computes: RTAMT dense-time robustness at t = 0 of the formula
    conjoined with the signal-space bounds (README: "... and (always (x1 >= -20 and x1 <= 20))"),
    on the point's coordinates at times 0..n-1.
  * ``run_findbox`` repeats the body of FindBox's ``FindBox(n, Box)`` (sample -> walkBox on points with
    d2 > 0 -> recon -> over/under-approximation check) with the sample size as a parameter (hard-coded
    to 1000 there) and a seed for Python's ``random`` (unseeded there).
"""
from __future__ import annotations

import ast
import contextlib
import io
import random
import sys
import time
import types
from pathlib import Path

import numpy as np

from . import stl
from .language import BoxUnion
from .monitors import RtamtMonitor

FINDBOX_DIR = Path(__file__).resolve().parents[2] / "external" / "FindBox"


def bounded(formula: stl.Formula, n: int, lo: float, hi: float) -> stl.Formula:
    """formula AND always[0, n-1](lo <= x <= hi): FindBox's way of bounding the signal space."""
    return stl.conj(formula, stl.always(0, n - 1, stl.between(lo, hi)))


def load_findbox(oracle, findbox_dir: Path = FINDBOX_DIR) -> dict:
    """Execute LanguageBoxGeneral.py's definitions (unchanged) with ``oracle`` as model.d2."""
    if not (findbox_dir / "LanguageBoxGeneral.py").exists():
        raise FileNotFoundError(f"FindBox not found in {findbox_dir}; see scripts/fetch_findbox.sh")
    fake_model = types.ModuleType("model")
    fake_model.d2 = oracle
    sys.modules["model"] = fake_model
    if str(findbox_dir) not in sys.path:
        sys.path.insert(0, str(findbox_dir))
    src = (findbox_dir / "LanguageBoxGeneral.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    keep = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            keep.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "Ocount" for t in node.targets):
            keep.append(node)
    tree.body = keep
    ns = {"__name__": "findbox_LanguageBoxGeneral", "__file__": str(findbox_dir / "LanguageBoxGeneral.py")}
    exec(compile(tree, str(findbox_dir / "LanguageBoxGeneral.py"), "exec"), ns)
    return ns


class Oracle:
    """FindBox's d2(p): robustness at t = 0 of the bounded formula; counts calls.

    impl='rtamt_dense' is what FindBox's model.py computes (PSY-TaLiRo's RTAMTDense); impl='scalar' is
    our pure-Python robustness, equal to RTAMT dense-time on these formulas (tests/test_findbox.py) and
    2-4x faster, which matters because FindBox calls the oracle millions of times."""

    def __init__(self, formula: stl.Formula, impl: str = "scalar"):
        self.formula = formula
        self.impl = impl
        self.mon = RtamtMonitor(formula, mode="dense") if impl == "rtamt_dense" else None
        self.calls = 0

    def __call__(self, p) -> float:
        self.calls += 1
        if self.mon is not None:
            return self.mon(np.asarray(p.coord, dtype=float))
        return stl.robustness_scalar(self.formula, p.coord)


def run_findbox(formula: stl.Formula, n: int, lo: float, hi: float, n_samples: int = 1000,
                seed: int = 0, n_check: int = 1000, quiet: bool = True, sampler: str = "integer",
                oracle_impl: str = "scalar") -> dict:
    """Approximate the language of ``formula`` within [lo, hi]^n with FindBox. Returns boxes + diagnostics.

    sampler='integer' is FindBox's FindBox() (``sample``: random.randint on the integer grid);
    sampler='continuous' uses FindBox's own ``sampleC`` (uniform reals; used in its opt.py). sampleC caps
    the points drawn per box at N/3, so it is asked for 3 * n_samples to obtain n_samples points."""
    oracle = Oracle(bounded(formula, n, lo, hi), impl=oracle_impl)
    fb = load_findbox(oracle)
    random.seed(seed)
    ALL = fb["space"](n)
    B = fb["Box"](n)
    B.Borders = [[lo, hi] for _ in range(n)]
    ALL.addBoxes(B)
    out = io.StringIO()
    t0 = time.perf_counter()
    with contextlib.redirect_stdout(out) if quiet else contextlib.nullcontext():
        Sam = fb["sample"](ALL, n_samples) if sampler == "integer" else fb["sampleC"](ALL, 3 * n_samples)[:n_samples]
        corners, n_inside = [], 0
        for p in Sam:
            if oracle(p) > 0:
                n_inside += 1
                corners += fb["walkBox"](p)
        t_walk = time.perf_counter() - t0
        boxes = fb["recon"](corners) if corners else []
    t_total = time.perf_counter() - t0
    calls_build = oracle.calls
    rec = fb["space"](n)
    rec.Boxes = boxes
    # FindBox's own check: points sampled in the boxes that are not in the language (over-approx.),
    # and points of the language (sampled in the domain) that are outside every box (under-approx.)
    over = under = in_lang = n_over_checked = 0
    if boxes:
        # FindBox samples the reconstructed boxes with random.randint, which rejects float borders on
        # Python >= 3.12; we use FindBox's own continuous sampler sampleC (as its opt.py does) instead.
        for p in fb["sampleC"](rec, n_check):
            n_over_checked += 1
            over += oracle(p) < 0
    for p in fb["sample"](ALL, n_check):
        if oracle(p) > 0:
            in_lang += 1
            under += (fb["d1"](p, rec) < 0) if boxes else 1
    lo_arr = np.array([[b.Borders[i][0] for i in range(n)] for b in boxes], dtype=float).reshape(-1, n)
    hi_arr = np.array([[b.Borders[i][1] for i in range(n)] for b in boxes], dtype=float).reshape(-1, n)
    return {"boxes": BoxUnion(lo_arr, hi_arr), "n_boxes": len(boxes), "n_samples": len(Sam), "seed": seed,
            "sampler": sampler, "oracle_impl": oracle_impl,
            "bounds": [lo, hi], "n": n, "samples_inside_language": n_inside, "corner_points": len(corners),
            "oracle_calls_build": calls_build, "walk_s": t_walk, "total_s": t_total,
            "check_over_bad_points": int(over), "check_box_points": int(n_over_checked),
            "check_language_points": int(in_lang),
            "check_under_bad_points": int(under), "findbox_stdout_chars": len(out.getvalue())}
