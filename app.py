import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/kaithheathcheck":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()
