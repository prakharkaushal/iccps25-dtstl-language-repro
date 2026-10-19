# Reference Project Analysis — SPGA (ICCPS '23)

Phase 1 deliverable · 2026-10-18 · reference tree treated as read-only (verified clean with `git status` apart from the user-added, untracked `reference_paper.pdf`).

**Source tags** used throughout (CLAUDE.md: every metric carries its source):

| Tag | Meaning |
|---|---|
| **[P …]** | `reference_project/CS637_SPGA/reference_paper.pdf` (paper pp. 110–119). Table 2 was read from the rendered page (p. 116), because text extraction scrambles its rows. |
| **[C path:line]** | Reference code. Paths are relative to `reference_project/CS637_SPGA/spga/`. |
| **[S]** | Stored result pickles under `*/results/` in the reference tree. |
| **[D]** | Derived by me with [analysis/reference_inspection/](../analysis/reference_inspection/) from [S]. Outputs are in `out_*.txt` there. The reference's own scripts were **not** run, since they write into `spga/artifacts/`. |
| *(ext.)* | External library behaviour inferred from general knowledge and **not verified** here. |

---

## 0. TL;DR

- **Paper.** *Self-Preserving Genetic Algorithms for Safe Learning in Discrete Action Spaces*, by Robinette, Hamilton and Johnson, ICCPS '23, DOI 10.1145/3576841.3585936 [P p.110]. The method (SPGA) is a neuro-evolution GA with action masking (AM) or run-time assurance (RTA) built into training. It is compared with PPO (RLlib) using the same safety mechanisms, called SRL.
- **Repository.** The repo is an unmodified fork of `pkrobinette/spga`: all 120 commits are by the upstream author, and HEAD `c356ed5` differs from the README-pinned `61141e2` only in `README.md`.
- **Experiment design.** The experiment matrix is 2 learners × 2 mechanisms × 3 environments (CartPole-v0 with 6 thresholds, FrozenLake 8/16/32, Knapsack 5/50/100 items) × 5 seeds. That gives 12 copy-pasted pipeline folders.
- **Headline claim reproduces.** Table 3 (geometric-mean xSpeedUp, "55.28x") **reproduces exactly** from the stored data [D]. All Table 2 training-time means and xSpeedUps reproduce too, with one cell that is likely a typo in the paper.
- **Several Table 2 columns do not reproduce from the repo.**
  - The "Safe Actions (%)" column cannot be reproduced at all.
  - The "±" values use two different statistics in the paper: a t-based CI for CartPole and population std for FrozenLake/Knapsack.
  - The Knapsack "Expected Return" values come from a different evaluation than the one the paper describes.
  - Some FrozenLake and CartPole expected returns differ from the stored rollouts.
