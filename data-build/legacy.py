"""Recover the pre-extraction CLI from its pinned local Git revision for verification."""

import json
from pathlib import Path
import subprocess

from common import LAB_ROOT


def ensure_legacy(source_repo):
    lock = json.loads(Path(__file__).with_name("fda_source.lock.json").read_text(encoding="utf-8"))
    source_repo = Path(source_repo).resolve()
    text = subprocess.check_output(["git", "-c", "safe.directory=" + source_repo.as_posix(),
        "-C", str(source_repo), "show", lock["source"]["revision"] + ":part2.py"], encoding="utf-8")
    root = LAB_ROOT / "generated" / "slice2" / "baseline"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "part2.py"
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise ValueError("Preserved baseline differs from the pinned Git revision.")
    else:
        path.write_text(text, encoding="utf-8", newline="\n")
    return root
