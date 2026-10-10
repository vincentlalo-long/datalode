from __future__ import annotations

import http.server
import json
import mimetypes
import os
import shutil
import socketserver
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from PIL import Image

mimetypes.add_type("application/octet-stream", ".skel")
mimetypes.add_type("text/plain", ".atlas")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("application/json", ".json")

RENDER_HTML_PATH = Path(__file__).resolve().parent / "render_page.html"
CONVERTER_EXE = Path(__file__).resolve().parent.parent.parent / "tools" / "SpineSkeletonDataConverter.exe"


def find_browser_executable() -> Path:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        p = Path(c)
        if p.is_file():
            return p

    # Check PATH
    for name in ["msedge", "chrome", "google-chrome", "chromium"]:
        found = shutil.which(name)
        if found:
            return Path(found)

    raise FileNotFoundError("Could not find Edge or Chrome executable for headless rendering.")


def ensure_spine_json(skel_path: Path) -> Path | None:
    json_path = skel_path.with_suffix(".json")
    if json_path.is_file() and json_path.stat().st_size > 100:
        return json_path

    if not CONVERTER_EXE.is_file():
        raise FileNotFoundError(f"SpineSkeletonDataConverter.exe not found at {CONVERTER_EXE}")

    cmd = [str(CONVERTER_EXE), str(skel_path), str(json_path)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if res.returncode == 0 and json_path.is_file():
        return json_path
    print(f"[Converter Error] {res.stderr or res.stdout}")
    return None


class RenderServerHandler(http.server.SimpleHTTPRequestHandler):
    output_dir: Path
    last_error: str | None = None

    def do_GET(self):
        if self.path.startswith("/render"):
            content = RENDER_HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        elif self.path.startswith("/assets/"):
            rel_asset = self.path[len("/assets/"):]
            asset_path = RENDER_HTML_PATH.parent / "assets" / rel_asset
            if asset_path.is_file():
                self.serve_file(asset_path, "application/javascript")
            else:
                self.send_error(404, "Asset not found")

        elif self.path.startswith("/api/log"):
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(self.path).query)
            if "error" in query:
                RenderServerHandler.last_error = query["error"][0]
                print(f"\n[Browser Error] {query['error'][0]}")
            elif "msg" in query:
                pass  # Silent logging in batch mode
            self.send_json({"ok": True})

        elif self.path.startswith("/api/info"):
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(self.path).query)
            char_id = query.get("char", [""])[0]
            char_dir = self.output_dir / char_id

            if not char_dir.is_dir():
                self.send_json({"error": f"Character directory not found: {char_id}"}, 404)
                return

            skel = list(char_dir.glob("*.skel"))
            atlas = list(char_dir.glob("*.atlas"))

            if not skel or not atlas:
                self.send_json({"error": "Missing .skel or .atlas"}, 400)
                return

            json_file = ensure_spine_json(skel[0])
            if not json_file:
                self.send_json({"error": "Failed to convert Spine binary (.skel) to JSON"}, 500)
                return

            self.send_json({
                "char": char_id,
                "json": json_file.name,
                "atlas": atlas[0].name,
            })

        elif self.path.startswith("/outputs/"):
            rel_path = self.path[len("/outputs/"):]
            file_path = (self.output_dir / rel_path).resolve()
            if file_path.is_file() and str(file_path).startswith(str(self.output_dir.resolve())):
                mime, _ = mimetypes.guess_type(str(file_path))
                self.serve_file(file_path, mime or "application/octet-stream")
            else:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "Not found")

    def serve_file(self, path: Path, content_type: str):
        try:
            content = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def send_json(self, data: object, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Silent


class HeadlessRenderer:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.browser_exe = find_browser_executable()
        RenderServerHandler.output_dir = output_dir

        self.server = socketserver.TCPServer(("127.0.0.1", 0), RenderServerHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def render_character(self, char_id: str, out_file: Path, width: int = 1600, height: int = 2200) -> bool:
        RenderServerHandler.last_error = None
        url = f"http://127.0.0.1:{self.port}/render?char={char_id}"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.browser_exe),
            "--headless=new",
            "--enable-webgl",
            "--use-gl=angle",
            "--default-background-color=00000000",
            f"--window-size={width},{height}",
            "--virtual-time-budget=3000",
            f"--screenshot={out_file}",
            url,
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)

            if RenderServerHandler.last_error:
                if out_file.is_file():
                    out_file.unlink(missing_ok=True)
                return False

            if out_file.is_file() and out_file.stat().st_size > 30000:
                # Autotrim transparent margins
                try:
                    img = Image.open(out_file)
                    bbox = img.getbbox()
                    if bbox:
                        w, h = img.size
                        pad = 16
                        box = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(w, bbox[2] + pad), min(h, bbox[3] + pad))
                        img.crop(box).save(out_file)
                except Exception:
                    pass
                return True
            elif out_file.is_file():
                # Corrupted / too small (e.g. error screen)
                out_file.unlink(missing_ok=True)
        except Exception:
            pass

        return False

    def close(self):
        try:
            self.server.shutdown()
            self.server.server_close()
        except Exception:
            pass
