# Table 4 — box difficulty (E4)

- Status: **FULL**
- Source: `results/raw/table4/main/` (records.jsonl, meta.json)
- Run created 2026-10-18T16:34:12; 1 session(s), source sha256 `43806dbaefab`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

S̄_min / S̄_max: modified PROF (runs until every box of L(¬φ) is falsified or 200 rounds), averaged over **all** trials: S_min counts 200 when no box was falsified, S_max counts 200 when at least one box never was (so S̄_min differs from Table 2's PROF S̄, which averages falsified trials only). FR, S̄, T̄_T, T̄_M: sequential single-box BO (random box order, fresh BO per box, ≤ 200 iterations per box); S̄ and T̄_T over falsified trials.

| Req | FR [paper] | FR [ours] | S̄_min [paper] | S̄_min [ours] | S̄_max [paper] | S̄_max [ours] | S̄ [paper] | S̄ [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | boxes never falsified (mean) [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | 20/20 | 8/20 | 11.3 | 129.20 ± 41.57 | 47.7 | 200.00 ± 0.00 | 31.8 | 1084.25 ± 529.75 | 5.009 | 78.813 ± 37.058 | 1.67 | 0.0700 | 10.50 |
| phi2 | 20/20 | 17/20 | 7.5 | 81.80 ± 40.89 | 37.1 | 200.00 ± 0.00 | 19.57 | 594.35 ± 247.90 | 4.831 | 41.141 ± 16.819 | 0.69 | 0.0707 | 6.70 |
| phi3 | 20/20 | 20/20 | 6.05 | 4.00 ± 3.04 | 200 | 200.00 ± 0.00 | 46.35 | 1112.60 ± 379.54 | 24.925 | 73.448 ± 26.049 | 0.293 | 0.0608 | 22.50 |
| phi4 | 20/20 | 20/20 | 31.1 | 7.65 ± 2.92 | 63.4 | 200.00 ± 0.00 | 25.5 | 883.45 ± 449.64 | 4.121 | 61.829 ± 31.135 | 0.186 | 0.0711 | 22.40 |
| phi5 | 20/20 | 14/20 | 7.9 | 122.45 ± 32.99 | 37.7 | 200.00 ± 0.00 | 19.7 | 746.64 ± 260.93 | 5.023 | 52.097 ± 17.449 | 0.718 | 0.0704 | 5.75 |

Consistency `[ours]`: S_min (modified PROF) equals PROF's iteration count in 77/77 matched (spec, trial) pairs of run `main` (same seeds; the paper's Table 4 S̄_min also equals its Table 2 PROF S̄).
