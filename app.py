import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/kaithheathcheck":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        elif self.path == "/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Save-Contents bot is up :)".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_health_check_server(port):
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logging.info(f"[Health Check] Server starting on port {port}")
        server.serve_forever()
    except Exception as e:
        logging.error(f"[Health Check] Failed to start server on port {port}: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    run_health_check_server(port)
