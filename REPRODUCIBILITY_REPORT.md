# Reproducibility Report — "Falsification and Control of CPS using the Language Set of DT-STL" (ICCPS '25)

Phase 4 audit of `target_project/` against `Paper.pdf` and [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).
Audit date: 2026-10-19. Final version: updated after the last FindBox runs and the Phase 5 code clean-up,
2026-10-19.

**Labels.** `[paper]` means reported in Paper.pdf. `[ours]` means measured by our runs. `[derived]` means
arithmetic on either.

**Automated evidence.** [`results/tables/audit.md`](results/tables/audit.md) is produced by `analysis/audit.py`. It
recomputes every headline number from the raw records, independently of the table generator. It also re-simulates
the stored falsifiers, checks the configurations, compares the audit re-runs and regenerates the tables. Final result: **71 PASS, 0 FAIL**. The first audit run gave
64 PASS, 1 FAIL; the failure was a documentation error (F1) that has since been corrected.

**Who audited.** The audit was done by the same agent that wrote the implementation. An independent human review
is still advisable.

---

## 1. Verdict

1. **The evaluation is implemented and traceable.**
   - Every experiment the paper reports (Tables 1–5 and the E6 claim in §4.3) is implemented and maps to a
     statement in the paper (§3).
   - Every reported number recomputes from stored raw outputs. One documentation error (F1) was found and
     corrected.
   - The current code reproduces the stored runs exactly, including after the final clean-up. Re-runs of subsets of
     every experiment were identical field by field (§4.2).
2. **The paper's headline quantitative claims are largely not reproduced in our setting.**
   - Falsification rates: 77–97 of 100 trials `[ours]` vs 100/100 `[paper]`.
   - Monitoring speedups: 2.3–2.7× `[ours]` vs 7.8–24× `[paper]`.
   - PROF needs about 2× more iterations than PBO-RTAMT `[ours]`; the paper reports parity.
   - SMuRF's iteration advantage over SBO-RTAMT does not survive counting failures.
   - The "3–7×" robustness-BO claim is not supported.
   - What does reproduce: the exact-language monitor equals RTAMT robustness; the language methods use less
     monitoring time per trial; LCP needs fewer iterations (rounds) than LCW on all 8 objectives.
3. **Main causes of the gaps.** These are our analysis, not established fact.
   - We use the exact language L(¬φ) instead of FindBox's approximation. Many exact boxes are unreachable by the
     system; for φ1, 2 of 11 are.
   - Runs with FindBox languages do not close the gap either (§5.3).
   - Settings the paper does not state: seeds, BO, FindBox, tracker, time grid.
   - Implementation-level monitoring costs differ.
   - The Chasing Cars model is **not** a cause. The Python port matches the official Simulink model to 6.7·10⁻⁷ m
     under accurate integration, and all 338 falsifiers carry over (§5.4).

---

## 2. Requirements checklist

Status: ✅ complete with evidence · ⚠️ complete with a caveat · ⏳ running or queued · ❌ not done or not reproducible.

### 2.1 Process requirements (Phase 3 instructions and CLAUDE.md)

| # | Requirement | Status | Evidence |
|---|---|---|---|
| R1 | Reference project not modified | ✅ | See below |
| R2 | Work only inside `target_project/` | ✅ | All code, configs, data and results are under `target_project/` (`external/` is inside it). Temporary scratch files were written to the session scratchpad and are not part of any result |
| R3 | Modular, documented implementation with deps, configs and scripts | ✅ | `src/langfal/` (library), `experiments/` (runners), `configs/*.yaml`, `requirements.txt`, `requirements-lock.txt`, `scripts/run_all.sh`, README.md |
| R4 | Seeds, configs, environment and costs tracked per run | ✅ | Each `results/raw/<exp>/<run>/meta.json` holds config, argv, environment and source sha256. Records hold seeds and per-run costs. Stored configs equal `configs/*.yaml` for all 8 main runs (audit C, 8/8 PASS) |
| R5 | Results re-obtainable with the current code | ✅ | Re-runs identical to the stored runs: audit RR-falsification 40/40, RR-table4 4/4, RR-e1, RR-control 4/4 (4,000 replications), RR-control_bo 10/10, RR-findbox 4/4; after the Phase 5 clean-up RR-final 8/8, RR-final-control 1/1 |
| R6 | Exact code version of each run recoverable | ⚠️ | The project is not a git repository. Source hashes are recorded, but old sources were not archived. Mitigated by R5 and by RR-pilot (code hash 437ea1b vs 43806db, 20/20 identical) |
| R7 | Validate code with tests before expensive runs | ✅ | `pytest -q`: 59 passed (`results/logs/audit/pytest.log`). `scripts/verify_cc_port.py`: 31/31 (`results/logs/audit/verify_cc_port.log`). Pilots ran before the main runs (`results/raw/*/pilot`, earlier timestamps in meta.json) |
| R8 | Never fabricate results; record the source of every metric | ✅ | 71/71 automated checks pass. The one quoted number that matched no stored run (F1) has been corrected. Tables carry "Source:" lines |
| R9 | Distinguish paper, reproduced and derived values | ✅ | `[paper]`, `[ours]` and `[derived]` labels in tables and README. Paper values live in `analysis/target_paper/paper_reported_values.py`, re-checked against the PDF in this audit (Tables 1–5 all match) |
| R10 | Document deviations | ✅ | DEVIATIONS.md (A1–A5, B1–B7, D1–D26). The wrong statement in D9 (F2) has been corrected |
| R11 | Update PROGRESS.md | ✅ | PROGRESS.md, Phase 4 and Phase 5 sections |
| R12 | Ask before expensive experiments or downloads | ⚠️ | See below |

