"""Run existing API regressions against the installed image, with test-only wheels."""

import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


def main():
    wheels = Path("/checks/wheels")
    for filename in ("certifi-2026.10.19-py3-none-any.whl", "httpcore-1.0.9-py3-none-any.whl",
                     "httpx-0.28.1-py3-none-any.whl"):
        path = wheels / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        sys.path.append(str(path))

    import backend
    from backend.config import Settings
    from common import sha256_file, write_json

    # Only the test module is mounted; app imports still resolve to the installed package.
    backend.__path__.append("/checks/backend")
    tests = importlib.import_module("backend.test_api")
    original = Path("/opt/fda/release")
    before = sha256_file(original / "fda.sqlite3")
    with tempfile.TemporaryDirectory(prefix="fda-api-regression-") as temporary:
        release = Path(temporary) / "release"
        shutil.copytree(original, release)
        identity = json.loads((release / "metadata.json").read_bytes())["releaseId"]
        tests.SETTINGS = Settings(release, identity)
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    unchanged = sha256_file(original / "fda.sqlite3") == before
    write_json("/evidence/regression-results.json", {"testsRun": result.testsRun,
               "failures": len(result.failures), "errors": len(result.errors), "releaseId": identity,
               "python": sys.version, "originalDatabaseUnchanged": unchanged,
               "method": "Installed Linux runtime; three pure-Python test wheels mounted read-only; corruption tests use temporary copies, not the serving release."})
    raise SystemExit(not result.wasSuccessful() or not unchanged)


if __name__ == "__main__":
    main()
