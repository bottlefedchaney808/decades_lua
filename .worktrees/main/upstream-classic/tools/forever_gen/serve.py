#!/usr/bin/env python3
"""Minimal static server: URL /forever/<path> -> dist/forever/<path>.
Also serves /classic/ -> dist/classic/ for comparison. Port 8080."""
import os, sys, http.server, functools

ROOT = r"E:\WoW4_SiMs\.worktrees\main\upstream-classic\dist"

class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # strip query
        path = path.split("?")[0]
        if path.startswith("/forever/"):
            rel = path[len("/forever/"):]
        elif path.startswith("/classic/"):
            rel = path[len("/classic/"):]
        elif path in ("/", "/forever", "/classic"):
            rel = ""
        else:
            rel = path.lstrip("/")
        base = "forever" if path.startswith("/forever") else "classic"
        full = os.path.join(ROOT, base, rel)
        return full
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Serving {ROOT} on http://127.0.0.1:{port}/forever/", flush=True)
    srv.serve_forever()
