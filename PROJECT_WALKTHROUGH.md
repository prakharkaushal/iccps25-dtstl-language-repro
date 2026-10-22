# Project walkthrough: what we did, why, and what we found

This is the story of the project from start to finish, for teammates who were not part of the day-to-day work. It
explains each step in plain terms and gives the reasoning behind the main decisions.

**How it relates to the other documents.**
- [README.md](README.md) is the reference: where things are and how to run them.
- [REPRODUCIBILITY_REPORT.md](REPRODUCIBILITY_REPORT.md) holds the evidence.
- [DEVIATIONS.md](DEVIATIONS.md) lists every decision in detail.
- This file ties them together.

**Who did the work.** The work was done with Claude Code (an AI coding assistant), directed by the project owner.
[PROGRESS.md](PROGRESS.md) records each step and which user request it came from. Every experiment-scale run was
either approved or explicitly requested.

---

## 1. The project in one paragraph

We took the ICCPS 2025 paper *Falsification and Control of CPS using the Language Set of Discrete-Time Temporal Logic*
(Abou-Mrad, Khandait, Pedrielli, Abbas) and tried to reproduce its whole evaluation.
- **Built from the text.** The authors did not publish code for their methods, so we built everything from the
  paper's description: the logic, the algorithms, the two test systems, and all five tables of experiments.
- **Ran and checked.** We ran every experiment, compared each number with the paper, and checked our own work with
  an automated audit.
- **Outcome.** The implementation is complete and every result traces back to raw data. Most of the paper's
  headline numbers do **not** reproduce in our setting, and we can explain most of the reasons.

---

## 2. The paper in plain words

**Requirements as formulas.**
- Engineers write safety requirements for systems such as cars or drones in a temporal logic (DT-STL).
- An example from the paper is φ1: "for the whole 100 s, the gap between car 5 and car 4 stays at most 40 m".
- **Robustness** (ρ) is a number that says *how much* a signal satisfies the requirement (ρ > 0) or violates it
  (ρ < 0). The standard tool to compute it is RTAMT.

**The paper's idea.**
- Write down the **language** of a requirement: the set of all signals that satisfy it.
- For these formulas the language is a **union of boxes** (hyper-rectangles), one coordinate per time sample.
- Once you have the boxes, three things become possible:

| Use | What it means | Paper experiment |
|---|---|---|
| **Faster monitoring** | Measuring the distance from a signal to the boxes can replace computing ρ | Table 1 (E1) |
| **Falsification** (searching for an input that breaks the requirement) | Instead of one search on ρ, run one Bayesian-optimisation (BO) search per box of the *violating* language L(¬φ): **PROF** in parallel, **SMuRF** serially. Baselines: BO on ρ (**PBO-RTAMT**, **SBO-RTAMT**) | Tables 2, 3, 4 (E2–E4) |
| **Control** | To make a drone satisfy a requirement, sample a reference trajectory inside the language, let the drone track it, and project the actual trajectory back into the language until it lands inside. **LCW** uses the whole language; **LCP** uses one box per parallel process | Table 5 (E5), plus one sentence claiming BO is 3–7× worse (E6) |

**What the paper claims.**
- The language monitor is up to 100× faster.
- All methods find counterexamples in 20 of 20 trials.
- The language methods need far less monitoring time and about the same or fewer iterations.
- LCP beats LCW by 2–4×.

---

## 3. The plan: five phases

| Phase | Goal | Output |
|---|---|---|
| 1 | Study a **reference project** (another ICCPS paper's repository, SPGA '23) to learn how a good evaluation is organised, without changing it | [docs/REFERENCE_ANALYSIS.md](docs/REFERENCE_ANALYSIS.md) |
| 2 | Dissect the **target paper**: every experiment, metric and setting, and everything it does *not* say | [docs/TARGET_ANALYSIS.md](docs/TARGET_ANALYSIS.md), [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) |
| 3 | **Implement** and **run** the evaluation: pilots first, then full runs | `src/`, `experiments/`, `results/` |
| 4 | **Audit** everything: does each number come from real outputs, and are the methods sound? | [REPRODUCIBILITY_REPORT.md](REPRODUCIBILITY_REPORT.md), `results/tables/audit.md` |
| 5 | Final clean-up for submission | this file, README, final checks |

Ground rules, written in [CLAUDE.md](CLAUDE.md):
- never modify the reference project;
- never invent results or citations;
- record the source of every number;
- keep everything reproducible;
- ask before expensive runs or downloads;
- keep [PROGRESS.md](PROGRESS.md) up to date.

