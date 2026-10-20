#!/usr/bin/env python3
"""Local, read-only showcase server, including HTTP byte ranges for video seeking."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = Path(self.translate_path(self.path))
        if any(part.startswith(".") or part == "node_modules" for part in path.relative_to(ROOT).parts):
            self.send_error(404)
            return None
        value = self.headers.get("Range")
        if not value or not path.is_file():
            return super().send_head()
        match = re.fullmatch(r"bytes=(\d+)-(\d*)", value)
        if not match:
            self.send_error(416)
            return None
        size = path.stat().st_size
        start = int(match[1])
        end = min(int(match[2]) if match[2] else size - 1, size - 1)
        if start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        stream = path.open("rb")
        stream.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.range_remaining = end - start + 1
        return stream

    def copyfile(self, source, outputfile):
        if not hasattr(self, "range_remaining"):
            return super().copyfile(source, outputfile)
        remaining = self.range_remaining
        del self.range_remaining
        try:
            while remaining:
                block = source.read(min(262144, remaining))
                if not block:
                    break
                outputfile.write(block)
                remaining -= len(block)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8249)
    args = parser.parse_args()
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port), functools.partial(Handler, directory=str(ROOT))
    )
    print(f"Briefing Studio: http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
