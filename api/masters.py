import json
import os
import sys

from lib import db

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

        masters = db.get_masters_by_tenant(tenant_id)
        self._json(200, masters)

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            action = data.get("action")
            tenant_id = data.get("tenant_id")

            if action == "add_master":
                db.add_master(tenant_id, data.get("name"), data.get("specialty"), data.get("telegram_id"))
                self._json(200, {"status": "ok"})
            elif action == "delete_master":
                db.delete_master(int(data.get("master_id")), tenant_id)
                self._json(200, {"status": "ok"})
            else:
                self._json(400, {"error": "invalid action"})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