---

## 4. What we did, step by step

### 4.1 Phase 1: learning from the reference project

We read the SPGA repository (a genetic-algorithm safe-RL paper) without running or changing anything. We re-derived
its tables from the result files the authors had stored.

- **What we learned to copy:**
  - every result belongs to a fixed seed and a fixed configuration;
  - raw results are stored separately from the scripts that build tables;
  - means are reported with 95 % confidence intervals;
  - speedups are summarised by geometric means;
  - one command regenerates everything.
- **What we learned to avoid.** The reference's headline 55× speedup recomputes exactly from its stored data, but:
  - several other columns cannot be reproduced;
  - two of its safety metrics can never count a violation;
  - the speedup comparison mixes different stopping rules and timers.

  So in our project every method is measured with the same ground-truth monitor (RTAMT), the same optimiser
  settings and the same timing code.

### 4.2 Phase 2: what the paper leaves out

We transcribed every number in the paper's tables into code (`analysis/target_paper/paper_reported_values.py`).
Then we listed what an implementer would need but the paper does not give:
- the random seeds;
- the Bayesian-optimisation settings (kernel, acquisition optimiser);
- FindBox's settings (the tool the authors used to compute the boxes);
- the drone's physical parameters and its tracking controller;
- the hardware;
- how time intervals in seconds map to samples.

We also found inconsistencies in the paper. For example:
- "10 time steps" is too few for a requirement with a 100-second horizon;
- a box count is attributed to φ4 in the text but to φ3 in the table;
- one row of Table 4 duplicates Table 3;
- the drone's inertia equation has a typo.

Each became a numbered entry in [DEVIATIONS.md](DEVIATIONS.md): A for missing resources, B for paper inconsistencies,
and D1–D26 for our own decisions.

### 4.3 Phase 3: building it

**The language: exact instead of approximate (the biggest decision, A1).**
- The paper computed its boxes with **FindBox**, an approximation tool whose settings are not given.
- For these formulas the language can be computed **exactly**, so we wrote a compiler (`src/langfal/language.py`):
  1. rewrite the formula into negation normal form;
  2. unroll the time operators;
  3. expand into a union of boxes;
  4. remove redundant boxes.
- That removes one unknown and makes the language monitor equal to ρ by construction. Tests confirm this on
  10,000 signals.
- Later we also ran FindBox itself (§4.4).

**The car model: we wrote our own port (A2).**
- The falsification benchmark ("Chasing Cars", from the ARCH competition) exists only as a MATLAB/Simulink model,
  and we had no MATLAB at the time.
- We downloaded the official model file, read it as text, and re-implemented it in Python
  (`src/langfal/systems/chasing_cars.py`):
  - **What it is:** five cars, in which the lead car is driven by throttle and brake inputs, and four followers switch
    between keeping, chasing and braking modes.
  - **First version too slow:** the first version stepped through time on a grid, at 144–194 ms per simulation.
  - **Rewrite:** we rewrote it as an **exact event-driven simulator**. Each mode has a closed-form trajectory, so it
    computes exactly when the next mode switch happens. That gives 15–20 ms per simulation, about 10× faster and
    with no time-step error.
  - **Structural check:** a script compares 31 structural facts (constants, guards, wiring) against the original
    model file: `scripts/verify_cc_port.py`.
- When MATLAB later became available, we checked the port against Simulink directly (§4.4).

**The drone (control experiments).**
- We implemented the paper's quadrotor equations, with the inertia typo corrected, and our own tracking controller
  (a cascaded PD controller).
- The paper gives neither the parameters nor the controller, so these results can only be compared as **trends**.
- We also tried the authors' own tracker, found inside the FindBox repository. It took 0.7–2.3 s per call
  (millions of calls are needed) and drifted away from its reference, so we did not use it (D26).

**The algorithms.**
- All of them sit on one shared Gaussian-process BO engine (`src/langfal/bo.py`):
  - PROF and SMuRF, the paper's methods;
  - the RTAMT baselines PBO-RTAMT and SBO-RTAMT;
  - the two Table 4 variants;
  - LangControl LCW and LCP;
  - a BO-on-robustness controller for the E6 claim.
- Shared settings make the comparison fair.
- One rule matters a lot: **a falsifier found through the language is accepted only if RTAMT confirms ρ < 0**. The
  paper does this too (p.6).

