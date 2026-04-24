"""
MailForge — single-command dev launcher.

    python run.py

Starts:
  • FastAPI backend  → http://localhost:8000
  • Static frontend  → http://localhost:8080
  • Opens browser    → http://localhost:8080  (after servers are ready)

Options:
  --api-only          Start API server only (no frontend, no browser)
  --api-port  INT     Override API port    (default: 8000)
  --ui-port   INT     Override UI port     (default: 8080)
  --no-browser        Don't open browser automatically
"""

import argparse
import os
import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# ── Paths (all absolute so os.chdir never breaks anything) ───────────────────
ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"


# ── Argument parsing ──────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="MailForge dev launcher")
    p.add_argument("--api-only",   action="store_true", help="Start API server only")
    p.add_argument("--api-port",   type=int, default=int(os.getenv("API_PORT", 8000)))
    p.add_argument("--ui-port",    type=int, default=int(os.getenv("FRONTEND_PORT", 8080)))
    p.add_argument("--no-browser", action="store_true", help="Skip opening browser")
    return p.parse_args()


# ── API server ────────────────────────────────────────────────────────────────

def run_api(api_port):
    import subprocess
    print(f"\n  API  ->  http://localhost:{api_port}")
    print(f"  Docs ->  http://localhost:{api_port}/docs  (dev only)\n")
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "app.api:app",
            "--host", "0.0.0.0",
            "--port", str(api_port),
            "--reload",
            "--reload-dir", str(ROOT / "app"),
        ],
        cwd=str(ROOT),
        check=True,
    )


# ── Frontend server ───────────────────────────────────────────────────────────

class _NoCacheHandler(SimpleHTTPRequestHandler):
    """Serve static files — no os.chdir needed, uses absolute FRONTEND_DIR."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # Suppress per-request noise


def run_frontend(ui_port):
    print(f"  UI   ->  http://localhost:{ui_port}\n")
    server = HTTPServer(("localhost", ui_port), _NoCacheHandler)
    server.serve_forever()


# ── Browser opener ────────────────────────────────────────────────────────────

def open_browser(ui_port, delay=2.5):
    """Wait briefly for servers to bind, then open default browser."""
    time.sleep(delay)
    url = f"http://localhost:{ui_port}"
    print(f"  Opening {url} in browser...\n")
    webbrowser.open(url)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print("\n" + "=" * 45)
    print("   MailForge — starting up")
    print("=" * 45)

    if args.api_only:
        run_api(args.api_port)
        return

    # API in background daemon thread
    threading.Thread(
        target=run_api, args=(args.api_port,), daemon=True, name="api"
    ).start()

    # Browser opener in background daemon thread
    if not args.no_browser:
        threading.Thread(
            target=open_browser, args=(args.ui_port,), daemon=True, name="browser"
        ).start()

    # Frontend blocks the main thread — Ctrl+C stops everything
    run_frontend(args.ui_port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Shutting down MailForge. Bye!\n")
