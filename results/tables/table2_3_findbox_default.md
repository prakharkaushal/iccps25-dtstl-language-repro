# Tables 2 and 3 — falsification on Chasing Cars (E2/E3)

- Status: **FULL**
- Source: `results/raw/falsification/findbox_default/` (records.jsonl, meta.json)
- Language of ¬φ: **findbox** (FindBox run `main`, variant `default`)
- 60 runs not applicable (empty language for: phi4); counted as not falsified.
- Run created 2026-10-18T21:34:52; 3 session(s), source sha256 `8ffecf40b85e`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

Columns: FR = falsified trials / trials; S̄ = mean iterations over falsified trials (± 95% t-CI); T̄_T = mean total monitoring time per falsified trial in ms on the critical path (parallel methods: slowest process per round); T̄_M = mean time per monitoring call in ms (one box for PROF, all boxes for SMuRF, one RTAMT evaluation for the baselines). Extra columns are ours only.

## Table 2: PBO-RTAMT vs PROF

| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | GP s/trial [ours] | wall s/trial [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | PBO-RTAMT | 20/20 | 19/20 | 12.50 | 14.42 ± 6.88 | 10.00 | 13.617 | 9.372 ± 3.613 | 1.107 | 0.3165 | 76 | 2.82 | 3.97 | 8.81 |
| phi1 | PROF | 20/20 | 0/20 | 11.30 | — | — | 0.355 | — | 0.034 | 0.0631 | 605 | 21.15 | 34.60 | 96.22 |
| phi2 | PBO-RTAMT | 20/20 | 15/20 | 7.40 | 74.53 ± 33.28 | 65.00 | 12.484 | 29.780 ± 12.672 | 1.675 | 0.3791 | 111 | 3.42 | 5.25 | 12.99 |
| phi2 | PROF | 20/20 | 0/20 | 7.50 | — | — | 0.484 | — | 0.067 | 0.0612 | 205 | 5.28 | 13.67 | 28.57 |
| phi3 | PBO-RTAMT | 20/20 | 20/20 | 6.30 | 2.30 ± 1.27 | 1.50 | 11.785 | 8.843 ± 3.368 | 1.877 | 0.3796 | 129 | 5.14 | 6.32 | 12.55 |
| phi3 | PROF | 20/20 | 20/20 | 6.05 | 3.80 ± 2.33 | 2.00 | 2.294 | 5.648 ± 2.708 | 0.380 | 0.0455 | 210 | 7.78 | 8.73 | 18.65 |
| phi4 | PBO-RTAMT | 20/20 | 0/20 | 24.40 | — | — | 44.700 | — | 1.820 | — | 0 | 0.00 | 0.00 | 0.00 |
| phi4 | PROF | 20/20 | 0/20 | 31.10 | — | — | 0.672 | — | 0.031 | — | 0 | 0.00 | 0.00 | 0.00 |
| phi5 | PBO-RTAMT | 20/20 | 11/20 | 7.40 | 50.36 ± 30.37 | 35.00 | 11.242 | 22.918 ± 12.312 | 1.540 | 0.4195 | 123 | 3.64 | 7.14 | 15.79 |
| phi5 | PROF | 20/20 | 0/20 | 7.90 | — | — | 0.468 | — | 0.063 | 0.0586 | 205 | 5.43 | 12.94 | 27.89 |

Speedups PBO-RTAMT / PROF `[derived]` (ratio of means; > 1 favours PROF):

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| T̄_T ratio, paper | 38.4 | 25.8 | 5.1 | 66.5 | 24.0 | 24.1 |
| T̄_T ratio, ours | — | — | 1.6 | — | — | 1.6 (1 of 5 req.) |
| S̄ ratio, paper | 1.11 | 0.99 | 1.04 | 0.78 | 0.94 | 0.96 |
| S̄ ratio, ours | — | — | 0.61 | — | — | 0.61 (1 of 5 req.) |
| S̄ ratio, ours, failures counted at 200 | 0.12 | 0.53 | 0.61 | — | 0.59 | 0.39 (4 of 5 req.) |
| paired Wilcoxon p (iterations), ours | 0.000 | 0.001 | 0.119 | — | 0.003 | |

## Table 3: SBO-RTAMT vs SMuRF

| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | GP s/trial [ours] | wall s/trial [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | SBO-RTAMT | 20/20 | 20/20 | 27.90 | 31.15 ± 16.33 | 12.00 | 30.438 | 10.336 ± 5.159 | 1.207 | 0.2810 | 36 | 1.31 | 1.32 | 3.18 |
| phi1 | SMuRF | 20/20 | 1/20 | 16.85 | 141.00 | 141.00 | 2.789 | 37.264 | 0.203 | 0.1991 | 202 | 7.25 | 32.73 | 76.25 |
| phi2 | SBO-RTAMT | 20/20 | 15/20 | 15.10 | 38.40 ± 18.03 | 35.00 | 19.245 | 16.518 ± 6.879 | 1.272 | 0.3875 | 84 | 2.72 | 4.11 | 10.41 |
| phi2 | SMuRF | 20/20 | 0/20 | 12.95 | — | — | 3.055 | — | 0.324 | 0.1732 | 205 | 5.42 | 13.08 | 28.13 |
| phi3 | SBO-RTAMT | 20/20 | 20/20 | 19.45 | 13.95 ± 13.07 | 3.50 | 38.564 | 9.829 ± 6.688 | 1.975 | 0.4839 | 19 | 0.74 | 0.60 | 1.61 |
| phi3 | SMuRF | 20/20 | 20/20 | 18.65 | 11.95 ± 8.15 | 4.50 | 11.150 | 5.265 ± 2.245 | 0.631 | 0.3395 | 17 | 0.68 | 17.33 | 29.16 |
| phi4 | SBO-RTAMT | 20/20 | 19/20 | 39.10 | 20.53 ± 9.21 | 13.00 | 70.265 | 13.980 ± 4.773 | 1.808 | 0.5745 | 34 | 1.20 | 1.13 | 2.82 |
| phi4 | SMuRF | 20/20 | 0/20 | 25.50 | — | — | 4.121 | — | 0.186 | — | 0 | 0.00 | 0.00 | 0.00 |
| phi5 | SBO-RTAMT | 20/20 | 11/20 | 13.40 | 75.73 ± 38.29 | 54.00 | 23.811 | 33.756 ± 14.575 | 1.701 | 0.4254 | 137 | 4.06 | 6.93 | 17.19 |
| phi5 | SMuRF | 20/20 | 0/20 | 11.65 | — | — | 3.254 | — | 0.353 | 0.1778 | 205 | 5.46 | 12.38 | 27.31 |

Speedups SBO-RTAMT / SMuRF `[derived]` (ratio of means; > 1 favours SMuRF):

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| T̄_T ratio, paper | 10.9 | 6.3 | 3.5 | 17.1 | 7.3 | 7.8 |
| T̄_T ratio, ours | 0.3 | — | 1.9 | — | — | 0.7 (2 of 5 req.) |
| S̄ ratio, paper | 1.66 | 1.17 | 1.04 | 1.53 | 1.15 | 1.29 |
| S̄ ratio, ours | 0.22 | — | 1.17 | — | — | 0.51 (2 of 5 req.) |
| S̄ ratio, ours, failures counted at 200 | 0.16 | 0.39 | 1.17 | — | 0.66 | 0.47 (4 of 5 req.) |
| paired Wilcoxon p (iterations), ours | 0.000 | 0.001 | 0.780 | — | 0.003 | |

Notes on the ratio rows:
- S̄ follows the paper: it averages falsified trials only. That is harmless at the paper's 20/20 success rates, but with unequal success rates it favours the method that fails more often.
- 'Failures counted at 200' averages all trials, with unfalsified trials at the 200-iteration cap (a restricted mean, a lower bound for a method that fails).
- Wilcoxon: two-sided signed-rank test on paired per-trial iteration counts, unfalsified trials at 200.

'—' = no ratio (a method falsified no trial of that requirement); the geometric mean then covers only the requirements shown.

## RTAMT re-checks of language claims (D9) `[ours]`

A language method claims a falsifier when the signal lies in a box of the given L(¬φ) (Dist > 0); the claim is accepted only if RTAMT gives ρ < 0. A rejected claim is a satisfying signal that the approximate language puts in L(¬φ). Records written before the `validation_rejections` counter existed give the count exactly for SMuRF (re-checks − 1 per falsified trial) and as bounds for PROF (1 to j boxes can succeed in the final round).

| Req | Method | trials | re-checks per trial (mean) | rejected claims, total | trials with a rejected claim |
|---|---|---|---|---|---|
| phi1 | PROF | 20 | 201.0 | 4020 | 20 |
| phi1 | SMuRF | 20 | 202.1 | 4040 | 20 |
| phi2 | PROF | 20 | 0.0 | 0 | 0 |
| phi2 | SMuRF | 20 | 0.0 | 0 | 0 |
| phi3 | PROF | 20 | 1.9 | 0–18 | 0–9 |
| phi3 | SMuRF | 20 | 1.0 | 0 | 0 |
| phi4 | PROF | 0 | — | — | — |
| phi4 | SMuRF | 0 | — | — | — |
| phi5 | PROF | 20 | 0.0 | 0 | 0 |
| phi5 | SMuRF | 20 | 0.0 | 0 | 0 |