**The experiment machinery.**
- **Runners and configs:** each experiment is one runner script plus one YAML config.
- **Run directories:** every run writes to `results/raw/<experiment>/<run-id>/`:
  - `records.jsonl`, with one line per (requirement, trial, method);
  - `meta.json`, with the config, command line, library versions and a hash of the source code.
- **Resumable:** runs can be resumed if interrupted.
- **Paired seeds:** in each trial, every method starts from the same five starting points, so comparisons are paired.

**Tests.**
- 59 unit and property tests, including:
  - our robustness equals RTAMT;
  - the exact language is correct;
  - the car simulator converges to an independent fixed-step solver;
  - the expected-improvement formula matches a Monte Carlo estimate;
  - LangControl's loop bounds.

**Pilots, then full runs.** Small pilot runs checked the pipeline and estimated costs first. Then the full runs:

| Experiment | Size | Time (10 parallel workers, laptop) |
|---|---|---|
| E1 / Table 1 | 10,000 simulations | ~1.5 min |
| E2–E3 / Tables 2–3 | 20 trials × 5 requirements × 4 methods = 400 runs | 22 min |
| E4 / Table 4 | 200 runs | 92 min |
| E5 / Table 5 | 8 formulas × 2 variants × 1,000 replications | 97 min |
| E6 (paper text only) | 8 formulas × 50 replications | 29 min |

### 4.4 Phase 3 extras: FindBox, MATLAB and figures

