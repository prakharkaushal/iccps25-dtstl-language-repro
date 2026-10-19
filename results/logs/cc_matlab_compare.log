# Python Chasing Cars port vs the official Simulink model `[ours]`

200 random inputs (results/matlab/cc_inputs.csv, seed 99), positions y1..y5 at t = 0, 10, …, 100 s. MATLAB run details: results/matlab/cc_outputs_simulink_meta.txt, results/matlab/cc_outputs_simulink_step_tol1e-10_meta.txt, results/matlab/cc_outputs_simulink_step_tol1e-6_meta.txt, results/matlab/falsifiers_main_simulink_meta.txt, results/matlab/falsifiers_main_simulink_step_tol1e-10_meta.txt, results/matlab/falsifiers_main_simulink_step_tol1e-6_meta.txt.

Simulink settings:
- (a) ARCH input convention (a 0.01 s ramp at every input switch) and the model's own solver settings (VariableStepAuto, RelTol 1e-3, AbsTol 1e-5, MinStep 0.01 s): the benchmark as usually run
- (b) exactly piecewise-constant inputs (as the port) and RelTol = AbsTol = 1e-6 requested; the model's MinStep of 0.01 s limits the accuracy reached at the input switches (Simulink warns; effective tolerances in results/logs/cc_simulink_*step_tol1e-6.log)
- (c) exactly piecewise-constant inputs, RelTol = AbsTol = 1e-10 and MinStep auto (overriding the model's 0.01 s)

## Random inputs, Simulink setting (a)

| car | max abs diff (m) | median | 95th percentile |
|---|---|---|---|
| 1 | 0.3076 | 0.009633 | 0.07226 |
| 2 | 1.522 | 0.02161 | 0.1844 |
| 3 | 1.245 | 0.01985 | 0.177 |
| 4 | 1.042 | 0.01843 | 0.1645 |
| 5 | 1.186 | 0.01588 | 0.1583 |

| requirement | verdict agreement (violated iff ρ < −1e-06) | boundary cases |ρ| ≤ 1e-06 (Python / Simulink) | max abs robustness diff | median |
|---|---|---|---|---|
| phi1 | 100.00 % | 0 / 0 | 1.042 | 0.00295 |
| phi2 | 100.00 % | 4 / 4 | 0.5389 | 0.0101 |
| phi3 | 100.00 % | 0 / 0 | 1.042 | 0.00286 |
| phi4 | 100.00 % | 0 / 0 | 1.042 | 0.00286 |
| phi5 | 100.00 % | 4 / 4 | 0.3795 | 0.00685 |

## Random inputs, Simulink setting (b)

| car | max abs diff (m) | median | 95th percentile |
|---|---|---|---|
| 1 | 0.01369 | 0.0007949 | 0.005119 |
| 2 | 0.05349 | 0.001861 | 0.01766 |
| 3 | 0.05032 | 0.001741 | 0.01736 |
| 4 | 0.0596 | 0.001503 | 0.01649 |
| 5 | 0.04755 | 0.00133 | 0.01557 |

| requirement | verdict agreement (violated iff ρ < −1e-06) | boundary cases |ρ| ≤ 1e-06 (Python / Simulink) | max abs robustness diff | median |
|---|---|---|---|---|
| phi1 | 100.00 % | 0 / 0 | 0.04936 | 0.000213 |
| phi2 | 100.00 % | 4 / 4 | 0.04487 | 0.000978 |
| phi3 | 100.00 % | 0 / 0 | 0.04936 | 0.000211 |
| phi4 | 100.00 % | 0 / 0 | 0.04936 | 0.000211 |
| phi5 | 100.00 % | 4 / 4 | 0.04102 | 0.000841 |

## Random inputs, Simulink setting (c)

| car | max abs diff (m) | median | 95th percentile |
|---|---|---|---|
| 1 | 1.291e-07 | 1.903e-09 | 2.528e-08 |
| 2 | 6.712e-07 | 5.302e-09 | 4.82e-08 |
| 3 | 6.447e-07 | 4.729e-09 | 4.696e-08 |
| 4 | 6.359e-07 | 4.456e-09 | 4.693e-08 |
| 5 | 6.017e-07 | 4.134e-09 | 4.466e-08 |

| requirement | verdict agreement (violated iff ρ < −1e-06) | boundary cases |ρ| ≤ 1e-06 (Python / Simulink) | max abs robustness diff | median |
|---|---|---|---|---|
| phi1 | 100.00 % | 0 / 0 | 1.077e-06 | 5.84e-10 |
| phi2 | 100.00 % | 4 / 4 | 1.117e-07 | 1.75e-09 |
| phi3 | 100.00 % | 0 / 0 | 1.077e-06 | 5.76e-10 |
| phi4 | 100.00 % | 0 / 0 | 1.077e-06 | 5.76e-10 |
| phi5 | 100.00 % | 4 / 4 | 7.783e-08 | 1.5e-09 |

## Lead car: where does the difference come from? `[ours]`

Car 1 never switches mode, so its exact trajectory can be computed to high accuracy here (DOP853, rtol = atol = 1e-12) under both input conventions.

| comparison (car 1, all samples) | max abs diff (m) | median | 95th percentile |
|---|---|---|---|
| port vs exact-step reference (accuracy of the port) | 3.33e-10 | 1e-11 | 7.36e-11 |
| Simulink (a) vs ARCH-ramp reference (Simulink's integration error at the model's tolerances) | 0.307 | 0.00875 | 0.0635 |
| exact-step vs ARCH-ramp reference (effect of the input convention) | 0.0613 | 0.00321 | 0.0267 |
| Simulink (a) vs port (observed) | 0.308 | 0.00963 | 0.0723 |

## Do the port's falsifiers falsify the Simulink model? (run `main`) `[ours]`

Every falsifying input found on the port in `results/raw/falsification/main/` (Tables 2–3, exact language), simulated on Simulink with settings (a), (b), (c) (defined above); ρ = robustness of φ on x = y5 − y4 (equals RTAMT).

| Req | Method | falsifiers | also falsify Simulink (a) | also falsify Simulink (b) | also falsify Simulink (c) | median ρ port | max abs ρ diff (a) | max abs ρ diff (b) | max abs ρ diff (c) |
|---|---|---|---|---|---|---|---|---|---|
| phi1 | PBO-RTAMT | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -22.1 | 0.532 | 0.0337 | 7.17e-07 |
| phi1 | PROF | 9 | 9 (100 %) | 9 (100 %) | 9 (100 %) | -1.48 | 0.0144 | 0.00264 | 2.8e-09 |
| phi1 | SBO-RTAMT | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -19.6 | 0.316 | 0.0275 | 1.44e-07 |
| phi1 | SMuRF | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -19.8 | 1.66 | 0.0186 | 1.91e-07 |
| phi2 | PBO-RTAMT | 19 | 16 (84 %) | 19 (100 %) | 19 (100 %) | -0.024 | 0.281 | 0.00169 | 6.07e-09 |
| phi2 | PROF | 14 | 13 (93 %) | 14 (100 %) | 14 (100 %) | -0.0225 | 0.0312 | 0.000715 | 6.06e-09 |
| phi2 | SBO-RTAMT | 15 | 12 (80 %) | 15 (100 %) | 15 (100 %) | -0.0171 | 0.133 | 0.00196 | 6.39e-09 |
| phi2 | SMuRF | 10 | 8 (80 %) | 10 (100 %) | 10 (100 %) | -0.035 | 0.0387 | 0.00123 | 2.03e-09 |
| phi3 | PBO-RTAMT | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -0.98 | 0.129 | 0.0136 | 1.3e-08 |
| phi3 | PROF | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -0.9 | 0.0774 | 0.00904 | 1.97e-08 |
| phi3 | SBO-RTAMT | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -0.994 | 0.16 | 0.0031 | 1.42e-08 |
| phi3 | SMuRF | 19 | 19 (100 %) | 19 (100 %) | 19 (100 %) | -1.27 | 0.0505 | 0.00966 | 7.27e-09 |
| phi4 | PBO-RTAMT | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -0.298 | 0.053 | 0.0111 | 8.6e-09 |
| phi4 | PROF | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -0.237 | 0.164 | 0.00779 | 1.31e-08 |
| phi4 | SBO-RTAMT | 19 | 19 (100 %) | 19 (100 %) | 19 (100 %) | -0.28 | 0.0292 | 0.00708 | 8.17e-09 |
| phi4 | SMuRF | 20 | 20 (100 %) | 20 (100 %) | 20 (100 %) | -0.293 | 0.132 | 0.00865 | 5.73e-09 |
| phi5 | PBO-RTAMT | 18 | 17 (94 %) | 18 (100 %) | 18 (100 %) | -0.0186 | 0.0963 | 0.00343 | 6.08e-09 |
| phi5 | PROF | 14 | 11 (79 %) | 13 (93 %) | 14 (100 %) | -0.0105 | 0.276 | 0.0512 | 4.06e-08 |
| phi5 | SBO-RTAMT | 11 | 8 (73 %) | 11 (100 %) | 11 (100 %) | -0.0174 | 0.448 | 0.00361 | 3.97e-09 |
| phi5 | SMuRF | 10 | 10 (100 %) | 10 (100 %) | 10 (100 %) | -0.0141 | 0.0112 | 0.00182 | 1.79e-09 |

Overall, falsifiers that also falsify the Simulink model: (a) 322 of 338 (95.3 %); (b) 337 of 338 (99.7 %); (c) 338 of 338 (100.0 %).
- (a): 16 do not carry over; their robustness on the port is between -0.0572 and -0.000576.
- (b): 1 falsifier does not carry over. phi5 PROF trial 10: ρ port -0.04718, Simulink 0.00402.

