#!/usr/bin/env bash
# Download FindBox (code of the paper's ref. [5]) at the commit used here, into the git-ignored external/.
# NOTE: the repository has NO license (all rights reserved by default). It is used locally for this
# research reproduction at the user's explicit request and must not be redistributed.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p external
if [ ! -d external/FindBox/.git ]; then
  git clone --quiet https://github.com/Chris-amV/FindBox external/FindBox
fi
git -C external/FindBox checkout --quiet bf19736f7cda031eb48927bd8793e0d6d8f2c9bb
echo "FindBox at $(git -C external/FindBox rev-parse --short HEAD) in external/FindBox"
