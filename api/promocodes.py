import json
from lib import db
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            tenant_id = params.get("tenant", [None])[0]
            code = params.get("code", [None])[0]

            if not tenant_id or not code:
                self._json(400, {"error": "tenant and code required"})
                return

            db_conn = db.get_db()
            res = db_conn.table("promocodes").select("*").eq("tenant_id", tenant_id).eq("code", code).eq("is_active", True).maybe_single().execute()
            
            if res.data:
                self._json(200, res.data)
            else:
                self._json(404, {"error": "Promocode not found"})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_POST(self):
        # Only owner can add promocodes
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            tenant_id = data.get("tenant_id")
            user_id = data.get("user_id")

            tenant = db.get_tenant_by_id(tenant_id)
            if not tenant or str(tenant["owner_telegram_id"]) != str(user_id):
                self._json(403, {"error": "Access denied"})
                return

            db_conn = db.get_db()
            db_conn.table("promocodes").insert({
                "tenant_id": tenant_id,
                "code": data["code"],
                "discount_percent": int(data["discount_percent"])
            }).execute()
            self._json(200, {"status": "ok"})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
