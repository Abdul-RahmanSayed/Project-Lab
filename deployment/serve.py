"""Production wiring for the existing API; the local backend runner is unchanged."""

import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit

import uvicorn

from backend.app import create_app
from backend.config import Settings
from .memory_log import with_memory_log
from .release import read_lock, verify_directory


def origins(value):
    result = value.split(",")
    if not value or len(result) > 5 or len(set(result)) != len(result):
        raise ValueError("Set one to five distinct HTTPS browser origins.")
    for item in result:
        parsed = urlsplit(item)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.path or parsed.query or parsed.fragment or parsed.netloc != parsed.netloc.lower()
                or "*" in item or item != item.strip() or parsed.geturl() != item
                or any(character.isspace() for character in item)):
            raise ValueError("Browser origins must be exact HTTPS origins without paths or credentials.")
        if parsed.port == 443 or (parsed.port is not None and not 1 <= parsed.port <= 65535):
            raise ValueError("Invalid browser origin port.")
    return tuple(result)


def settings_from_environment(lock, environment):
    if environment.get("FDA_RELEASE_ID", lock["releaseId"]) != lock["releaseId"]:
        raise ValueError("Configured release differs from the deployment pin.")
    directory = Path(environment["FDA_RELEASE_DIRECTORY"]).resolve()
    allowed = origins(environment.get("FDA_ALLOWED_ORIGINS", ""))
    port = environment.get("PORT", "10000")
    if not port.isascii() or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise ValueError("PORT must be between 1 and 65535.")
    return Settings(directory, lock["releaseId"], allowed_origins=allowed), int(port)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--host", choices=("127.0.0.1", "0.0.0.0"), default="0.0.0.0")
    parser.add_argument("--ssl-certfile", type=Path)
    parser.add_argument("--ssl-keyfile", type=Path)
    args = parser.parse_args()
    if bool(args.ssl_certfile) != bool(args.ssl_keyfile) or (args.ssl_certfile and args.host != "127.0.0.1"):
        parser.error("Local TLS checks require both certificate files and loopback binding.")
    lock = read_lock(args.lock)
    settings, port = settings_from_environment(lock, os.environ)
    verify_directory(settings.release_directory, lock)
    app = with_memory_log(create_app(settings), lock["releaseId"], os.environ)
    uvicorn.run(app, host=args.host, port=port, workers=1, proxy_headers=False,
                limit_concurrency=64, backlog=64, h11_max_incomplete_event_size=8192,
                timeout_keep_alive=5, access_log=False, log_level="warning",
                ssl_certfile=str(args.ssl_certfile) if args.ssl_certfile else None,
                ssl_keyfile=str(args.ssl_keyfile) if args.ssl_keyfile else None)


if __name__ == "__main__":
    main()
