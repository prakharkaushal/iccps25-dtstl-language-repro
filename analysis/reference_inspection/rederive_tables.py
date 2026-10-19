"""Re-derive the reference project's Table 2 and Table 3 from its stored pickles.

Mirrors spga/generate_table_2.py and spga/generate_table_3.py (rounding order, t-based 95% CI,
geometric mean of *rounded* per-variant ratios, "All Envs" = geometric mean of the six
per-env/mechanism geometric means). Deliberate differences, to keep the reference read-only:
  * pickles are read with safe_pickle.load instead of pd.read_pickle
  * output goes to stdout (the originals write spga/artifacts/table_{2,3}.txt)
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import scipy.stats

from safe_pickle import DEFAULT_SPGA_ROOT, load

warnings.filterwarnings("ignore")
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SPGA_ROOT
VERS = {"cpole": ["1.5", "1.25", "1.0", "0.75", "0.5", "0.25"], "frolake": ["8", "16", "32"], "knapsack": ["5", "50", "100"]}
NAMES = {"cpole": "CartPole-v0", "frolake": "FrozenLake-v1", "knapsack": "Knapsack-v0"}
MODES = {"rta": ("run_time_assurance", "rta"), "am": ("action_masking", "masking")}


def mci(data, confidence=0.95):
    a = 1.0 * np.array(data)
    m, se = np.mean(a), scipy.stats.sem(a)
    return m, se * scipy.stats.t.ppf((1 + confidence) / 2.0, len(a) - 1)


def cell(env, mode, method, v):
    folder, tag = MODES[mode]
    base = ROOT / folder / env / "results"
    df = load(base / f"{env}_{method}_{tag}_seeded_results-{v}.pkl")
    exp = load(base / "expected_return" / f"{env}_{method}_{tag}_seeded_expreturn-{v}.pkl")
    _, tc = mci(df["train_time"])
    em, ec = mci(exp)
    # generate_table_2.py: try mask_safe_rolls, fall back to norm_safe_rolls
    safe_key = "mask_safe_rolls" if "mask_safe_rolls" in df else "norm_safe_rolls"
    return {"t": round(df["avg_train_time"], 2), "tc": round(tc, 0), "er": round(em, 2), "erc": round(ec, 1),
            "safe": round(df[safe_key], 2), "safe_key": safe_key, "n": len(df["train_time"]),
            # not in generate_table_2.py: population std of train times (generate_table_3.py's "Time Std")
            # and the training-time final_evaluation reward, to compare against the paper's Table 2
            "tstd": round(float(np.std(df["train_time"])), 1),
            "train_eval": round(float(df.get("mask_eval_reward", df.get("norm_eval_reward", np.nan))), 3)}


print("TABLE 2 (re-derived from stored pkl files)")
print("env | mech | ver | GA time +-CI | GA ER +-CI | GA safe% [key] | PPO time +-CI | PPO ER +-CI | PPO safe% [key] | xSpeedUp | n(GA,PPO)")
speedups = {}
for env in VERS:
    for mode in ("rta", "am"):
        ratios = []
        for v in VERS[env]:
            g, p = cell(env, mode, "ga", v), cell(env, mode, "ppo", v)
            s = round(p["t"] / g["t"], 2)
            ratios.append(s)
            print(f"{NAMES[env]} | {mode} | {v} | {g['t']}+-{g['tc']} | {g['er']}+-{g['erc']} | {g['safe']} [{g['safe_key']}] | "
                  f"{p['t']}+-{p['tc']} | {p['er']}+-{p['erc']} | {p['safe']} [{p['safe_key']}] | {s} | ({g['n']},{p['n']})")
        speedups[(env, mode)] = ratios

print("\nSUPPLEMENT (not part of the original scripts): population std of train times, train-time eval reward")
print("env | mech | ver | GA time std | GA train-eval reward | PPO time std | PPO train-eval reward")
for env in VERS:
    for mode in ("rta", "am"):
        for v in VERS[env]:
            g, p = cell(env, mode, "ga", v), cell(env, mode, "ppo", v)
            print(f"{NAMES[env]} | {mode} | {v} | {g['tstd']} | {g['train_eval']} | {p['tstd']} | {p['train_eval']}")

print("\nTABLE 3 (geometric mean of rounded per-variant ratios)")
gms = []
for env in VERS:
    for mode in ("rta", "am"):
        gm = round(float(np.exp(np.log(speedups[(env, mode)]).mean())), 2)
        gms.append(gm)
        print(f"{env} - {mode.upper()} SpeedUp: {gm}")
print(f"All Envs: {round(float(np.exp(np.log(gms).mean())), 2)}")
