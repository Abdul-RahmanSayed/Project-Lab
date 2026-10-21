"""Loopback HTTPS static preview, without an API proxy or deployment side effects."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPSServer


class QuietFiles(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--port", type=int, default=4174)
    parser.add_argument("--certfile", required=True)
    parser.add_argument("--keyfile", required=True)
    args = parser.parse_args()
    server = ThreadingHTTPSServer(("127.0.0.1", args.port), partial(QuietFiles, directory=args.directory),
                                 certfile=args.certfile, keyfile=args.keyfile)
    try:
        server.serve_forever()
    finally:
        server.server_close()
