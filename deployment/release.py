"""Package or install exactly one checksum-pinned, existing FDA release."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from common import sha256_file
from runtime import OverviewRuntime


FILES = ("release.json", "fda.sqlite3", "metadata.json", "page-inventory.json", "saved-overview.json")
MAX_BYTES = 128 * 1024 * 1024
HEX = re.compile(r"[0-9a-f]{64}")
REDIRECT_HOSTS = {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def read_lock(path):
    value = json.loads(Path(path).read_bytes())
    if (not isinstance(value, dict) or set(value) != {"formatVersion", "releaseId", "archive", "files"}
            or type(value["formatVersion"]) is not int or value["formatVersion"] != 1):
        raise ValueError("Unsupported deployment lock.")
    identity = value["releaseId"]
    if not isinstance(identity, str) or not re.fullmatch(r"fda-release-sha256:[0-9a-f]{64}", identity):
        raise ValueError("Invalid pinned release identity.")
    archive = value["archive"]
    if (not isinstance(archive, dict) or set(archive) != {"name", "bytes", "sha256"}
            or archive["name"] != f"fda-{identity.split(':')[1]}.tar.gz"):
        raise ValueError("Invalid archive identity.")
    if not isinstance(value["files"], dict) or set(value["files"]) != set(FILES):
        raise ValueError("Incomplete pinned file inventory.")
    for item in value["files"].values():
        if not isinstance(item, dict) or set(item) != {"bytes", "sha256"}:
            raise ValueError("Invalid pinned file record.")
    records = [archive, *value["files"].values()]
    for item in records:
        if (type(item["bytes"]) is not int or not 0 < item["bytes"] <= MAX_BYTES
                or not isinstance(item["sha256"], str) or not HEX.fullmatch(item["sha256"])):
            raise ValueError("Invalid pinned size or checksum.")
    if sum(item["bytes"] for item in value["files"].values()) > MAX_BYTES:
        raise ValueError("Unpacked release exceeds the bounded size.")
    return value


def inventory(root):
    root = Path(root)
    if {item.name for item in root.iterdir()} != set(FILES):
        raise ValueError("Release must contain only the five approved files.")
    result = {}
    for name in FILES:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Release members must be ordinary files.")
        result[name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    return result


def verify_directory(root, lock):
    if inventory(root) != lock["files"]:
        raise ValueError("Installed release bytes differ from the deployment lock.")
    reader = OverviewRuntime(root)
    if reader.release_id != lock["releaseId"]:
        raise ValueError("Installed release identity differs from the deployment lock.")
    return reader


def pack_release(root, release_id, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError("Packaging output must be outside the source release.")
    reader = OverviewRuntime(root)
    if reader.release_id != release_id:
        raise ValueError("Source release differs from the selected release.")
    files = inventory(root)
    if sum(item["bytes"] for item in files.values()) > MAX_BYTES:
        raise ValueError("Release exceeds the bounded size.")
    output.mkdir(parents=True, exist_ok=False)
    archive = output / f"fda-{release_id.split(':')[1]}.tar.gz"
    # No timestamps, owners, ACLs or platform-dependent archive paths.
    with archive.open("xb") as destination, gzip.GzipFile(fileobj=destination, filename="", mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as bundle:
            for name in FILES:
                member = tarfile.TarInfo(name)
                member.size, member.mode, member.mtime = files[name]["bytes"], 0o444, 0
                with (root / name).open("rb") as stream:
                    bundle.addfile(member, stream)
    if inventory(root) != files:
        raise ValueError("Source release changed during packaging.")
    lock = {"formatVersion": 1, "releaseId": release_id,
            "archive": {"name": archive.name, "bytes": archive.stat().st_size, "sha256": sha256_file(archive)},
            "files": files}
    write_json(output / "release.lock.json", lock)
    read_lock(output / "release.lock.json")
    return lock


def extract_release(archive, lock, destination):
    if Path(destination).is_symlink():
        raise ValueError("Destination must not be a symlink.")
    archive, destination = Path(archive), Path(destination).resolve()
    if archive.stat().st_size != lock["archive"]["bytes"] or sha256_file(archive) != lock["archive"]["sha256"]:
        raise ValueError("Archive differs from its pinned size or checksum.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # A fresh directory inherits its parent's permissions, not a private temp ACL.
    destination.mkdir(exist_ok=False)
    seen = set()
    try:
        with tarfile.open(archive, mode="r:gz") as bundle:
            for member in bundle:
                if member.name not in FILES or member.name in seen or not member.isreg() or member.pax_headers:
                    raise ValueError("Unsafe, duplicate or unexpected archive member.")
                expected = lock["files"][member.name]
                if member.size != expected["bytes"]:
                    raise ValueError("Archive member exceeds its exact pinned size.")
                seen.add(member.name)
                digest, size = hashlib.sha256(), 0
                with bundle.extractfile(member) as source, (destination / member.name).open("xb") as target:
                    while chunk := source.read(1024 * 1024):
                        size += len(chunk)
                        if size > expected["bytes"]:
                            raise ValueError("Archive member exceeded its pinned size.")
                        digest.update(chunk)
                        target.write(chunk)
                if size != expected["bytes"] or digest.hexdigest() != expected["sha256"]:
                    raise ValueError("Extracted file failed its checksum.")
        if seen != set(FILES):
            raise ValueError("Archive is missing approved release files.")
        verify_directory(destination, lock)
    except Exception:
        # Only remove our allowlisted files from the directory we just created.
        for name in FILES:
            (destination / name).unlink(missing_ok=True)
        destination.rmdir()
        raise
    for name in FILES:
        (destination / name).chmod(0o444)
    return destination


def approved_url(url, lock):
    parsed = urlsplit(url)
    prefix = "/Abdul-RahmanSayed/Project-Lab/releases/download/"
    if (parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment
            or not parsed.path.startswith(prefix)):
        raise ValueError("Use the reviewed repository's exact HTTPS release-asset URL.")
    tail = parsed.path[len(prefix):].split("/")
    if (len(tail) != 2 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", tail[0])
            or tail[0].lower() == "latest" or tail[1] != lock["archive"]["name"]):
        raise ValueError("A fixed release tag and the pinned archive filename are required.")
    return url


class ReleaseRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if (parsed.scheme != "https" or parsed.hostname not in REDIRECT_HOSTS or parsed.username
                or parsed.password or parsed.port not in (None, 443)):
            raise ValueError("Unexpected release-download redirect.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_release(url, lock, destination):
    request = Request(approved_url(url, lock), headers={"User-Agent": "Project-Lab-release-build"})
    with tempfile.TemporaryDirectory(prefix="fda-download-") as temporary:
        archive = Path(temporary) / "release.tar.gz"
        with build_opener(ReleaseRedirects()).open(request, timeout=30) as response, archive.open("xb") as target:
            size = 0
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > lock["archive"]["bytes"]:
                    raise ValueError("Download exceeded the pinned archive size.")
                target.write(chunk)
        return extract_release(archive, lock, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("pack")
    pack.add_argument("--release-directory", type=Path, required=True)
    pack.add_argument("--release-id", required=True)
    pack.add_argument("--output-directory", type=Path, required=True)
    for name in ("extract", "fetch"):
        command = commands.add_parser(name)
        command.add_argument("--lock", type=Path, required=True)
        command.add_argument("--destination", type=Path, required=True)
        command.add_argument("--archive" if name == "extract" else "--url", required=True)
    args = parser.parse_args()
    if args.command == "pack":
        print(json.dumps(pack_release(args.release_directory, args.release_id, args.output_directory), indent=2))
    else:
        lock = read_lock(args.lock)
        if args.command == "extract":
            extract_release(args.archive, lock, args.destination)
        else:
            fetch_release(args.url, lock, args.destination)
        print("Installed checked release: " + lock["releaseId"])


if __name__ == "__main__":
    main()
