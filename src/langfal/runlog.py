"""Run metadata and result records (JSON Lines), for provenance and resumable experiments."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = Path(__file__).resolve().parent


def source_hash() -> str:
    """sha256 over all source files of the package (the project is not a git repository)."""
    h = hashlib.sha256()
    for p in sorted(SRC_ROOT.rglob("*.py")):
        h.update(p.relative_to(SRC_ROOT).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def environment() -> dict:
    import numpy, scipy, sklearn
    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "numpy": numpy.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__,
    }
    try:
        from importlib.metadata import version
        info["rtamt"] = version("rtamt")
        info["antlr4-python3-runtime"] = version("antlr4-python3-runtime")
    except Exception:          # pragma: no cover
        pass
    try:
        import ctypes

        class _MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
        ms = _MS()
        ms.dwLength = ctypes.sizeof(_MS)
        if hasattr(ctypes, "windll") and ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            info["ram_gb"] = round(ms.ullTotalPhys / 2**30, 1)
    except Exception:          # pragma: no cover
        pass
    return info


def now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


class RunDir:
    """results/raw/<experiment>/<run_id>/ with meta.json and records.jsonl (append-only)."""

    def __init__(self, experiment: str, run_id: str, config: dict, root: Path | None = None):
        root = root or PROJECT_ROOT / "results" / "raw"
        self.path = root / experiment / run_id
        self.path.mkdir(parents=True, exist_ok=True)
        self.records = self.path / "records.jsonl"
        meta_path = self.path / "meta.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {
            "experiment": experiment, "run_id": run_id, "created": now(), "sessions": []}
        meta["config"] = config
        meta["sessions"].append({"started": now(), "argv": sys.argv, "source_sha256": source_hash(),
                                 "environment": environment()})
        meta_path.write_text(json.dumps(meta, indent=1, default=str))
        self.meta_path = meta_path

    def done_keys(self, key_fields) -> set:
        if not self.records.exists():
            return set()
        keys = set()
        for line in self.records.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                keys.add(tuple(r.get(k) for k in key_fields))
        return keys

    def append(self, record: dict):
        with self.records.open("a") as f:
            f.write(json.dumps(record, default=_json_default) + "\n")

    def finish(self, **summary):
        meta = json.loads(self.meta_path.read_text())
        meta["sessions"][-1].update(finished=now(), **summary)
        self.meta_path.write_text(json.dumps(meta, indent=1, default=str))


def _json_default(o):
    import numpy as np
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def read_records(path) -> list:
    path = Path(path)
    if path.is_dir():
        path = path / "records.jsonl"
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