**FindBox (the paper's own language tool).**
- **Getting it:** at the owner's request we downloaded it. It has **no license**, so it is used locally only and is
  not in this repository.
- **Making it run:** its main file starts a 50-dimensional computation as soon as it is imported, and it imports a
  tool we don't have. So we wrote an adapter (`src/langfal/findbox_adapter.py`) that loads only FindBox's functions,
  unchanged, and gives it our robustness function as its "oracle".
- **Settings we tried:** we ran it with two settings, because the paper gives none:
  - **"default"**, as shipped: integer sample points;
  - **"best-effort"**: continuous samples in a range close to what the cars actually reach.
- **Coverage:** 9 of the 10 languages were built. The tenth (best-effort φ1) was stopped after 5.5 h. FindBox's
  box-reconstruction step slows down sharply with continuous coordinates: we measured 26 s, 72 s and 542 s for
  50, 100 and 200 points, which projects to 16–20 h or more for the full run. The evidence is in
  `results/raw/findbox/main/INCOMPLETE.md`.
- **Re-runs:** we then repeated E2/E3 with the FindBox languages.

**MATLAB / Simulink check of the car model.**
- MATLAB R2026b with Simulink became available. Stateflow didn't show up as installed, but the official model,
  which contains a Stateflow chart, still loaded and ran from the command line.
- We compared our Python port with Simulink on 200 random inputs under three Simulink settings, and re-simulated
  all 338 counterexamples from Tables 2–3:
  - **Accurate settings** (tight tolerance): Simulink and our port agree to **0.00000067 m**, and all 338
    counterexamples also break the Simulink model.
  - **The benchmark's usual settings:** Simulink itself is off by up to 1.5 m, because of its integration
    tolerance and the way the benchmark feeds the inputs. 322 of 338 counterexamples still carry over; the other 16
    violate the requirement only marginally (|ρ| ≤ 0.057).
- **Conclusion:** our car model is right, and it is not a reason for any difference from the paper.

**Figures 1–4.** These are illustrations of languages and of one LangControl run, drawn with our own data, in
`results/figures/`.

### 4.5 Phase 4: the audit

We audited our own work as if we were reviewers. The script `analysis/audit.py` writes `results/tables/audit.md`.
1. **Paper match:** we mapped every experiment to the exact page or table of the paper and re-checked all
   transcribed paper numbers against the PDF.
2. **Numbers:** every number quoted in our documents was recomputed from the raw data with independent code.
3. **Counterexamples:** all 931 stored counterexamples were re-simulated. Each one still breaks its requirement,
   with exactly the stored ρ.
4. **Re-runs:** we re-ran part of every experiment and compared field by field. Everything was identical,
   including runs made with an older code version.
5. **Configs:** each run's stored config was compared with the current config files.
6. **Reference project:** we confirmed it is unmodified (git shows no changes).

**What the audit caught:**
- one number in the README that matched no run (fixed);
- one wrong statement about the paper in DEVIATIONS (fixed);
- one claimed agreement with the paper that does not survive counting failed trials (reworded);
- a statistic whose fine print was missing (added).

It also produced new findings, for example that LCP's advantage is in parallel time, not total computation.

### 4.6 Phase 5: final clean-up

- **Documentation:**
  - applied every correction from the audit;
  - rewrote the README for teammates;
  - moved background documents to `docs/`;
  - added `scripts/rebuild_results.sh`, which rebuilds every table from the raw data in about 2 minutes.
- **Code:** removed unused code and stale comments, without changing any algorithm.
- **Final check, after the clean-up:**
  - all 59 tests pass;
  - a fresh re-run matches the stored results exactly;
  - the full rebuild changes no number;
  - the audit passes **71/71**.
- **Publishing:** pushed to a private GitHub repository, without the third-party code.

---

## 5. The results

| Paper claim | Paper | Ours | Verdict |
|---|---|---|---|
| Language monitor up to 100× faster per call | 3.9–103× | 1.1–2.0× | Not reproduced (timing depends on implementation) |
| All four falsifiers succeed in 20/20 trials | 100/100 | PROF 77, PBO-RTAMT 97, SMuRF 79, SBO-RTAMT 85 | Not reproduced |
| PROF needs about as many iterations as parallel BO on ρ | ratio 0.96 | 0.47 (0.34 counting failures) | Not reproduced: PROF needs about 2× more |
| SMuRF needs fewer iterations than serial BO on ρ | 1.29 | 1.23 on successes, 1.03 counting failures | Not clearly reproduced |
| Language methods use far less monitoring time | 24× and 7.8× | 2.7× and 2.3× | Right direction, much smaller |
| Some boxes are much harder than others (Table 4) | S̄_max 37–200 | 200 for every requirement | Reproduced, and stronger |
| LCP beats LCW by 2–4× | 1.3–4.0× | 1.0–70× fewer rounds | Right direction; LCP uses more total compute on 5 of 8 |
| BO on ρ needs 3–7× the iterations of LCW | 3–7× | 0.52× | Not supported (BO needed fewer) |

**Why the numbers differ.** This is our explanation, backed by data where possible.
1. **Unreachable boxes.**
   - The exact language L(¬φ) contains boxes the cars can never enter. For φ1, random simulations enter only 2 of
     its 11 boxes, and every PROF success came from one box.
   - A PROF search assigned to an unreachable box can never succeed, while BO on ρ is never "stuck" on one box.
   - This explains PROF's lower success rate and the Table 4 results (`results/tables/box_reachability_main.md`).
2. **FindBox doesn't fix it.**
   - With FindBox's default settings, the language methods fail almost completely on 3 of 5 requirements:
     - one φ4 language has no boxes at all;
     - for φ1, one box contains every possible signal, so RTAMT had to reject about 4,000 false claims;
     - for φ2 and φ5, the boxes are never reached.
   - With the best-effort settings, the methods fall behind exactly where FindBox's boxes miss reachable violations.
     For φ3 they cover only 17 % of them.
3. **Unstated settings.** The paper gives no seeds, BO settings, FindBox settings, drone controller or hardware.
4. **Timing.** Our RTAMT calls are much cheaper than the paper's, so the language monitor has less to gain.
5. **Not the car model.** The Simulink check rules it out.

One discrepancy remains unexplained: the paper's E1 "satisfaction ratios" for φ1, φ2 and φ5 (for example, 7.08 %
vs our 0.70 % for φ1). No time grid we tried reproduces them.

---

## 6. Problems we hit and how we solved them

These are useful if anyone asks "what went wrong along the way?".

| Problem | Fix |
|---|---|
| RTAMT does not import on Python 3.14 (it uses a removed `typing.io` module) | A small compatibility shim (`monitors.ensure_typing_io`) |
| The first car simulator was too slow (≈ 170 ms per run) | Rewrote it as an exact event-driven simulator (15–20 ms) |
| Two simulator bugs: an absolute time used where a relative one was needed, and a mode switch missed when already due | Fixed; tests compare against an independent solver |
| Sequential BO in Table 4 slowed down without limit because it reused data across boxes | Fresh BO per box (D13) |
| Monitor timings drifted while the computer warmed up | Time all monitors interleaved on the same signals |
| The first E6 run used a weaker success test for BO than for LangControl | Re-ran with an identical test; the old run is kept, labelled superseded |
| One baseline was wrongly marked "not applicable" when FindBox returned no boxes | Fixed and re-ran the 20 affected records; noted in the run's metadata |
| A table generator shifted columns when a value was missing (pilot table only) | Fixed and regenerated |
| FindBox runs a huge computation on import and needs a tool we don't have | Adapter that loads only its functions |
| FindBox's own final check crashes on Python ≥ 3.12 | Used FindBox's continuous sampler for that check |
| FindBox best-effort φ1 would take 16–20 h or more | Measured the scaling, stopped it, documented it |
| Simulink at its default settings disagreed slightly with our port | Showed with three Simulink settings that the gap is Simulink's own numerical error |
| The laptop ran on battery during the audit (CPU at 1.3 GHz) | Results are deterministic; timings from that period are not used |

