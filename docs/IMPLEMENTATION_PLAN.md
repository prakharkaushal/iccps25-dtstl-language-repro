# Implementation Plan — Reproducing the ICCPS '25 Language-Set Paper

**Status: IMPLEMENTED (Phase 3).** This was the Phase 2 proposal; it is kept unchanged below for the record. The *final* decisions are in [DEVIATIONS.md](../DEVIATIONS.md). Some changed during implementation, based on evidence:
- **D4** (state bounds) was dropped: the exact language needs none.
- **D6** uses an isotropic kernel, not ARD: ARD fits measured 10–30× slower.
- **D9** requires a strict Dist > 0: boundary signals with ρ = 0 satisfy φ.
- **D13** uses a fresh BO per box: reusing data across boxes made each GP grow unboundedly.
- **U1** was resolved by porting the official ARCH Chasing Cars model from its Simulink text file. Once MATLAB +
  Simulink were installed, the port was checked against the official model (DEVIATIONS A2, `results/tables/cc_port_vs_simulink.md`).
- **U3** was resolved by not using FindBox for the main results: languages are compiled exactly (A1). At the
  user's request, FindBox was later also run, and E2/E3 were repeated with its languages (A1b, D25).

It is based on [TARGET_ANALYSIS.md](TARGET_ANALYSIS.md) (cited as [A §x]) and [REFERENCE_ANALYSIS.md](REFERENCE_ANALYSIS.md) ([R §x]).

## 0. What "reproduce" can mean here

| Level | Meaning | Achievable? |
|---|---|---|
| L1 exact | same numbers as Tables 1–5 | **No**: seeds, starting points, GP settings, discretisation and hardware are unstated [A §5] |
| L2 statistical | same system, same formulas, our documented choices for the gaps; compare FR, iteration distributions and **speedup ratios** with CIs | **Yes, if** we get the paper's CC model (decision U1) |
| L3 re-implementation | same algorithms on a substitute CC implementation or UAV tracker | Yes; results labelled "re-implementation" |

**Claims we will test, phrased as the paper states them** [A §1, §6]:

- **C1:** the language monitor's sign agrees with RTAMT (all but one case of 50,000).
- **C2:** the language monitor is about 1–2 orders of magnitude faster per call than RTAMT.
- **C3:** PROF has falsification rate and iterations comparable to PBO-RTAMT, with much lower monitoring time.
- **C4:** SMuRF needs fewer iterations and less monitoring time than SBO-RTAMT.
- **C5:** FR = 20/20 everywhere.
- **C6:** some boxes are much harder to falsify (Table 4).
- **C7:** LCP needs fewer iterations than LCW (2–4x).
- **C8:** LangControl needs few iterations on easy formulas.

We will **not** tune anything to match the paper's numbers.

---

## 1. Decisions only you can make (blocking)

| ID | Question | Options | My recommendation |
|---|---|---|---|
| **U1** | Chasing Cars model source | (a) You provide MATLAB + Simulink, and we run the ARCH CC model through the MATLAB Engine for Python (most faithful; no MATLAB on this machine). (b) I download the ARCH benchmark repository (approval) and **port CC to Python**, validated against the Simulink behaviour if possible, else labelled L3. (c) Ask the authors for their exact setup | **(c) now + (b) as fallback**. P1 below needs no simulator, so work can start while waiting |
| **U2** | Python environment | (a) new `target_project/.venv` with Python 3.11 (needs downloading Python + packages, a few hundred MB). (b) try the existing Python 3.14 (RTAMT/PSY-TaLiRo compatibility unverified) | **(a)**: pinned and reproducible. I'll ask before each download |
| **U3** | FindBox (language generator, ref. [5]) has **no license** | (a) clone and use it for research reproduction, unmodified, not redistributed. (b) ask the authors first. (c) re-implement ref. [5]'s algorithm | **(a) + (b)**. (c) only if refused, since it adds a large source of divergence |
| **U4** | Scope | Falsification only (E1–E4), or also control (E5, optional E6) | **Both**, with control after falsification. Control can only reach L3 because the tracker is unspecified |
| **U5** | Contact the authors? | I can draft an email listing the blocking gaps for you to send | **Yes**: ref. [4] shows the first author shares details |

---

## 2. Our implementation decisions (to fill paper gaps)

Each is **our decision**, logged in the run configs and stated in every results table. "Sensitivity" means we will also run the alternative on a small pilot and report the effect.

