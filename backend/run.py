"""Loopback-only local server; optional benchmark limits affect this process only."""

import argparse
from contextlib import ExitStack
from pathlib import Path
import sys
import threading

import uvicorn
from common import environment, peak_memory, write_json

from .app import create_app
from .config import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--constrained", action="store_true")
    parser.add_argument("--keep-awake", action="store_true")
    parser.add_argument("--control-stdin", action="store_true", help="Benchmark controller closes stdin to stop this server.")
    parser.add_argument("--metrics-output", type=Path)
    args = parser.parse_args()
    with ExitStack() as stack:
        limits = None
        if args.keep_awake:
            from windows_limits import prevent_idle_sleep
            stack.enter_context(prevent_idle_sleep())
        if args.constrained:
            from windows_limits import constrain
            limits = constrain()
        app = create_app(Settings(args.release_directory.resolve(), args.release_id))
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, workers=1,
            limit_concurrency=64, backlog=64, h11_max_incomplete_event_size=8192,
            timeout_keep_alive=5, access_log=False, log_level="warning"))
        if args.control_stdin:
            def stop():
                sys.stdin.readline()
                server.should_exit = True
            threading.Thread(target=stop, daemon=True).start()
        server.run()
        if args.metrics_output:
            write_json(args.metrics_output, {"memory": peak_memory(), "limits": limits, "environment": environment(),
                       "peakActiveSql": app.state.jobs.peak_active, "remainingActiveSql": len(app.state.jobs.active),
                       "outcomes": app.state.jobs.outcomes,
                       "heavyImports": [name for name in ("pandas", "numpy", "matplotlib", "fda_core") if name in sys.modules]})


if __name__ == "__main__":
    main()