---

## 7. Decisions that are ours, not the paper's

The full list is in [DEVIATIONS.md](DEVIATIONS.md). These matter most:
- **Exact language** for the main results; FindBox reported separately (A1, A1b).
- **11 samples** at t = 0, 10, …, 100 s. Time bounds [a, b] seconds map to samples [⌈a/10⌉, ⌊b/10⌋] (D1, D2).
- **Our BO settings,** identical for every method (D6).
- **Iteration counting** starts after the 5 shared starting points (D7, D8).
- **Monitoring time of parallel methods** is measured on the critical path, i.e. the slowest process per round (D11).
  Summing over all processes gives 3.4× instead of 2.7×; the conclusion is the same.
- **Drone parameters, tracker and LangControl limits:** M = 500 restarts, K = 10 projections, at most 64 LCP
  processes (D14–D21).

---

## 8. What is not done, and the limitations

**Not done or partial:**
- **Best-effort φ1 FindBox language:** not computed (16–20 h or more).
- **E6:** run at reduced scale (50 replications per formula); the paper gives no scale.
- **Table 4's volume ratios** for never-falsified boxes: not computable, because exact boxes are unbounded.
- **Figures 1–4:** illustrations, not reproductions.

**Limitations:**
- **No exact paper numbers.** Too many settings are unstated for any paper number to be matched exactly.
- **Timing claims are machine-specific.**
- **Control experiments:** only trends are comparable, because the controller and parameters are ours.
- **Self-audit.** The audit was done by the same assistant that wrote the code. A human review is still worthwhile.

---

## 9. Explaining the project (a 2-minute version and likely questions)

**The 2-minute version.**
> The paper says that writing a temporal-logic requirement as a union of boxes makes monitoring 100× faster and lets
> you search for counterexamples box by box, as well as or better than searching on robustness. We rebuilt
> everything from the paper, ran all its experiments, and audited our own results. Monitoring with boxes is only
> about 2× faster in our implementation. Box-by-box search finds fewer counterexamples than plain BO on robustness,
> mainly because many boxes describe violations the system can never reach. Using the paper's own box tool, FindBox,
> doesn't fix this. Our car model is verified against the official Simulink model, so the differences are not caused
> by the simulator. For control, the one-box-per-process variant does need fewer rounds, as the paper says.

**Likely questions.**
- *Why didn't you use FindBox for everything?*
  - Its settings are not in the paper, and an exact language removes that uncertainty.
  - We did run FindBox too; it does not change the conclusions.
- *How do we know the results aren't bugs?*
  - 59 tests check the core pieces.
  - Every number recomputes from raw data, and every counterexample is re-checked with RTAMT.
  - Re-runs reproduce the stored results exactly.
  - The car model matches Simulink.
- *Could the paper still be right?*
  - On its own setup, possibly: different seeds, settings, FindBox languages and hardware.
  - Our results show that its claims depend on those unstated choices. In particular, box-by-box search is only as
    good as how well the boxes match what the system can actually reach.
- *Why is the reference project in the analysis?*
  - The assignment was to follow a reference project's evaluation methodology.
  - It is not part of the method; it shaped how we organised seeds, records, statistics and the audit.
- *How long does it take to reproduce?*
  - Tables from stored data: about 2 minutes (`bash scripts/rebuild_results.sh`).
  - All experiments from scratch: about 4–5 hours on a laptop, plus FindBox if wanted.

---

## 10. Where to find things

| You want… | Look at |
|---|---|
| The results tables | `results/tables/` (index in [results/README.md](results/README.md)) |
| The evidence behind every claim | [REPRODUCIBILITY_REPORT.md](REPRODUCIBILITY_REPORT.md), `results/tables/audit.md` |
| Why a setting was chosen | [DEVIATIONS.md](DEVIATIONS.md) |
| What happened when | [PROGRESS.md](PROGRESS.md) |
| How to run anything | [README.md](README.md) §4 |
| The code | `src/langfal/` (map in README §2 and §5) |
| The paper's own numbers | `analysis/target_paper/paper_reported_values.py` |
