# E6 — robustness-BO control baseline vs LangControl (paper Sec. 4.3, no table in the paper)

- Status: **complete at reduced scale (50 replications per objective, D24) — new evidence for a claim the paper states without data**
- Source: `results/raw/control_bo/main/` (records.jsonl, meta.json)
- Run created 2026-10-18T20:08:14; 1 session(s), source sha256 `06b563d0fb3e`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

Paper claim (text only): 'Compared to LCW, we observe that BO consistently requires 3-7x the number of iterations.' `[paper]`. BO: 50 replications per objective, ≤ 205 Track calls (initial samples included); LCW: E5 records (one iteration = one Track call). Because BO is capped, both methods are compared within the same budget of 205 Track calls.

| Formula | BO success ≤ 205 [ours] | LCW success ≤ 205 [ours] | BO mean iterations given success [ours] | LCW mean iterations given success ≤ 205 [ours] | ratio BO/LCW `[derived]` | LCW P̄ (all, E5) [ours] | BO median best ρ when failing [ours] |
|---|---|---|---|---|---|---|---|
| phi1 | 48/50 (96 %) | 97.7 % | 62.23 | 51.60 | 1.21 | 56.60 | -0.16 |
| phi2 | 50/50 (100 %) | 97.2 % | 38.28 | 53.50 | 0.72 | 59.29 | — |
| phi3 | 50/50 (100 %) | 100.0 % | 2.58 | 10.63 | 0.24 | 10.63 | — |
| phi4 | 50/50 (100 %) | 99.8 % | 22.88 | 30.14 | 0.76 | 30.73 | — |
| phi5 | 6/50 (12 %) | 0.7 % | 116.17 | 106.86 | 1.09 | 2672.63 | -3.31 |
| phi6 | 1/50 (2 %) | 30.8 % | 47.00 | 95.94 | 0.49 | 580.87 | -3.30 |
| phi7 | 50/50 (100 %) | 99.6 % | 4.46 | 35.30 | 0.13 | 36.06 | — |
| phi8 | 47/50 (94 %) | 20.5 % | 49.74 | 92.60 | 0.54 | 949.81 | -1.29 |

Geometric mean of the BO/LCW iteration ratio over formulas where both succeed `[derived]`: 0.52 (8 formulas); over formulas where both have ≥ 5 successes within the budget: 0.53 (7 formulas). Paper claim: 3–7 (BO needs 3–7× the iterations of LCW). Values < 1 mean BO needed fewer iterations.