- **The safety metrics cannot fail in two environments.** In FrozenLake and Knapsack the violation counters can never fire (§6, A1–A2), so "100 % safe" carries no information there.
- **The speedup comparison has confounds.** The stopping rules differ (best individual vs mean return), some stop thresholds are unreachable, the time instrumentation differs, and so do network sizes and parallelism (§6, C).
- **Reusable parts** are the *evaluation harness*: the seeds × variants × methods matrix, paired initial conditions, t-CI, the speedup ratio with geometric mean, and one-command artifact regeneration with Docker packaging. Everything RL/GA-specific is not reusable (§7).
- **Target paper.** It is a different domain (STL falsification and control, ICCPS '25), but its central claim is also a 10–100x speedup over 20 independent trials, so SPGA's speedup and statistics harness transfers well (§8).

---

## 1. What is being evaluated

**Contributions claimed [P §1].**

1. The SPGA framework.
2. SPGA implemented in three discrete-action environments.
3. SRL safety approaches implemented in the same three environments.
4. A comparative analysis.

**Implicit research questions.** These are my framing, taken from §5–6 of the paper:

- **RQ1:** Does SPGA reach SRL-level return and safety?
- **RQ2:** How much faster does SPGA train (xSpeedUp)?
- **RQ3:** How do safety-constraint tightness (CartPole boundary *b*) and problem scale (grid size, item count) affect both?
- **RQ4:** AM vs RTA.

**Headline results [P abstract, §6.4, Table 3].**

- "comparable reward and safety"
- 55.28x geometric-mean speedup
- "up to 3341.45x" (FrozenLake-RTA 8×8)

**Hardware [P §5; README].** 2.3 GHz 8-core i9, 16 GB RAM. The README estimates ~72 h to train everything and ~10 min to regenerate artifacts from the shipped data.

---

## 2. Repository architecture

```
CS637_SPGA/
├─ Dockerfile, setup.py          # python:3.9 image; `pip install .` of ~110 pinned deps
├─ README.md                     # artifact-evaluation instructions
└─ spga/
   ├─ generate_artifacts.sh      # runs ONLY the post-processing stage (tables + figs)
   ├─ generate_table_2.py        # Table 2 from results/*.pkl + results/expected_return/*.pkl
   ├─ generate_table_3.py        # Table 3 geometric-mean speedups
   ├─ retrieve.sh                # docker cp of artifacts to host
   ├─ artifacts/logs/            # output dir (placeholder only — no artifacts shipped)
   ├─ action_masking/{cpole,frolake,knapsack}/
   └─ run_time_assurance/{cpole,frolake,knapsack}/
        ├─ train_{ga,ppo}_<env>_<amask|rta>.py   # 5-seed training + final_evaluation → results/*.pkl
        ├─ demo_{ga,ppo}_*.py                    # load seed-4 agent, roll out
        ├─ expected_return.py                    # seed-4 agents × 500 rollouts → results/expected_return/
        ├─ generate_figure_{2,3,4}.py            # (cpole-AM, frolake-AM, knapsack-RTA only)
        ├─ scripts/{train,test}.sh               # exact CLI args used for the paper
        ├─ trained_agents/                       # seed-4 checkpoints only (GA: JSON weights; PPO: RLlib ckpt)
        └─ utils/  ga_*.py (GA), custom_*.py (env wrapper + mask/RTA), masking_model.py (RLlib model)
```

**Duplication.** Each of the 12 pipelines carries its own copy of the GA, the environment wrapper and the RLlib model. Only a few copies are byte-identical: `masking_model.py` for cpole AM and RTA, the knapsack `ga_masking.py` and `masking_model.py` for AM and RTA, and `custom_*_biggerlake.py`. All other copies differ in small, environment-specific edits (§4). No code is shared across the tree, and imports work only when scripts run from the pipeline folder (`from utils.…`).

**Dependency stack** [C setup.py, Dockerfile]:

- Pinned packages: Python 3.9, `gym==0.19.0` (old 4-tuple step API), `or-gym==0.5.0`, `ray==1.12.0` (RLlib `ppo.PPOTrainer`), `tensorflow==2.11.0`, numpy 1.22, pandas 1.4, scipy 1.8, matplotlib, seaborn.
- Unrelated pins are also present, e.g. fastapi and arcade.
- **The local machine has Python 3.14 and no gym/ray**, so the training stack cannot run here without a separate Py3.9 environment or Docker.

**Hygiene.** `.pyc` files and `.ipynb_checkpoints` are committed despite `.gitignore`. All results are pickles, which execute code on load; I read them with a numpy-only whitelisted unpickler ([safe_pickle.py](../analysis/reference_inspection/safe_pickle.py)).

---

## 3. End-to-end workflow

```
(1) scripts/train.sh  (~72 h total)                      (2) expected_return.py (not in generate_artifacts.sh)
    for variant in versions:                                 seed-4 GA + PPO checkpoints
      for seed in [4,36,27,2,98]:                            × 500 rollouts (fixed init set, np.random.seed(10) for cpole)
        GA: Generation(...).simulate()  ← wall-clock time    → results/expected_return/<env>_<ga|ppo>_<mode>_seeded_expreturn-<v>.pkl
        PPO: trainer.train() loop       ← time_total_s
        save checkpoint (only seed 4 shipped)            (3) generate_artifacts.sh (~10 min)
      final_evaluation(last-trained agent = seed 98)         generate_table_2.py, generate_table_3.py,
    → results/<env>_<ga|ppo>_<mode>_seeded_results-<v>.pkl   generate_figure_{2,3,4}.py → artifacts/
```

- **Data.** There are no datasets; all data is simulated. Environments are Gym CartPole-v0 and FrozenLake-v1 (non-slippery, plus custom 16×16 and 32×32 maps), and OR-Gym Knapsack-v0 with hard-coded item weights and values for 50 and 100 items.
- **What the artifact actually reproduces.** It reproduces stage (3) only, from shipped pickles and checkpoints. Stages (1) and (2) must be re-run to verify anything beyond arithmetic.

---

## 4. Methodology ↔ implementation

### 4.1 SPGA genetic algorithm — paper vs code

[P §2.1.3, §4.1] vs [C action_masking/cpole/utils/ga_masking.py] (other copies analogous)

| Aspect | Paper says | Code does |
|---|---|---|
| Individual | NN, 1 hidden layer of 16 | `w1,b1,w2,b2`, ReLU, `argmax` action (deterministic) [:24-66]; hidden=8 for FrozenLake-RTA [C run_time_assurance/frolake/train_ga_frolake_rta.py:182] |
| Population *n* | 30 | 30 CartPole, 50 FrozenLake and Knapsack-AM, **100** Knapsack-RTA [C train_ga_knapsack_rta.py:229] |
| Init | uniform | `np.random.randn` weights, `b1 = 1` [:33-37] |
| Mutation μ | 0.2 | 0.3 CartPole and FrozenLake-AM, 0.5 FrozenLake-RTA, 0.4 Knapsack. Each weight gets `+U(-0.1,0.1)` w.p. μ; **every bias gets `+U(0,0.1)` every generation** (positive drift, not μ-gated) [:70-90] |
| Elitism | not described | top 20 % (rounded up to even) carried over [:167-174, 222-224]. They are then **mutated in place** with the children [:285-286], so no individual survives unchanged |
| Selection | tournament | binary tournament per parent [:228-238] |
| Crossover | two-point over 16 hidden nodes | correct for `w1/b1`. `w2/b2` are cut along the *output* axis with the hidden-axis indices [:198-202], so the output layer comes mostly from parent 1 |
| Fitness | single-episode return incl. safety penalty | single episode [:246-262]. Penalty only in CartPole-AM (`-10` when any mask entry is 0, [:257-258]); see 4.2 for the others |
| Stop | mean of fittest over last 30 gens = solved score, *G* = 500 | `mean(best[-30:]) >= stop_reward and k > 30` [:301]. `stop_reward` comes from `train.sh` and can differ from the paper's solved score (4.4) |
| Final pick | evaluate last population once more, take best | same [:312-319] |

### 4.2 Safety mechanisms per environment

| | CartPole-v0 (threshold *b*) | FrozenLake-v1 | Knapsack-v0 |
|---|---|---|---|
| **AM mask** | block "left" if `x ≤ −b`, "right" if `x ≥ b`, on the *current* state (reactive) [C custom_amask_cpole.py:102-122] | precomputed per cell: no move into holes or off-grid [C custom_amask_frolake.py:143-271] | OR-Gym built-in mask (`'mask': True`) *(ext.)* |
| **RTA monitor** | one-step replay of Gym dynamics; unsafe if `|x'| ≥ b` [C custom_rta_cpole.py:117-155] | next cell is a hole/off-grid; **any action in the bottom row is flagged unsafe** [C custom_rta_frolake.py:363] | `env.current_weight + w[a] > max_weight` [C custom_knapsack.py:78] |
| **RTA backup** | push toward centre [:90-99] | uniform random available action | random choice among items `range(5)` using a **stale** weight (0) [C custom_knapsack.py:35,62-65] |
| **GA-specific** | AM: −10 fitness penalty. **RTA: no backup controller in GA training**: the episode is *truncated* at the first unsafe proposal [C run_time_assurance/cpole/utils/ga_masking.py:255-266] | AM: no penalty. RTA: env-level shaping (goal 5.1, −0.1/step) for both learners [C custom_rta_frolake.py:318-320] | AM: none (−10 removed). RTA: −5 in env for both learners |
| **PPO integration** | AM: `ActionMaskModel` adds `log(mask)` (clamped) to logits [C masking_model.py:43-54]; RTA: env wrapper | same; FrozenLake obs one-hot (`true_obs_shape` 64/256/1024) vs **scalar index** for GA [C ga_frolake_masking.py:162] | same |

[P §4.3] says both learners get the same reward and a negative reward whenever the mechanism triggers. In code this holds only for **Knapsack-RTA**. CartPole-AM penalises GA only, and the other four combinations have no trigger penalty.

### 4.3 SRL baseline

RLlib 1.12 `PPOTrainer` with `ppo.DEFAULT_CONFIG` [P §4.2]. Overrides:

- CartPole sets only `gamma=0.99` and `lr=3e-4` [C train_ppo_cpole_amask.py:72-102], even though its docstring cites RLlib's tuned CartPole config.
- FrozenLake and Knapsack use pure defaults, and their PPO seed is commented out or not set [C train_ppo_frolake_amask.py:97].

The RLlib defaults that apply include a 256×256 FC net and multiple rollout workers *(ext.)*, against the GA's 16-unit net in one process.

The stop rule is `mean(episode_reward_mean[-30:]) >= stop_reward and iters >= 30`, or more than 500 iterations [:198].

### 4.4 Experimental protocol

| | Paper | Code / stored data |
|---|---|---|
| Training seeds | 2, 4, 27, 36, 98 [P §5.1] | `[4,36,27,2,98]`. **Stored FrozenLake GA 8×8 (AM and RTA) has 1 trial** [S]. Knapsack PPO-RTA code now says `[4]` [C train_ppo_knapsack_rta.py:249] but the stored file has 5 |
| Solved score / stop | CartPole 200; FrozenLake 1.0; Knapsack 36 / 103 / 104 [P Table 1] | CartPole 190 (default). FrozenLake: GA-AM 1, PPO-AM 0.95, RTA 3.68 / 2 / 5 (shaped). Knapsack 35–36 / 100 / 104 [C scripts/train.sh] |
| Test seed / episodes | seed 4, 500 episodes [P §5.2] | expected return: seed 4 × 500 ✔. "Safe %": from training-time `final_evaluation` on the **last-trained seed (98)**, over **20 episodes for CartPole** (`--num_eval_eps` default) and 500 elsewhere |
| Safety mechanism during expected-return eval | not stated | **CartPole: OFF**. **FrozenLake and Knapsack: ON** [C cpole/expected_return.py:54; frolake/expected_return.py:60; knapsack/expected_return.py:101] |
| Policy at eval | not stated | GA deterministic argmax; PPO `compute_single_action` with RLlib default exploration, i.e. stochastic *(ext.)* |

### 4.5 Metrics

| Metric | Paper definition [P §5.3] | Code |
|---|---|---|
| Training time | mean wall time over 5 seeds | GA: `time.time()` around `simulate()`. PPO: RLlib `time_total_s` [C train_ppo_cpole_amask.py:204]. "±" = 95 % t-CI [C generate_table_2.py:20-37,89] |
| Expected return | mean episode reward over 500 rollouts | mean of `expected_return` pickle, ± t-CI [:91-93] |
| Safe actions (%) | per-*action* % satisfying the predicate, averaged over 500 episodes | per-*episode* %: `100 − 100·(episodes with ≥1 violation)/N` [C train_ga_cpole_amask.py:144]; ± hard-coded `+/-0` [C generate_table_2.py:136] |
| xSpeedUp | — | `PPO_time / GA_time` [:135] |
| Table 3 | geometric mean | `exp(mean(log(rounded ratios))) `per env×mechanism; "All Envs" = geometric mean of the 6 values [C generate_table_3.py:13-26,73-84,124] |

The safety predicate itself varies between scripts. Examples: `|x| > 1.5` [C train_ga_cpole_amask.py:80]; `|x| ≥ 1.5 or |θ| ≥ 0.10` [C train_ppo_cpole_rta.py, generate_figure_2.py:50]. It is always 1.5 regardless of the training threshold *b*.

---

## 5. Reported results vs what the repo reproduces

**Table 3 [P p.116] vs [D].**

| | Paper | Re-derived [D] |
|---|---|---|
| CartPole RTA | 12.95 | 12.95 |
| CartPole AM | 3.21 | 3.21 |
| FrozenLake RTA | 1177.54 | 1177.54 |
| FrozenLake AM | 45.82 | 45.82 |
| Knapsack RTA | 306.16 | 306.16 |
| Knapsack AM | 41.58 | 41.58 |
| **All** | **55.28** | **55.28** |

All seven values match exactly.

**Table 2 [P p.116] vs [D].** Full re-derivation is in `analysis/reference_inspection/out_tables_2_3.txt`.

| Column | Reproduced? | Evidence |
|---|---|---|
| Training time (mean) | ✔ 47/48 cells | Exception: Knapsack-RTA-100 SPGA. The paper prints 55.33 ± 3; stored data give 97.01, and the paper's own xSpeedUp 177.77 = 17245.11 / 97.01. Likely a typo in the paper |
| Training time "±" | CartPole ✔ (t-CI); FrozenLake/Knapsack ✘ | Paper's FrozenLake/Knapsack "±" = **population std** (e.g. 7395.7 → "7396.0", 361.2 → "361.0", 1705.6 → "1706.0" [D supplement]); `generate_table_2.py` prints t-CI (10267, 501, 2368) |
| Expected return | partial | CartPole GA ✔. CartPole PPO: small drifts (RTA *b*=1.25: paper 196.4 ± 1.3 vs [D] 197.97 ± 1.0), consistent with stochastic PPO re-rollouts. FrozenLake: 3 cells differ (SPGA-RTA 32×32: 0.54 vs 0.476; SRL-RTA 16×16: 1.0 vs 0.0; SRL-AM 32×32: 1.0 vs 0.0). **Knapsack: the paper uses the training-time `final_evaluation` reward**, not the seed-4 500-rollout pickles (SPGA-AM 50: paper 94.0 = train-eval; expected-return pickle 104.0). The Knapsack "±" cannot be derived from any stored file |
| Safe actions (%) | ✘ | The paper shows 100.0 ± 0 everywhere except SPGA-RTA CartPole *b*=0.25 at 96.1 ± 0.6. Stored data give 100 for that cell, and 25 / 60 / 85 / 95 % for SRL-AM CartPole *b*=1.5 / 1.25 / 0.75 / 0.5 and 95 % for SRL-RTA *b*=0.5. No script in the repo produces per-action % with a ±. (`utils.rollout` computes per-action % but keeps only the last episode [C action_masking/cpole/utils/utils.py:57]) |
| xSpeedUp | ✔ 24/24 | |

**Provenance.** The stored results were committed on 2023-02-09 (`44b627c`), and the training scripts were edited afterwards ("cpole cleanup" `50722c9`, "file updates", 2023-02-12). The stored pickles also lack keys that the current code writes (e.g. cpole-AM has no `ep_reward` / `norm_*`). **The shipped numbers therefore did not come from the code as committed.**

---

## 6. Issues that affect validity or reproducibility

Ordered by impact on the paper's conclusions. All are from code reading plus [S]/[D] checks; I executed nothing in the reference.

**A. Metric correctness**

1. **FrozenLake violations are never counted.** The hole check runs on the state *before* stepping, and stepping into a hole sets `done` and breaks the loop [C train_ga_frolake_amask.py:83-95, all FrozenLake eval functions]. "100 % safe" is therefore true by construction.
2. **Knapsack violations are never counted.** The checks read the wrapper's `current_weight`, which is copied once at construction and never updated [C custom_knapsack.py:35; train_ga_knapsack_amask.py:77]. The RTA backup also uses that stale weight and only items 0–4 [:62-65]. Whether OR-Gym itself can ever exceed capacity is *(ext.)* to verify.
3. **"Safe %" is mis-described.** It is per-episode rather than per-action, comes from a different agent (seed 98) than every other test metric (seed 4), uses only 20 episodes for CartPole, and has its "±" hard-coded to 0.

**B. Evaluation asymmetries**

4. The safety mechanism is OFF during CartPole expected-return evaluation but ON for FrozenLake and Knapsack. For CartPole-RTA, SPGA's Safe % is measured *without* RTA, while SRL's is measured *with* RTA [C generate_table_2.py:94-97 key fallback].
5. SPGA-RTA on CartPole never uses the backup controller in training; it truncates the episode instead (§4.2). This is a different mechanism from SRL-RTA.
6. GA policies are evaluated with deterministic argmax, PPO policies by stochastic sampling *(ext.)*.
7. The safety predicates differ between scripts (§4.5).

**C. Fairness of the speedup comparison**

8. The stopping statistics differ: best individual for the GA vs mean return for PPO. The paper acknowledges this in §6.6.
9. Some stop thresholds are unreachable. Under FrozenLake-RTA shaping (goal +5.0 net, −0.1/step), a 32×32 path needs about 62 steps, so `stop_reward 5` can never be met. Both learners then run to the 500-iteration cap, and the "speedup" measures per-iteration cost rather than learning speed. (Derived from code; worth confirming empirically.)
10. Different time sources (wall-clock vs `time_total_s`), parallelism (single process vs RLlib workers) and model sizes (16 vs 256×256 *(ext.)*).
11. The paper's hyperparameters (*n*=30, μ=0.2, uniform init, 16 hidden) differ from the code (§4.1). The paper's "same reward function" claim does not hold in code (§4.2).
12. GA operator quirks: elites are mutated, biases drift upward, and crossover uses the wrong axis for `w2` (§4.1).

**D. Reproducibility**

13. The stored results predate the final code (§5). PPO seeds are unset for FrozenLake and Knapsack. One stored cell has n = 1, which gives a NaN CI.
14. The stack is a legacy pinned set (Py3.9 / TF2.11 / ray1.12 / gym0.19), and the Docker base is not pinned by digest.
15. `generate_figure_4.py` draws both plots on `plt.figure(1)` without clearing [C run_time_assurance/knapsack/generate_figure_4.py:99], so the SRL figure also contains the SPGA curves. Separately, the paper's Fig. 3 caption says AM while the §6.2 text discusses RTA.

---

## 7. Reusable vs paper-specific

| Component | Location | Generic? | Use for target |
|---|---|---|---|
| Experiment matrix: method × variant × fixed seed list, driven by one shell script per cell | `scripts/train.sh`, `rand_seeds` in `train_*.py` | ✔ pattern | Requirements φ1–φ5 × methods × 20 trials |
| Paired conditions: identical initial states for every method | `cpole/expected_return.py:28,53` | ✔ | Target also starts both methods from the same 5 points |
| Per-run record (raw per-seed times + summary) | `data` dicts in `train_*.py` | ✔ pattern | Keep the raw per-trial lists; use JSON/CSV, not pickle |
| `mean_confidence_interval` (t-based 95 %) | `generate_table_2.py:20-37` | ✔ directly | Every mean ± CI in the target tables |
| Speedup ratio + geometric mean across variants | `generate_table_3.py:13-26,73-84` | ✔ directly | Target claims "10x to 100x" speedups |
| Separate train/eval stages; tables and figures regenerated only from stored results | `generate_*.py`, `generate_artifacts.sh`, `retrieve.sh` | ✔ pattern | One-command artifact regeneration |
| Docker + time estimates + hardware statement | `Dockerfile`, README | ✔ pattern | Artifact-evaluation packaging |
| "With vs without the safety layer" ablation | `final_evaluation` mask/norm | concept | Analogue: validate language-monitor falsifiers with RTAMT |
| GA, PPO/RLlib, env wrappers, masks, RTA, reward shaping, maps/items | `utils/*`, `train_*` | ✘ specific | none |

The design of the target harness should also **avoid §6**:

- one predicate or monitor source of truth;
- one dispersion statistic stated in every caption;
- every metric computed on the same trial set;
- stop/termination reason logged per run;
- time instrumented identically for all methods;
- no rounding before aggregation.

---

## 8. Preliminary relevance to the target paper

This section is for orientation only; Phase 2 will analyse the target paper properly.

**Paper.** `Paper.pdf` is *Falsification and Control of CPS using the Language Set of Discrete-Time Temporal Logic*, by Abou-Mrad, Khandait, Pedrielli and Abbas, ICCPS '25, DOI 10.1145/3716550.3722040.

**Evaluation structure** (from a `pdftotext` read; math symbols were lost and must be checked visually):

- Falsification on the ARCH **Chasing Cars** benchmark: PROF vs PBO-RTAMT, and SMuRF vs SBO-RTAMT, for 5 requirements over **20 independent trials**. Metrics are falsification rate, mean iterations, total time and time per iteration (Tables 2–4).
- Monitor accuracy on 10,000 uniformly sampled inputs (Table 1).
- LangControl (LCW / LCP) on a UAV model with 1000 replications (Table 5).
- Tools named: Psy-TaLiRo, RTAMT, and FindBox (`github.com/Chris-amV/FindBox`).

**How it maps.** The target's structure lines up with the SPGA harness:

- requirement ↔ variant
- proposed vs baseline method ↔ SPGA vs SRL
- trial ↔ seed
- time ratio and geometric mean ↔ xSpeedUp

None of the RL/GA code applies.

---

## 9. Open questions for your review

1. **Scope of Phase 2.** Should we reproduce the target paper's own tables (FR, iterations, timing), add an SPGA-style geometric-mean speedup summary, or both?
2. **Benchmark availability.** Is the Chasing Cars model a MATLAB/Simulink artifact or a Python port? Downloading it, FindBox, Psy-TaLiRo or RTAMT needs your approval (CLAUDE.md).
3. **`reference_paper.pdf` location.** It currently sits untracked inside the reference repo. I have left it untouched. Do you want it moved to `target_project/` (a change to the reference folder, so your call)?
4. **Reference issues.** Should the §6 issues in the reference be reported only as caveats (my default), or do you also want a corrected re-run of SPGA? That would need a Py3.9 stack and many hours of training.
