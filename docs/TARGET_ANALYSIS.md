# Target Paper Analysis — Falsification & Control with the DT-STL Language Set (ICCPS '25)

Phase 2 deliverable · 2026-10-18 · no implementation yet. The proposed plan is in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

## Sources and labels

| Tag | Meaning |
|---|---|
| **[T p.N]** | `Paper.pdf`, PDF page N of 10. Equations and Tables 1–5 were read from 300-dpi renders, because text extraction drops the math symbols. Every reported number is transcribed in [analysis/target_paper/paper_reported_values.py](../analysis/target_paper/paper_reported_values.py). |
| **[T-D]** | Arithmetic on the paper's own numbers. Output is in `analysis/target_paper/out_paper_derived.txt`. These are **not** results we produced. |
| **[ARCH19]** | ARCH-COMP 2019 Falsification report (Ernst et al.), p.6. Used only to compare the CC requirements. |
| **[R §x]** | [REFERENCE_ANALYSIS.md](REFERENCE_ANALYSIS.md). |
| *(ext.)* | General knowledge, not verified in this session. |
| **Paper claim** / **Our decision** | Used to keep what the paper states separate from what we propose. |

**Supplementary material.** None. `Paper.pdf` is the only target-paper file in `target_project/`, and it has no embedded attachments.

**Code availability.**

- Searching found no public code for this paper.
- The paper links only the language-generation code of its ref. [5]: `github.com/Chris-amV/FindBox`. That is a Python repo with 21 commits, **no license**, and none of the paper's falsification or control code.
- Ref. [4] is a "private communication" with the first author, so the authors are a plausible source for the missing details (§9.4).

---

## 1. Research problem and contributions

**Problem [T p.1–2].**

- *Falsification:* find an input **u** such that the system output **x** = M(**u**) violates a DT-STL formula φ.
- *Control:* find an input whose output satisfies φ.
- State-of-the-art tools optimise the robustness ρ_φ, using it only as an oracle. The paper asks whether an **explicit representation of the language** L(φ) (all satisfying signals, approximated as a union of boxes by ref. [5]) makes both tasks faster. That would amortise the offline cost of computing the language.

**Contributions as claimed [T p.1–2].**

1. Adding the distance of a candidate signal to *each* polytope of the language into falsification "accelerate[s] falsification runtime by up to 100x, and generally reduce[s] the number of tests". The abstract states "10x to 100x speedups".
2. Treating each polytope as its own objective yields a satisfying control signal "in as little as two iterations".
3. The algorithms are trivially parallelisable.

---

## 2. Method

### 2.1 Formal background [T p.2–3]

- **Notation.** The distance between signals is `‖x−y‖_∞ := max_t ‖x(t)−y(t)‖₂`. A *box* is `[a₁,b₁]×…×[a_N,b_N]`.
- **DT-STL (Def. 2.1).** Syntax: `φ ::= ⊤ | p | ¬φ | φ∧φ | φ U_I φ`, with I an integer interval. An atom holds iff **μ_p(x(t)) ≤ 0**. ◇, □ and ∨ are derived.
- **Language.** `L(φ) := {x ∈ X^ℕ | (x,0) ⊨ φ}`. It depends only on the formula, not on any system.
- **Robustness.** ρ_φ : X^N → ℝ.
  - **Thm 2.2:** if ρ_φ(x) > 0, then x ∈ L(φ) and ρ_φ(x) < dist(x, ∂L(φ)); if ρ_φ(x) < 0, then x ∉ L(φ) and ρ_φ(x) > −dist(x, L(φ)).
  - **Eq. (1), signed distance:** `Dist(x,A) = dist(x,∂A)` if x ∈ A, and `−dist(x,A)` otherwise.
- **Thm 2.3 / Cor. 2.4.** Assume:
  1. the state space is a bounded box;
  2. the μ_p are affine;
  3. the horizon `hrz_φ` is finite.

  Then L(φ) is a union of polytopes in ℝ^{N·d}. For 1-D signals it is a **union of axis-aligned boxes in ℝ^{hrz_φ}**. The paper works only with 1-D signals and uses ref. [5]'s *approximation* of the language.
- **Falsification, Eq. (2).** `u* = argmin_u ρ_φ(x)`. If ρ < 0 at u*, then x violates φ. Robustness is computed with RTAMT [37].

