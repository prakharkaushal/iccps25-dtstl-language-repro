"""Check the Python Chasing Cars port against the official Simulink/Stateflow model text.

Run scripts/fetch_cc_model.sh first. Parses external/chasing-cars/cars.mdl (read as data, nothing is
executed) and checks that the Stateflow during-actions, transition guards, initial values, car wiring
and solver settings are the ones transcribed in src/langfal/systems/chasing_cars.py.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MDL = ROOT / "external" / "chasing-cars" / "cars.mdl"


def main():
    if not MDL.exists():
        sys.exit(f"missing {MDL}; run scripts/fetch_cc_model.sh first")
    txt = MDL.read_text(encoding="utf-8", errors="replace")
    sf = txt[txt.index("\nStateflow {"):]
    model = txt[:txt.index("\nStateflow {")]
    lab = lambda b: "".join(re.findall(r'"([^"]*)"', re.findall(r'labelString\s+((?:"[^"]*"\s*)+)', b, re.S)[0])) \
        if re.search(r"labelString", b) else ""
    charts = {re.search(r"^\s*id\s+(\d+)", m.group(1), re.M).group(1): re.search(r'name\s+"(.*?)"', m.group(1)).group(1)
              for m in re.finditer(r"\n  chart \{\n(.*?)\n  \}", sf, re.S)}
    states = {}
    for m in re.finditer(r"\n  state \{\n(.*?)\n  \}", sf, re.S):
        b = m.group(1)
        states.setdefault(charts[re.search(r"chart\s+(\d+)", b).group(1)], []).append(lab(b).replace("\\n", " ").replace(" ", ""))
    guards = {}
    for m in re.finditer(r"\n  transition \{\n(.*?)\n  \}", sf, re.S):
        b = m.group(1)
        g = re.search(r"\[(.*?)\]", lab(b))
        if g:
            guards.setdefault(charts[re.search(r"chart\s+(\d+)", b).group(1)], set()).add(g.group(1).replace(" ", ""))
    inits = {}
    for m in re.finditer(r"\n  data \{\n(.*?)\n  \}", sf, re.S):
        b = m.group(1)
        iv = re.search(r'initialValue\s+"(.*?)"', b)
        if iv:
            inits[(charts[re.search(r"linkNode\s+\[(\d+)", b).group(1)], re.search(r'name\s+"(.*?)"', b).group(1))] = float(iv.group(1))
    checks = []
    checks.append(("lead dynamics", any("v_dot=-Throttle-Brake*v;y_dot=v;" in s for s in states["Car 1"])))
    for c in ("Car 2", "Car 3", "Car 4", "Car 5"):
        s = " ".join(states[c])
        checks.append((f"{c} Chasing", "Chasing" in s and "v_dot=1;y_dot=-v;" in s))
        checks.append((f"{c} Keeping (y_dot=+v, no v_dot)", any(x.startswith("Keeping") and "y_dot=v;" in x and "v_dot" not in x for x in states[c])))
        checks.append((f"{c} Braking", "v_dot=-v;y_dot=-v;" in s))
        checks.append((f"{c} guards", guards[c] == {"y-y_in<=10", "y-y_in>=15", "y-y_in>=20", "y-y_in<=5"}))
    for i, c in enumerate(["Car 1", "Car 2", "Car 3", "Car 4", "Car 5"]):
        checks.append((f"{c} y(0) = {10 * i}", inits.get((c, "y")) == 10.0 * i))
        checks.append((f"{c} v(0) = 0", inits.get((c, "v")) == 0.0))
    wires, i = set(), 0
    while (j := model.find("Line {", i)) >= 0:          # walk balanced braces (Lines nest Branch blocks)
        depth, k = 0, j
        while True:
            depth += {"{": 1, "}": -1}.get(model[k], 0)
            if depth == 0 and model[k] == "}":
                break
            k += 1
        blk, i = model[j:k + 1], k + 1
        src = re.search(r'SrcBlock\s+"(.*?)"', blk)
        for dst in re.findall(r'DstBlock\s+"(.*?)"', blk):
            if src:
                wires.add((src.group(1), dst))
    checks.append(("wiring Car i -> Car i+1", all((f"Car {i}", f"Car {i + 1}") in wires for i in range(1, 5))))
    for k, v in (("Solver", "VariableStepAuto"), ("RelTol", "1e-3"), ("StopTime", "100")):
        m = re.search(r'^\s*%s\s+"(.*?)"' % k, model, re.M)
        checks.append((f"{k} = {v}", bool(m) and m.group(1) == v))
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    sys.exit(0 if all(ok for _, ok in checks) else 1)


if __name__ == "__main__":
    main()
