#!/usr/bin/env bash
# Download the canonical ARCH-COMP Chasing Cars model (~85 KB of Simulink text) for verification of
# the Python port. Not needed to run the experiments. The model stays in external/ (git-ignored):
# ARCH-COMP's license grants hosting/use for non-commercial research reproduction, content remains
# owned by its contributors, so we do not redistribute it.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p external/chasing-cars
BASE="https://gitlab.com/api/v4/projects/goranf%2FARCH-COMP/repository/files/models%2FFALS%2Fchasing-cars"
for f in cars.mdl requirements.txt run_cars.m test_cars.m; do
  curl -fsSL -o "external/chasing-cars/$f" "$BASE%2F$f/raw?ref=8e11a799"
done
EXPECTED=3fe04206e40ac8b32203c49e494d5ae981873ef6dbd5d9f54c72c42de0d33520
ACTUAL=$(sha256sum external/chasing-cars/cars.mdl | cut -d' ' -f1)
if [ "$ACTUAL" != "$EXPECTED" ]; then echo "sha256 mismatch: $ACTUAL" >&2; exit 1; fi
echo "OK: external/chasing-cars/cars.mdl (sha256 verified). Now run: python scripts/verify_cc_port.py"
