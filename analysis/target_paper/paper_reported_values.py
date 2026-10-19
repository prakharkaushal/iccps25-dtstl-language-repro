"""Values REPORTED in the target paper, transcribed by hand from 300-dpi renders of Paper.pdf.

Source: Abou-Mrad, Khandait, Pedrielli, Abbas. "Falsification and Control of CPS using the
Language Set of Discrete-Time Temporal Logic", ICCPS '25, doi:10.1145/3716550.3722040.
Page numbers refer to the PDF (1-10). These are the paper's claims, not reproduced results.

Running this file prints quantities DERIVED from the reported values (ratios, geometric means,
internal consistency checks). Derived numbers are arithmetic on the paper's tables only.
"""
import math

REQS = ["phi1", "phi2", "phi3", "phi4", "phi5"]

# Table 1 (PDF p.6): monitoring results over 10,000 uniformly sampled inputs on the CC model.
TABLE1 = {
    "value_agreement_pct":        [100.00, 42.60, 100.00, 42.61, 100.00],
    "sign_only_agreement_pct":    [0.00, 57.40, 0.00, 57.38, 0.00],
    "complete_disagreement_pct":  [0.00, 0.00, 0.00, 0.01, 0.00],
    "mean_rtamt_time_ms":         [8.69e-01, 6.72e-01, 1.38, 1.37, 1.05],
    "mean_language_monitor_ms":   [3.64e-02, 1.51e-02, 3.51e-01, 1.33e-02, 3.68e-02],
    "satisfaction_ratio_pct":     [7.08, 1.82, 3.84, 0.87, 7.08],
    "number_of_boxes":            [7, 3, 85, 2, 7],
}

# Tables 2 and 3 (PDF p.6-7): 20 independent trials. Columns: FR, S_bar (mean iterations),
# T_T (total monitoring time, ms), T_M (mean monitoring time per iteration, ms).
TABLE2 = {  # PBO-RTAMT vs PROF
    "PBO-RTAMT": {"FR": [20] * 5, "S": [12.50, 7.40, 6.30, 24.40, 7.40],
                  "TT": [13.617, 12.484, 11.785, 44.700, 11.242], "TM": [1.107, 1.675, 1.877, 1.820, 1.540]},
    "PROF":      {"FR": [20] * 5, "S": [11.30, 7.50, 6.05, 31.10, 7.90],
                  "TT": [0.355, 0.484, 2.294, 0.672, 0.468], "TM": [0.034, 0.067, 0.380, 0.031, 0.063]},
}
TABLE3 = {  # SBO-RTAMT vs SMuRF
    "SBO-RTAMT": {"FR": [20] * 5, "S": [27.90, 15.10, 19.45, 39.10, 13.40],
                  "TT": [30.438, 19.245, 38.564, 70.265, 23.811], "TM": [1.207, 1.272, 1.975, 1.808, 1.701]},
    "SMuRF":     {"FR": [20] * 5, "S": [16.85, 12.95, 18.65, 25.50, 11.65],
                  "TT": [2.789, 3.055, 11.150, 4.121, 3.254], "TM": [0.203, 0.324, 0.631, 0.186, 0.353]},
}
# Table 4 (PDF p.7): modified PROF / sequential single-thread BO, 20 trials.
TABLE4 = {"FR": [20] * 5, "S_min": [11.3, 7.5, 6.05, 31.1, 7.9], "S_max": [47.7, 37.1, 200, 63.4, 37.7],
          "S": [31.8, 19.57, 46.35, 25.50, 19.7], "TT": [5.009, 4.831, 24.925, 4.121, 5.023],
          "TM": [1.670, 0.690, 0.293, 0.186, 0.718]}
# Table 5 (PDF p.9): LangControl, mean iterations P_bar over 1000 replications.
TABLE5 = {"LCW": [1.88423, 4.80769, 1.25672, 135.036, 4.27235, 6.31527, 206.935, 1965],
          "LCP": [1, 2.32152, 1, 41.2362, 2.37237, 2.94731, 89.7326, 488.345]}


def gmean(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def ratios(num, den):
    return [a / b for a, b in zip(num, den)]


if __name__ == "__main__":
    print("== Derived from paper-reported values (arithmetic only) ==\n")
    r1 = ratios(TABLE1["mean_rtamt_time_ms"], TABLE1["mean_language_monitor_ms"])
    print("T1 per-trajectory monitor speedup RTAMT/language:", [round(x, 1) for x in r1],
          "geomean", round(gmean(r1), 1))
    for name, tab, base, ours in (("T2", TABLE2, "PBO-RTAMT", "PROF"), ("T3", TABLE3, "SBO-RTAMT", "SMuRF")):
        tt = ratios(tab[base]["TT"], tab[ours]["TT"])
        tm = ratios(tab[base]["TM"], tab[ours]["TM"])
        it = ratios(tab[base]["S"], tab[ours]["S"])
        print(f"{name} total-monitoring-time speedup {base}/{ours}:", [round(x, 1) for x in tt], "geomean", round(gmean(tt), 1))
        print(f"{name} per-iteration monitoring speedup:          ", [round(x, 1) for x in tm], "geomean", round(gmean(tm), 1))
        print(f"{name} iteration ratio (>1 = ours needs fewer):   ", [round(x, 2) for x in it], "geomean", round(gmean(it), 2))
        for m in (base, ours):
            prod = [s * t for s, t in zip(tab[m]["S"], tab[m]["TM"])]
            print(f"   consistency {m:9s} S*TM vs TT:", [f"{p:.3f}/{t:.3f}" for p, t in zip(prod, tab[m]["TT"])])
    t5 = ratios(TABLE5["LCW"], TABLE5["LCP"])
    print("T5 LCW/LCP iteration ratio:", [round(x, 2) for x in t5], "geomean", round(gmean(t5), 2))

    print("\n== Internal-consistency observations ==")
    print("T4 S_min == T2 PROF S_bar:", TABLE4["S_min"] == [round(x, 2) for x in TABLE2["PROF"]["S"]])
    i = 3
    print("T4 phi4 (S, TT, TM) == T3 SMuRF phi4:",
          (TABLE4["S"][i], TABLE4["TT"][i], TABLE4["TM"][i]) == (TABLE3["SMuRF"]["S"][i], TABLE3["SMuRF"]["TT"][i], TABLE3["SMuRF"]["TM"][i]))
    print("T1 phi1 vs phi5 (satisfaction %, #boxes):",
          (TABLE1["satisfaction_ratio_pct"][0], TABLE1["number_of_boxes"][0]),
          (TABLE1["satisfaction_ratio_pct"][4], TABLE1["number_of_boxes"][4]))
    print("T1 formula with 85 boxes:", REQS[TABLE1["number_of_boxes"].index(85)], "(text on p.7 says phi4)")
