// Removed WebSocket intercept; using window.genesisWsInstance directly.

let activeRecorder = null;
let activeStream = null;

function getSupportedMimeType() {
    const preferred = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/ogg;codecs=opus"
    ];
    for (const type of preferred) {
        if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) {
            return type;
        }
    }
    return "";
}

function stopRecording() {
    if (activeRecorder && activeRecorder.state !== "inactive") {
        activeRecorder.stop();
    }
    if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop());
    }
    activeRecorder = null;
    activeStream = null;
}

// Start microphone streaming
window.startMicrophoneStreaming = async function() {
    const currentWs = window.genesisWsInstance;
    if (!currentWs || currentWs.readyState !== 1) { // 1 = OPEN
        console.error("[MIC] Voice socket not ready");
        return;
    }

    if (activeRecorder && activeRecorder.state !== "inactive") {
        console.log("[MIC] Microphone streaming already active.");
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("[MIC] Microphone access granted.");

        const mimeType = getSupportedMimeType();
        const mediaRecorder = mimeType
            ? new MediaRecorder(stream, { mimeType })
            : new MediaRecorder(stream);

        activeRecorder = mediaRecorder;
        activeStream = stream;

        mediaRecorder.ondataavailable = (event) => {
            const ws = window.genesisWsInstance;
            if (!event.data || event.data.size <= 0 || !ws || ws.readyState !== 1) return;
            ws.send(event.data);
        };

        mediaRecorder.onstop = () => {
            if (activeStream) activeStream.getTracks().forEach(track => track.stop());
            activeRecorder = null;
            activeStream = null;
        };

        mediaRecorder.onerror = (event) => {
            console.error("[MIC] Recorder error:", event.error || event);
            stopRecording();
        };

        // If the socket closes, stop recording
        currentWs.addEventListener("close", () => {
            console.log("[MIC] WebSocket closed. Stopping recording.");
            stopRecording();
        }, { once: true });

        // Emit self-contained audio chunks every 2 seconds
        mediaRecorder.start(2000);
        console.log("[MIC] Streaming audio to backend every 2 seconds...");

    } catch (err) {
        console.error("[MIC] Failed to access microphone:", err);
        alert("Microphone access denied or unavailable.");
        stopRecording();
    }
};
