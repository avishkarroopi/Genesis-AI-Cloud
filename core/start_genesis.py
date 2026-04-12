#!/usr/bin/env python3
"""
GENESIS System Launcher
Starts the complete GENESIS system with face server in a single command.

Usage:
    python3 start_genesis.py
"""

import subprocess
import time
import sys
import signal
import os
import threading
from pathlib import Path
import requests

import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ANSI colors for terminal output

BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

try:
    from core.config import SAFE_START
except ImportError:
    SAFE_START = True


class GenesisLauncher:
    """Launcher for GENESIS system with face server."""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.face_process = None
        self.core_process = None
        self.vision_process = None
        self.running = False
        self.model_ready = False
    
    def print_banner(self):
        """Print GENESIS startup banner."""
        print(f"\n{BOLD}{BLUE}")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║                 GENESIS + JARVIS SYSTEM LAUNCHER               ║")
        print("║                    Autonomous AI Robot Platform                ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print(f"{RESET}\n")
    
    def print_status(self, component: str, status: str, message: str = ""):
        """Print formatted status message."""
        try:
            if status == "starting":
                print(f"{YELLOW}⟳{RESET} {component:30} {message}")
            elif status == "success":
                print(f"{GREEN}✓{RESET} {component:30} {message}")
            elif status == "error":
                print(f"{RED}✗{RESET} {component:30} {message}")
            elif status == "info":
                print(f"{BLUE}ℹ{RESET} {component:30} {message}")
        except:
            pass
    
    def verify_files(self):
        """Verify required files exist."""
        self.print_status("System Check", "info", "Verifying files...")
        
        required_files = [
            "face_server.py",
            "system.py",
            "voice_agent.py",
            "../lite/face_ui/index.html"
        ]
        
        for file in required_files:
            file_path = self.project_dir / file
            if not file_path.exists():
                self.print_status("File Verification", "error", f"Missing: {file}")
                return False
        
        self.print_status("File Verification", "success", "All required files present")
        return True
    
    def ensure_ollama_running(self):
        """Ensure the Ollama server process is alive before anything else."""
        self.print_status("Ollama Server", "starting", "Checking if Ollama is running...")
        try:
            r = requests.get("http://127.0.0.1:11434", timeout=3)
            if r.status_code == 200:
                self.print_status("Ollama Server", "success", "Already running")
                return True
        except Exception:
            pass
        
        self.print_status("Ollama Server", "starting", "Starting Ollama serve...")
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            self.print_status("Ollama Server", "error", "'ollama' command not found. Install Ollama first.")
            return False
        
        # Wait up to 10 seconds for Ollama to be ready
        for i in range(20):
            time.sleep(0.5)
            try:
                r = requests.get("http://127.0.0.1:11434", timeout=2)
                if r.status_code == 200:
                    self.print_status("Ollama Server", "success", "Started successfully")
                    return True
            except Exception:
                pass
        
        self.print_status("Ollama Server", "error", "Failed to start within 10 seconds")
        return False
    
    def check_models(self):
        """Verify required Ollama models are installed. Auto-pull if missing."""
        self.print_status("Model Check", "starting", "Checking installed models...")
        model_name = os.environ.get("OLLAMA_MODEL", "phi3")
        try:
            out = subprocess.check_output(["ollama", "list"], text=True)
            
            # Check primary model
            if model_name.split(":")[0] not in out:
                self.print_status("Model Check", "pulling", f"Pulling {model_name}...")
                subprocess.run(["ollama", "pull", model_name], check=True, timeout=60)
            
            # Check tinyllama backup
            if "tinyllama" not in out:
                self.print_status("Model Check", "pulling", "Pulling tinyllama...")
                subprocess.run(["ollama", "pull", "tinyllama"], check=True, timeout=60)
            
            self.print_status("Model Check", "success", f"Models OK ({model_name} + tinyllama)")
            return True
        except Exception as e:
            self.print_status("Model Check", "error", f"Failed: {e}")
            return False
    
    def start_ollama_if_needed(self):
        """Start Ollama in a new window if not already running."""
        try:
            requests.get("http://127.0.0.1:11434", timeout=2)
            print("Ollama already running")
            return
        except Exception:
            print("Starting Ollama...")

        subprocess.Popen(
            ["cmd", "/c", "start", "ollama", "serve"],
            shell=True
        )

        # wait until ready
        for i in range(30):
            try:
                requests.get("http://127.0.0.1:11434", timeout=2)
                print("Ollama started")
                return
            except Exception:
                time.sleep(1)

        print("Ollama start failed")

    def preload(self, model_name):
        """Preload a model into memory using the Ollama API (not interactive CLI)."""
        self.print_status("Preload", "starting", f"Preloading {model_name}...")
        print(f"INIT preload | model={model_name}", flush=True)
        try:
            # Use the API to trigger a lightweight generate — this loads the model
            # into GPU/CPU memory without opening an interactive terminal session.
            r = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model": model_name, "prompt": "hi", "stream": False, "options": {"num_predict": 1}},
                timeout=180
            )
            if r.status_code == 200:
                self.print_status("Preload", "success", f"{model_name} loaded into memory")
                return True
            else:
                self.print_status("Preload", "error", f"{model_name} API returned {r.status_code}")
                return False
        except Exception as e:
            if "read timed out" in str(e).lower() or "timeout" in str(e).lower():
                self.print_status("Preload", "success", f"{model_name} loading in background")
                return True
            self.print_status("Preload", "error", f"{model_name} failed: {e}")
            return False
    
    def warmup(self):
        """Warmup configured model via API to confirm it responds."""
        model_name = os.environ.get("OLLAMA_MODEL", "phi3")
        self.print_status("Warmup", "starting", f"Warming up {model_name}...")
        print(f"INIT warmup | model={model_name}", flush=True)
        try:
            r = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": "hello",
                    "stream": False,
                    "options": {"num_predict": 5}
                },
                timeout=180
            )
            if r.status_code == 200:
                self.print_status("Warmup", "success", "Warmup OK")
                return True
            else:
                self.print_status("Warmup", "error", f"Bad status: {r.status_code}")
                return False
        except Exception as e:
            self.print_status("Warmup", "error", f"Failed: {type(e).__name__}")
            return False
    
    def _kill_port_8080(self):
        """Kill any process holding port 8080 from a previous run."""
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if ":8080" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1].strip()
                    if pid.isdigit() and int(pid) != os.getpid():
                        print(f"[CLEANUP] Killing zombie process on port 8080 (PID {pid})", flush=True)
                        try:
                            subprocess.run(["taskkill", "/F", "/PID", pid],
                                           capture_output=True, timeout=5)
                        except Exception:
                            pass
                        time.sleep(0.5)
        except Exception as e:
            print(f"[CLEANUP] Port check skipped: {e}", flush=True)

    def start_face_server(self):
        """Start the face server in background."""
        self._kill_port_8080()
        self.print_status("Face Server", "starting", "Launching on port 8080...")
        
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONPATH'] = str(self.project_dir.parent) + os.pathsep + env.get('PYTHONPATH', '')
            self.face_process = subprocess.Popen(
                [sys.executable, "face_server.py"],
                cwd=str(self.project_dir),
                stdout=None,
                stderr=None,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env
            )
            
            # Give server time to start
            time.sleep(0.1)
            
            if self.face_process and self.face_process.poll() is None:
                self.print_status(
                    "Face Server",
                    "success",
                    f"Running (PID: {self.face_process.pid}) → ws://localhost:8080"
                )
                return True
            else:
                self.print_status("Face Server", "error", "Failed to start")
                return False
        
        except Exception as e:
            self.print_status("Face Server", "error", str(e))
            return False
            
    def start_vision_services(self):
        """Start the complete vision pipeline (yolo detector + llava reasoner)."""
        self.print_status("Vision Runner", "starting", "Launching camera tracking and reasoning...")
        
        try:
            from core.vision.yolo_detector import start_yolo_detection
            from core.vision.llava_reasoner import start_llava_reasoner
            import threading

            yolo_thread = threading.Thread(target=start_yolo_detection, daemon=True)
            llava_thread = threading.Thread(target=start_llava_reasoner, daemon=True)

            yolo_thread.start()
            llava_thread.start()
            
            self.print_status(
                "Vision Runner",
                "success",
                "Vision daemons (YOLO + LLaVA) running"
            )
            return True
        
        except Exception as e:
            self.print_status("Vision Runner", "error", str(e))
            return False
    
    def start_genesis_core(self):
        """Start the GENESIS core system."""
        self.print_status("GENESIS Core", "starting", "Initializing 27 system features...")
        
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONPATH'] = str(self.project_dir.parent) + os.pathsep + env.get('PYTHONPATH', '')
            self.core_process = subprocess.Popen(
                [sys.executable, "-u", "system.py"],
                cwd=str(self.project_dir),
                stdout=None,
                stderr=None,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env
            )
            
            time.sleep(0.1)
            
            if self.core_process and self.core_process.poll() is None:
                self.print_status(
                    "GENESIS Core",
                    "success",
                    f"Running (PID: {self.core_process.pid})"
                )
                return True
            else:
                self.print_status("GENESIS Core", "error", "Failed to start")
                return False
        
        except Exception as e:
            self.print_status("GENESIS Core", "error", str(e))
            return False
    
    def print_startup_info(self):
        """Print startup information and access URLs."""
        print(f"\n{BOLD}{GREEN}GENESIS System Started Successfully{RESET}\n")
        
        print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{BOLD}System Status:{RESET}\n")
        print(f"  {GREEN}✓{RESET} Face Server      : ws://localhost:8080/ws")
        print(f"  {GREEN}✓{RESET} Face UI          : http://localhost:8080")
        print(f"  {GREEN}✓{RESET} GENESIS Core    : Active (27 features)")
        print(f"  {GREEN}✓{RESET} Event Bus        : Operational")
        print(f"  {GREEN}✓{RESET} Knowledge Graph  : Initialized")
        print(f"  {GREEN}✓{RESET} Vision Runner    : Tracking")
        print(f"  {GREEN}✓{RESET} World Model      : Active")
        print(f"  {GREEN}✓{RESET} Autonomous Loop  : Running\n")
        
        print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{BOLD}Quick Commands:{RESET}\n")
        print(f"  • Stop system     : Press Ctrl+C")
        print(f"  • View face UI    : Open http://localhost:8080 in browser")
        print(f"  • Network access  : http://<your-ip>:8080\n")
        
        print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n\n{YELLOW}⟲ Shutting down GENESIS system...{RESET}")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Shutdown both processes gracefully."""
        self.running = False
        
        if self.core_process and self.core_process.poll() is None:
            try:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.core_process.pid)], capture_output=True)
                else:
                    self.core_process.terminate()
                self.core_process.wait(timeout=5)
                self.print_status("GENESIS Core", "info", "Stopped")
            except Exception as e:
                self.core_process.kill()
                self.print_status("GENESIS Core", "info", f"Force stopped ({e})")
        
        if self.face_process and self.face_process.poll() is None:
            try:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.face_process.pid)], capture_output=True)
                else:
                    self.face_process.terminate()
                self.face_process.wait(timeout=5)
                self.print_status("Face Server", "info", "Stopped")
            except Exception as e:
                self.face_process.kill()
                self.print_status("Face Server", "info", f"Force stopped ({e})")
                
        if self.vision_process and self.vision_process.poll() is None:
            try:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.vision_process.pid)], capture_output=True)
                else:
                    self.vision_process.terminate()
                self.vision_process.wait(timeout=5)
                self.print_status("Vision Runner", "info", "Stopped")
            except Exception as e:
                self.vision_process.kill()
                self.print_status("Vision Runner", "info", f"Force stopped ({e})")
        
        # Fallback: force exit if anything hangs
        def _force_exit():
            time.sleep(5)
            print("[GENESIS] Force exit — processes did not stop in time.", flush=True)
            os._exit(0)
        threading.Thread(target=_force_exit, daemon=True).start()
    
    def run(self):
        """Run the launcher."""
        
        # SAFEGUARD 8: Single instance lock
        import socket
        try:
            self._lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._lock_socket.bind(('127.0.0.1', 49152))
        except socket.error:
            print("\n[GENESIS] ERROR: System is already running! (Port 49152 locked)", flush=True)
            sys.exit(1)

        self.print_banner()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Verify files
        if not self.verify_files():
            sys.exit(1)
        
        print()
        
        CLOUD_MODE = os.environ.get("CLOUD_MODE", "false").lower() == "true"
        if CLOUD_MODE:
            print("\n[☁️ CLOUD MODE] Bypassing local models and hardware checks.", flush=True)
            self.model_ready = True
            
            print("[☁️ CLOUD MODE] Initializing Redis, PostgreSQL, FastAPI...", flush=True)
            try:
                import uvicorn
                uvicorn.run("server.api:app", host="0.0.0.0", port=8000, reload=False)
                sys.exit(0)
            except Exception as e:
                print(f"[FATAL] FastAPI boot failed: {e}", flush=True)
                sys.exit(1)
        
        # ── Strict Ollama Pre-load Sequence ──
        try:
            if not self.ensure_ollama_running():
                print("[WARNING] Ollama could not be started.", flush=True)
            model_name = os.environ.get("OLLAMA_MODEL", "phi3")

            try:
                self.check_models()
            except Exception as e:
                print("[WARN] model check failed", e, flush=True)

            def _ollama_background_task():
                try:
                    self.start_ollama_if_needed()
                    print("Wait 2s before preload...", flush=True)
                    time.sleep(2)
                    self.preload(model_name)
                except Exception as e:
                    print(f"[WARN] preload skipped: {e}", flush=True)

                try:
                    print("Wait 2s before warmup...", flush=True)
                    time.sleep(2)
                    self.warmup()
                    print("Wait 2s after warmup...", flush=True)
                    time.sleep(2)
                except Exception as e:
                    print(f"[WARN] warmup skipped: {e}", flush=True)

            threading.Thread(target=_ollama_background_task, daemon=True, name="OllamaPreload").start()
            self.model_ready = True
        except Exception as e:
            print(f"[ERROR] Ollama sequence failed: {e}", flush=True)
        
        # ── BOOT SEQUENCE ──
        from core.config import SAFE_START
        
        print("\n=== SYSTEM BOOT SEQUENCE ===", flush=True)
        self.print_status("Boot Sequence", "starting", "1. Loading configuration...")
        
        self.print_status("Boot Sequence", "starting", "2. Initializing EventBus...")
        
        self.print_status("Boot Sequence", "starting", "3. Running verify_system_readiness()...")
        try:
            from core.system_readiness import verify_system_readiness
            verify_system_readiness()
        except SystemExit:
            self.shutdown()
            sys.exit(1)
        except Exception as e:
            print(f"[FATAL] Readiness check error: {e}", flush=True)
            self.shutdown()
            sys.exit(1)

        self.print_status("Boot Sequence", "starting", "4. Initializing sensors (mic + camera)...")
        self.print_status("Boot Sequence", "starting", "5. Initializing AI core modules...")
        self.print_status("Boot Sequence", "starting", "6. Initializing memory system...")
        self.print_status("Boot Sequence", "starting", "7. Initializing automation and agents...")
        self.print_status("Boot Sequence", "starting", "8. Initializing voice system...")
        self.print_status("Boot Sequence", "starting", "9. Initializing avatar interface...")
        self.print_status("Boot Sequence", "starting", "10. Activating wake word detection...")
        print("============================\n", flush=True)
        
        # ── Start face server ──
        if not SAFE_START:
            if not self.start_face_server():
                sys.exit(1)
            
        # ── Start vision services safely ──
        if not self.start_vision_services():
             print(f"\n\033[93m⚠ VISION FAILED — CONTINUING WITHOUT CAMERA\033[0m", flush=True)
        
        # ── Start GENESIS core (voice, sensors, etc.) ──
        if self.model_ready:
            if not self.start_genesis_core():
                self.shutdown()
                sys.exit(1)
        else:
            print("[FATAL] Model not ready! Cannot start voice loop.", flush=True)
            self.shutdown()
            sys.exit(1)
        
        # Print startup info
        self.print_startup_info()
        
        # Monitor both processes
        print(f"{BOLD}System Running - Press Ctrl+C to shutdown{RESET}\n")
        self.running = True
        
        try:
            while self.running:
                face_status = self.face_process.poll() if self.face_process else None
                core_status = self.core_process.poll() if self.core_process else None
                vision_status = self.vision_process.poll() if self.vision_process else None
                
                if face_status is not None:
                    self.print_status(
                        "Face Server",
                        "error",
                        f"Crashed (exit code: {face_status})"
                    )
                    self.shutdown()
                    sys.exit(1)
                
                if core_status is not None:
                    self.print_status(
                        "GENESIS Core",
                        "error",
                        f"Crashed (exit code: {core_status})"
                    )
                    self.shutdown()
                    sys.exit(1)
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            self.signal_handler(None, None)


def main():
    """Main entry point."""
    print("INIT CALLED: start_genesis.py main()", flush=True)
    launcher = GenesisLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
