import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_json({
                "message": "Welcome to the tiny backend!",
                "endpoints": ["/api/hello", "/api/time"]
            })
        elif self.path == '/api/hello':
            self.send_json({"message": "Hello, World!"})
        elif self.path == '/api/time':
            self.send_json({
                "epoch_time": int(time.time()),
                "local_time": time.ctime()
            })
        else:
            self.send_json({"error": "Endpoint not found"}, status=404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), SimpleHandler)
    print("Server running on http://localhost:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
