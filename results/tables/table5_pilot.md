# Table 5 — LangControl on the UAV model (E5)

- Status: **PILOT (20 of 1000 replications)**
- Source: `results/raw/control/pilot/` (records.jsonl, meta.json)
- Run created 2026-10-18T15:37:03; 1 session(s), source sha256 `f9e4f386fa0a`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

P̄ = mean number of iterations until a feasible signal over successful replications (one iteration = one Track call for LCW, one lock-step round of all processes for LCP). Our tracker, UAV parameters, sampling, projection and limits are our own choices (the paper gives none), so this is a re-implementation (L3), not a reproduction of the paper's numbers.

| Formula | P̄ LCW [paper] | P̄ LCW [ours] | failures LCW [ours] | P̄ LCP [paper] | P̄ LCP [ours] | failures LCP [ours] | LCP processes [ours] | Track calls per replication LCW / LCP [ours] | boxes in L(φ) [ours] | M, K [ours] |
|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | 1.88423 | 59.95 | 0/20 | 1 | 1.00 | 0/20 | 64 | 60.0 / 64.0 | 2048 | 50, 10 |
| phi2 | 4.80769 | 57.85 | 0/20 | 2.32152 | 3.60 | 0/20 | 8 | 57.9 / 28.8 | 8 | 50, 10 |
| phi3 | 1.25672 | 10.60 | 0/20 | 1 | 1.00 | 0/20 | 64 | 10.6 / 64.0 | 110 | 50, 10 |
| phi4 | 135.036 | 35.40 | 0/20 | 41.2362 | 1.20 | 0/20 | 36 | 35.4 / 43.2 | 36 | 50, 10 |
| phi5 | 4.27235 | — | 20/20 | 2.37237 | 139.05 | 0/20 | 64 | 561.0 / 8899.2 | 1073741824 | 50, 10 |
| phi6 | 6.31527 | 225.53 | 5/20 | 2.94731 | 174.75 | 8/20 | 1 | 309.4 / 329.2 | 1 | 50, 10 |
| phi7 | 206.935 | 37.05 | 0/20 | 89.7326 | 1.00 | 0/20 | 64 | 37.0 / 64.0 | 870 | 50, 10 |
| phi8 | 1965 | 216.25 | 12/20 | 488.345 | 22.30 | 0/20 | 64 | 423.1 / 1427.2 | 1000 | 50, 10 |

P̄ counts iterations (LCP: parallel rounds), as in the paper. In total tracking effort (all Track calls, failed replications included), LCP uses more than LCW on 7 of 8 formulas: its advantage is wall-clock time given enough processors, not total computation.
