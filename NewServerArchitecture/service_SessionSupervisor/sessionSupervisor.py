import socketserver
import argparse

import http.server

class RandomHTTPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port

    def start_server(self):
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer((self.host, self.port), handler) as httpd:
            print(f"Serving HTTP on {self.host} port {self.port} (http://{self.host}:{self.port}/) ...")
            httpd.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start a simple HTTP server.')
    parser.add_argument('--host', type=str, default='localhost', help='Hostname to listen on')
    parser.add_argument('--port', type=int, default=15000, help='Port to listen on')
    args = parser.parse_args()

    server = RandomHTTPServer(host=args.host, port=args.port)
    server.start_server()
    print("Running")
    print("Stopped")