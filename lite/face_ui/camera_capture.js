// camera_capture.js — Handle video stream for Vision Engine
(function() {
    let videoElement = document.createElement('video');
    videoElement.style.display = 'none';
    videoElement.autoplay = true;
    videoElement.playsInline = true;
    document.body.appendChild(videoElement);

    let stream = null;
    let cameraActive = false;
    let captureInterval = null;

    window.toggleCamera = async function() {
        const btn = document.getElementById("cameraToggle");
        if (cameraActive) {
            // TURN OFF
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            if (captureInterval) {
                clearInterval(captureInterval);
                captureInterval = null;
            }
            videoElement.srcObject = null;
            cameraActive = false;
            btn.innerText = "Camera OFF";
            btn.style.color = "gray";
        } else {
            // TURN ON
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                videoElement.srcObject = stream;
                cameraActive = true;
                btn.innerText = "Camera ON";
                btn.style.color = "#0ff";

                // Frame capture loop for Vision Engine (5 FPS = 200ms)
                captureInterval = setInterval(() => {
                    if (window.processVisionFrame) {
                        window.processVisionFrame(videoElement);
                    }
                }, 200);
            } catch (e) {
                console.error("Camera access denied:", e);
                alert("Camera access denied or unavailable.");
            }
        }
    };
})();
