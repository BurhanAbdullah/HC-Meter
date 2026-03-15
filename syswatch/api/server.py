import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

def run(cmd):
    return subprocess.getoutput(cmd)

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/metrics":

            cpu = run("top -bn1 | grep 'Cpu(s)' | awk '{print int($2)}'")
            mem = run("free | awk '/Mem:/ {printf(\"%d\"), $3/$2*100}'")
            disk = run("df / | awk 'NR==2 {print $5}'")

            ports = run("ss -tuln | awk 'NR>1 {print $5}'")

            data = {
                "cpu": cpu,
                "memory": mem,
                "disk": disk,
                "ports": ports.split()
            }

            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()

            self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0",8080),Handler)

print("SYSWATCH dashboard server running on port 8080")

server.serve_forever()
