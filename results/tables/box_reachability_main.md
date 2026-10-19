# Reachability of the boxes of L(¬φ) on the Chasing Cars model `[ours]`

Signals: 10000 uniform inputs from E1 run `main`; PROF falsifiers from run `main`; modified PROF from run `main`.

| Req | boxes j | boxes entered by ≥1 random signal | PROF falsified trials | distinct falsifying boxes (PROF) | falsifying box → trials | PBO-RTAMT falsified trials | never falsified by modified PROF (mean) |
|---|---|---|---|---|---|---|---|
| phi1 | 11 | 2 (indices [3, 4]) | 9/20 | 1 | {3: 9} | 20/20 | 10.5 |
| phi2 | 8 | 5 (indices [3, 4, 5, 6, 7]) | 14/20 | 6 | {2: 1, 3: 2, 4: 2, 5: 3, 6: 2, 7: 4} | 19/20 | 6.7 |
| phi3 | 27 | 12 (indices [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15]) | 20/20 | 5 | {2: 13, 4: 1, 5: 1, 6: 4, 9: 1} | 20/20 | 22.5 |
| phi4 | 27 | 6 (indices [2, 4, 5, 6, 7, 9]) | 20/20 | 6 | {2: 11, 4: 2, 5: 1, 6: 4, 7: 1, 9: 1} | 20/20 | 22.4 |
| phi5 | 7 | 4 (indices [3, 4, 5, 6]) | 14/20 | 3 | {3: 1, 5: 5, 6: 8} | 18/20 | 5.75 |

Reading: a PROF process is tied to one box; processes on boxes that the system cannot enter (e.g. φ1's box 'x(0) > 40' while x(0) = 10 always) cannot succeed, whereas every PBO-RTAMT process optimises the full robustness. The paper's FindBox languages had different (fewer for φ1, φ2, φ4) boxes.
