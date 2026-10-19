import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from langfal.monitors import ensure_typing_io  # noqa: E402

ensure_typing_io()
