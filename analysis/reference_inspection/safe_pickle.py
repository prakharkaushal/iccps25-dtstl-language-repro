"""Whitelisted unpickler for the SPGA reference result files.

The reference project stores results as pickles. pickle.load / pd.read_pickle can execute
arbitrary code, so we only allow the numpy globals these files actually reference
(verified with list_pickle_globals.py: numpy.core.multiarray.scalar and numpy.dtype).
"""
import io
import pickle
from pathlib import Path

ALLOWED = {
    ("numpy.core.multiarray", "_reconstruct"), ("numpy._core.multiarray", "_reconstruct"),
    ("numpy.core.multiarray", "scalar"), ("numpy._core.multiarray", "scalar"),
    ("numpy", "ndarray"), ("numpy", "dtype"),
    ("numpy.core.numeric", "_frombuffer"), ("numpy._core.numeric", "_frombuffer"),
}

DEFAULT_SPGA_ROOT = Path(__file__).resolve().parents[2] / "reference_project" / "CS637_SPGA" / "spga"


class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in ALLOWED:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"blocked global {module}.{name}")


def load(path):
    return SafeUnpickler(io.BytesIO(Path(path).read_bytes())).load()
