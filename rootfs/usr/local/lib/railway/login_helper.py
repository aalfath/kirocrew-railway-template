"""Loopback-only helper behind Caddy's basic auth on /login.

Mints a short-lived KiroCrew dashboard link with the gateway's own
`kirocrew token` command (which only works from this container) and
redirects the browser to it. It never logs the token.
"""
import os
import subprocess
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ["KIROCREW_LOGIN_PORT"])
GW_PORT = os.environ["KIROCREW_INTERNAL_PORT"]
TTL = os.environ.get("KIROCREW_LOGIN_TTL", "15m")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # keep tokens out of the logs
        return

    def _send(self, code, body):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.split("?")[0] != "/login":
            return self._send(404, "not found\n")
        try:
            out = subprocess.run(
                ["kirocrew", "token", "--ttl", TTL, "--port", GW_PORT],
                capture_output=True, text=True, timeout=60,
            )
        except Exception as exc:  # noqa: BLE001
            return self._send(503, f"could not mint a sign-in link: {exc.__class__.__name__}\n")
        token = None
        for line in out.stdout.split():
            if "token=" in line:
                query = urllib.parse.urlparse(line.strip()).query
                token = urllib.parse.parse_qs(query).get("token", [None])[0]
                if token:
                    break
        if not token:
            return self._send(503, "KiroCrew is still starting; try again in a minute.\n")
        self.send_response(302)
        self.send_header("Location", "/?token=" + urllib.parse.quote(token, safe=""))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
