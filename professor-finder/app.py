"""
Web UI Server for PhD Advisor Finder.
Provides a Start Scraping button and serves the dashboard.
"""

import http.server
import socketserver
import threading
import json
import os
import subprocess
import sys
from urllib.parse import urlparse, parse_qs

PORT = 8000
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
DASHBOARD_PATH = os.path.join(RESULTS_DIR, "professors_report.html")

class ScraperHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/start":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            # Start scraper in a background thread
            thread = threading.Thread(target=self.run_scraper)
            thread.daemon = True
            thread.start()
            
            self.wfile.write(json.dumps({"status": "started"}).encode())
            return
            
        # Serve the dashboard at root
        if self.path == "/" or self.path == "":
            if os.path.exists(DASHBOARD_PATH):
                self.path = "/results/professors_report.html"
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Dashboard not generated yet. Click 'Start' to begin.")
                return

        return super().do_GET()

    def run_scraper(self):
        print("Starting scraper background process...")
        try:
            # Run main.py as a subprocess
            subprocess.run([sys.executable, "main.py"], check=True)
            print("Scraper finished successfully.")
        except Exception as e:
            print(f"Scraper error: {e}")

def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("", PORT), ScraperHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        print("Open this URL in your browser to access the dashboard and Start Scraping.")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
