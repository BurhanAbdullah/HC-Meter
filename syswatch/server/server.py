from http.server import BaseHTTPRequestHandler, HTTPServer
import json

events = []

class Handler(BaseHTTPRequestHandler):

    def do_POST(self):

        if self.path == "/telemetry":

            length = int(self.headers['Content-Length'])
            data = self.rfile.read(length)

            event = json.loads(data.decode())
            events.append(event)

            print("Telemetry received:", event)

            self.send_response(200)
            self.end_headers()

    def do_GET(self):

        if self.path == "/events":

            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()

            self.wfile.write(json.dumps(events).encode())

server = HTTPServer(("0.0.0.0",9000),Handler)

print("SYSWATCH control server running on port 9000")

server.serve_forever()