### 2.2 Falsification with the language [T p.3–5]

- **Eq. (3).** `L(φ) = B^φ := ⋃_{k=1..j} b_k^φ`, and `X^ℕ = B^φ ∪ B^{¬φ}`.
- **Eq. (4).** Falsification becomes reaching *any* box of ¬φ: `u* = argmax_u Dist(x, b_k^{¬φ})`. **u** is a falsifier if `Dist > 0`.

**PROF: Parallelised Robustness Optimisation for Falsification (Alg. 1, Eq. 5).**

1. One independent Bayesian-optimisation (BO) loop runs **per box, in parallel**.
2. Each box starts from n₀ evaluated inputs, giving a dataset `D_k = {u_i, Dist(x_i, b_k^{¬φ})}`.
3. At each step it fits a GP surrogate, picks the next input by maximising Expected Improvement (EI, Eq. 5), simulates, and appends to `D_k`.
4. If any box reaches `Dist ≥ 0`, **all** boxes stop. Otherwise each box stops after n_BO iterations.

**SMuRF: Serialised Multi-Robustness Falsification (Alg. 2, Eqs. 6–7).**

1. Objective (Eq. 6): `u* = argmax_u max_k Dist(x, b_k^{¬φ})`.
2. All boxes are initialised from the same n₀ inputs.
3. Each iteration fits **one GP per box** and computes the MinBO expected improvement EI_k (Eq. 7, from ref. [34]). Here y* is the best distance over **all** D_k.
4. It picks `u* = argmax_k EI_k(u^k)`, simulates once, and appends `Dist(x*, b_k)` to **every** D_k.
5. It stops when `max_k Dist ≥ 0` or after n_MinBO iterations.

### 2.3 Control with the language [T p.7–8]

- **Setting.** A motion planner produces a reference x_ref, and a tracking controller follows it.
- **Eq. (13):** `u* = argmax_u ρ_φ(M_s(u))`, with a simplified model M_s. This is the robustness-based state of the art and is given as context only.

**LangControl (Alg. 3).**

1. Outer loop `m ≤ M`: sample `x_ref ← Sample(B)` "from the constraint set without replacement".
2. Inner loop `count ≤ K`:
   1. `x,u ← Track(x_ref)`.
   2. If `x ∈ B`, return x and u.
   3. Otherwise set `x_ref ← Projection(x, B)` and track again.
3. If no feasible signal is found within the limits, return ⊥.

There are two variants:

- **LCW:** B = L(φ), the whole language.
- **LCP:** B is a single box, and boxes are spread over processors. Each tracking result is checked against *any* box.

---

## 3. Data and experimental setup

There are **no datasets**; all data is simulated.

### 3.1 Falsification system: ARCH "Chasing Cars" (CC) [T p.5]

- Five cars. Car 1 is driven by **throttle** and **brake** ∈ [0,1]; cars 2–5 follow it using ref. [26]'s algorithm (Hu et al.). The outputs are positions y₁…y₅.
- **Input:** 10 control points per input, so **u ∈ [0,1]²⁰**.
- **Output:** horizon **100 s**, sampled at **0.1 Hz**, giving "10 time steps". The signal is **x := y₅ − y₄**, and "the language is a subset of ℝ¹⁰".
- The language is computed with FindBox [5]; falsification uses **PSY-TaLiRo** [51]; the baseline monitor is **RTAMT** [37].

### 3.2 Falsification requirements [T p.5, Eqs. 8–12] vs ARCH-COMP [ARCH19]

| Paper | Formula as printed | Official ARCH counterpart |
|---|---|---|
| φ₁ | □[0,100] (y₅−y₄ ≤ 40) | identical to CC1 |
| φ₂ | □[0,70] ◇[0,30] (y₅−y₄ ≥ 10) | CC2 uses ≥ **15** |
| φ₃ | □[0,80] ((□[0,20] y₅−y₄ ≤ 30) ∨ (◇[0,20] y₅−y₄ ≥ 35)) | CC3 uses **y₂−y₁ ≤ 20** ∨ y₅−y₄ ≥ **40** (2-D) |
| φ₄ | □[0,80] ((□[0,20] y₅−y₄ ≤ 32) ∨ (◇[0,20] y₅−y₄ ≥ 33)) | (variant of CC3) |
| φ₅ | □[0,65] ◇[0,30] □[0,5] (y₅−y₄ ≥ 10) | CC4: □[0,20] and ≥ **8** |

