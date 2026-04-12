import cv2
from ultralytics import YOLO
import time
import signal
import sys
from core.event_bus import get_event_bus

cap = None

# Clean exit handler
def signal_handler(sig, frame):
    print("\n[VISION] Shutting down camera...", flush=True)
    global cap
    if cap is not None:
        cap.release()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_yolo_detection():
    try:
        from core.config import SAFE_START
    except ImportError:
        SAFE_START = True
        
    if SAFE_START:
        print("[SAFE_START] yolo_detector loop disabled.", flush=True)
        sys.exit(0)
        
    print("[VISION] Starting yolo detector...", flush=True)
    
    try:
        model = YOLO("yolov8n.pt")
        print("[VISION] YOLO model loaded successfully.", flush=True)
    except Exception as e:
        print(f"[VISION] Failed to load YOLO model: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

    global cap
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[VISION] Cannot open camera 0", file=sys.stderr, flush=True)
        sys.exit(1)

    print("[VISION] Camera opened. Running detection loop...", flush=True)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[VISION] Failed to read frame from camera. Exiting...", file=sys.stderr, flush=True)
                break
            # classes=[0] forces YOLO to only look for 'person' (humans)
            # conf=0.45 increases the strictness to stop shadow hallucinations 
            results = model(frame, verbose=False, classes=[0], conf=0.45)
            
            # Print detected labels
            detected_labels = []
            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    labels = [model.names[int(c)] for c in boxes.cls]
                    detected_labels.extend(labels)
                    print(f"[VISION] Detected: {', '.join(labels)}", flush=True)
            
            if detected_labels:
                try:
                    bus = get_event_bus()
                    if bus:
                        bus.publish_sync(
                            "VISION_DETECTED",
                            "yolo_detector",
                            {
                                "objects": detected_labels,
                                "raw": []
                            }
                        )
                except Exception:
                    pass
            
            time.sleep(0.1) # Prevent maxing out CPU
            
    except KeyboardInterrupt:
        pass
    finally:
        if cap is not None:
            cap.release()
        print("[VISION] Stopped.", flush=True)

if __name__ == "__main__":
    start_yolo_detection()
