#!/usr/bin/env bash
# Rebuild every table and figure in results/ from the stored raw records. No experiment is re-run, except
# grid_sensitivity.py, which re-simulates 2,000 seeded Chasing Cars inputs (about a minute).
# Optional stages (FindBox, Simulink) run only if their raw outputs exist.
# Usage: bash scripts/rebuild_results.sh          (PY=... and WORKERS=... override the defaults)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/Scripts/python.exe}     # Linux/macOS: .venv/bin/python
W=${WORKERS:-4}
export PYTHONUTF8=1

"$PY" analysis/make_tables.py --e1 main --falsification main --table4 main --control main --control-bo main
"$PY" analysis/make_tables.py --falsification pilot --table4 pilot --control pilot
"$PY" analysis/plot_falsification.py --run-id main
"$PY" analysis/plot_falsification.py --run-id pilot
"$PY" analysis/box_reachability.py --e1 main --falsification main --table4 main
"$PY" analysis/grid_sensitivity.py --n 2000 --workers "$W"
"$PY" analysis/plot_figures.py

for run in findbox_default findbox_besteffort; do
  if [ -f "results/raw/falsification/$run/records.jsonl" ]; then
    "$PY" analysis/make_tables.py --falsification "$run"
    "$PY" analysis/plot_falsification.py --run-id "$run"
  fi
done
if [ -f results/raw/findbox/main/records.jsonl ]; then
  "$PY" analysis/findbox_quality.py --findbox main --e1 main
fi
if [ -f results/matlab/cc_outputs_simulink.csv ]; then
  "$PY" scripts/cc_matlab_compare.py compare
fi
"$PY" analysis/audit.py                 # last: checks the rebuilt tables against the raw records
echo "results rebuilt; audit summary: $(grep -m1 'PASS,' results/tables/audit.md)"
