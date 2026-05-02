import http.server
import socketserver
import os
import json
import database as db
from urllib.parse import urlparse, parse_qs

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        tenant_id = query.get('tenant', [None])[0]

        if path.startswith('/api/'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = []
            try:
                if not tenant_id:
                    raise ValueError("tenant is required")
                
                if path == '/api/bookings':
                    appointments = db.get_appointments_by_tenant(tenant_id)
                    for appt in appointments:
                        response.append({
                            "id": appt[0],
                            "name": appt[1],
                            "phone": appt[2],
                            "service": appt[3],
                            "date": appt[4],
                            "time": appt[5],
                            "status": appt[6],
                            "master": appt[7]
                        })
                elif path == '/api/services':
                    services = db.get_services_by_tenant(tenant_id)
                    for s in services:
                        response.append({
                            "id": s[0],
                            "name": s[2],
                            "price": s[3],
                            "duration": s[4]
                        })
                elif path == '/api/masters':
                    masters = db.get_masters_by_tenant(tenant_id)
                    for m in masters:
                        response.append({
                            "id": m[0],
                            "name": m[2],
                            "specialty": m[3],
                            "telegram_id": m[4]
                        })
                else:
                    raise ValueError("Unknown API endpoint")
                    
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                err = json.dumps({"error": str(e)})
                self.wfile.write(err.encode('utf-8'))
        else:
            super().do_GET()

def run():
    os.chdir(DIRECTORY)
    Handler = CustomHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Local server started at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            httpd.shutdown()

if __name__ == "__main__":
    run()
