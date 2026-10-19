# PROGRESS

## Completed

### Phase 1 — reference analysis (2026-10-18) → [docs/REFERENCE_ANALYSIS.md](docs/REFERENCE_ANALYSIS.md)
- SPGA (ICCPS '23) repository analysed read-only; Tables 2–3 re-derived from stored pickles
  (`analysis/reference_inspection/`); Table 3 (55.28x) reproduced exactly; several Table 2 columns not reproducible.

### Phase 2 — target paper analysis (2026-10-18) → [docs/TARGET_ANALYSIS.md](docs/TARGET_ANALYSIS.md), [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- Paper values transcribed in `analysis/target_paper/paper_reported_values.py` (source of every [paper] number).

### Phase 3 — implementation (2026-10-18)
- **Environment**: `.venv` (Python 3.14.7, reuses system numpy 2.5.2 / scipy 1.18.1 / scikit-learn 1.9.1) +
  RTAMT 0.3.5, antlr4-python3-runtime 4.7, pytest 9.1.1 (`requirements.txt`, `requirements-lock.txt`).
  RTAMT needs a `typing.io` shim on Python ≥ 3.13 (DEVIATIONS A4).
- **Chasing Cars model**: no MATLAB at the time → ported the canonical ARCH-COMP model (cars.mdl, commit 8e11a799)
  after reading it as text; exact event-driven simulator, 15–20 ms/simulation; verified (31/31 checks,
  `scripts/verify_cc_port.py`) and validated (first-order convergence of an independent fixed-step solver).
  Later checked against Simulink (Phase 3b below).
- **Library** `src/langfal/`: DT-STL + robustness (= RTAMT on all paper formulas), exact box languages
  (replaces FindBox, DEVIATIONS A1), Eq. (1) distances, GP-BO (EI, MinBO EI), PROF, PBO-RTAMT, SMuRF,
  SBO-RTAMT, modified PROF, sequential BO, UAV model + tracker, LangControl LCW/LCP, stats, provenance.
- **Tests**: 52 passing (`pytest -q`).
- **Experiments run** (all records in `results/raw/`, tables in `results/tables/`):
  - E1 / Table 1 — FULL, 10,000 simulations (`e1_monitoring/main`). Language monitor = RTAMT value in 100 %
    of cases (exact language); violation rates 0.70/0.84/4.23/0.85/0.52 % vs paper 7.08/1.82/3.84/0.87/7.08 %;
    per-call RTAMT/language speedup 1.1–2.0x (paper 3.9–103x); RTAMT on 101-sample traces costs
    0.53–1.00 ms, comparable to the paper's 0.67–1.38 ms (corrected in Phase 4: an earlier version said 0.41–1.08).
    Source: `results/tables/table1_main.md`.
  - Grid sensitivity (extra) — `results/tables/grid_sensitivity.md` (N = 2000, seed 12345).
  - E2/E3 pilot (1 trial) — `falsification/pilot`, 266 s on 10 workers; 18/20 runs falsified.
  - **E2/E3 / Tables 2–3 — FULL** (approved by the user; 20 trials × 5 specs × 4 methods = 400 runs,
    `falsification/main`, 2026-10-18 16:04–16:26, 1336 s wall, 12,654 CPU-s). Every falsifier was re-validated
    by RTAMT (ρ < 0).
    Sources: `results/tables/table2_3_main.md`, `falsification_main.png`, `box_reachability_main.md`.
    - Falsified trials out of 100: PROF 77, PBO-RTAMT 97, SMuRF 79, SBO-RTAMT 85 (paper: 100 each).
    - T̄_T speedup, geometric mean: PBO/PROF 2.7× (paper 24.1×); SBO/SMuRF 2.3× (paper 7.8×).
    - S̄ ratio, geometric mean: SBO/SMuRF 1.23 (paper 1.29) over falsified trials only. Phase 4 audit: counting
      unfalsified trials at the 200-iteration cap gives 1.03, with per-φ ratios on both sides of 1, and only φ4 is
      significant (p = 0.017), so the paper's SMuRF iteration advantage is not clearly reproduced.
    - PBO/PROF S̄ ratio 0.47 (paper 0.96); 0.34 when unfalsified trials count at the cap. PROF needs more rounds
      (Wilcoxon p < 0.05 for φ1, φ4, φ5). This is explained by unreachable boxes of the exact language: for φ1,
      2 of 11 boxes are reachable and all 9 PROF falsifications used box index 3 (0-based; x(3) > 40, t = 30 s).
    - Wall-clock time per trial is dominated by GP fitting and simulation; the language methods are slower end to
      end in our implementation.
    - The same 9 trials were falsified by an initial sample for all four methods (paired design check).
  - E4 pilot (1 trial) — `table4/pilot`, 434 s; S_min = PROF's S in 5/5 cases; most exact boxes are
    unreachable by the CC system (10/11, 7/8, 21/27, 21/27, 5/7 never falsified).
  - E5 pilot (20 reps, M = 50) — `control/pilot`, 302 s; LCP needs fewer iterations than LCW wherever both
    succeed; φ5 LCW fails 20/20, φ6/φ8 have failures (our tracker; L3 only).
  - **E4 / Table 4 — FULL** (approved by the user; 200 runs, `table4/main`, 92 min).
    Source: `results/tables/table4_main.md`, `box_reachability_main.md`.
    - S_min equals PROF's S in 77/77 matched trials.
    - S̄_max = 200 everywhere: on average 10.5/11, 6.7/8, 22.5/27, 22.4/27, 5.75/7 boxes are never falsified
      (unreachable).
    - Sequential BO falsifies 8/17/20/20/14 of 20 trials with S̄ 594–1,113 (paper 19.6–46.4).
  - **E5 / Table 5 — FULL** (approved; 16 × 1000 replications, `control/main`, 97 min).
    Source: `results/tables/table5_main.md`.
    - LCP < LCW on all 8 objectives (as in the paper). LCW/LCP ratio 1.0–70 (paper 1.3–4.0).
    - LCW fails 786/1000 replications on φ5 and 3/1000 on φ8 within M = 500, K = 10.
    - Absolute P̄ differ from the paper (tracker/time base are ours: L3).
  - **E6 (robustness-BO control baseline)** — implemented after the user said to run the next job without asking
    (2026-10-18), at reduced scale (50 replications, ≤ 205 Track calls; D22–D24).
    - The first run (`control_bo/main_superseded_v1`) used plain ρ ≥ 0 as success. That test is more lenient than
      LangControl's domain-bounded language test, so the run is superseded and kept only for provenance
      (`SUPERSEDED.md` there).
    - **Corrected run complete** (`control_bo/main`, 2026-10-18 20:08–20:37, 400 replications).
      Source: `results/tables/e6_control_bo_main.md`.
      - BO uses RTAMT robustness of φ ∧ □(domain), so it has the same success test as LangControl.
      - Within 205 Track calls, BO needs fewer iterations than LCW on 6/8 objectives. BO/LCW geometric mean is
        0.52 over 8 formulas, 0.53 over the 7 with ≥ 5 successes each. The paper's claim is 3–7×, so it is not
        supported in our setting.
      - BO is worse on φ1 (1.21×) and on φ6's success rate (2 % vs 30.8 %).
- **Final check**: all 52 tests pass (2026-10-18, after the last code change).

### Phase 3b — FindBox, MATLAB, figures (2026-10-18, user requests "install and use findbox to do rest of the stuff",
"simulink is installed ... try from your end and then queue the remaining parts")
- **FindBox** (ref. [5], commit bf19736, no license: local use only, `scripts/fetch_findbox.sh`) runs through
  `src/langfal/findbox_adapter.py`, which executes FindBox's unchanged functions with our oracle (D25, A1b).
  - The authors' tracker `ss_tracker` was tried and is not used (D26).
  - **FindBox run `findbox/main`** (2 variants × 5 requirements, 10 workers, started 21:24). 8/10 languages are
    built; besteffort φ1 and φ3 are still running (> 2.5 h each at 23:50). Source: `results/raw/findbox/main/`.
    - default: φ1 3 boxes (one, x(0) ≤ 40, contains every reachable signal), φ2 1, φ3 54, φ4 **0** (integer
      sampling cannot hit 32 < x < 33), φ5 1.
    - besteffort: φ2 5, φ4 53 (FindBox's own check: 886/1023 points in the boxes are outside L(¬φ4)), φ5 5.
  - **E2/E3 with FindBox languages, default variant — FULL** (`falsification/findbox_default`, 400 runs).
    Source: `results/tables/table2_3_findbox_default.md`, `falsification_findbox_default.png`.
    - Falsified trials out of 20: PROF 0/0/20/n.a./0 and SMuRF 1/0/20/n.a./0 for φ1–φ5. For comparison,
      PBO-RTAMT 19/15/20/n.a./11 and SBO-RTAMT 20/15/20/19/11.
    - φ1: the box x(0) ≤ 40 makes every PROF/SMuRF step a language claim. RTAMT rejected 4020 PROF and 4040
      SMuRF claims (D9). Without the re-check, these would have been reported as falsifications.
    - φ2, φ5: the single box is never entered (0 claims).
    - SBO-RTAMT (language-independent) is identical to `falsification/main` in 100/100 trials.
  - **E2/E3 with FindBox languages, besteffort variant — φ2/φ4/φ5 complete** (`falsification/findbox_besteffort`,
    240 runs; first run with the `validation_rejections` counter).
    - Falsified trials out of 20: PROF 14/20/13 and SMuRF 6/20/8; PBO-RTAMT 19/20/17 and SBO-RTAMT 15/19/11.
    - 0 rejected claims.
    - SBO-RTAMT is identical to `main` in 60/60 trials.
- **MATLAB R2026b + Simulink 26.2**. `ver` lists no Stateflow product, yet the official model (with its Stateflow
  chart) loads and simulates via `matlab -batch` (`scripts/matlab/run_cc_reference.m`, now tested).
  - **Port vs Simulink, 200 random inputs** (`results/tables/cc_port_vs_simulink.md`):
    - **Verdicts:** 100 % agreement for φ1–φ5.
    - **Differences at the model's usual settings** (ARCH input convention, RelTol 1e-3): positions max 1.5 m
      (median ≤ 0.02 m), robustness max 1.04 (median ≤ 0.01).
    - **With exact-step inputs and RelTol = AbsTol = 1e-6 requested:** positions max 0.06 m, robustness max 0.05.
      The model's MinStep of 0.01 s caps Simulink's effective tolerance at input switches (400 warnings, worst
      1.3e-4; `results/logs/cc_simulink_step_tol1e-6.log`).
    - **With exact-step inputs, RelTol = AbsTol = 1e-10 and MinStep auto:** positions max 6.7e-7 m, robustness max
      1.1e-6, no warnings (`results/logs/cc_simulink_step_tol1e-10.log`).
    - **Lead car (no mode switches):** the port is exact (≤ 3.3e-10 m vs a 1e-12 reference). Simulink's own error
      at RelTol 1e-3 is ≤ 0.31 m. The ARCH input ramp accounts for ≤ 0.06 m.
    - **Conclusion:** the port reproduces the model (A2 resolved, A-CC1 confirmed). The differences come from
      Simulink's integration tolerance and the input convention.
  - **Falsifier transfer.** The 338 falsifiers of `falsification/main` (Tables 2–3) were re-simulated on
    Simulink.
    - Accurate settings (exact steps, tolerance 1e-10, MinStep auto): all 338 falsify it, with robustness within
      7.2e-7 of the port's.
    - Model's MinStep with tolerance 1e-6 requested: 337.
    - Usual settings: 322 (95.3 %).
    - φ1, φ3, φ4 at the usual settings: 100 % for every method.
    - φ2, φ5: 73–100 %. These falsifiers violate φ by a median of only 0.01–0.04. On random inputs at the same
      Simulink settings, the robustness difference to the port has a median of 0.003–0.01 and a maximum of 1.04.
    - No CC-based table needs re-running.
- **Figures 1–4**: illustrations with our exact languages and tracker (`analysis/plot_figures.py` →
  `results/figures/`); the paper's projections and data are unknown, so they are not reproductions.
- **Fixes**:
  - `make_tables.py`: the speedup rows of Tables 2–3 dropped requirements without a ratio, which shifted the
    remaining values one column left. Only the pilot table was affected; it has been regenerated.
  - Status now reflects per-(requirement, method) completeness. FindBox runs get an RTAMT re-check section.
  - `plot_falsification.py` handles not-applicable runs.
  - FindBox analysis no longer depends on absolute paths.
- **Tests**: 59 passing (`pytest -q`, 2026-10-18 23:47), including FindBox (6) and the rejection counter (1).

## Phase 4 — reproducibility audit (2026-10-19) → [REPRODUCIBILITY_REPORT.md](REPRODUCIBILITY_REPORT.md)
- `analysis/audit.py` → `results/tables/audit.md`: **64 PASS, 1 FAIL**.
  - Headline claims are recomputed independently from the raw records.
  - All 867 stored falsifiers are re-simulated.
  - E1 signals and metrics are recomputed.
  - Stored configs are compared with `configs/*.yaml`.
  - Tables are regenerated.
  - Re-runs are compared with the stored runs.
- **Re-runs with the current code** (run id `audit_rerun`) are identical to the stored runs:
  - E1: all metrics and signals.
  - E2/E3: 40/40.
  - E4: 4/4.
  - E5: 4/4 (4,000 replications).
  - E6: 10/10.
  - FindBox: 4/4.
  - Pilot vs main (older code): 20/20.
  - New option `run_falsification.py --trial-ids`.
- **Reference project unchanged:** git clean apart from the pre-existing untracked `reference_paper.pdf`; file times
  equal the clone time.
- **Tests:** 59 passed. `verify_cc_port.py`: 31/31.
- **Documentation errata found** (applied in Phase 5; REPRODUCIBILITY_REPORT.md §9):
  - F1: the 101-sample RTAMT cost is 0.53–1.00 ms, not 0.41–1.08.
  - F2: D9 is wrong; the paper does validate falsifiers with RTAMT (p.6).
  - F3: SMuRF's iteration advantage is 1.03 when failures count at the cap, not a robust reproduction of the
    paper's 1.29.
  - F5: the Wilcoxon footnote.
  - F8: LCP uses more total Track calls than LCW on 5 of 8 objectives.
- **Still running at the time:** FindBox best-effort φ1 (> 4 h). It was stopped in Phase 5 (see below).
- **The laptop was on battery during the audit.** If the queue stops, re-run the same commands; they resume.

## Phase 5 — final submission (2026-10-19)

User requests: "make all the necessary changes and refactor the project and readme for final submission so that my
teammates are also able to understand what has been done", then "dont be askking any permissions just complete what
was asked".

- **FindBox completed as far as feasible.**
  - Best-effort φ3 language finished: 108 boxes, 9,301 s.
  - **Best-effort φ1 stopped after 5.5 h.** FindBox's `recon` step slows down sharply with distinct floating-point
    corners. Measured 26/72/542 s for 50/100/200 points (`results/logs/findbox_recon_scaling.log`), which
    extrapolates to 16–20 h or more. Documented in `results/raw/findbox/main/INCOMPLETE.md` and DEVIATIONS D25.
  - E2/E3 best-effort φ3 run: 80 runs, 62 min (`falsification/findbox_besteffort`). PROF 15/20, SMuRF 9/20,
    PBO-RTAMT 20/20, SBO-RTAMT 20/20; 0 claims rejected by RTAMT.
  - FindBox quality table `results/tables/findbox_quality_main.md`: the best-effort φ3 boxes cover only 17 % of the
    reachable violations.
- **Phase 4 errata applied:**
  - F1: 0.53–1.00 ms.
  - F2: D9 corrected.
  - F3/F4: the failure-counted ratios are quoted in README and PROGRESS and shown in Tables 2–3.
  - F5: Wilcoxon note under Tables 2–3.
  - F8: Track-call column and note in Table 5.
  - Box numbering made explicit.
- **Documentation for teammates.**
  - README rewritten: results-at-a-glance table, repository map, experiment guide, run instructions, code
    walkthrough, glossary.
  - Analysis and plan moved to `docs/`.
  - `results/README.md` indexes every table, figure and run.
  - REPRODUCIBILITY_REPORT.md updated to the final state.
- **Code clean-up (behaviour-preserving).**
  - Unused imports removed: `src/langfal/{falsification,specs,control}.py`, tests, `run_findbox.py`.
  - Stale A-CC1 comment and doc paths fixed.
  - `make_tables.py`: status for requirements without a language, failure-counted ratio row, notes, Table 5
    Track-call column.
  - `findbox_quality.py` lists missing languages.
  - New `scripts/rebuild_results.sh`.
  - Simulink caches removed and git-ignored.
- **Verification after the clean-up.**
  - `pytest -q`: 59 passed.
  - Re-run with the new source hash (`*/final_check`) identical to `main`: falsification 8/8, control 1/1.
  - `scripts/rebuild_results.sh` rebuilt every table: grid sensitivity, box reachability and the Simulink
    comparison byte-identical; other tables changed only by the planned additions.
  - `analysis/audit.py`: **71 PASS, 0 FAIL**.

## Pending

Nothing is running or queued. Optional:
- Complete the best-effort φ1 FindBox language. This takes 16–20 h or more; the command is in
  `results/raw/findbox/main/INCOMPLETE.md`.

## Blockers / open issues
- The paper does not state FindBox's settings, seeds, BO settings, drone controller or hardware, so no paper number
  can be reproduced exactly (REPRODUCIBILITY_REPORT.md §6, §8).
- E1 violation rates for φ1, φ2 and φ5 remain unexplained (REPRODUCIBILITY_REPORT.md §6).
- `reference_paper.pdf` remains untracked inside the reference repo. It is the user's file and was not touched.
