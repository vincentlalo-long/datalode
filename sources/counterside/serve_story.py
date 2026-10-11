#!/usr/bin/env python3
# DataLode: Launch local web server and open Story & Comic Reader

from __future__ import annotations

import http.server
import socketserver
import sys
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_CUTSCENES_DIR, SOURCE_DATA_DIR

PORT = 8765


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from data/counterside root so relative paths to ../backgrounds work seamlessly
        super().__init__(*args, directory=str(SOURCE_DATA_DIR), **kwargs)

    def log_message(self, format, *args):
        # Suppress noisy HTTP request logs
        pass


def main() -> int:
    index_file = DEFAULT_CUTSCENES_DIR / "index.html"
    if not index_file.is_file():
        print(f"[!] Story Reader not built yet. Run first: python sources/counterside/build_stories.py")
        return 1

    url = f"http://localhost:{PORT}/cutscenes/index.html"
    print(f"[*] Starting CounterSide Story & Comic Reader at:")
    print(f"    -> {url}")
    print(f"[*] Press Ctrl+C to stop the server.")

    webbrowser.open(url)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[OK] Server stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
