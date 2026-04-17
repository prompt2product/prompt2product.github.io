#!/usr/bin/env python3
"""
Simple HTTP server for local development.
This solves CORS issues when viewing 3D models locally.

Usage:
    python3 serve_local.py
    
Then open: http://localhost:8000
"""

import http.server
import socketserver
import os
import sys

# Change to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 8004

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow local file access
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"🚀 Local development server starting...")
            print(f"📂 Serving directory: {os.getcwd()}")
            print(f"🌐 Open your browser and go to: http://localhost:{PORT}")
            print(f"🛑 Press Ctrl+C to stop the server")
            print("=" * 50)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except OSError as e:
        print(f"❌ Error starting server: {e}")
        print(f"💡 Try a different port or check if port {PORT} is already in use")
        sys.exit(1)
