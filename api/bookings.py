import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import lib.db as db

from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        tenant_id = params.get("tenant", [None])[0]

        if not tenant_id:
            self._json(400, {"error": "tenant parameter required"})
            return

        bookings = db.get_appointments_by_tenant(tenant_id)
        self._json(200, bookings)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
