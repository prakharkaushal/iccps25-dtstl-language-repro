# Reproducing "Falsification and Control of CPS using the Language Set of DT-STL" (ICCPS '25)

This project re-implements and re-runs the evaluation of Abou-Mrad, Khandait, Pedrielli and Abbas, *Falsification and
Control of CPS using the Language Set of Discrete-Time Temporal Logic*, ICCPS 2025 ([Paper.pdf](Paper.pdf)). It covers
every experiment in the paper (Tables 1–5, plus one claim the paper states without data) and documents where and why
our results differ. The code is a Python package (`langfal`).

**Start here.**
1. [What the paper claims and what we found](#1-results-at-a-glance): this README, about 5 minutes.
2. [PROJECT_WALKTHROUGH.md](PROJECT_WALKTHROUGH.md): the story of the project in plain words. It covers what we did
   in each phase and why, the problems we hit, a 2-minute summary and likely questions.
3. [REPRODUCIBILITY_REPORT.md](REPRODUCIBILITY_REPORT.md): the final audit, with a requirement checklist, the
   evidence for every result, the discrepancies and the limitations.
4. [DEVIATIONS.md](DEVIATIONS.md): every place where we had to decide something the paper does not state.
5. [PROGRESS.md](PROGRESS.md): a chronological log of what was done, when, and on whose request.

**Labels used throughout.** `[paper]` = reported in Paper.pdf. `[ours]` = measured by our runs. `[derived]` =
arithmetic on either. **No number of ours is presented as a reproduction of an exact paper value.**

---

## 1. Results at a glance

The paper's idea: compute the **language** of a temporal-logic requirement, meaning the set of signals that satisfy
it, as a union of boxes. Then use the boxes to
- monitor signals faster (E1);
- search for counterexamples ("falsification") with one optimiser per box (E2–E4);
- steer a drone so that it satisfies a requirement (E5, E6).

| # | Paper claim | `[paper]` | `[ours]` | Verdict |
|---|---|---|---|---|
| E1 | The box "language monitor" is up to two orders of magnitude faster than RTAMT | 3.9–103× per call | 1.1–2.0× per call | **Not reproduced** (implementation-dependent timing) |
| E1 | The language monitor gives the correct sign of robustness | 42.6–100 % same value | 100 % same value | Holds. Our language is *exact*, so the monitor equals robustness |
| E2/E3 | All four falsifiers find a counterexample in 20/20 trials | 100/100 per method | PROF 77, PBO-RTAMT 97, SMuRF 79, SBO-RTAMT 85 (of 100) | **Not reproduced** |
| E2 | PROF needs about as many iterations as parallel BO on robustness | ratio 0.96 | 0.47 (PROF needs about 2× more) | **Not reproduced** |
| E3 | SMuRF needs fewer iterations than serial BO on robustness | ratio 1.29 | 1.23 on successes only, **1.03** when failures count at the cap; only φ4 significant | **Not clearly reproduced** |
| E2/E3 | Language methods spend far less time monitoring | 24.1× and 7.8× | 2.7× and 2.3× | Direction reproduced, size not |
| E4 | Some boxes are much harder to falsify than others | S̄_max 37–200 | S̄_max = 200 for every φ | Reproduced qualitatively, and more extreme (many boxes are unreachable) |
| E5 | Running one box per process (LCP) beats the whole language (LCW), "2× to 4×" | 1.3–4.0× | 1.0–70× fewer rounds, but LCP uses more total tracking calls on 5 of 8 objectives | Direction reproduced; size differs |
| E6 | BO on robustness needs 3–7× the iterations of LCW | 3–7× (text, no data) | 0.52× (BO needs *fewer*) | **Not supported** |

**Why the results differ.** This is our analysis.
- **Different language.** The paper approximates the language with the tool FindBox. We compute it **exactly**.
  The exact language contains many boxes the car system can never reach: for φ1, only 2 of 11 boxes are entered by
  10,000 random signals. A falsifier process assigned to such a box cannot succeed.
- **FindBox languages do not close the gap.** We also ran E2/E3 with FindBox's languages. With FindBox's default
  settings, the language methods fail on 3 of the 5 requirements (§3, E2/E3-FB).
- **Unstated settings.** The paper gives no seeds, BO settings, FindBox settings, drone controller or hardware.
- **The car model is not the cause.** Our Python version of the Chasing Cars benchmark matches the official Simulink
  model to 6.7·10⁻⁷ m when Simulink integrates accurately, and every counterexample we found also breaks the
  Simulink model (§3, CC).

**Reproducibility of our own results.** An automated audit (`analysis/audit.py` →
[results/tables/audit.md](results/tables/audit.md)):
- recomputes every number quoted here from the stored raw outputs;
- re-simulates all 867 stored counterexamples;
- re-runs part of every experiment with the current code. Every re-run was identical to the stored result.

---

## 2. Repository map

```
Paper.pdf                    the paper being reproduced
README.md                    this file
REPRODUCIBILITY_REPORT.md    final audit: checklist, evidence, discrepancies, limitations, commands
DEVIATIONS.md                every decision the paper leaves open (A: missing resources, B: paper inconsistencies, D1–D26: our choices)
PROGRESS.md                  chronological work log (required by CLAUDE.md)
docs/                        background: REFERENCE_ANALYSIS.md (the reference project we followed for methodology),
                             TARGET_ANALYSIS.md (the paper, dissected), IMPLEMENTATION_PLAN.md (the approved plan)

src/langfal/                 the library (pip-installable, see pyproject.toml)
  stl.py                     discrete-time STL formulas, robustness, RTAMT syntax, negation normal form
  specs.py                   the paper's formulas (Eqs. 8–12 falsification, 14–21 control) and their discretisation
  language.py                exact language compiler: formula -> union of boxes; signed distance (paper Eq. 1)
  monitors.py                RTAMT wrapper (the reference monitor) and the box "language monitor"
  bo.py                      Gaussian-process Bayesian optimisation (EI and the paper's MinBO EI)
  falsification.py           PROF, SMuRF (the paper's methods), PBO-RTAMT, SBO-RTAMT (baselines), Table 4 variants
  control.py                 LangControl LCW / LCP (paper Alg. 3) and the robustness-BO control baseline
  systems/chasing_cars.py    exact event-driven port of the ARCH-COMP Chasing Cars Simulink model
  systems/uav.py             quadrotor model of paper §4.2 with our tracking controller
  findbox_adapter.py         runs the external FindBox tool with our robustness oracle
  stats.py, runlog.py        confidence intervals and tests; run directories with provenance (meta.json)
experiments/                 one runner per experiment (all take --config, --run-id, --workers; all resumable)
configs/                     every setting of every run (YAML), commented with [paper] or our decision ID
analysis/                    turns raw records into tables and figures; audit.py = automated audit
scripts/                     run_all.sh (everything), rebuild_results.sh (tables only), model download and checks, MATLAB
tests/                       59 unit and property tests
results/raw/                 raw per-trial records (records.jsonl) + provenance (meta.json) for each run
results/tables/              every table (.md) and plot (.png) cited in the docs — see results/README.md
results/figures/             illustrations for the paper's Figs. 1–4
results/matlab/              inputs and outputs of the Simulink comparison
results/logs/                console logs of the long runs
external/                    (git-ignored) downloaded third-party code: the official CC model, FindBox
reference_project/           the reference project (read-only, never modified)
```

---

## 3. The experiments

Each entry gives the paper location, what is compared, how we ran it, and where the results are. Commands are in §4.

**E1 — monitoring accuracy (paper Table 1).**
- **What:** 10,000 random inputs to the Chasing Cars model. For each requirement φ1–φ5, the box-language monitor is
  compared with RTAMT robustness: same value, same sign, or disagreement, plus time per call.
- **Run:** `e1_monitoring/main` → [table1_main.md](results/tables/table1_main.md).
- **Result:**
  - The values agree in 100 % of cases, as expected for an exact language.
  - RTAMT is 1.1–2.0× slower per call (`[paper]` 3.9–103×).
  - Violation rates are 0.70/0.84/4.23/0.85/0.52 % (`[paper]` 7.08/1.82/3.84/0.87/7.08). They match for φ3 and φ4;
    the paper's φ1, φ2 and φ5 values are not explained by any time grid we tried
    ([grid_sensitivity.md](results/tables/grid_sensitivity.md)).

**E2/E3 — falsification (paper Tables 2 and 3).**
- **What:** PROF runs one optimiser per box of L(¬φ) in parallel; it is compared with PBO-RTAMT, the same number of
  optimisers on RTAMT robustness. SMuRF runs one optimiser that scores every box; it is compared with SBO-RTAMT,
  one optimiser on robustness. 20 trials, 5 shared starting points, at most 200 iterations.
- **Run:** `falsification/main` →
  - [table2_3_main.md](results/tables/table2_3_main.md),
  - [falsification_main.png](results/tables/falsification_main.png),
  - [box_reachability_main.md](results/tables/box_reachability_main.md) for why PROF fails: unreachable boxes.
- **Result:** see §1.
  - The paper's S̄ averages successful trials only. Ours does the same, and the audit also reports versions that
    count failures (report §5.2).
  - Paired Wilcoxon tests use iteration counts with failed trials at 200.

**E2/E3-FB — falsification with FindBox languages (extra).**
- **What:** the paper built its languages with FindBox (its ref. [5]). We ran FindBox with two settings (D25):
  - "default", as shipped: integer samples of [0, 100]¹¹;
  - "best-effort": continuous samples of [0, 70]¹¹. These bounds were taken from simulations, a mild information
    leak in favour of the language methods.
- **Runs:**
  - `findbox/main` (the languages);
  - `falsification/findbox_default` → [table2_3_findbox_default.md](results/tables/table2_3_findbox_default.md);
  - `falsification/findbox_besteffort` → [table2_3_findbox_besteffort.md](results/tables/table2_3_findbox_besteffort.md);
  - language quality → [findbox_quality_main.md](results/tables/findbox_quality_main.md).
- **Result (default):** PROF and SMuRF fail on φ1, φ2 and φ5, at 0–1 of 20 trials.
  - φ4 gets no box at all, because integer samples cannot hit 32 < x < 33.
  - For φ1, one FindBox box contains every reachable signal. RTAMT rejected about 4,000 false claims per method.
- **Result (best-effort):** PROF 14/15/20/13 and SMuRF 6/9/20/8 on φ2/φ3/φ4/φ5; the baselines get 11–20. No
  language claim was rejected by RTAMT.
  - Where the language methods fall behind, FindBox's boxes miss reachable violations. For φ3, the 108 boxes cover
    only 17 % of the violations that random simulations reach.
- **Not computed: the best-effort φ1 language.** We stopped it after 5.5 h.
  - FindBox's box reconstruction slows down sharply with distinct floating-point corner coordinates: we measured
    26 s, 72 s and 542 s for 50, 100 and 200 points.
  - That extrapolates to 16–20 h or more for the full 1,000 points.
  - Details: `results/raw/findbox/main/INCOMPLETE.md`. The default-setting φ1 language exists.

**E4 — box difficulty (paper Table 4).**
- **What:** modified PROF continues until every box is falsified, giving the iterations to the first and last box
  (S̄_min, S̄_max). Sequential BO searches the boxes one at a time in random order.
- **Run:** `table4/main` → [table4_main.md](results/tables/table4_main.md).
- **Result:**
  - S̄_min equals PROF's S in 77/77 trials, matching the paper's own consistency.
  - S̄_max = 200 everywhere: on average 5.8–22.5 boxes per requirement are never falsified.
  - Sequential BO needs 594–1,113 iterations (`[paper]` 19.6–46.4).

**E5 — control with the language (paper Table 5).**
- **What:** a drone must follow a reference signal that satisfies a formula. LangControl repeatedly projects the
  tracked trajectory back into the language. LCW uses the whole language; LCP uses one box per process. Eight
  formulas, 1000 replications each.
- **Run:** `control/main` → [table5_main.md](results/tables/table5_main.md).
- **Result:**
  - LCP needs fewer rounds on 8/8 formulas.
  - LCW fails 786/1000 replications on φ5 within its limits.
  - The tracker, drone parameters and LangControl limits are ours (the paper gives none), so only trends are
    comparable.

**E6 — robustness-BO control baseline (paper §4.3, text only).**
- **What:** the paper says BO on robustness "consistently requires 3-7x the number of iterations" of LCW. We tested
  this with the same success test and a budget of 205 tracking calls, 50 replications per formula.
- **Run:** `control_bo/main` → [e6_control_bo_main.md](results/tables/e6_control_bo_main.md).
- **Result:** BO needed fewer iterations on 6/8 formulas (geometric mean 0.52×).
- **Provenance:** a first run with a more lenient success test is kept in `control_bo/main_superseded_v1` with an
  explanation.

**CC — is our car model right? (supports E1–E4).**
- **What:** the paper used the official ARCH-COMP Simulink model. We ported it to Python (exact event-driven
  simulation), then compared it with Simulink in MATLAB R2026b. The comparison used 200 random inputs plus all 338
  counterexamples from Tables 2–3, under three Simulink settings.
- **Result:** [cc_port_vs_simulink.md](results/tables/cc_port_vs_simulink.md).
  - With accurate integration, Simulink matches the port to ≤ 6.7·10⁻⁷ m, and all 338 counterexamples carry over.
  - With the model's default tolerance, Simulink itself is off by up to 1.5 m, so 16 marginal counterexamples
    (|ρ| ≤ 0.057) do not carry over.

**Figures 1–4.** Illustrations drawn from our exact languages and tracker, in [results/figures/](results/figures/).
They are not reproductions: the paper's projections and data are unknown.

---

## 4. How to run

### Setup (Python ≥ 3.10; we used 3.14.7 on Windows 11)

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt     # Linux/macOS: .venv/bin/python; exact versions: requirements-lock.txt
export PYTHONUTF8=1                                              # Windows consoles: formulas contain φ, □, ◇
PY=.venv/Scripts/python.exe
$PY -m pytest -q                                                 # 59 tests, ~20 s (FindBox tests skip if FindBox is absent)
```

### Look at the results (nothing to run)

All tables are Markdown files in `results/tables/`; [results/README.md](results/README.md) lists what each contains.

### Rebuild every table and figure from the stored raw records (minutes)

```bash
bash scripts/rebuild_results.sh
```

### Re-run the experiments (hours)

Every runner is resumable: re-running a command skips finished trials. Times are for 10 workers on an i5-1335U
laptop.

```bash
$PY experiments/run_e1_monitoring.py --config configs/e1_monitoring.yaml --run-id main --workers 10   # E1,  ~2 min
$PY experiments/run_falsification.py --config configs/falsification.yaml --run-id main --workers 10   # E2/E3, ~22 min
$PY experiments/run_falsification.py --config configs/table4.yaml        --run-id main --workers 10   # E4,  ~92 min
$PY experiments/run_control.py       --config configs/control.yaml       --run-id main --workers 10   # E5,  ~97 min
$PY experiments/run_control_bo.py    --config configs/control_bo.yaml    --run-id main --workers 10   # E6,  ~29 min
bash scripts/run_all.sh          # all of the above + analysis; FindBox and MATLAB stages run only if available
```

Smaller pilots: add `--trials 1` (falsification) or `--reps 20 --M 50` (control) and use another `--run-id`.

### Optional: FindBox languages (unlicensed third-party code)

FindBox has **no license**. It is cloned locally at a pinned commit, used locally, and **must not be redistributed**.

```bash
bash scripts/fetch_findbox.sh                                                                            # -> external/FindBox
$PY experiments/run_findbox.py --config configs/findbox.yaml --run-id main --workers 10   # ~2.6 h for 9 of 10 languages; best-effort phi1 needs 16-20 h+
$PY experiments/run_falsification.py --config configs/falsification_findbox_default.yaml    --run-id findbox_default    --workers 10
$PY experiments/run_falsification.py --config configs/falsification_findbox_besteffort.yaml --run-id findbox_besteffort --workers 10
```

### Optional: check the car model against Simulink (MATLAB + Simulink)

```bash
bash scripts/fetch_cc_model.sh && $PY scripts/verify_cc_port.py     # official model text -> 31 structural checks
$PY scripts/cc_matlab_compare.py export && $PY scripts/cc_matlab_compare.py export-falsifiers --run main
matlab -batch "run('scripts/matlab/run_cc_reference.m')"            # setting (a); the other five runs: scripts/run_all.sh
$PY scripts/cc_matlab_compare.py compare                            # -> results/tables/cc_port_vs_simulink.md
```

### Audit

```bash
$PY analysis/audit.py            # -> results/tables/audit.md (recomputes every quoted number, compares re-runs)
```

The re-runs it compares against are produced by the commands in REPRODUCIBILITY_REPORT.md §11.

---

## 5. How the code fits together

```
specs.py ─ formula φ ──► language.py ─ boxes of L(φ) / L(¬φ) ──► monitors.py ─ distance to boxes (language monitor)
   │                                                              ▲
   └──► stl.py ─ robustness ρ (= RTAMT, tested) ──────────────────┘ ground truth for every method

systems/chasing_cars.py ─ input u ∈ [0,1]²⁰ ─► signal x = y5 − y4 (11 samples)
falsification.py: GP-BO (bo.py) over u, scoring each simulation by box distance (PROF, SMuRF) or −ρ (baselines);
                  a language "hit" is accepted only if RTAMT confirms ρ < 0
control.py:       LangControl samples a reference in the language, tracks it with systems/uav.py, projects back

experiments/run_*.py ─ configs/*.yaml ─► results/raw/<experiment>/<run-id>/{records.jsonl, meta.json}
analysis/make_tables.py ─► results/tables/*.md          analysis/audit.py ─► results/tables/audit.md
```

**Conventions.**
- One record per (requirement, trial, method).
- Seeds are derived from `seed_base + trial`, so every method sees the same five starting points.
- `meta.json` stores the config, command line, environment and a hash of `src/`.
- Changing a config file never silently changes old results: they stay in their own run directory.

---

## 6. Key decisions (full list in DEVIATIONS.md)

| ID | Decision | Why |
|---|---|---|
| A1 | Exact language instead of FindBox for the main results; FindBox runs reported separately (A1b) | FindBox's settings are not in the paper; an exact language removes one source of error |
| A2 | Python port of the Chasing Cars Simulink model | No MATLAB at first; later verified against Simulink |
| D1/D2 | 11 samples at t = 0, 10, …, 100 s; time bounds [a, b] s ↦ [⌈a/10⌉, ⌊b/10⌋] samples | The paper's "10 time steps" contradicts φ2's 100-s horizon (B-item) |
| D6 | Our GP-BO settings, identical for proposed methods and baselines | Not stated in the paper |
| D8/D9 | S = iterations after the 5 initial samples; a language hit must be confirmed by RTAMT (as in the paper, p.6) | Unambiguous counting; no false counterexamples |
| D11 | Monitoring time of parallel methods measured on the critical path (slowest process per round) | What a truly parallel run would see; summing over processes changes PBO/PROF from 2.7× to 3.4× |
| D14–D21 | Drone parameters, tracker, LangControl sampling/projection, M = 500, K = 10, ≤ 64 LCP processes | Not stated in the paper |
| D22–D24 | E6 design: BO over the reference signal, same success test as LangControl, 205-call budget, 50 replications | The paper gives only one sentence |

---

## 7. Glossary

| Term | Meaning |
|---|---|
| DT-STL | Discrete-time Signal Temporal Logic: requirements such as "always within the next 30 s the gap is at least 10" |
| Robustness ρ | How strongly a signal satisfies (ρ > 0) or violates (ρ < 0) a formula; computed by RTAMT |
| Language L(φ) | The set of all signals that satisfy φ, here a union of axis-aligned boxes in ℝⁿ |
| Language monitor | Signed distance from a signal to the boxes, used instead of ρ |
| Falsification | Searching for an input that makes the system violate φ (a counterexample, "falsifier") |
| PROF / PBO-RTAMT | Parallel falsification: one optimiser per box of L(¬φ) / the same number of optimisers on −ρ |
| SMuRF / SBO-RTAMT | Serial falsification: one optimiser scoring all boxes (MinBO EI) / one optimiser on −ρ |
| FR, S̄, T̄_T, T̄_M | Falsified trials of 20; mean iterations to falsify; total monitoring time per trial; time per monitoring call |
| LangControl LCW / LCP | Control by projection onto the whole language / onto one box per parallel process; P̄ = mean iterations to success |
| CC | ARCH-COMP Chasing Cars benchmark: five cars, the signal is the gap between cars 5 and 4 |

---

## 8. Third-party code and data

- **No datasets**: all data is simulated.
- **RTAMT 0.3.5** (BSD) is installed from PyPI. Python ≥ 3.13 needs a small `typing.io` shim (DEVIATIONS A4).
- **The ARCH-COMP Chasing Cars model** is downloaded by `scripts/fetch_cc_model.sh` (pinned commit, sha256 checked).
  It was used to write the port and to verify it.
- **FindBox** (the paper's ref. [5]) has no license and is used locally at the project owner's request
  (DEVIATIONS A1b).
- **MATLAB + Simulink** are optional; R2026b was used.
- **Reference project.** The evaluation methodology follows the reference project (`reference_project/`, SPGA,
  ICCPS '23; analysed in [docs/REFERENCE_ANALYSIS.md](docs/REFERENCE_ANALYSIS.md)). Re-used ideas, re-implemented
  rather than copied:
  - a seeded method × variant × trial design;
  - raw records kept separate from table generation;
  - t-based 95 % confidence intervals and geometric-mean ratios;
  - one-command regeneration.

  Its evaluation flaws were avoided: one ground-truth monitor for all methods, identical settings for proposed and
  baseline methods, and unrounded aggregation.
