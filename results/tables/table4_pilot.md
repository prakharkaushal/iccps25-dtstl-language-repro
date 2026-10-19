# Table 4 — box difficulty (E4)

- Status: **PILOT (1 of 20 trials)**
- Source: `results/raw/table4/pilot/` (records.jsonl, meta.json)
- Run created 2026-10-18T15:43:00; 1 session(s), source sha256 `43806dbaefab`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

S̄_min / S̄_max: modified PROF (runs until every box of L(¬φ) is falsified or 200 rounds), averaged over **all** trials: S_min counts 200 when no box was falsified, S_max counts 200 when at least one box never was (so S̄_min differs from Table 2's PROF S̄, which averages falsified trials only). FR, S̄, T̄_T, T̄_M: sequential single-box BO (random box order, fresh BO per box, ≤ 200 iterations per box); S̄ and T̄_T over falsified trials.

| Req | FR [paper] | FR [ours] | S̄_min [paper] | S̄_min [ours] | S̄_max [paper] | S̄_max [ours] | S̄ [paper] | S̄ [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | boxes never falsified (mean) [ours] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | 20/20 | 1/1 | 11.3 | 23.00 | 47.7 | 200.00 | 31.8 | 1872.00 | 5.009 | 110.122 | 1.67 | 0.0573 | 10.00 |
| phi2 | 20/20 | 1/1 | 7.5 | 11.00 | 37.1 | 200.00 | 19.57 | 337.00 | 4.831 | 21.850 | 0.69 | 0.0630 | 7.00 |
| phi3 | 20/20 | 1/1 | 6.05 | 4.00 | 200 | 200.00 | 46.35 | 821.00 | 24.925 | 58.002 | 0.293 | 0.0686 | 21.00 |
| phi4 | 20/20 | 1/1 | 31.1 | 10.00 | 63.4 | 200.00 | 25.5 | 242.00 | 4.121 | 16.089 | 0.186 | 0.0638 | 21.00 |
| phi5 | 20/20 | 1/1 | 7.9 | 57.00 | 37.7 | 200.00 | 19.7 | 277.00 | 5.023 | 18.485 | 0.718 | 0.0644 | 5.00 |

Consistency `[ours]`: S_min (modified PROF) equals PROF's iteration count in 5/5 matched (spec, trial) pairs of run `pilot` (same seeds; the paper's Table 4 S̄_min also equals its Table 2 PROF S̄).
