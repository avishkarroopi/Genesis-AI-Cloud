"""
stats_server.py — Standalone lightweight stats API for GENESIS HUD
Serves CPU / RAM / GPU usage as JSON on port 8082.
Run alongside face_server.py:  python stats_server.py
Does NOT touch face_server, websocket, or any GENESIS core.
"""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("[STATS] psutil not found — CPU/RAM will show N/A")

try:
    import GPUtil
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

PORT = 8082

# Cached stats (updated in background thread)
_stats = {"cpu": None, "ram": None, "gpu": None, "gpu_name": None}
_lock = threading.Lock()


def _update_stats():
    """Background thread: update stats every 2 seconds."""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1) if HAS_PSUTIL else None
            ram = psutil.virtual_memory().percent if HAS_PSUTIL else None
            gpu = None
            gpu_name = None
            if HAS_GPU:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = round(gpus[0].load * 100, 1)
                    gpu_name = gpus[0].name
            with _lock:
                _stats["cpu"] = cpu
                _stats["ram"] = ram
                _stats["gpu"] = gpu
                _stats["gpu_name"] = gpu_name
        except Exception as e:
            print(f"[STATS] Update error: {e}")
        time.sleep(2)


class StatsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/stats":
            with _lock:
                data = dict(_stats)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logs


if __name__ == "__main__":
    # Start background stats collection
    t = threading.Thread(target=_update_stats, daemon=True)
    t.start()

    server = HTTPServer(("0.0.0.0", PORT), StatsHandler)
    print(f"[STATS] Stats API running on http://localhost:{PORT}/stats")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[STATS] Shutting down.")
        server.server_close()
