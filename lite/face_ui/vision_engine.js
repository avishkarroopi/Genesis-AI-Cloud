// vision_engine.js — Process video frames to emit VISION_EVENT to Backend
(function() {
    let faceDetector = null;

    // We assume @mediapipe/tasks-vision loaded natively, or we fall back to a dummy placeholder
    // Real implementation uses FaceLandmarker from mediapipe if available, else simple dummy event.
    async function initVision() {
        if (window.FilesetResolver && window.FaceDetector) {
            try {
                const vision = await window.FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm");
                faceDetector = await window.FaceDetector.createFromOptions(vision, {
                    baseOptions: {
                        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
                        delegate: "GPU"
                    },
                    runningMode: "IMAGE"
                });
            } catch(e) {
                console.error("Vision model failed to load", e);
            }
        }
    }
    
    // Call init in background
    setTimeout(initVision, 1000);

    let canvas = document.createElement("canvas");
    let ctx = canvas.getContext("2d");

    window.processVisionFrame = function(video) {
        if (!video.videoWidth) return;
        
        let faces = 0;
        let emotion = "neutral";
        let user_present = false;

        // Run MediaPipe Face Detector
        if (faceDetector) {
            try {
                const detections = faceDetector.detect(video);
                if (detections && detections.detections && detections.detections.length > 0) {
                    faces = detections.detections.length;
                    user_present = true;
                }
            } catch(e) {
                // Ignore detector errors
            }
        } else {
            // Stub fallback if mediapipe tasks-vision isn't globally exposed yet
            faces = 1;
            user_present = true;
        }

        const visionEvent = {
            type: "VISION_EVENT",
            user_present: user_present,
            faces: faces,
            emotion: emotion,
            timestamp: Date.now()
        };

        // Emit over websocket
        if (window.currentWs && window.currentWs.readyState === WebSocket.OPEN) {
            // Lightweight JSON, max 5 FPS, no streams.
            window.currentWs.send(JSON.stringify(visionEvent));
        }
    };
})();
