# Importable alias for 02_build_schema.py
# Scripts with numeric prefixes cannot be imported directly as Python modules.
# This thin wrapper re-exports build_schema() for use in tests and other scripts.
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_module_path = Path(__file__).parent / "02_build_schema.py"
_spec = spec_from_file_location("_02_build_schema", _module_path)
_mod = module_from_spec(_spec)
_spec.loader.exec_module(_mod)

build_schema = _mod.build_schema
