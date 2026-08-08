import { useState, useRef, useCallback, useEffect } from "react";

export function useAudioRecorder() {
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [error, setError] = useState(null);

    const mediaRecorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);

    const startRecording = useCallback(async () => {
        setError(null);
        setRecordingTime(0);
        chunksRef.current = [];

        if (!navigator?.mediaDevices?.getUserMedia) {
            setError("UNSUPPORTED");
            return false;
        }

        try {
            // Add a 3 second timeout for getUserMedia permission prompt in case it hangs in automated environments
            const getUserMediaPromise = navigator.mediaDevices.getUserMedia({ audio: true });
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error("PermissionTimeout")), 4000)
            );

            const stream = await Promise.race([getUserMediaPromise, timeoutPromise]);
            mediaStreamRef.current = stream;

            let mimeType = "";
            if (typeof MediaRecorder !== "undefined") {
                if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
                    mimeType = "audio/webm;codecs=opus";
                } else if (MediaRecorder.isTypeSupported("audio/webm")) {
                    mimeType = "audio/webm";
                } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
                    mimeType = "audio/mp4";
                } else if (MediaRecorder.isTypeSupported("audio/wav")) {
                    mimeType = "audio/wav";
                }
            }

            const options = mimeType ? { mimeType } : undefined;
            const mediaRecorder = new MediaRecorder(stream, options);
            mediaRecorderRef.current = mediaRecorder;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorder.start(200);
            setIsRecording(true);

            timerRef.current = setInterval(() => {
                setRecordingTime((prev) => prev + 1);
            }, 1000);

            return true;
        } catch (err) {
            console.error("Microphone access error:", err);
            if (
                err.name === "NotAllowedError" ||
                err.name === "PermissionDeniedError" ||
                err.message === "PermissionTimeout"
            ) {
                setError("PERMISSION_DENIED");
            } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
                setError("NO_MIC");
            } else {
                setError("GENERIC_MIC_ERROR");
            }
            return false;
        }
    }, []);

    const stopRecording = useCallback(() => {
        return new Promise((resolve) => {
            if (!mediaRecorderRef.current || mediaRecorderRef.current.state === "inactive") {
                setIsRecording(false);
                resolve(null);
                return;
            }

            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }

            mediaRecorderRef.current.onstop = () => {
                const mimeType = mediaRecorderRef.current?.mimeType || "audio/webm";
                const blob = new Blob(chunksRef.current, { type: mimeType });

                let ext = "webm";
                if (mimeType.includes("mp4") || mimeType.includes("m4a")) ext = "m4a";
                else if (mimeType.includes("wav")) ext = "wav";

                const file = new File([blob], `voice-memo-${Date.now()}.${ext}`, { type: mimeType });

                if (mediaStreamRef.current) {
                    mediaStreamRef.current.getTracks().forEach((track) => track.stop());
                    mediaStreamRef.current = null;
                }

                setIsRecording(false);
                resolve({ blob, file });
            };

            mediaRecorderRef.current.stop();
        });
    }, []);

    const cancelRecording = useCallback(() => {
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
            mediaRecorderRef.current.onstop = null;
            mediaRecorderRef.current.stop();
        }
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach((track) => track.stop());
            mediaStreamRef.current = null;
        }
        setIsRecording(false);
        setRecordingTime(0);
        chunksRef.current = [];
    }, []);

    useEffect(() => {
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
            if (mediaStreamRef.current) {
                mediaStreamRef.current.getTracks().forEach((track) => track.stop());
            }
        };
    }, []);

    return {
        isRecording,
        recordingTime,
        error,
        startRecording,
        stopRecording,
        cancelRecording,
        resetError: () => setError(null)
    };
}
