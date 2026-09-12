#!/usr/bin/env python3
"""
Lightweight zero-dependency HTTP server for Nexus AI Landing Page.
Runs on port 8080 by default (or the next available port) and serves the nexus_ai directory.
"""

import http.server
import socketserver
import os
import sys
import webbrowser

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS and caching headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

def run_server(port=PORT):
    while port < 8100:
        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                print("=" * 60)
                print(f" Nexus AI — B2B SaaS MVP Landing Page Server Running")
                print(f" URL: http://localhost:{port}")
                print(f" Directory: {DIRECTORY}")
                print(" Press Ctrl+C to stop the server")
                print("=" * 60)
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\nShutting down server gracefully.")
                    break
            return
        except OSError:
            print(f"Port {port} is in use, trying port {port + 1}...")
            port += 1

if __name__ == "__main__":
    target_port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(target_port)
