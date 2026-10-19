# Tables 2 and 3 — falsification on Chasing Cars (E2/E3)

- Status: **FULL**
- Source: `results/raw/falsification/main/` (records.jsonl, meta.json)
- Language of ¬φ: **exact** (compiled exactly, DEVIATIONS A1)
- Run created 2026-10-18T16:04:10; 1 session(s), source sha256 `43806dbaefab`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

Columns: FR = falsified trials / trials; S̄ = mean iterations over falsified trials (± 95% t-CI); T̄_T = mean total monitoring time per falsified trial in ms on the critical path (parallel methods: slowest process per round); T̄_M = mean time per monitoring call in ms (one box for PROF, all boxes for SMuRF, one RTAMT evaluation for the baselines). Extra columns are ours only.

## Table 2: PBO-RTAMT vs PROF

| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | GP s/trial [ours] | wall s/trial [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | PBO-RTAMT | 20/20 | 20/20 | 12.50 | 9.95 ± 4.06 | 5.50 | 13.617 | 5.894 ± 3.522 | 1.107 | 0.1598 | 114 | 2.71 | 2.20 | 5.40 |
| phi1 | PROF | 20/20 | 9/20 | 11.30 | 42.67 ± 44.97 | 19.00 | 0.355 | 2.871 ± 3.041 | 0.034 | 0.0431 | 1426 | 35.09 | 47.41 | 136.38 |
| phi2 | PBO-RTAMT | 20/20 | 19/20 | 7.40 | 24.26 ± 19.45 | 11.00 | 12.484 | 9.570 ± 6.138 | 1.675 | 0.2237 | 269 | 5.37 | 7.48 | 17.74 |
| phi2 | PROF | 20/20 | 14/20 | 7.50 | 31.14 ± 25.48 | 17.00 | 0.484 | 2.336 ± 1.853 | 0.067 | 0.0414 | 659 | 14.66 | 19.38 | 52.95 |
| phi3 | PBO-RTAMT | 20/20 | 20/20 | 6.30 | 2.50 ± 1.34 | 2.00 | 11.785 | 3.880 ± 1.536 | 1.877 | 0.2538 | 72 | 1.95 | 2.03 | 4.35 |
| phi3 | PROF | 20/20 | 20/20 | 6.05 | 4.00 ± 3.04 | 2.00 | 2.294 | 1.421 ± 1.613 | 0.380 | 0.0293 | 113 | 3.12 | 2.84 | 6.89 |
| phi4 | PBO-RTAMT | 20/20 | 20/20 | 24.40 | 4.80 ± 2.63 | 3.00 | 44.700 | 12.406 ± 7.343 | 1.820 | 0.3515 | 135 | 4.55 | 4.81 | 10.30 |
| phi4 | PROF | 20/20 | 20/20 | 31.10 | 7.65 ± 2.92 | 6.00 | 0.672 | 3.730 ± 1.162 | 0.031 | 0.0458 | 212 | 6.71 | 6.43 | 15.08 |
| phi5 | PBO-RTAMT | 20/20 | 18/20 | 7.40 | 28.33 ± 22.17 | 13.00 | 11.242 | 26.611 ± 19.960 | 1.540 | 0.3423 | 324 | 8.54 | 14.42 | 32.24 |
| phi5 | PROF | 20/20 | 14/20 | 7.90 | 89.21 ± 33.15 | 81.00 | 0.468 | 13.761 ± 4.954 | 0.063 | 0.0619 | 862 | 25.06 | 33.81 | 93.09 |

Speedups PBO-RTAMT / PROF `[derived]` (ratio of means; > 1 favours PROF):

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| T̄_T ratio, paper | 38.4 | 25.8 | 5.1 | 66.5 | 24.0 | 24.1 |
| T̄_T ratio, ours | 2.1 | 4.1 | 2.7 | 3.3 | 1.9 | 2.7 |
| S̄ ratio, paper | 1.11 | 0.99 | 1.04 | 0.78 | 0.94 | 0.96 |
| S̄ ratio, ours | 0.23 | 0.78 | 0.62 | 0.63 | 0.32 | 0.47 |
| S̄ ratio, ours, failures counted at 200 | 0.08 | 0.40 | 0.62 | 0.63 | 0.37 | 0.34 |
| paired Wilcoxon p (iterations), ours | 0.000 | 0.084 | 0.281 | 0.047 | 0.003 | |

## Table 3: SBO-RTAMT vs SMuRF

| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | GP s/trial [ours] | wall s/trial [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | SBO-RTAMT | 20/20 | 20/20 | 27.90 | 31.15 ± 16.33 | 12.00 | 30.438 | 6.572 ± 2.911 | 1.207 | 0.1883 | 36 | 0.81 | 0.61 | 1.68 |
| phi1 | SMuRF | 20/20 | 20/20 | 16.85 | 22.30 ± 13.05 | 15.00 | 2.789 | 4.265 ± 2.045 | 0.203 | 0.1755 | 27 | 0.66 | 3.69 | 9.24 |
| phi2 | SBO-RTAMT | 20/20 | 15/20 | 15.10 | 38.40 ± 18.03 | 35.00 | 19.245 | 11.561 ± 4.891 | 1.272 | 0.2626 | 84 | 1.86 | 2.31 | 6.04 |
| phi2 | SMuRF | 20/20 | 10/20 | 12.95 | 45.00 ± 26.11 | 42.50 | 3.055 | 7.507 ± 3.802 | 0.324 | 0.1441 | 128 | 2.27 | 29.58 | 71.57 |
| phi3 | SBO-RTAMT | 20/20 | 20/20 | 19.45 | 13.95 ± 13.07 | 3.50 | 38.564 | 7.475 ± 5.454 | 1.975 | 0.3669 | 19 | 0.52 | 0.40 | 1.10 |
| phi3 | SMuRF | 20/20 | 19/20 | 18.65 | 7.63 ± 6.45 | 3.00 | 11.150 | 1.851 ± 1.030 | 0.631 | 0.1422 | 22 | 0.65 | 15.16 | 30.25 |
| phi4 | SBO-RTAMT | 20/20 | 19/20 | 39.10 | 20.53 ± 9.21 | 13.00 | 70.265 | 12.367 ± 4.768 | 1.808 | 0.4592 | 34 | 1.20 | 1.11 | 2.87 |
| phi4 | SMuRF | 20/20 | 20/20 | 25.50 | 18.10 ± 13.12 | 7.00 | 4.121 | 4.240 ± 2.335 | 0.186 | 0.1937 | 23 | 0.78 | 11.48 | 23.24 |
| phi5 | SBO-RTAMT | 20/20 | 11/20 | 13.40 | 75.73 ± 38.29 | 54.00 | 23.811 | 28.797 ± 13.118 | 1.701 | 0.3809 | 137 | 3.77 | 6.03 | 14.94 |
| phi5 | SMuRF | 20/20 | 10/20 | 11.65 | 67.40 ± 45.10 | 49.00 | 3.254 | 12.461 ± 7.704 | 0.353 | 0.1790 | 139 | 3.45 | 36.41 | 97.33 |

Speedups SBO-RTAMT / SMuRF `[derived]` (ratio of means; > 1 favours SMuRF):

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| T̄_T ratio, paper | 10.9 | 6.3 | 3.5 | 17.1 | 7.3 | 7.8 |
| T̄_T ratio, ours | 1.5 | 1.5 | 4.0 | 2.9 | 2.3 | 2.3 |
| S̄ ratio, paper | 1.66 | 1.17 | 1.04 | 1.53 | 1.15 | 1.29 |
| S̄ ratio, ours | 1.40 | 0.85 | 1.83 | 1.13 | 1.12 | 1.23 |
| S̄ ratio, ours, failures counted at 200 | 1.40 | 0.64 | 0.81 | 1.63 | 0.98 | 1.03 |
| paired Wilcoxon p (iterations), ours | 0.314 | 0.102 | 0.755 | 0.017 | 0.955 | |

Notes on the ratio rows:
- S̄ follows the paper: it averages falsified trials only. That is harmless at the paper's 20/20 success rates, but with unequal success rates it favours the method that fails more often.
- 'Failures counted at 200' averages all trials, with unfalsified trials at the 200-iteration cap (a restricted mean, a lower bound for a method that fails).
- Wilcoxon: two-sided signed-rank test on paired per-trial iteration counts, unfalsified trials at 200.