| ID | Gap [A] | Paper says | Our default | Alternative / sensitivity |
|---|---|---|---|---|
| **D1** | Output grid (§7.7) | 100 s, 0.1 Hz, "10 steps", ℝ¹⁰ | **11 samples, t = 0, 10, …, 100 s**, so φ₂'s 100 s horizon fits | 10 samples (t = 0…90) with the trace end handled RTAMT-style. Report box counts and satisfaction ratios for both against Table 1 |
| **D2** | Seconds → steps | intervals in seconds | `[a,b] ↦ [⌈a/10⌉, ⌊b/10⌋]`; φ₅'s □[0,5] ↦ [0,0] | report effect on φ₅ |
| **D3** | Input interpolation | 10 control points per input, range [0,1] | piecewise constant, ten 10-s segments (ARCH "instance 2" style) | piecewise linear (pilot only) |
| **D4** | Bounded state space for y₅−y₄ (Thm 2.3) | not given | envelope of the 10,000-sample E1 run, padded 10 % | physics-based bounds if the model allows |
| **D5** | Distance and language monitor (§7) | Eq. (1), ‖·‖_∞ | closed-form signed distance to each box; language monitor = `max_k Dist(x, b_k)` | exact distance to the union boundary on a subsample, to quantify the gap |
| **D6** | GP / BO settings | GP + EI | scikit-learn GP, Matérn-5/2 ARD + white noise, inputs in [0,1]²⁰, normalised targets, MLE with 3 restarts. **EI for maximisation** (Eq. 5 rewritten per §7.5), ξ = 0. Acquisition: 2,000 random candidates, then L-BFGS-B from the best 5. **Identical for all 4 falsifiers** | — |
| **D7** | Starting points | "same five starting points" | per trial, 5 uniform points from the trial seed, **shared by all methods and all boxes** (paired design, as in the reference [R §7]) | — |
| **D8** | Iteration count | "number of iterations" | S = BO iterations **after** n₀. For PROF/PBO, one lock-step round = one iteration of every active box/process. Also log S+n₀ and **total simulations** (our extra column) | — |
| **D9** | Falsifier acceptance (§7.6) | Dist ≥ 0 (algs), Dist > 0 (Eq. 4); validate with RTAMT | stop when Dist ≥ 0 (language methods) or ρ < 0 (RTAMT methods). Re-check with RTAMT; if validation fails, log it and **continue**. FR counts validated falsifiers only | — |
| **D10** | PBO-RTAMT diversity | "runs on j processors" | j processes share the n₀ points but use different acquisition RNG streams; stop when any finds ρ < 0 | j identical processes (degenerate case, pilot only) |
| **D11** | Timing | T̄_T, T̄_M = monitoring ms | `perf_counter_ns` around monitor calls only. T_M = mean per call; T_T = sum per trial. **Also log** simulation, GP-fit and total wall time (extra columns, labelled as ours) | — |
| **D12** | Seeds and trials | 20 independent trials | seeds `1000 + t`, t = 0…19, logged in every record | — |
| **D13** | Table 4 procedure (§7.4) | two procedures, one table | S̄_min/S̄_max from modified PROF (stops when all boxes falsified or 200 rounds). S̄/T̄_T/T̄_M from sequential BO (seeded random box order, ≤ 200 iterations per box, stop at first falsifier) | — |
| **D14** | UAV model (§7.8) | equations, no parameters | standard Euler form `(I_y−I_z)/I_x`; parameters from ref. [47] if accessible (approval), else typical small-quadrotor values; RK4 integration; 1 time unit per sample | — |
| **D15** | Tracker | "control system tracker" | cascaded controller: outer PD on x-position → desired pitch; inner attitude PD; altitude hold. **Our design**, held fixed for LCW and LCP | LQR on hover linearisation (pilot) |
| **D16** | Sample(B), Projection, M, K | not specified | Sample: pick a box uniformly, then a uniform point inside, without reuse. Projection: per-coordinate clip onto the nearest box (L2). M = 500, K = 10, which is above Table 5's largest P̄ = 1965; log failures | volume-weighted box choice |
| **D17** | Control lengths (§7.7) | lengths 10 and 30; [8,10] used | length-10 formulas on 11 samples (index 0…10); length-30 on 30 samples | — |
| **D18** | Statistics | means only | mean ± 95 % t-CI and median for every metric; speedup = ratio of means, plus geometric mean over requirements (method reused from the reference [A §9.1]); paired Wilcoxon test on per-trial iterations (our addition, labelled) | — |

---

## 3. Proposed code layout (new files only; the reference stays read-only)

```
target_project/
├─ pyproject.toml / requirements.lock     # pinned (U2)
├─ src/langfal/
│  ├─ specs.py            # φ definitions (CC φ1–φ5, UAV φ1–φ8) → RTAMT discrete-time; D1, D2, D17
│  ├─ monitors.py         # RTAMT wrapper + language monitor, both timed (D5, D11)
│  ├─ boxes.py            # Box/union: signed distance (Eq. 1), membership, projection, sampling (D16)
│  ├─ findbox_adapter.py  # calls external FindBox checkout, caches boxes to JSON (+ generation time)
│  ├─ systems/cc.py       # CC model per U1; inputs.py: 20 control points → signals (D3)
│  ├─ systems/uav.py      # quadrotor dynamics + tracker (D14, D15)
│  ├─ bo.py               # GP, EI (Eq. 5), MinBO EI (Eq. 7), acquisition optimiser (D6)
│  ├─ falsify.py          # PROF, PBO-RTAMT (lock-step, D8, D10), SMuRF, SBO-RTAMT, Table-4 variants (D13)
│  └─ control.py          # LangControl LCW/LCP (Alg. 3)
├─ experiments/  configs/*.yaml + run_e1.py … run_e6.py  (resumable; one JSONL record per trial)
├─ results/raw/  results/tables/  results/figures/
├─ analysis/     paper_reported_values.py (done) · stats.py (D18) · make_tables.py · make_figures.py
├─ tests/        unit + property tests (below)
└─ generate_artifacts.sh, Dockerfile, README.md   (reference packaging pattern [R §7])
```

