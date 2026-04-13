// Intercept the WebSocket constructor to capture the existing WS connection
// This ensures we reuse genesis_ws.js's connection without modifying it
const OriginalWebSocket = window.WebSocket;
let currentWs = null;

window.WebSocket = function(...args) {
    const ws = new OriginalWebSocket(...args);
    // Since we know the app only opens one WebSocket for GENESIS, capture it
    currentWs = ws;
    return ws;
};

// Start microphone streaming
window.startMicrophoneStreaming = async function() {
    if (!currentWs || currentWs.readyState !== WebSocket.OPEN) {
        console.error("[MIC] WebSocket not ready. Cannot stream audio.");
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("[MIC] Microphone access granted.");

        const options = { mimeType: "audio/webm;codecs=opus" };
        const mediaRecorder = new MediaRecorder(stream, options);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0 && currentWs.readyState === WebSocket.OPEN) {
                currentWs.send(event.data);
            }
        };

        // If the socket closes, stop recording
        currentWs.addEventListener("close", () => {
            console.log("[MIC] WebSocket closed. Stopping recording.");
            if (mediaRecorder.state !== "inactive") {
                mediaRecorder.stop();
            }
            stream.getTracks().forEach(track => track.stop());
        });

        // Start recording and emit chunks every 250ms
        mediaRecorder.start(250);
        console.log("[MIC] Streaming audio to backend every 250ms...");

    } catch (err) {
        console.error("[MIC] Failed to access microphone:", err);
        alert("Microphone access denied or unavailable.");
    }
};