**R1 evidence.**
- `git status` in `reference_project/CS637_SPGA` shows only `?? reference_paper.pdf`. That file was already
  present in Phase 1.
- `git diff HEAD` is empty; HEAD is `c356ed5`.
- All 375 tracked files carry the clone time, 2026-10-18 14:13.
- `.git/index` was last written at 14:15, before Phase 1.

**R12 history.**
- E2/E3: approved by the user.
- E4 and E5: requested by the user.
- E6: run under "don't ask for my permission".
- FindBox: installed at the user's request.
- The ~30 min of Simulink-check runs: run under "try from your end and then queue the remaining parts".
- The ~40 min of audit re-runs: part of this audit request.
- Phase 5: the user said "dont be askking any permissions just complete what was asked". Under that instruction I
  stopped the best-effort φ1 FindBox job (§8), ran best-effort φ3 (~1 h) and ran the final check re-runs.

### 2.2 Paper experiments

| ID | Paper source | What | Status | Evidence (raw → table) |
|---|---|---|---|---|
| E1 | §3.2 "Monitoring accuracy", Table 1 (p.6) | Language monitor vs RTAMT on 10,000 uniform inputs | ✅ | `results/raw/e1_monitoring/main` → `table1_main.md`; audit E1-1…5, D-e1-*, RR-e1 |
| E2 | §3.2 "Falsification performance", Table 2 (p.6) | PROF vs PBO-RTAMT, 20 trials, φ1–φ5 | ✅ | `falsification/main` → `table2_3_main.md`; audit E23-*, D-falsification-main, RR-falsification |
| E3 | Table 3 (p.7) | SMuRF vs SBO-RTAMT | ✅ | same as E2 |
| E4 | Table 4 and text (p.7) | Modified PROF (S̄_min, S̄_max) and sequential BO | ⚠️ | `table4/main` → `table4_main.md`; audit E4-*, RR-table4. The paper's in-text volume ratios of never-falsified boxes are not reproduced (§6) |
| E5 | §4.3, Table 5 (p.9) | LangControl LCW vs LCP, 8 objectives, 1000 runs each | ⚠️ | `control/main` → `table5_main.md`; audit E5-*, RR-control. Re-implementation: tracker and UAV parameters are ours (L3) |
| E6 | §4.3 text (p.9) "BO … requires 3-7x the number of iterations" | Robustness-BO control baseline | ⚠️ | `control_bo/main` → `e6_control_bo_main.md`; audit E6-*, RR-control_bo. Reduced scale (50 replications); the paper gives no numbers |
| Figs. 1–4 | pp.4, 5, 8, 9 | Illustrations | ⚠️ | `results/figures/`. Drawn from our exact languages and tracker, not reproductions |
| FB | §3.2 "we used the code from [5]" | FindBox languages for φ1–φ5, 2 settings | ⚠️ | `results/raw/findbox/main`: 9/10 built. Best-effort φ1 was stopped after 5.5 h (FindBox's reconstruction step would need an estimated 16–20 h or more; `INCOMPLETE.md`). Quality: `findbox_quality_main.md`. Audit FB-6/7/8, RR-findbox |
| E2/E3-FB | Tables 2–3 with FindBox languages | Falsification with the paper's language tool | ⚠️ | Default variant ✅ (400 runs, audit FB-1…3). Best-effort ✅ for φ2–φ5 (320 runs, audit FB-4); φ1 has no language. `table2_3_findbox_*.md` |
| CC | §3.2 benchmark (ARCH [29]) | Python port vs the official Simulink model | ✅ | `results/matlab/*`, `cc_port_vs_simulink.md`; audit CC-a, CC-c, CC-f |

---

## 3. Mapping of experiments to the paper (verified against the PDF)

| Paper statement (page) | Our implementation | Notes |
|---|---|---|
| CC benchmark, inputs ∈ [0,1], 10 control points each, 100 s, 0.1 Hz, x := y5 − y4 (p.5) | `systems/chasing_cars.py`; D1: 11 samples t = 0..100 s; D3: piecewise-constant inputs | The paper's "10 time steps / ℝ¹⁰" conflicts with φ2's horizon (B-item); grid sensitivity in `grid_sensitivity.md` |
| φ1–φ5, Eqs. 8–12 (p.5) | `specs.py` (printed side by side in the audit; all 5 match); D2: [a,b] s ↦ [⌈a/10⌉, ⌊b/10⌋] | φ5's □[0,5] becomes □[0,0] |
| Value agreement, sign-only agreement, complete disagreement, mean RTAMT and language-monitor times, satisfaction ratios, number of boxes (Table 1, p.6) | `run_e1_monitoring.py` (same definitions); "satisfaction ratio" read as the violation rate (B5) | Our box counts are for the exact L(¬φ) |
| PROF vs PBO-RTAMT on j processors, j = boxes of ¬φ; SMuRF vs SBO-RTAMT; same 5 starting points; ≤ 200 iterations; falsifiers validated with RTAMT (p.6) | `falsification.py`; D7 shared starts, D8 counting, D9 RTAMT re-check, D10 PBO processes, D11 timing | Matches all stated settings |
| FR, S̄ (mean iterations to falsify), T̄_T (total monitoring time), T̄_M (time per component: distance to a box for PROF/SMuRF, one formula evaluation for RTAMT methods) (p.6) | `make_tables.tables23` | T̄_M for SMuRF covers all boxes per iteration (matches the caption, "time per iteration"). The text's "a single component … distance … from the box" is ambiguous |
| Modified PROF exiting when all boxes are falsified or after 200 iterations → S̄_min, S̄_max; sequential BO, random box, ≤ 200 iterations per box (p.7) | `run_prof(until="all")`, `run_sequential_bo` (D13) | Matches |
| Alg. 3 LangControl; LCW (B = L(φ)) and LCP (one box per process, success if the trajectory enters *any* box); 1000 runs; P̄ = mean iterations (pp.8–9) | `control.py` (`lang.contains` checks the whole language in LCP); D16 M = 500, K = 10; D21 ≤ 64 processes | Loop bounds verified: K+1 Track calls per reference, M+1 references |
| Eqs. 14–21 (p.8) | `specs.uav_specs` (all 8 match); domains D19 | — |
| UAV dynamics, ref. [47] (p.8) | `systems/uav.py`; inertia ratio corrected to (I_y−I_z)/I_x (B4); parameters D14; tracker D15 | The paper gives no parameters or tracker |
| "BO consistently requires 3-7x the number of iterations" (p.9) | `robustness_bo_control`, `run_control_bo.py` (D22–D24) | Same success test as LangControl |

---

## 4. How the results were checked

### 4.1 Traceability (audit sections A, B, E)
- **Claims.** 38 headline claims were recomputed from `results/raw/` and `results/matlab/` with fresh code, and all
  38 match. F1 failed in the first audit run and was corrected.
- **Falsifiers.** All 931 stored falsifiers (main, table4, both FindBox runs) were re-simulated. Each reproduces its
  stored signal and violates φ with the stored robustness.
- **E1 data.** The E1 inputs equal the seed-7 draws, and 300 random rows re-simulate exactly. The E1 percentages
  recompute exactly from the stored signals.
- **Tables.** In Phase 5, every table and figure was rebuilt from the raw records with `scripts/rebuild_results.sh`.
  Grid sensitivity, box reachability and the Simulink comparison came out byte-identical. Other tables changed
  only by the planned additions: header format, the failure-counted ratio row, notes, and the Table 5 Track-call
  column.

### 4.2 Re-runs with the current code (audit section D)

| Experiment | Re-run subset | Compared fields | Result |
|---|---|---|---|
| E1 | all 10,000 inputs | all non-timing metrics, the 10,000 signals | identical |
| E2/E3 | trials 0 and 13 × φ1–φ5 × 4 methods (40 runs) | falsified, iterations, simulations, falsifier input, ρ, stop reason, re-checks | 40/40 identical |
| E4 | trial 0: SEQ-BO φ2, φ4, φ5; PROF-all φ5 | iterations, box order, per-box iterations, S_min, S_max | 4/4 identical |
| E5 | φ3, φ4 × LCW, LCP, 1000 replications each | per-replication iterations, Track calls | 4/4 identical |
| E6 | φ1, φ3 × replications 0–4 | success, iterations, best ρ | 10/10 identical |
| FindBox | default φ2, φ4, φ5; best-effort φ2 | box files | 4/4 identical |
| Cross-version | E2/E3 pilot (older code) vs main trial 0 | falsified, iterations, simulations | 20/20 identical |
| After the Phase 5 clean-up | E2/E3 trial 13 × φ3, φ4 × 4 methods; E5 φ4 LCP (1000 replications) | as above | 8/8 and 1/1 identical |

Timing fields are not expected to match. The E1 re-run measured per-call speedups of 1.4–2.5×, against 1.1–2.0× in
the main run. Part of the audit ran on battery power at a reduced CPU clock (§7).

---

## 5. Results compared with the paper

### 5.1 E1, Table 1 (10,000 inputs)

| | φ1 | φ2 | φ3 | φ4 | φ5 |
|---|---|---|---|---|---|
| Value agreement % [paper] | 100 | 42.60 | 100 | 42.61 | 100 |
| Value agreement % [ours] | 100 | 100 | 100 | 100 | 100 |
| RTAMT ms/call [paper] | 0.869 | 0.672 | 1.38 | 1.37 | 1.05 |
| RTAMT ms/call, 11 samples [ours] | 0.087 | 0.169 | 0.193 | 0.205 | 0.167 |
| RTAMT ms/call, 101 samples [ours] | 0.533 | 0.861 | 0.948 | 1.001 | 0.859 |
| Language monitor ms/call [paper] | 0.0364 | 0.0151 | 0.351 | 0.0133 | 0.0368 |
| Language monitor ms/call [ours] | 0.078 | 0.110 | 0.094 | 0.100 | 0.093 |
| Violation ("satisfaction") % [paper] | 7.08 | 1.82 | 3.84 | 0.87 | 7.08 |
| Violation % [ours] | 0.70 | 0.84 | 4.23 | 0.85 | 0.52 |
| Boxes [paper] (FindBox) / [ours] (exact L(¬φ)) | 7 / 11 | 3 / 8 | 85 / 27 | 2 / 27 | 7 / 7 |

- **Value agreement.** 100 % is expected, because our language is exact. The paper's 42.6 % reflects FindBox's
  approximation.
- **Speedup.** Our per-call speedup is 1.1–2.0×, against 3.9–103× `[paper]`. Our language monitor is a vectorised
  NumPy distance; the paper's implementation is unknown.
- **Violation rates.** φ3 and φ4 roughly agree. φ1, φ2 and φ5 do not, and no time grid we tried reproduces them
  (§6).

### 5.2 E2/E3, Tables 2–3 (20 trials per cell)

| Method | FR φ1–φ5 [ours] | S̄ φ1–φ5 [ours] (falsified trials only) | S̄ [paper] (FR 20/20 everywhere) |
|---|---|---|---|
| PBO-RTAMT | 20/19/20/20/18 | 9.95/24.26/2.50/4.80/28.33 | 12.50/7.40/6.30/24.40/7.40 |
| PROF | 9/14/20/20/14 | 42.67/31.14/4.00/7.65/89.21 | 11.30/7.50/6.05/31.10/7.90 |
| SBO-RTAMT | 20/15/20/19/11 | 31.15/38.40/13.95/20.53/75.73 | 27.90/15.10/19.45/39.10/13.40 |
| SMuRF | 20/10/19/20/10 | 22.30/45.00/7.63/18.10/67.40 | 16.85/12.95/18.65/25.50/11.65 |

| Derived, geometric mean over φ | [ours] | [paper] |
|---|---|---|
| T̄_T ratio PBO/PROF (critical path; total over processes) | 2.7 (3.4) | 24.1 |
| T̄_T ratio SBO/SMuRF | 2.3 | 7.8 |
| S̄ ratio PBO/PROF, falsified trials only (failures counted at 200) | 0.47 (0.34) | 0.96 |
| S̄ ratio SBO/SMuRF, falsified trials only (failures counted at 200) | 1.23 (**1.03**; per φ 1.40/0.64/0.81/1.63/0.98) | 1.29 |

### 5.3 E2/E3 with FindBox languages (20 trials; FindBox settings are ours, D25)

| Variant | FR PROF | FR SMuRF | FR PBO-RTAMT | FR SBO-RTAMT |
|---|---|---|---|---|
| Default, φ1/φ2/φ3/φ4/φ5 | 0/0/20/n.a./0 | 1/0/20/n.a./0 | 19/15/20/n.a./11 | 20/15/20/19/11 |
| Best-effort, φ2/φ3/φ4/φ5 (no φ1 language) | 14/15/20/13 | 6/9/20/8 | 19/20/20/17 | 15/20/19/11 |

- **Default φ4.** FindBox finds no box: integer sampling cannot hit 32 < x < 33.
- **Default φ1.** One box contains every reachable signal. RTAMT rejected 4,020 PROF and 4,040 SMuRF language
  claims (D9).
- **Best-effort coverage.** The FindBox boxes cover 43 %, 17 %, 100 % and 69 % of the reachable (E1) violations of
  φ2, φ3, φ4 and φ5. The language methods fall behind exactly where coverage is below 100 %; no claim was rejected
  by RTAMT (`findbox_quality_main.md`).
- **Table 1 recomputed with FindBox languages.** Value agreement with RTAMT is 0–100 % (`[paper]` 42.6–100 %). For
  example, default φ2 gives 37.4 % against 42.6 % in the paper.
- **SBO-RTAMT** does not use the language, and it is identical to the main run in 180/180 trials.

### 5.4 Chasing Cars port vs the official Simulink model (MATLAB R2026b)

- **Verdicts.** On 200 random inputs, all verdicts agree under every Simulink setting.
- **Accurate integration** (exact steps, tolerance 1e-10, MinStep auto): positions agree to ≤ 6.7·10⁻⁷ m and
  robustness to ≤ 1.1·10⁻⁶.
- **The model's usual settings** (ARCH 0.01 s input ramps, RelTol 1e-3, MinStep 0.01 s): Simulink deviates by up to
  1.5 m and 1.04 in robustness.
- **Falsifiers.** All 338 Table 2–3 falsifiers falsify accurately integrated Simulink. Under the usual settings,
  322 do; the other 16 have |ρ| ≤ 0.057.
- Source: `cc_port_vs_simulink.md`; audit CC-a, CC-c, CC-f.

### 5.5 E4, E5, E6

| | [ours] | [paper] |
|---|---|---|
| E4 S_min = PROF S | 77/77 matched trials | S̄_min = Table 2 PROF S̄ |
| E4 S̄_max | 200 for all φ | 37–64, and 200 for φ3 |
| E4 sequential BO, FR and S̄ | 8/17/20/20/14; 594–1,113 | 20/20; 19.6–46.4 |
| E5 LCP < LCW (P̄, rounds) | 8/8 | 8/8 |
| E5 LCW/LCP ratio | 1.0–70 | 1.3–4.0 |
| E5 LCW failures | φ5 786/1000, φ8 3/1000 | none reported |
| E6 BO/LCW iterations within 205 calls | 0.52 (restricted mean 0.53) | 3–7 |

- **E5 P̄ (LCW, ours):** 56.6/59.3/10.6/30.7/2,673/581/36.1/950.
- **E5 P̄ (LCP, ours):** 1.19/5.06/1.00/1.23/128/571/1.00/13.7.

---

## 6. Discrepancies and their likely causes

| Discrepancy | Likely cause | Evidence |
|---|---|---|
| FR < 20/20 for all methods | Our BO settings (D6), the exact language and our seeds; φ2 and φ5 have small violation margins (median \|ρ\| of falsifiers 0.01–0.04) | `table2_3_main.md`, `cc_port_vs_simulink.md` |
| PROF needs more iterations than PBO-RTAMT (0.47) | Unreachable exact boxes: PROF processes tied to them cannot succeed (φ1: 2 of 11 boxes entered by 10,000 random signals; all 9 PROF successes in box index 3, i.e. x(3) > 40) | `box_reachability_main.md`; audit E23-7/8 |
| Smaller monitoring speedups | Our RTAMT calls on 11-sample traces are cheap (0.09–0.21 ms vs the paper's 0.67–1.38 ms), and our language monitor (0.08–0.11 ms) is not 10–100× cheaper than RTAMT. Both costs are implementation-dependent | `table1_main.md` |
| S̄_max = 200 everywhere | Exact languages contain boxes the system never enters | `box_reachability_main.md` |
| SEQ-BO needs 594–1,113 iterations | Random box order: up to 200 iterations are spent on each unreachable box | `table4_main.md` |
| E1 violation rates for φ1, φ2, φ5 | Not explained. Neither the time grid (`grid_sensitivity.md`: 11 samples, 10 samples, 1 s grid) nor the Simulink model (§5.4) accounts for 7.08 % on φ1. Candidates: the meaning of "Satisfaction Ratios" (B5) and PSY-TaLiRo's input interpolation | `grid_sensitivity.md` |
| E5 absolute P̄ and ratios | Our tracker, UAV parameters, Sample and Projection, M, K and the LCP process cap; none is given in the paper | `table5_main.md`, D14–D21 |
| E6 3–7× not supported | Paper gives no data; our BO and tracker choices (D22–D24) | `e6_control_bo_main.md` |
| FindBox languages differ from the paper's (box counts: default 3/1/54/0/1, best-effort —/5/108/53/5, paper 7/3/85/2/7) | The paper does not state FindBox's sampling, bounds or seed | `results/raw/findbox/main`, D25 |

---

## 7. Audit findings: errors and methodological issues

| # | Finding | Severity | Status |
|---|---|---|---|
| F1 | README and PROGRESS say RTAMT on 101-sample traces costs **0.41–1.08 ms**. The stored E1 run says **0.53–1.00 ms**, and no stored run supports 0.41–1.08 | Documentation error (number without a source) | **Fixed** (README, PROGRESS; audit E1-4 now checks 0.53–1.00) |
| F2 | DEVIATIONS D9 says "The paper does not say whether it re-checked". It does: p.6, "any encountered falsifier is validated using RTAMT" | Documentation error | **Fixed** (D9 corrected) |
| F3 | The SMuRF iteration advantage was reported as matching the paper (1.23 vs 1.29). It rests on conditional means: counting unfalsified trials at the cap gives 1.03, per-φ ratios lie on both sides of 1, and only φ4 is significant | Overstated conclusion | **Fixed** (README, PROGRESS; audit E23-9) |
| F4 | S̄, P̄ and the E6 means follow the paper's definition (successful runs only). With unequal success rates this favours the method that fails more. Restricted means: PBO/PROF 0.47 → 0.34 (stronger), E6 0.52 → 0.53 (unchanged), E5 φ5 LCW/LCP 20.8 → ≥ 38.2 | Statistical caveat | **Addressed**: Tables 2–3 now include a "failures counted at 200" row; README and this report quote both versions; `audit.md` §F |
| F5 | The Wilcoxon tests in Tables 2–3 use iteration counts capped at 200 for unfalsified trials; the table text does not say so | Reporting gap | **Fixed** (note under Tables 2–3) |
| F6 | The best-effort FindBox bounds [0, 70] were chosen from the reachable range of the E1 simulations. That is information about the system flowing into the language, an advantage the language methods would not normally have | Leakage (one variant only) | Documented as "best-effort" in D25; the default variant has none |
| F7 | In the initial phase, PROF re-checks only the deepest initial sample per box; SMuRF re-checks each one. Irrelevant for exact languages; for FindBox languages a falsifier could be missed | Minor asymmetry | Checked: no trial affected in either FindBox run |
| F8 | LCP's advantage is in rounds (parallel time). In total Track calls, LCP uses more than LCW on 5 of 8 objectives (φ1: 76 vs 57 per replication; φ5: 8,222 vs 4,904) | Interpretation caveat | **Addressed**: Table 5 column and note; README; audit E5-5 |
| F9 | T̄_T for parallel methods uses the critical path (D11). Summing over processes changes PBO/PROF from 2.7 to 3.4; the conclusion is unchanged | Definition sensitivity | `audit.md` §G |
| F10 | PBO-RTAMT uses j = number of exact boxes (11/8/27/27/7), the paper j = FindBox boxes (7/3/85/2/7), so PBO runs a different number of processes per round than in the paper | Setting mismatch (by design, D10) | Documented |
| F11 | Fixed before this audit: Table 2–3 speedup rows were misaligned when a ratio was missing (pilot only); E6 first run used a weaker success test (superseded, kept); SBO-RTAMT wrongly marked "not applicable" for empty FindBox languages (20 records replaced, noted in meta.json) | Bugs | Fixed; provenance kept |
| F12 | Timings depend on machine state. Main runs used 10 workers on a laptop with P- and E-cores. The best-effort FindBox falsification ran next to FindBox and MATLAB, and the audit re-runs partly on battery (1.3 GHz) | Timing noise | Iterations and outcomes are deterministic (§4.2); compare timings within a run only |
| F13 | FindBox's `recon` step slows down sharply with distinct floating-point corner coordinates (26/72/542 s for 50/100/200 points). This makes the best-effort φ1 language impractical: 16–20 h or more | Tool limitation | Run stopped after 5.5 h and documented (`results/raw/findbox/main/INCOMPLETE.md`, `results/logs/findbox_recon_scaling.log`) |

**Checked without finding a problem.**
- **Leakage.** No test-on-train or tuning on evaluation trials was found. The pilot shares seeds with main trial 0
  but was only used to validate the pipeline. Mid-project changes (D6 kernel speed, D13 GP growth, the E6
  success-test fix) are documented with their reasons.
- **Baselines** share the BO configuration with the proposed methods (D6), as the paper implies.
- **Metric definitions** match Table 1's text.
- **LCP** checks any box, as the paper states.
- **Algorithm 3's loop bounds** match.

---

## 8. Missing or incomplete experiments

| Item | Status | Reason |
|---|---|---|
| FindBox best-effort φ1 language, and with it best-effort E2/E3 on φ1 | ❌ | Stopped after 5.5 h. FindBox's reconstruction step would need an estimated 16–20 h or more (F13). The default-setting φ1 language exists. Everything else in the FindBox study is complete |
| Table 4 in-text volume ratios of never-falsified boxes (0 and 0.00129) | ❌ | Our boxes are unbounded (D4), so the ratios are undefined without a bounded state space the paper does not give |
| Exact reproduction of any paper number | ❌ | Unknown seeds, BO and FindBox settings, tracker, UAV parameters and hardware (docs/TARGET_ANALYSIS.md §5, §9.5) |
| E6 at the paper's scale | ⚠️ | The paper gives no scale; ours is 50 replications |
| Figures 1–4 as in the paper | ⚠️ | Illustrations only; the paper's projections and data are unknown |

---

## 9. Errata: all applied in Phase 5

A README edit during the audit was declined, so these corrections were first only proposed. They were all applied
in Phase 5, after the request to "make all the necessary changes":

1. **F1, README §E1 and PROGRESS line 28.** "0.41–1.08 ms … which is the paper's RTAMT range" →
   "0.53–1.00 ms, comparable to the paper's 0.67–1.38 ms".
2. **F2, DEVIATIONS D9.** Replace "The paper does not say whether it re-checked; without the re-check these claims
   would count as falsifications" with "The paper also validates falsifiers with RTAMT (p.6)".
3. **F3/F4, README and PROGRESS E2/E3.**
   - SMuRF: "SMuRF needs fewer iterations (1.23, falsified trials only); counting unfalsified trials at the
     200-iteration cap gives 1.03 with per-φ ratios on both sides of 1, so the paper's iteration advantage is not
     clearly reproduced".
   - PROF: add "(0.34 when unfalsified trials count at the cap)".
4. **F5, Tables 2–3 footnote.** "Wilcoxon on iteration counts with unfalsified trials at 200".
5. **README/PROGRESS "box 3"** → "box index 3 (0-based; x(3) > 40, t = 30 s)".
6. **F8, README E5.** Add the Track-call qualification.

---

## 10. Limitations

- **Self-audit.** The implementer audited its own work; an independent human review is recommended.
- **No archived code history.** The project is not under git (R6). Re-runs show behavioural equivalence for the
  subsets tested, not for every record.
- **Timing claims depend on hardware and implementation.** They should not be compared across machines.
- **E5 and E6** depend on our tracker, UAV parameters and LangControl choices; only trends are comparable.
- **FindBox is unlicensed.** It is used locally at the user's request and cannot be redistributed, so others need
  their own copy (`scripts/fetch_findbox.sh`).
- **One FindBox language is missing.** The best-effort φ1 language was not computed (F13).

---

## 11. Commands to reproduce

Run from `target_project/`. Use `.venv/bin/python` on Linux/macOS.

**Setup and checks.** The test suite takes about 15–20 s on mains power; it took 188 s on battery.

```bash
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt   # exact: requirements-lock.txt
export PYTHONUTF8=1; PY=.venv/Scripts/python.exe
$PY -m pytest -q                                                          # 59 tests
bash scripts/fetch_cc_model.sh && $PY scripts/verify_cc_port.py           # 31 checks of the CC port vs cars.mdl
```

**Full runs.** Wall times are for 10 workers on an i5-1335U, taken from meta.json.

```bash
$PY experiments/run_e1_monitoring.py --config configs/e1_monitoring.yaml --run-id main --workers 10   # 1.4 min
$PY experiments/run_falsification.py --config configs/falsification.yaml --run-id main --workers 10   # 22 min
$PY experiments/run_falsification.py --config configs/table4.yaml        --run-id main --workers 10   # 92 min
$PY experiments/run_control.py       --config configs/control.yaml       --run-id main --workers 10   # 97 min
$PY experiments/run_control_bo.py    --config configs/control_bo.yaml    --run-id main --workers 10   # 29 min
$PY analysis/make_tables.py --e1 main --falsification main --table4 main --control main --control-bo main
$PY analysis/grid_sensitivity.py --n 2000 --workers 10
$PY analysis/box_reachability.py --e1 main --falsification main --table4 main
$PY analysis/plot_falsification.py --run-id main; $PY analysis/plot_figures.py
```

**FindBox.** FindBox is unlicensed and opt-in.

```bash
bash scripts/fetch_findbox.sh
$PY experiments/run_findbox.py --config configs/findbox.yaml --run-id main --workers 10              # hours
$PY experiments/run_falsification.py --config configs/falsification_findbox_default.yaml    --run-id findbox_default    --workers 10
$PY experiments/run_falsification.py --config configs/falsification_findbox_besteffort.yaml --run-id findbox_besteffort --workers 10
$PY analysis/make_tables.py --falsification findbox_default; $PY analysis/make_tables.py --falsification findbox_besteffort
$PY analysis/findbox_quality.py --findbox main --e1 main
```

**Simulink check.** Needs MATLAB and Simulink. The six `matlab -batch` commands are listed in README "Checking the
port against Simulink":

```bash
$PY scripts/cc_matlab_compare.py export && $PY scripts/cc_matlab_compare.py export-falsifiers --run main
# ... six matlab -batch runs (README) ...
$PY scripts/cc_matlab_compare.py compare
```

**This audit.** The re-runs took about 40 min on battery and write to run id `audit_rerun`.

```bash
$PY experiments/run_e1_monitoring.py --config configs/e1_monitoring.yaml --run-id audit_rerun --workers 8
$PY experiments/run_falsification.py --config configs/falsification.yaml --run-id audit_rerun --trial-ids 0 13 --workers 8
$PY experiments/run_falsification.py --config configs/table4.yaml --run-id audit_rerun --trial-ids 0 --specs phi2 phi4 phi5 --methods SEQ-BO --workers 3
$PY experiments/run_falsification.py --config configs/table4.yaml --run-id audit_rerun --trial-ids 0 --specs phi5 --methods PROF-all
$PY experiments/run_control.py    --config configs/control.yaml    --run-id audit_rerun --specs phi3 phi4 --workers 4
$PY experiments/run_control_bo.py --config configs/control_bo.yaml --run-id audit_rerun --specs phi1 phi3 --reps 5 --workers 8
$PY experiments/run_findbox.py    --config configs/findbox.yaml    --run-id audit_rerun --variants default --specs phi2 phi4 phi5 --workers 3
$PY experiments/run_findbox.py    --config configs/findbox.yaml    --run-id audit_rerun --variants besteffort --specs phi2
# after the Phase 5 code clean-up (run id final_check, about 1 min)
$PY experiments/run_falsification.py --config configs/falsification.yaml --run-id final_check --trial-ids 13 --specs phi3 phi4 --workers 8
$PY experiments/run_control.py    --config configs/control.yaml    --run-id final_check --specs phi4 --variants LCP
$PY analysis/audit.py                                                     # -> results/tables/audit.md
```

**Rebuild every table and figure from the stored raw records.** This takes about 2 minutes and ends with the audit.

```bash
bash scripts/rebuild_results.sh
```

`scripts/run_all.sh` chains the full runs and analysis. Its FindBox and MATLAB stages run only when those tools are
available.
