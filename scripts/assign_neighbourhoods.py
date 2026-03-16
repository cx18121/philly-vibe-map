# Importable alias for 03_assign_neighbourhoods.py
# Scripts with numeric prefixes cannot be imported directly as Python modules.
# This thin wrapper re-exports assign_neighbourhoods() for use in tests and other scripts.
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_module_path = Path(__file__).parent / "03_assign_neighbourhoods.py"
if not _module_path.exists():
    raise ImportError(
        f"03_assign_neighbourhoods.py not found at {_module_path}. "
        "Create the implementation file first."
    )

_spec = spec_from_file_location("_03_assign_neighbourhoods", _module_path)
_mod = module_from_spec(_spec)
_spec.loader.exec_module(_mod)

assign_neighbourhoods = _mod.assign_neighbourhoods
