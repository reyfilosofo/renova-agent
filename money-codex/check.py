"""Run the module's acceptance tests from any working directory."""
from pathlib import Path
import os
import sys
import unittest

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
# Tests that spawn Python must resolve this package from any invoking directory.
inherited_python_path = os.environ.get("PYTHONPATH")
os.environ["PYTHONPATH"] = str(root) + (os.pathsep + inherited_python_path if inherited_python_path else "")
suite = unittest.defaultTestLoader.discover(str(root / 'tests'))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
