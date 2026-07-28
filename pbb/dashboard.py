from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse

from pbb import stats

HTML = Path(__file__).with_name("dashboard.html").read_bytes().rstrip(b"\r\n")


def _isoDate(value: str | None, fallback: datetime) -> str:
    if value:
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            return date.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace(
                "+00:00",
                "Z",
            )
        except ValueError:
            pass
    return fallback.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class DashboardHandler(BaseHTTPRequestHandler):
    def _sendJson(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        request = urlparse(self.path)

        if request.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(HTML)))
            self.end_headers()
            self.wfile.write(HTML)
            return

        if request.path == "/stats":
            self._sendJson(stats.getStatsPayload())
            return

        if request.path == "/balance-events":
            now = datetime.now(timezone.utc)
            query = parse_qs(request.query)
            fromDate = _isoDate(query.get("from", [None])[0], now - timedelta(days=1))
            toDate = _isoDate(query.get("to", [None])[0], now)
            self._sendJson({"events": stats.getBalanceEvents(fromDate, toDate)})
            return

        self._sendJson({"error": "not found"}, 404)

    def log_message(self, format: str, *args: object) -> None:
        return


def startServer(port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("", port), DashboardHandler)
    Thread(target=server.serve_forever, name="dashboard", daemon=True).start()
    return server


def stopServer(server: ThreadingHTTPServer | None) -> None:
    if server is None:
        return
    server.shutdown()
    server.server_close()
