"""List the globals referenced by every .pkl under the SPGA tree, without unpickling anything."""
import pickletools
import sys
from collections import Counter
from pathlib import Path

from safe_pickle import DEFAULT_SPGA_ROOT

root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SPGA_ROOT
refs = Counter()
for p in sorted(root.rglob("*.pkl")):
    strings = []
    for op, arg, _ in pickletools.genops(p.read_bytes()):
        if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE", "BINUNICODE8"):
            strings.append(arg)
        if op.name == "GLOBAL":
            refs[arg] += 1
        elif op.name == "STACK_GLOBAL" and len(strings) >= 2:
            refs[f"{strings[-2]} {strings[-1]}"] += 1
for k, v in refs.most_common():
    print(v, k)