So φ₂–φ₅ are **paper-specific 1-D variants**, presumably because Cor. 2.4 needs 1-D signals. **The results cannot be compared with ARCH-COMP numbers.** Two further notes: the paper cites the 2024 ARCH report [29], which I did not check, and ARCH's own protocol (50 trials, 300 simulations, 20 input segments) [ARCH19] also differs from the paper's.

### 3.3 Control system: UAV [T p.8]

- Quadrotor model from ref. [47] (a KTH MSc thesis), with translational, rotational and kinematic equations. The controlled output is the **x-position x₁**.
- **Inputs:** thrust f_t and torques τ_x, τ_y, τ_z.
- **Parameters** m, I_x, I_y, I_z and g appear in the equations but have **no values given**.

### 3.4 Control objectives [T p.8, Eqs. 14–21]

Length-10 trajectories:

| | Formula |
|---|---|
| φ₁ | □(0≤x₁≤10) ∧ □¬(3<x₁<5) |
| φ₂ | ◇[0,7](0≤x₁≤3) ∧ □[8,10](0≤x₁≤3) |
| φ₃ | ◇[0,10](0≤x₁≤3) ∧ ◇[0,10](7≤x₁≤10) |
| φ₄ | ◇[0,2](0≤x₁≤2) ∧ ◇[3,5](4≤x₁≤6) ∧ ◇[6,9](15≤x₁≤17) |

Length-30 trajectories:

| | Formula |
|---|---|
| φ₅ | □(0≤x₁≤100) ∧ □¬(30<x₁<50) |
| φ₆ | ◇[0,20](40≤x₁≤45) ∧ □[20,29](40≤x₁≤45) |
| φ₇ | ◇[0,29](30≤x₁≤35) ∧ ◇[0,29](75≤x₁≤80) |
| φ₈ | ◇[0,9](0≤x₁≤5) ∧ ◇[10,19](95≤x₁≤100) ∧ ◇[20,29](0≤x₁≤5) |

The names φ₁…φ₅ are **reused** with different meanings in §3 and §4.

---

## 4. Experiments, baselines, metrics

| ID | Experiment [paper] | Methods compared | Metrics | Repetitions | Output |
|---|---|---|---|---|---|
| **E1** | Language-monitor accuracy: Dist(x, L) vs RTAMT robustness [T p.6] | language monitor vs RTAMT | value agreement %, sign-only agreement %, complete disagreement %, mean monitor time (ms), satisfaction ratio %, number of boxes | 10,000 uniform inputs | Table 1 |
| **E2** | Parallel falsification [T p.6] | **PROF** vs **PBO-RTAMT** (BO on RTAMT robustness on j processors, j = number of boxes of ¬φ) | FR (successes out of 20), S̄ (mean iterations), T̄_T (total *monitoring* time, ms), T̄_M (mean monitoring time per iteration, ms) | 20 trials; same 5 starting points for both methods; cap of 200 iterations; falsifiers re-checked with RTAMT | Table 2 |
| **E3** | Serial falsification [T p.6–7] | **SMuRF** vs **SBO-RTAMT** (non-parallel BO) | same as E2 | same as E2 | Table 3 |
| **E4** | Box difficulty [T p.7] | (a) modified PROF that exits only when *every* box is falsified or after 200 iterations; (b) sequential BO that starts at a random box, spends ≤ 200 iterations per box, then switches | S̄_min, S̄_max (from a); S̄, T̄_T, T̄_M (from b, by my reading); volume ratios of 2 never-falsified boxes | 20 trials | Table 4 |
| **E5** | LangControl [T p.8–9] | **LCW** vs **LCP** | P̄ = mean iterations until a feasible signal | 1000 runs per formula, varying the initial x_ref | Table 5 |
| **E6** | Robustness-based control baseline [T p.9] | RTAMT + BO (maximise ρ) vs LCW | "BO consistently requires 3-7x the number of iterations" | "preliminary"; **no table and no per-formula numbers** | text only |

