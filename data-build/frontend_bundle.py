"""Export only checked public metadata, the default overview, and API schemas."""

import argparse
import json
from pathlib import Path

from backend.app import create_app
from backend.config import Settings
from backend.fda.service import Service
from common import sha256_file


def write_public_json(path, value):
    # These byte-hashed public files have a matching narrow Git LF rule.
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def export(directory, release_id, output):
    settings = Settings(directory.resolve(), release_id)
    checked = Service(settings)
    schema = create_app(settings).openapi()
    schema["x-project-lab-release"] = checked.release_id
    artifacts = {
        "saved-overview.json": json.loads(checked.default_payload),
        "metadata.json": json.loads(checked.metadata_payload),
        "api-schema.json": schema,
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        write_public_json(output / name, content)
    write_public_json(output / "bundle.json", {"releaseId": checked.release_id, "files": {
        name: {"sha256": sha256_file(output / name), "bytes": (output / name).stat().st_size}
        for name in artifacts}})
    print(f"Exported checked public frontend bundle: {checked.release_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--output-directory", type=Path, default=Path("web/src/generated"))
    args = parser.parse_args()
    export(args.release_directory, args.release_id, args.output_directory)
