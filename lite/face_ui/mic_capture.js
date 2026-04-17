// Removed WebSocket intercept; using window.genesisWsInstance directly.

// Start microphone streaming
window.startMicrophoneStreaming = async function() {
    const currentWs = window.genesisWsInstance;
    if (!currentWs || currentWs.readyState !== 1) { // 1 = OPEN
        console.error("Voice socket not ready");
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("[MIC] Microphone access granted.");

        const options = { mimeType: "audio/webm;codecs=opus" };
        const mediaRecorder = new MediaRecorder(stream, options);

        let audioChunks = [];
        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0 && currentWs.readyState === 1) { // 1 = OPEN
                audioChunks.push(event.data);
                // 250ms chunks, 8 chunks = 2 seconds
                if (audioChunks.length >= 8) {
                    const blob = new Blob(audioChunks, { type: "audio/webm;codecs=opus" });
                    currentWs.send(blob);
                    audioChunks = [];
                }
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
