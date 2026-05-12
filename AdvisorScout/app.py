"""
Web UI Server for AdvisorScout.
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
            
        if url.path == "/status.json":
            status_path = os.path.join(RESULTS_DIR, "status.json")
            if os.path.exists(status_path):
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(status_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Status file not found yet.")
                return

        if url.path == "/get_keywords":
            from config import SEARCH_KEYWORDS
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(SEARCH_KEYWORDS).encode())
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

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/save_keywords":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                keywords = json.loads(post_data.decode('utf-8'))
                from config import KEYWORDS_FILE
                with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
                    json.dump(keywords, f, indent=4)
                
                # We need to force reload the module or just update the variable in main if it's running
                # For now, saving to file is enough as next main.py run will pick it up
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
            return

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
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ScraperHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        print("Open this URL in your browser to access the dashboard and Start Scraping.")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