---

## 4. Phases, deliverables and gates

Simulation counts are **estimates** derived from the paper's own S̄ values [A §6]. Per-simulation cost is unknown until a pilot measures it. **Every ⚠ gate asks for your approval before running.**

| Phase | Work | Verification | Approx. load | Gate |
|---|---|---|---|---|
| **P0 Unblock** | U1–U5; set up `.venv`; install RTAMT and PSY-TaLiRo; clone FindBox | import smoke tests; RTAMT evaluates a toy DT-STL formula | downloads only | ⚠ downloads |
| **P1 Specs + language** (no simulator needed) | `specs.py`, `boxes.py`, `monitors.py`, FindBox adapter; compute boxes for φ and ¬φ, φ₁–φ₅, under D1/D2/D4-provisional | **tests:** Dist sign = RTAMT sign on 10⁴ random signals in the bounds; union membership ⇔ RTAMT sat; Dist matches brute force on small cases. **Fidelity check:** box counts vs Table 1 (7, 3, 85, 2, 7) | FindBox runtime unknown (ref. [5] calls it expensive) | ⚠ if FindBox pilot > 1 h |
| **P2 CC system + E1** | `cc.py` per U1; input parametrisation; finalise D4; Table 1 | pilot of 100 sims timed; sanity plots of y₅−y₄; compare satisfaction ratios and agreement with Table 1 | 10,000 sims; 5 RTAMT + 5 language evaluations each | ⚠ full run |
| **P3 BO + E2/E3** | `bo.py`, `falsify.py`; Tables 2–3 | EI unit test vs closed form; seeded determinism; pilot of 1 trial × 5 requirements × 4 methods | ~15k sims each for PROF/PBO, ~2–3k each for SMuRF/SBO, ~40k GP fits (paper-like). Worst case (all hit the 200 cap): ~0.4M sims per parallel method | ⚠ after pilot timing |
| **P4 E4** | modified PROF + sequential BO; Table 4 + box-volume ratios | S̄_min should equal PROF's S̄ from P3 (same seeds), mirroring the paper's own consistency | **Heaviest:** φ₃'s 85 boxes × ≤ 200 rounds × 20 trials ≈ up to 340k sims + GP fits | ⚠ mandatory |
| **P5 Control (L3)** | `uav.py`, tracker, `control.py`; Table 5; optional E6 | tracker step-response test; projection/membership tests; pilot of 10 runs per formula | 16,000 runs. φ₈ LCW alone ≈ 1000 × 1965 ≈ 2M tracking sims (paper-like) | ⚠ full run |
| **P6 Report** | comparison tables (paper vs ours, CI, ratios, geometric means), Figs 1–4, `generate_artifacts.sh`, Docker, README with hardware and time | regenerate every table from `results/raw` alone | light | — |

**Order.** P0 → P1 can start right after your approval, even before U1 is resolved. P2–P4 need U1. P5 is independent of U1.

---

## 5. Reporting and reproducibility rules

These are partly lessons from the reference [R §6].

1. One ground truth: the **RTAMT** robustness sign decides falsification for **all** methods (D9).
2. One dispersion statistic: 95 % t-CI, named in every caption (D18).
3. Identical timing instrumentation and BO settings for proposed and baseline methods (D6, D11).
4. Every metric comes from the same trial set; per-trial raw records are kept (JSONL, not pickle).
5. Stop reason logged for every run: falsified, validation-failed, or cap.
6. Each results table has three column groups: **paper** (from `paper_reported_values.py`), **ours**, and **extra (not in paper)**.
7. All decisions D1–D18 and the environment (versions, CPU, RAM) are recorded in `results/` metadata and in `PROGRESS.md`.

---

## 6. Main risks

| Risk | Effect | Mitigation |
|---|---|---|
| No faithful CC model (U1) | Tables 1–4 only reach L3 | ask the authors; label clearly; focus on ratio-level claims |
| FindBox settings unknown | box counts differ from Table 1, which changes j and every downstream result | report the box counts we get; run a sensitivity check on FindBox sample size; ask the authors |
| Discretisation ambiguity (D1/D2) | language and formulas differ subtly | dual-grid pilot; report both |
| GP fitting dominates runtime (85 boxes) | long P3/P4 | parallelise across boxes (12 threads); pilot before scaling |
| Python 3.14 incompatibilities | install failures | U2 (a): Python 3.11 venv |
| Tracker design drives Table 5 | P̄ not comparable | compare only trends (C7, C8); report the tracker in full |