**Ablations.** None are formal. E4 and the PROF/SMuRF and LCW/LCP comparisons are the closest equivalents.

**Statistics.** Only means are reported. There are no confidence intervals, std, medians or significance tests.

---

## 5. Hyperparameters, implementation details, compute

| Item | Stated in paper | Not stated (needed to reproduce) |
|---|---|---|
| BO | GP surrogate; EI (Eq. 5) / MinBO EI (Eq. 7); n₀ = 5 shared starting points; cap of 200 iterations | GP kernel; mean function; hyperparameter fitting (MLE? restarts?); noise term; acquisition optimiser; EI exploration parameter; input scaling |
| Trials | 20 independent trials (falsification); 1000 runs (control); 10,000 samples (Table 1) | random seeds; how the 5 starting points are drawn and whether they change between trials |
| Iteration counting | "number of iterations" | whether S̄ includes the n₀ initial samples; how PROF/PBO count iterations across j parallel processes (rounds or total simulations) |
| Timing | T̄_T, T̄_M in ms, **monitoring only** | simulation time; wall-clock time; how T̄_M is averaged. T̄_T ≠ S̄·T̄_M by up to ~30 % in some rows [T-D] |
| PBO-RTAMT | runs on j processors | what differs between the j processes if they share the same starting points |
| CC model | 5 cars, inputs ∈ [0,1], 10 control points each, 100 s, 0.1 Hz | model implementation and version (ARCH's is Simulink *(ext.)*); input interpolation; solver/step; initial conditions; whether samples are at t = 0…90 or 0…100 |
| Language | computed with FindBox [5]; box counts (Table 1) | FindBox settings (sample size, resolution); **state bounds** for y₅−y₄ (Thm 2.3 needs a bounded X); time discretisation of [a,b]-second intervals; whether "Number of Boxes" counts L(φ) or L(¬φ); language-generation time (needed for the amortisation claim) |
| Language monitor | Dist(x, L) | how dist to ∂(union of boxes) is computed (true union boundary or max over boxes) |
| UAV control | dynamics equations; formulas; 1000 runs; LCW / LCP | parameter values; tracking controller; integration step; Sample(B) distribution; Projection metric; M and K; how P̄ is counted for LCP; box counts |
| Software | PSY-TaLiRo, RTAMT, FindBox | versions; language (Python implied) |
| Hardware | — | **nothing stated**, including processor count, even though PROF and PBO need up to 85 processes for φ₃ |

---

## 6. Reported results

Full transcription is in `paper_reported_values.py`. All values below are **paper claims**.

**Table 1 [T p.6].**

| | φ₁ | φ₂ | φ₃ | φ₄ | φ₅ |
|---|---|---|---|---|---|
| Value agreement % | 100.00 | 42.60 | 100.00 | 42.61 | 100.00 |
| Sign-only agreement % | 0.00 | 57.40 | 0.00 | 57.38 | 0.00 |
| Complete disagreement % | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |
| RTAMT time (ms) | 0.869 | 0.672 | 1.38 | 1.37 | 1.05 |
| Language monitor time (ms) | 0.0364 | 0.0151 | 0.351 | 0.0133 | 0.0368 |
| Satisfaction % | 7.08 | 1.82 | 3.84 | 0.87 | 7.08 |
| Number of boxes | 7 | 3 | 85 | 2 | 7 |

**Tables 2 and 3 [T p.6–7].** Every method reaches FR = 20/20 on every requirement. Each cell is S̄ / T̄_T (ms) / T̄_M (ms).

| | PBO-RTAMT | PROF | SBO-RTAMT | SMuRF |
|---|---|---|---|---|
| φ₁ | 12.50 / 13.617 / 1.107 | 11.30 / 0.355 / 0.034 | 27.90 / 30.438 / 1.207 | 16.85 / 2.789 / 0.203 |
| φ₂ | 7.40 / 12.484 / 1.675 | 7.50 / 0.484 / 0.067 | 15.10 / 19.245 / 1.272 | 12.95 / 3.055 / 0.324 |
| φ₃ | 6.30 / 11.785 / 1.877 | 6.05 / 2.294 / 0.380 | 19.45 / 38.564 / 1.975 | 18.65 / 11.150 / 0.631 |
| φ₄ | 24.40 / 44.700 / 1.820 | 31.10 / 0.672 / 0.031 | 39.10 / 70.265 / 1.808 | 25.50 / 4.121 / 0.186 |
| φ₅ | 7.40 / 11.242 / 1.540 | 7.90 / 0.468 / 0.063 | 13.40 / 23.811 / 1.701 | 11.65 / 3.254 / 0.353 |

**Table 4 [T p.7].** FR is 20/20 throughout.

| | S̄_min | S̄_max | S̄ | T̄_T | T̄_M |
|---|---|---|---|---|---|
| φ₁ | 11.3 | 47.7 | 31.8 | 5.009 | 1.670 |
| φ₂ | 7.5 | 37.1 | 19.57 | 4.831 | 0.690 |
| φ₃ | 6.05 | **200** | 46.35 | 24.925 | 0.293 |
| φ₄ | 31.1 | 63.4 | 25.50 | 4.121 | 0.186 |
| φ₅ | 7.9 | 37.7 | 19.7 | 5.023 | 0.718 |

The text adds that 2 of 85 boxes were never falsified, with volume ratios 0 and 0.00129.

**Table 5 [T p.9], P̄.**

| | φ₁ | φ₂ | φ₃ | φ₄ | φ₅ | φ₆ | φ₇ | φ₈ |
|---|---|---|---|---|---|---|---|---|
| LCW | 1.884 | 4.808 | 1.257 | 135.036 | 4.272 | 6.315 | 206.935 | 1965 |
| LCP | 1 | 2.322 | 1 | 41.236 | 2.372 | 2.947 | 89.733 | 488.345 |

**Derived from the paper's numbers [T-D].**

- **The "10x–100x" claim refers to monitoring time, not falsification effort.**
  - Total monitoring-time speedup is 5.1–66.5x for PBO→PROF (geometric mean 24.1) and 3.5–17.1x for SBO→SMuRF (geometric mean 7.8).
  - Per-trajectory monitor speedup in Table 1 is 3.9–103x (geometric mean 26.2). The only ≥100x value is φ₄ in Table 1.
- **Iterations, which drive simulation cost:**
  - PROF needs about as many as PBO-RTAMT (ratio geometric mean 0.96; φ₄ needs 27 % *more*).
  - SMuRF needs 1.04–1.66x fewer than SBO-RTAMT (geometric mean 1.29).
  - No end-to-end time including simulation is reported, so "significantly faster overall runtimes" [T p.6] is argued, not measured.
- **LCW/LCP iteration ratio:** 1.26–4.02 (geometric mean 2.21). The text says "from 2x to 4x"; three formulas fall below 2x.

---

## 7. Inconsistencies and likely typos in the paper

These are observations; they do not change what is reproduced.

1. **Box count.** Table 1 gives 85 boxes to **φ₃**, and Table 4's S̄_max = 200 is on φ₃. The text [T p.7] says "**φ₄**, which contains 85 boxes".
2. **Duplicated row.** Table 4's φ₄ values (S̄ 25.50, T̄_T 4.121, T̄_M 0.186) are **identical** to Table 3's SMuRF φ₄ row. This could be a copy error.
3. **Suspicious coincidence.** Table 1 gives φ₁ and φ₅ the same satisfaction ratio (7.08 %) and the same box count (7), although the formulas differ completely. Agreement values for φ₂ and φ₄ are nearly identical too (42.60 vs 42.61).
4. **Table 4 caption.** It mixes two procedures: "random box sampling … single thread" vs the modified PROF that produces S̄_min/S̄_max. Table 4's S̄_min equals Table 2's PROF S̄ exactly, which is consistent with the modified PROF reusing the same runs.
5. **Eq. (5) has three issues.**
   - Its Φ argument uses ŷ_k(**x**) instead of ŷ_k(u).
   - ŝ is called a "variance"; EI uses the standard deviation.
   - The `(y* − ŷ)` form is EI for *minimisation*, while Eq. (4) *maximises* Dist.
6. **Strict vs non-strict falsifier condition.** Eq. (4) uses `Dist > 0`; Algs. 1–2 terminate on `Dist ≥ 0`. Separately, §2.3 refers to "optimization (4)" where Eq. (2) is meant.
7. **Time discretisation.** "100 s at 0.1 Hz = 10 time steps" and "language ⊂ ℝ¹⁰" are inconsistent with φ₂ (horizon 70 + 30 = 100 s, which needs 11 samples at 10-s spacing). φ₅'s □[0,5] spans **less than one sample**. For control, length-10 formulas use □[8,10] and ◇[0,10], i.e. index 10, but the length-30 formulas use [·,29].
8. **UAV rotational dynamics.** They are printed as `φ̇₂ = I_x/(I_y−I_z)·θ₂ψ₂ + τ_x/I_x` (and cyclic). The standard Euler rigid-body form is `(I_y−I_z)/I_x` *(ext.)*. This needs checking against ref. [47].

---

## 8. Comparison with the reference project methodology

| Dimension | Reference (SPGA, ICCPS '23) [R] | Target (ICCPS '25) |
|---|---|---|
| Claim type | new learner is faster at equal safety/return | new algorithms are faster (monitoring) with equal or fewer iterations |
| Comparison unit | method × environment variant × 5 seeds | method × requirement × 20 trials (falsification); × 1000 runs (control) |
| Paired design | same seed list; same initial states for evaluation | **same 5 starting points** for both methods |
| Primary metric | wall-clock training time; xSpeedUp; geometric mean | FR; iterations; monitoring time (ms); P̄ |
| Correctness check | safety predicate at evaluation (§6 there: broken counters) | falsifiers re-validated with RTAMT; Table 1 agreement vs RTAMT |
| Statistics | mean ± (t-CI or std, mixed) | means only |
| Baselines | library-default PPO | BO on RTAMT robustness, structured to match (parallel/serial) |
| Artifacts | code, checkpoints, results, Docker | **no code**; language-generator repo only |
| Compute stated | yes (i9, 16 GB) | **no** |
| Stack | Py3.9, TF, RLlib, Gym | Python, PSY-TaLiRo, RTAMT, FindBox, GP-BO; CC model *(Simulink in ARCH, ext.)* |

The two papers share an evaluation shape but no domain code: a proposed method against a matched baseline, over a matrix of problem variants and repeated trials, with time ratios as the headline. The reference's weaknesses [R §6] carry over as **design rules** for our harness:

- one ground-truth monitor;
- one dispersion statistic;
- identical timing instrumentation for all methods;
- every metric computed on the same trial set;
- the stop reason logged for every run.

---

## 9. Reproduction mapping

### 9.1 Reuse directly

| What | From | Note |
|---|---|---|
| t-based 95 % CI and geometric-mean speedup | reference `generate_table_2.py:20-37`, `generate_table_3.py:13-26` | Only ~15 lines of logic. **Our decision:** re-implement them, because the reference repo declares no license, and cite them as the method source. Use for every mean we report and for "x-speedup" summaries |
| Paired-initialisation pattern | reference `expected_return.py` (shared init points) | The paper itself requires the same 5 starting points across methods |
| Separate "run → raw per-trial records → regenerate tables" stages | reference `train_*.py` → `generate_*.py` | Lets tables be rebuilt without re-running experiments |
| Provenance tooling and PROGRESS discipline | `analysis/reference_inspection/`, `analysis/target_paper/` | `paper_reported_values.py` becomes the "paper column" of every comparison table |
| External tools | RTAMT (pip 0.3.5), PSY-TaLiRo (pip 1.0.0), FindBox (GitHub) | Used as published, after install approval; FindBox has no license (§9.5) |

### 9.2 Adapt

| What | From → to |
|---|---|
| Experiment driver | `scripts/train.sh` loops → config-driven runner over requirement × method × trial, with resumable per-trial JSONL output |
| Result schema | SPGA pickles of means → per-trial records: inputs, iterations, falsified flag, RTAMT validation, monitor / simulation / wall times, stop reason, seed |
| Table generators | `generate_table_2/3.py` → Tables 1–5 in the paper's layout, with a "paper" column next to "ours", plus CI |
| Figure scripts | matplotlib trajectory plots → 3D projections of box unions (Figs. 1, 2, 4) and the LangControl run visual (Fig. 3) |
| Artifact packaging | Docker + `generate_artifacts.sh` + README time estimates → same pattern on a Python-only stack (MATLAB cannot be containerised under its license) |
| Ground-truth check | SPGA's "evaluate with/without shield" → validate each language-based falsifier with RTAMT; Table 1 agreement |

### 9.3 Implement from scratch

None of the reference's RL/GA code applies.

1. **Spec layer.** φ₁–φ₅ (CC) and φ₁–φ₈ (UAV) in RTAMT discrete-time syntax, with an explicit seconds→steps mapping.
2. **System layer.**
   - CC simulator interface and 20-control-point input parametrisation; the route depends on a decision in the plan.
   - Sampling of y₅−y₄ at the chosen grid.
   - UAV dynamics, an integrator, and a **tracking controller** (unspecified in the paper).
3. **Language layer.**
   - FindBox adapter that computes and caches the boxes of φ and ¬φ.
   - Box algebra: signed distance per Eq. (1) under ‖·‖_∞, membership, projection onto a box or union, sampling.
   - Language monitor Dist(x, L).
4. **BO layer.** GP surrogate, EI (Eq. 5) and MinBO EI (Eq. 7) with a shared acquisition optimiser and hyperparameter fitting for all methods.
5. **Algorithms.**
   - PROF and PBO-RTAMT, run with a lock-step scheduler so j "processors" can be emulated on 12 threads.
   - SMuRF and SBO-RTAMT.
   - Modified PROF and sequential BO (Table 4).
   - LangControl LCW / LCP (Alg. 3).
   - Optional robustness-BO control baseline (E6).
6. **Experiments E1–E6** with instrumentation that times monitoring, simulation and GP fitting separately.
7. **Tests.**
   - Dist sign vs RTAMT sign on random signals.
   - Box-union membership vs RTAMT satisfaction.
   - EI against a closed-form check.
   - Determinism given a seed.

### 9.4 Missing or unclear in the paper

These become explicit decision IDs in the plan.

- **Blocking:**
  - CC model implementation, interpolation and sampling grid.
  - Interval discretisation (§7.7).
  - y₅−y₄ state bounds and FindBox settings.
  - The UAV tracker and its parameters.
  - Iteration and timing definitions.
- **Important:**
  - GP and acquisition settings.
  - PBO-RTAMT process diversity.
  - Seeds and starting points.
  - Sample(B) and Projection.
  - M and K.
  - Whether "Number of Boxes" counts L(φ) or L(¬φ).
  - Table 4 procedure (§7.4).
- **Cannot be recovered from the paper:** the E6 baseline numbers and the language-generation cost.

Since ref. [4] is a private communication with the first author, **asking the authors** for their scripts or settings is the cheapest way to close these gaps.

### 9.5 Not reproducible with the available data, hardware or information

| Item | Why | What we can do instead |
|---|---|---|
| CC results on the *same* model | No MATLAB on this machine (checked), and ARCH's CC model is Simulink *(ext.)*. No Python CC implementation was found | (a) your MATLAB + ARCH model, (b) an approved Python port of the ARCH model, labelled a *re-implementation*, or (c) the authors' setup |
| Exact numbers in Tables 1–4 | Seeds, starting points, GP settings and discretisation are unknown | Statistical comparison: FR, S̄ distributions, and speedup *ratios* with CIs |
| Absolute times (ms) | Hardware is unstated; our machine is an i5-1335U (10 cores / 12 threads), 15.7 GB RAM | Compare per-call timing **ratios** (language vs RTAMT) measured on the same machine |
| True parallel PROF/PBO with j = 85 | 12 logical CPUs | Lock-step emulation preserves iteration counts. The paper reports no parallel wall-clock, so nothing is lost |
| Table 5 values | Tracker, parameters, Sample/Projection, M and K are unspecified, so P̄ depends on our choices | Reproduce the **trend** (LCP ≤ LCW, φ₄/φ₇/φ₈ hardest), clearly labelled as our design |
| E6 "3–7x" | No reported data | Optional re-run with our BO baseline, reported as new evidence, not as a reproduction |
| Amortisation claim | No language-generation cost is reported | Measure our FindBox cost and report it |
| FindBox reuse rights | The repository has no license | Your call: use it for research reproduction, ask the authors, or re-implement from ref. [5] |
