# Tables 2 and 3 — falsification on Chasing Cars (E2/E3)

- Status: **FULL for phi2, phi3, phi4, phi5; not run: phi1**
- Source: `results/raw/falsification/findbox_besteffort/` (records.jsonl, meta.json)
- Language of ¬φ: **findbox** (FindBox run `main`, variant `besteffort`)
- Not run: phi1 (no language of ¬φ available; see `results/raw/findbox/main/INCOMPLETE.md`).
- Run created 2026-10-18T23:27:44; 2 session(s), source sha256 `ebb7c1956c5d`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

Columns: FR = falsified trials / trials; S̄ = mean iterations over falsified trials (± 95% t-CI); T̄_T = mean total monitoring time per falsified trial in ms on the critical path (parallel methods: slowest process per round); T̄_M = mean time per monitoring call in ms (one box for PROF, all boxes for SMuRF, one RTAMT evaluation for the baselines). Extra columns are ours only.

## Table 2: PBO-RTAMT vs PROF

| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | GP s/trial [ours] | wall s/trial [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | PBO-RTAMT | 20/20 | 0/0 | 12.50 | — | — | 13.617 | — | 1.107 | — | — | — | — | — |
| phi1 | PROF | 20/20 | 0/0 | 11.30 | — | — | 0.355 | — | 0.034 | — | — | — | — | — |
| phi2 | PBO-RTAMT | 20/20 | 19/20 | 7.40 | 25.68 ± 19.23 | 13.00 | 12.484 | 9.824 ± 6.822 | 1.675 | 0.2340 | 177 | 3.83 | 5.46 | 12.66 |
| phi2 | PROF | 20/20 | 14/20 | 7.50 | 57.64 ± 30.05 | 50.00 | 0.484 | 4.275 ± 2.542 | 0.067 | 0.0469 | 507 | 12.24 | 15.66 | 42.37 |
| phi3 | PBO-RTAMT | 20/20 | 20/20 | 6.30 | 1.90 ± 0.93 | 1.50 | 11.785 | 7.211 ± 5.386 | 1.877 | 0.2209 | 210 | 4.91 | 5.70 | 11.58 |
| phi3 | PROF | 20/20 | 15/20 | 6.05 | 47.47 ± 37.25 | 22.00 | 2.294 | 4.913 ± 3.829 | 0.380 | 0.0359 | 9250 | 196.95 | 308.78 | 794.17 |
| phi4 | PBO-RTAMT | 20/20 | 20/20 | 24.40 | 4.20 ± 2.36 | 2.50 | 44.700 | 6.009 ± 3.037 | 1.820 | 0.2650 | 228 | 5.85 | 6.08 | 13.06 |
| phi4 | PROF | 20/20 | 20/20 | 31.10 | 4.10 ± 1.56 | 3.50 | 0.672 | 0.538 ± 0.179 | 0.031 | 0.0297 | 222 | 5.37 | 5.81 | 12.32 |
| phi5 | PBO-RTAMT | 20/20 | 17/20 | 7.40 | 21.88 ± 11.81 | 13.00 | 11.242 | 9.478 ± 4.362 | 1.540 | 0.2780 | 248 | 5.45 | 8.30 | 19.20 |
| phi5 | PROF | 20/20 | 13/20 | 7.90 | 70.62 ± 31.07 | 59.00 | 0.468 | 4.688 ± 2.118 | 0.063 | 0.0464 | 584 | 13.49 | 17.09 | 46.72 |

Speedups PBO-RTAMT / PROF `[derived]` (ratio of means; > 1 favours PROF):

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| T̄_T ratio, paper | 38.4 | 25.8 | 5.1 | 66.5 | 24.0 | 24.1 |
| T̄_T ratio, ours | — | 2.3 | 1.5 | 11.2 | 2.0 | 3.0 (4 of 5 req.) |
| S̄ ratio, paper | 1.11 | 0.99 | 1.04 | 0.78 | 0.94 | 0.96 |
| S̄ ratio, ours | — | 0.45 | 0.04 | 1.02 | 0.31 | 0.27 (4 of 5 req.) |
| S̄ ratio, ours, failures counted at 200 | — | 0.34 | 0.02 | 1.02 | 0.42 | 0.24 (4 of 5 req.) |
| paired Wilcoxon p (iterations), ours | — | 0.005 | 0.000 | 0.969 | 0.003 | |

## Table 3: SBO-RTAMT vs SMuRF

| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | GP s/trial [ours] | wall s/trial [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | SBO-RTAMT | 20/20 | 0/0 | 27.90 | — | — | 30.438 | — | 1.207 | — | — | — | — | — |
| phi1 | SMuRF | 20/20 | 0/0 | 16.85 | — | — | 2.789 | — | 0.203 | — | — | — | — | — |
| phi2 | SBO-RTAMT | 20/20 | 15/20 | 15.10 | 38.40 ± 18.03 | 35.00 | 19.245 | 14.973 ± 10.272 | 1.272 | 0.2970 | 84 | 2.00 | 2.56 | 6.55 |
| phi2 | SMuRF | 20/20 | 6/20 | 12.95 | 78.17 ± 57.66 | 85.00 | 3.055 | 17.174 ± 16.524 | 0.324 | 0.1603 | 168 | 3.51 | 29.68 | 68.20 |
| phi3 | SBO-RTAMT | 20/20 | 20/20 | 19.45 | 13.95 ± 13.07 | 3.50 | 38.564 | 8.844 ± 4.328 | 1.975 | 0.8447 | 19 | 0.43 | 0.31 | 0.89 |
| phi3 | SMuRF | 20/20 | 9/20 | 18.65 | 28.89 ± 27.36 | 7.00 | 11.150 | 10.230 ± 11.472 | 0.631 | 0.2051 | 128 | 2.79 | 323.60 | 788.06 |
| phi4 | SBO-RTAMT | 20/20 | 19/20 | 39.10 | 20.53 ± 9.21 | 13.00 | 70.265 | 8.841 ± 3.225 | 1.808 | 0.3474 | 34 | 0.87 | 0.80 | 2.08 |
| phi4 | SMuRF | 20/20 | 20/20 | 25.50 | 17.25 ± 9.20 | 8.50 | 4.121 | 3.748 ± 1.614 | 0.186 | 0.1645 | 22 | 0.58 | 14.66 | 24.14 |
| phi5 | SBO-RTAMT | 20/20 | 11/20 | 13.40 | 75.73 ± 38.29 | 54.00 | 23.811 | 23.707 ± 10.688 | 1.701 | 0.3026 | 137 | 2.90 | 4.30 | 10.71 |
| phi5 | SMuRF | 20/20 | 8/20 | 11.65 | 65.62 ± 56.93 | 45.00 | 3.254 | 10.209 ± 8.070 | 0.353 | 0.1414 | 151 | 3.10 | 25.06 | 53.04 |

Speedups SBO-RTAMT / SMuRF `[derived]` (ratio of means; > 1 favours SMuRF):

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| T̄_T ratio, paper | 10.9 | 6.3 | 3.5 | 17.1 | 7.3 | 7.8 |
| T̄_T ratio, ours | — | 0.9 | 0.9 | 2.4 | 2.3 | 1.4 (4 of 5 req.) |
| S̄ ratio, paper | 1.66 | 1.17 | 1.04 | 1.53 | 1.15 | 1.29 |
| S̄ ratio, ours | — | 0.49 | 0.48 | 1.19 | 1.15 | 0.76 (4 of 5 req.) |
| S̄ ratio, ours, failures counted at 200 | — | 0.48 | 0.11 | 1.71 | 0.90 | 0.54 (4 of 5 req.) |
| paired Wilcoxon p (iterations), ours | — | 0.002 | 0.000 | 0.170 | 0.594 | |

Notes on the ratio rows:
- S̄ follows the paper: it averages falsified trials only. That is harmless at the paper's 20/20 success rates, but with unequal success rates it favours the method that fails more often.
- 'Failures counted at 200' averages all trials, with unfalsified trials at the 200-iteration cap (a restricted mean, a lower bound for a method that fails).
- Wilcoxon: two-sided signed-rank test on paired per-trial iteration counts, unfalsified trials at 200.

'—' = no ratio (a method falsified no trial of that requirement); the geometric mean then covers only the requirements shown.

## RTAMT re-checks of language claims (D9) `[ours]`

A language method claims a falsifier when the signal lies in a box of the given L(¬φ) (Dist > 0); the claim is accepted only if RTAMT gives ρ < 0. A rejected claim is a satisfying signal that the approximate language puts in L(¬φ). Records written before the `validation_rejections` counter existed give the count exactly for SMuRF (re-checks − 1 per falsified trial) and as bounds for PROF (1 to j boxes can succeed in the final round).

| Req | Method | trials | re-checks per trial (mean) | rejected claims, total | trials with a rejected claim |
|---|---|---|---|---|---|
| phi1 | PROF | 0 | — | — | — |
| phi1 | SMuRF | 0 | — | — | — |
| phi2 | PROF | 20 | 0.7 | 0 | 0 |
| phi2 | SMuRF | 20 | 0.3 | 0 | 0 |
| phi3 | PROF | 20 | 0.8 | 0 | 0 |
| phi3 | SMuRF | 20 | 0.5 | 0 | 0 |
| phi4 | PROF | 20 | 1.8 | 0 | 0 |
| phi4 | SMuRF | 20 | 1.0 | 0 | 0 |
| phi5 | PROF | 20 | 0.7 | 0 | 0 |
| phi5 | SMuRF | 20 | 0.4 | 0 | 0 |

