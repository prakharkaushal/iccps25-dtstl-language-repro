# Tables 2 and 3 — falsification on Chasing Cars (E2/E3)

- Status: **PILOT (1 of 20 trials)**
- Source: `results/raw/falsification/pilot/` (records.jsonl, meta.json)
- Language of ¬φ: **exact** (compiled exactly, DEVIATIONS A1)
- Run created 2026-10-18T15:25:45; 1 session(s), source sha256 `437ea1b43816`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

Columns: FR = falsified trials / trials; S̄ = mean iterations over falsified trials (± 95% t-CI); T̄_T = mean total monitoring time per falsified trial in ms on the critical path (parallel methods: slowest process per round); T̄_M = mean time per monitoring call in ms (one box for PROF, all boxes for SMuRF, one RTAMT evaluation for the baselines). Extra columns are ours only.

## Table 2: PBO-RTAMT vs PROF

| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | GP s/trial [ours] | wall s/trial [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | PBO-RTAMT | 20/20 | 1/1 | 12.50 | 10.00 | 10.00 | 13.617 | 7.370 | 1.107 | 0.1999 | 115 | 3.75 | 3.44 | 7.88 |
| phi1 | PROF | 20/20 | 1/1 | 11.30 | 23.00 | 23.00 | 0.355 | 5.276 | 0.034 | 0.0534 | 258 | 8.29 | 7.00 | 17.91 |
| phi2 | PBO-RTAMT | 20/20 | 1/1 | 7.40 | 176.00 | 176.00 | 12.484 | 87.066 | 1.675 | 0.2644 | 1413 | 32.42 | 35.98 | 105.66 |
| phi2 | PROF | 20/20 | 1/1 | 7.50 | 11.00 | 11.00 | 0.484 | 2.847 | 0.067 | 0.0505 | 93 | 2.51 | 2.35 | 5.52 |
| phi3 | PBO-RTAMT | 20/20 | 1/1 | 6.30 | 1.00 | 1.00 | 11.785 | 5.213 | 1.877 | 0.2681 | 32 | 1.03 | 1.79 | 3.03 |
| phi3 | PROF | 20/20 | 1/1 | 6.05 | 4.00 | 4.00 | 2.294 | 2.372 | 0.380 | 0.0389 | 113 | 3.43 | 4.08 | 8.15 |
| phi4 | PBO-RTAMT | 20/20 | 1/1 | 24.40 | 2.00 | 2.00 | 44.700 | 5.538 | 1.820 | 0.2708 | 59 | 1.95 | 2.97 | 5.30 |
| phi4 | PROF | 20/20 | 1/1 | 31.10 | 10.00 | 10.00 | 0.672 | 2.046 | 0.031 | 0.0406 | 275 | 8.27 | 7.90 | 17.90 |
| phi5 | PBO-RTAMT | 20/20 | 1/1 | 7.40 | 13.00 | 13.00 | 11.242 | 18.940 | 1.540 | 0.4115 | 96 | 3.27 | 3.04 | 7.26 |
| phi5 | PROF | 20/20 | 1/1 | 7.90 | 57.00 | 57.00 | 0.468 | 3.920 | 0.063 | 0.0417 | 404 | 8.88 | 7.37 | 21.04 |

Speedups PBO-RTAMT / PROF `[derived]` (ratio of means; > 1 favours PROF):

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| T̄_T ratio, paper | 38.4 | 25.8 | 5.1 | 66.5 | 24.0 | 24.1 |
| T̄_T ratio, ours | 1.4 | 30.6 | 2.2 | 2.7 | 4.8 | 4.1 |
| S̄ ratio, paper | 1.11 | 0.99 | 1.04 | 0.78 | 0.94 | 0.96 |
| S̄ ratio, ours | 0.43 | 16.00 | 0.25 | 0.20 | 0.23 | 0.60 |
| S̄ ratio, ours, failures counted at 200 | 0.43 | 16.00 | 0.25 | 0.20 | 0.23 | 0.60 |
| paired Wilcoxon p (iterations), ours | — | — | — | — | — | |

## Table 3: SBO-RTAMT vs SMuRF

| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | GP s/trial [ours] | wall s/trial [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | SBO-RTAMT | 20/20 | 1/1 | 27.90 | 103.00 | 103.00 | 30.438 | 23.494 | 1.207 | 0.2175 | 108 | 3.51 | 3.22 | 8.94 |
| phi1 | SMuRF | 20/20 | 1/1 | 16.85 | 127.00 | 127.00 | 2.789 | 21.841 | 0.203 | 0.1655 | 132 | 3.30 | 31.97 | 131.21 |
| phi2 | SBO-RTAMT | 20/20 | 0/1 | 15.10 | — | — | 19.245 | — | 1.272 | 0.3276 | 205 | 6.55 | 9.41 | 23.85 |
| phi2 | SMuRF | 20/20 | 0/1 | 12.95 | — | — | 3.055 | — | 0.324 | 0.1616 | 205 | 4.34 | 61.35 | 262.15 |
| phi3 | SBO-RTAMT | 20/20 | 1/1 | 19.45 | 19.00 | 19.00 | 38.564 | 9.005 | 1.975 | 0.3752 | 24 | 0.75 | 0.51 | 1.39 |
| phi3 | SMuRF | 20/20 | 1/1 | 18.65 | 2.00 | 2.00 | 11.150 | 1.010 | 0.631 | 0.1442 | 7 | 0.20 | 2.41 | 2.96 |
| phi4 | SBO-RTAMT | 20/20 | 1/1 | 39.10 | 13.00 | 13.00 | 70.265 | 8.775 | 1.808 | 0.4875 | 18 | 0.55 | 0.32 | 0.96 |
| phi4 | SMuRF | 20/20 | 1/1 | 25.50 | 50.00 | 50.00 | 4.121 | 9.736 | 0.186 | 0.1770 | 55 | 1.28 | 16.54 | 31.45 |
| phi5 | SBO-RTAMT | 20/20 | 1/1 | 13.40 | 5.00 | 5.00 | 23.811 | 3.818 | 1.701 | 0.3818 | 10 | 0.39 | 0.33 | 0.76 |
| phi5 | SMuRF | 20/20 | 1/1 | 11.65 | 111.00 | 111.00 | 3.254 | 13.588 | 0.353 | 0.1171 | 116 | 2.37 | 14.70 | 26.30 |

Speedups SBO-RTAMT / SMuRF `[derived]` (ratio of means; > 1 favours SMuRF):

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| T̄_T ratio, paper | 10.9 | 6.3 | 3.5 | 17.1 | 7.3 | 7.8 |
| T̄_T ratio, ours | 1.1 | — | 8.9 | 0.9 | 0.3 | 1.2 (4 of 5 req.) |
| S̄ ratio, paper | 1.66 | 1.17 | 1.04 | 1.53 | 1.15 | 1.29 |
| S̄ ratio, ours | 0.81 | — | 9.50 | 0.26 | 0.05 | 0.55 (4 of 5 req.) |
| S̄ ratio, ours, failures counted at 200 | 0.81 | 1.00 | 9.50 | 0.26 | 0.05 | 0.62 |
| paired Wilcoxon p (iterations), ours | — | — | — | — | — | |

Notes on the ratio rows:
- S̄ follows the paper: it averages falsified trials only. That is harmless at the paper's 20/20 success rates, but with unequal success rates it favours the method that fails more often.
- 'Failures counted at 200' averages all trials, with unfalsified trials at the 200-iteration cap (a restricted mean, a lower bound for a method that fails).
- Wilcoxon: two-sided signed-rank test on paired per-trial iteration counts, unfalsified trials at 200.

'—' = no ratio (a method falsified no trial of that requirement); the geometric mean then covers only the requirements shown.

