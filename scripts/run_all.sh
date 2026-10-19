#!/usr/bin/env bash
# Full evaluation pipeline. Stages can be run separately; every runner is resumable (finished
# trials are skipped when re-run with the same --run-id). Times are measured on an i5-1335U
# (10 cores / 12 threads, 15.7 GB RAM) with --workers 10.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/Scripts/python.exe}     # Linux/macOS: .venv/bin/python
W=${WORKERS:-10}
MATLAB=${MATLAB:-matlab}               # e.g. MATLAB="/c/Program Files/MATLAB/R2026b/bin/matlab.exe"
export PYTHONUTF8=1

"$PY" -m pytest -q                                                      # ~1 min: all unit tests
"$PY" experiments/run_e1_monitoring.py --config configs/e1_monitoring.yaml --run-id main --workers "$W"   # ~2 min  (Table 1)
"$PY" experiments/run_falsification.py --config configs/falsification.yaml --run-id main --workers "$W"   # ~22 min (Tables 2-3)
"$PY" experiments/run_falsification.py --config configs/table4.yaml --run-id main --workers "$W"         # ~92 min (Table 4)
"$PY" experiments/run_control.py --config configs/control.yaml --run-id main --workers "$W"              # ~97 min (Table 5)
"$PY" experiments/run_control_bo.py --config configs/control_bo.yaml --run-id main --workers "$W"        # E6 (reduced scale)
"$PY" analysis/make_tables.py --e1 main --falsification main --table4 main --control main --control-bo main
"$PY" analysis/grid_sensitivity.py --n 2000 --workers "$W"
"$PY" analysis/plot_falsification.py --run-id main
"$PY" analysis/box_reachability.py --e1 main --falsification main --table4 main
"$PY" analysis/plot_figures.py                                          # illustrations for Figs. 1-4

# FindBox languages (paper ref. [5]). FindBox has NO license: it is fetched only on explicit request
# (bash scripts/fetch_findbox.sh), used locally, never redistributed (DEVIATIONS A1b).
if [ -d external/FindBox ]; then
  # ~2.6 h for 9 of the 10 languages; best-effort phi1 alone needs 16-20 h+ (results/raw/findbox/main/INCOMPLETE.md)
  "$PY" experiments/run_findbox.py --config configs/findbox.yaml --run-id main --workers "$W"
  for v in default besteffort; do
    "$PY" experiments/run_falsification.py --config "configs/falsification_findbox_$v.yaml" \
      --run-id "findbox_$v" --workers "$W"
    "$PY" analysis/make_tables.py --falsification "findbox_$v"
    "$PY" analysis/plot_falsification.py --run-id "findbox_$v"
  done
  "$PY" analysis/findbox_quality.py --findbox main --e1 main
else
  echo "external/FindBox missing: FindBox stages skipped (see scripts/fetch_findbox.sh)"
fi

# Check of the Chasing Cars port against the official Simulink model (needs MATLAB + Simulink).
if command -v "$MATLAB" >/dev/null 2>&1; then
  bash scripts/fetch_cc_model.sh
  "$PY" scripts/cc_matlab_compare.py export                             # 200 seeded inputs + our outputs
  "$PY" scripts/cc_matlab_compare.py export-falsifiers --run main       # the falsifiers of Tables 2-3
  RUN="run('scripts/matlab/run_cc_reference.m')"
  STEP="input_mode='step'; reltol='1e-6'; abstol='1e-6';"                   # setting (b)
  TIGHT="input_mode='step'; reltol='1e-10'; abstol='1e-10'; minstep='auto';" # setting (c)
  FALS="in_csv='falsifiers_main_inputs.csv';"
  "$MATLAB" -batch "$RUN"                                                                    # (a) ~10 min
  "$MATLAB" -batch "$STEP out_csv='cc_outputs_simulink_step_tol1e-6.csv'; $RUN"              # (b) ~3 min
  "$MATLAB" -batch "$TIGHT out_csv='cc_outputs_simulink_step_tol1e-10.csv'; $RUN"            # (c)
  "$MATLAB" -batch "$FALS out_csv='falsifiers_main_simulink.csv'; $RUN"                      # (a) ~5 min
  "$MATLAB" -batch "$FALS $STEP out_csv='falsifiers_main_simulink_step_tol1e-6.csv'; $RUN"    # (b) ~5 min
  "$MATLAB" -batch "$FALS $TIGHT out_csv='falsifiers_main_simulink_step_tol1e-10.csv'; $RUN"  # (c)
  "$PY" scripts/cc_matlab_compare.py compare                            # -> results/tables/cc_port_vs_simulink.md
else
  echo "MATLAB not found: Simulink comparison skipped"
fi
