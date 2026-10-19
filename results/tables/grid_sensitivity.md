# Violation rate (% of uniform inputs with ρ < 0) under three time grids

`[ours]` N = 2000 uniform inputs (seed 12345); `[paper]` Table 1 'Satisfaction Ratios' (our interpretation: share inside L(¬φ), see DEVIATIONS.md B5).

| Grid | φ1 | φ2 | φ3 | φ4 | φ5 |
|---|---|---|---|---|---|
| [paper] | 7.08 | 1.82 | 3.84 | 0.87 | 7.08 |
| D1: 11 samples t=0..100 s (used) | 0.50 | 0.95 | 5.50 | 1.00 | 0.55 |
| 10 samples t=0..90 s (truncated windows) | 0.50 | 1.90 | 5.50 | 1.00 | 0.55 |
| 1 s grid, 101 samples | 4.25 | 0.00 | 17.10 | 4.95 | 19.05 |
