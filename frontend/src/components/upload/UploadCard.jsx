import { useRef, useState, useCallback, useEffect } from "react";
import {
    UploadCloud,
    CheckCircle2,
    Loader2,
    FileAudio,
    Mic,
    Brain,
    Sparkles,
    X,
    Square,
    ShieldAlert,
    Radio,
    Zap
} from "lucide-react";
import API from "../../services/api";
import { useAudioRecorder } from "../../hooks/useAudioRecorder";

const STEPS = [
    { key: "upload",    label: "Uploading Audio",       icon: UploadCloud },
    { key: "whisper",   label: "Whisper Transcription", icon: Mic },
    { key: "emotion",   label: "Emotion Detection",     icon: Sparkles },
    { key: "analysis",  label: "Driver Intelligence",   icon: Brain },
    { key: "complete",  label: "AI Race Engineer",      icon: CheckCircle2 },
];

function formatTimer(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

function WaveformBars() {
    const barHeights = [14, 28, 42, 20, 36, 18, 48, 30, 22, 40, 16, 32, 26, 44, 18, 38, 24, 46, 20, 34, 16, 28, 40, 14];
    return (
        <div className="flex items-center justify-center gap-1.5 h-12 py-1 my-2">
            {barHeights.map((h, i) => (
                <div
                    key={i}
                    className="w-1.5 rounded-full"
                    style={{
                        background: "linear-gradient(180deg, #FF453A 0%, #FF9F0A 100%)",
                        height: `${h}px`,
                        animation: `soundWave 1.2s ease-in-out infinite`,
                        animationDelay: `${(i % 7) * 0.15}s`
                    }}
                />
            ))}
        </div>
    );
}

// Generate a synthetic WAV audio file for demo/fallback when microphone hardware is unavailable
function createDemoAudioFile() {
    const sampleRate = 16000;
    const duration = 2.5;
    const numSamples = sampleRate * duration;
    const buffer = new Int16Array(numSamples);

    for (let i = 0; i < numSamples; i++) {
        const t = i / sampleRate;
        const tone = Math.sin(2 * Math.PI * 440 * t) * 0.3;
        const noise = (Math.random() - 0.5) * 0.1;
        buffer[i] = Math.floor((tone + noise) * 32767);
    }

    const wavBuffer = new ArrayBuffer(44 + buffer.length * 2);
    const view = new DataView(wavBuffer);

    const writeString = (offset, string) => {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    };

    writeString(0, "RIFF");
    view.setUint32(4, 36 + buffer.length * 2, true);
    writeString(8, "WAVE");
    writeString(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, "data");
    view.setUint32(40, buffer.length * 2, true);

    for (let i = 0; i < buffer.length; i++) {
        view.setInt16(44 + i * 2, buffer[i], true);
    }

    const blob = new Blob([view], { type: "audio/wav" });
    return new File([blob], `voice-memo-demo-${Date.now()}.wav`, { type: "audio/wav" });
}

export default function UploadCard({ setAnalysis }) {

    const fileInputRef = useRef(null);
    const audioURLRef = useRef(null);

    const [audioFile, setAudioFile]   = useState(null);
    const [audioURL, setAudioURL]     = useState(null);
    const [uploading, setUploading]   = useState(false);
    const [status, setStatus]         = useState("");
    const [transcript, setTranscript] = useState("");
    const [activeStep, setActiveStep] = useState(-1);
    const [isDragging, setIsDragging] = useState(false);
    const [uploadError, setUploadError] = useState(null);

    // The browser keeps blob URLs alive until we explicitly revoke them.
    useEffect(() => {
        return () => {
            if (audioURLRef.current) URL.revokeObjectURL(audioURLRef.current);
        };
    }, []);

    const {
        isRecording,
        recordingTime,
        error: micError,
        startRecording,
        stopRecording,
        cancelRecording,
        resetError
    } = useAudioRecorder();

    async function handleFile(file) {
        if (!file) return;

        setUploadError(null);
        setAudioFile(file);
        // Revoke previous URL before creating a new one — otherwise they accumulate.
        if (audioURLRef.current) URL.revokeObjectURL(audioURLRef.current);
        const url = URL.createObjectURL(file);
        audioURLRef.current = url;
        setAudioURL(url);

        const formData = new FormData();
        formData.append("file", file);

        try {
            setUploading(true);

            setActiveStep(0);
            setStatus("🎤 Uploading Audio...");
            await new Promise(r => setTimeout(r, 500));

            setActiveStep(1);
            setStatus("📝 Transcribing with Whisper...");

            const response = await API.post("/upload", formData);

            await new Promise(r => setTimeout(r, 300));

            setActiveStep(2);
            setStatus("😊 Detecting Emotion...");

            await new Promise(r => setTimeout(r, 300));

            setActiveStep(3);
            setStatus("🧠 Generating Driver Intelligence...");

            await new Promise(r => setTimeout(r, 300));

            setAnalysis(response.data);
            setTranscript(response.data.transcript);

            setActiveStep(4);
            setStatus("✅ Analysis Complete");

        } catch (err) {
            console.error(err);
            setStatus("❌ Upload Failed");
            setUploadError("Failed to process audio file. Please ensure backend server is active.");
            setActiveStep(-1);
        } finally {
            setUploading(false);
        }
    }

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
        if (isRecording || uploading) return;
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith("audio/")) {
            handleFile(file);
        }
    }, [isRecording, uploading]);

    async function handleRecordClick(e) {
        if (e) e.preventDefault();
        if (isRecording) {
            const result = await stopRecording();
            if (result && result.file) {
                handleFile(result.file);
            }
        } else {
            resetError();
            setUploadError(null);
            await startRecording();
        }
    }

    function handleDemoRecord(e) {
        if (e) e.preventDefault();
        resetError();
        setUploadError(null);
        const demoFile = createDemoAudioFile();
        handleFile(demoFile);
    }

    function resetUpload(e) {
        if (e) e.preventDefault();
        setAudioFile(null);
        setAudioURL(null);
        setTranscript("");
        setStatus("");
        setActiveStep(-1);
        setUploadError(null);
        if (isRecording) {
            cancelRecording();
        }
    }

    /* ── Render Error Card if Mic or Upload Error ── */
    if (micError || uploadError) {
        const errorTitle = micError === "PERMISSION_DENIED"
            ? "Microphone Access Denied"
            : micError === "NO_MIC"
            ? "No Microphone Found"
            : micError === "UNSUPPORTED"
            ? "Browser Unsupported"
            : "Audio Processing Error";

        const errorMessage = micError === "PERMISSION_DENIED"
            ? "Microphone access is required to record race radio communications. Please enable microphone permissions in your browser settings or run a simulated demo recording."
            : micError === "NO_MIC"
            ? "No active audio recording device was detected on your system. Please connect a microphone or run a simulated demo recording."
            : micError === "UNSUPPORTED"
            ? "Your browser does not support audio recording via the MediaRecorder API."
            : uploadError || "An unexpected error occurred during audio processing.";

        return (
            <div
                className="rounded-3xl p-10 transition-all duration-300 animate-fade-in-up"
                style={{
                    background: "rgba(255, 69, 58, 0.04)",
                    backdropFilter: "blur(24px)",
                    WebkitBackdropFilter: "blur(24px)",
                    border: "1px solid rgba(255, 69, 58, 0.15)",
                    boxShadow: "0 4px 24px rgba(0,0,0,0.3)"
                }}
            >
                <div className="flex items-start gap-5">
                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0"
                        style={{
                            background: "rgba(255, 69, 58, 0.12)",
                            border: "1px solid rgba(255, 69, 58, 0.2)"
                        }}
                    >
                        <ShieldAlert size={28} style={{ color: "#FF453A" }} />
                    </div>

                    <div className="flex-1">
                        <h3 className="text-xl font-bold text-white tracking-tight mb-2">
                            {errorTitle}
                        </h3>
                        <p className="text-sm leading-relaxed mb-6" style={{ color: "#A1A1AA" }}>
                            {errorMessage}
                        </p>

                        <div className="flex flex-wrap items-center gap-3">
                            <button
                                type="button"
                                onClick={() => {
                                    resetError();
                                    setUploadError(null);
                                }}
                                className="px-6 py-2.5 rounded-full text-xs font-semibold text-white transition-all duration-200"
                                style={{
                                    background: "rgba(255, 255, 255, 0.08)",
                                    border: "1px solid rgba(255, 255, 255, 0.12)"
                                }}
                                onMouseEnter={e => e.currentTarget.style.background = "rgba(255, 255, 255, 0.12)"}
                                onMouseLeave={e => e.currentTarget.style.background = "rgba(255, 255, 255, 0.08)"}
                            >
                                Dismiss
                            </button>

                            {micError && micError !== "UNSUPPORTED" && (
                                <>
                                    <button
                                        type="button"
                                        onClick={handleRecordClick}
                                        className="px-6 py-2.5 rounded-full text-xs font-semibold text-white transition-all duration-200"
                                        style={{ background: "#FF453A" }}
                                        onMouseEnter={e => e.currentTarget.style.background = "#FF5D53"}
                                        onMouseLeave={e => e.currentTarget.style.background = "#FF453A"}
                                    >
                                        Try Recording Again
                                    </button>

                                    <button
                                        type="button"
                                        onClick={handleDemoRecord}
                                        className="flex items-center gap-2 px-6 py-2.5 rounded-full text-xs font-semibold text-white transition-all duration-200"
                                        style={{
                                            background: "rgba(10, 132, 255, 0.15)",
                                            border: "1px solid rgba(10, 132, 255, 0.3)",
                                            color: "#0A84FF"
                                        }}
                                        onMouseEnter={e => e.currentTarget.style.background = "rgba(10, 132, 255, 0.25)"}
                                        onMouseLeave={e => e.currentTarget.style.background = "rgba(10, 132, 255, 0.15)"}
                                    >
                                        <Zap size={14} />
                                        Simulate Demo Recording
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    /* ── Render Processing Pipeline Screen while uploading ── */
    if (uploading) {
        return (
            <div
                className="rounded-3xl p-10 transition-all duration-300 animate-fade-in-up"
                style={{
                    background: "rgba(255,255,255,0.04)",
                    backdropFilter: "blur(24px)",
                    WebkitBackdropFilter: "blur(24px)",
                    border: "1px solid rgba(255,255,255,0.05)",
                    boxShadow: "0 4px 24px rgba(0,0,0,0.3)"
                }}
            >
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(10,132,255,0.1)", border: "1px solid rgba(10,132,255,0.18)" }}>
                        <Loader2 size={20} style={{ color: "#0A84FF" }} className="animate-spin" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white tracking-tight">Processing Audio</h2>
                        <p className="text-xs mt-0.5" style={{ color: "#52525B" }}>PitSense AI Pipeline Active</p>
                    </div>
                </div>

                {/* Pipeline Steps List */}
                <div className="space-y-4 my-8">
                    {STEPS.map((step, idx) => {
                        const StepIcon = step.icon;
                        const isDone = activeStep > idx;
                        const isActive = activeStep === idx;

                        return (
                            <div
                                key={step.key}
                                className="flex items-center gap-4 p-4 rounded-2xl transition-all duration-300"
                                style={{
                                    background: isDone
                                        ? "rgba(48, 209, 88, 0.05)"
                                        : isActive
                                        ? "rgba(10, 132, 255, 0.08)"
                                        : "rgba(255, 255, 255, 0.02)",
                                    border: `1px solid ${isDone ? "rgba(48, 209, 88, 0.15)" : isActive ? "rgba(10, 132, 255, 0.2)" : "rgba(255, 255, 255, 0.04)"}`
                                }}
                            >
                                <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                                    style={{
                                        background: isDone
                                            ? "rgba(48, 209, 88, 0.15)"
                                            : isActive
                                            ? "rgba(10, 132, 255, 0.15)"
                                            : "rgba(255, 255, 255, 0.04)"
                                    }}
                                >
                                    {isDone ? (
                                        <CheckCircle2 size={16} style={{ color: "#30D158" }} />
                                    ) : isActive ? (
                                        <Loader2 size={16} style={{ color: "#0A84FF" }} className="animate-spin" />
                                    ) : (
                                        <StepIcon size={16} style={{ color: "#3F3F46" }} />
                                    )}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-white truncate">
                                        {step.label}
                                    </p>
                                </div>

                                <span className="text-xs font-medium px-3 py-1 rounded-full shrink-0"
                                    style={{
                                        background: isDone
                                            ? "rgba(48, 209, 88, 0.1)"
                                            : isActive
                                            ? "rgba(10, 132, 255, 0.12)"
                                            : "transparent",
                                        color: isDone ? "#30D158" : isActive ? "#0A84FF" : "#3F3F46"
                                    }}
                                >
                                    {isDone ? "Complete" : isActive ? "Processing…" : "Pending"}
                                </span>
                            </div>
                        );
                    })}
                </div>

                <div className="pt-2 text-center">
                    <p className="text-xs font-medium" style={{ color: "#A1A1AA" }}>
                        {status}
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div
            className="rounded-3xl p-10 transition-all duration-300 animate-fade-in-up"
            style={{
                background: "rgba(255,255,255,0.04)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                border: "1px solid rgba(255,255,255,0.05)",
                boxShadow: "0 2px 24px rgba(0,0,0,0.25)"
            }}
        >
            <input
                hidden
                type="file"
                accept="audio/*"
                ref={fileInputRef}
                onChange={(e) => handleFile(e.target.files[0])}
            />

            {!audioFile ? (

                /* ── Hero Upload & Record View ── */
                <div
                    className={`relative rounded-3xl p-12 text-center transition-all duration-300 ${isDragging ? "drop-zone-active" : ""}`}
                    style={{
                        border: `1.5px dashed ${isDragging ? "#0A84FF" : isRecording ? "rgba(255, 69, 58, 0.3)" : "rgba(255,255,255,0.08)"}`,
                        background: isDragging ? "rgba(10,132,255,0.03)" : isRecording ? "rgba(255, 69, 58, 0.02)" : "rgba(255,255,255,0.015)"
                    }}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                >
                    {/* Ambient Glow */}
                    <div className="absolute inset-0 rounded-3xl pointer-events-none"
                        style={{
                            background: isRecording
                                ? "radial-gradient(ellipse at 50% 40%, rgba(255, 69, 58, 0.08) 0%, transparent 70%)"
                                : "radial-gradient(ellipse at 50% 30%, rgba(10,132,255,0.06) 0%, transparent 60%)",
                            opacity: 1,
                            transition: "opacity 0.3s ease"
                        }}
                    />

                    {isRecording ? (
                        /* ── Live Voice Recording UI ── */
                        <div className="relative py-4 animate-scale-pop">
                            {/* Recording Indicator */}
                            <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full mb-6"
                                style={{
                                    background: "rgba(255, 69, 58, 0.12)",
                                    border: "1px solid rgba(255, 69, 58, 0.25)"
                                }}
                            >
                                <div className="w-2.5 h-2.5 rounded-full animate-red-pulse"
                                    style={{ background: "#FF453A" }} />
                                <span className="text-xs font-bold uppercase tracking-wider text-red-400">
                                    Recording
                                </span>
                            </div>

                            {/* Timer */}
                            <div className="text-5xl font-black tracking-tight text-white mb-2 tabular-nums">
                                {formatTimer(recordingTime)}
                            </div>

                            <p className="text-xs font-medium mb-6" style={{ color: "#A1A1AA" }}>
                                🎤 Microphone Active • HD Voice Memos Quality
                            </p>

                            {/* Waveform Visualization */}
                            <WaveformBars />

                            {/* Controls */}
                            <div className="flex items-center justify-center gap-4 mt-8">
                                <button
                                    type="button"
                                    onClick={cancelRecording}
                                    className="px-6 py-3 rounded-full text-xs font-semibold text-zinc-400 transition-all duration-200"
                                    style={{
                                        background: "rgba(255,255,255,0.05)",
                                        border: "1px solid rgba(255,255,255,0.08)"
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.color = "#FFFFFF"}
                                    onMouseLeave={e => e.currentTarget.style.color = "#A1A1AA"}
                                >
                                    Cancel
                                </button>

                                <button
                                    type="button"
                                    onClick={handleRecordClick}
                                    className="flex items-center gap-2.5 px-8 py-3.5 rounded-full text-sm font-semibold text-white transition-all duration-300"
                                    style={{
                                        background: "#FF453A",
                                        boxShadow: "0 0 24px rgba(255, 69, 58, 0.4)"
                                    }}
                                    onMouseEnter={e => {
                                        e.currentTarget.style.background = "#FF5D53";
                                        e.currentTarget.style.boxShadow = "0 0 32px rgba(255, 69, 58, 0.6)";
                                    }}
                                    onMouseLeave={e => {
                                        e.currentTarget.style.background = "#FF453A";
                                        e.currentTarget.style.boxShadow = "0 0 24px rgba(255, 69, 58, 0.4)";
                                    }}
                                >
                                    <Square size={14} fill="#FFFFFF" />
                                    Stop Recording
                                </button>
                            </div>
                        </div>
                    ) : (
                        /* ── Dual Actions: Upload or Record ── */
                        <div className="relative">
                            <div className="w-20 h-20 mx-auto rounded-3xl flex items-center justify-center mb-6"
                                style={{
                                    background: "rgba(10,132,255,0.1)",
                                    border: "1px solid rgba(10,132,255,0.15)",
                                    boxShadow: "0 8px 32px rgba(10,132,255,0.12)"
                                }}
                            >
                                <Radio size={34} style={{ color: "#0A84FF" }} />
                            </div>

                            <h2 className="text-2xl font-bold text-white mb-2 tracking-tight">
                                PitSense Race Radio Input
                            </h2>
                            <p className="text-sm mb-8" style={{ color: "#71717A" }}>
                                Upload an existing race audio file or record live driver comms
                            </p>

                            <div className="flex items-center justify-center gap-2 mb-10">
                                {["MP3", "WAV", "M4A", "LIVE MIC"].map(fmt => (
                                    <span key={fmt} className="px-3.5 py-1 rounded-full text-[11px] font-medium"
                                        style={{
                                            background: fmt === "LIVE MIC" ? "rgba(255,69,58,0.1)" : "rgba(255,255,255,0.05)",
                                            border: `1px solid ${fmt === "LIVE MIC" ? "rgba(255,69,58,0.2)" : "rgba(255,255,255,0.07)"}`,
                                            color: fmt === "LIVE MIC" ? "#FF453A" : "#71717A"
                                        }}>
                                        {fmt}
                                    </span>
                                ))}
                            </div>

                            {/* Dual Primary Action Buttons */}
                            <div className="flex flex-wrap items-center justify-center gap-4">
                                <button
                                    type="button"
                                    disabled={uploading}
                                    onClick={() => fileInputRef.current.click()}
                                    className="flex items-center gap-2.5 px-8 py-3.5 rounded-full text-sm font-semibold text-white transition-all duration-300 disabled:opacity-50"
                                    style={{
                                        background: "#0A84FF",
                                        boxShadow: "0 4px 20px rgba(10,132,255,0.3)"
                                    }}
                                    onMouseEnter={e => {
                                        if (!uploading) {
                                            e.currentTarget.style.background = "#1A8DFF";
                                            e.currentTarget.style.boxShadow = "0 8px 32px rgba(10,132,255,0.4)";
                                            e.currentTarget.style.transform = "translateY(-1px)";
                                        }
                                    }}
                                    onMouseLeave={e => {
                                        e.currentTarget.style.background = "#0A84FF";
                                        e.currentTarget.style.boxShadow = "0 4px 20px rgba(10,132,255,0.3)";
                                        e.currentTarget.style.transform = "translateY(0)";
                                    }}
                                >
                                    <UploadCloud size={18} />
                                    Upload Audio
                                </button>

                                <button
                                    type="button"
                                    disabled={uploading}
                                    onClick={handleRecordClick}
                                    className="flex items-center gap-2.5 px-8 py-3.5 rounded-full text-sm font-semibold text-white transition-all duration-300 disabled:opacity-50"
                                    style={{
                                        background: "rgba(255, 255, 255, 0.05)",
                                        border: "1px solid rgba(255, 255, 255, 0.15)",
                                        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.2)"
                                    }}
                                    onMouseEnter={e => {
                                        if (!uploading) {
                                            e.currentTarget.style.background = "rgba(255, 69, 58, 0.15)";
                                            e.currentTarget.style.borderColor = "rgba(255, 69, 58, 0.4)";
                                            e.currentTarget.style.color = "#FF453A";
                                            e.currentTarget.style.transform = "translateY(-1px)";
                                        }
                                    }}
                                    onMouseLeave={e => {
                                        e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
                                        e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.15)";
                                        e.currentTarget.style.color = "#FFFFFF";
                                        e.currentTarget.style.transform = "translateY(0)";
                                    }}
                                >
                                    <Mic size={18} />
                                    Record Audio
                                </button>
                            </div>
                        </div>
                    )}
                </div>

            ) : (

                /* ── File / Recording Loaded & Analyzed View ── */
                <div className="space-y-6">
                    {/* File header */}
                    <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0"
                            style={{
                                background: "rgba(10,132,255,0.1)",
                                border: "1px solid rgba(10,132,255,0.15)"
                            }}
                        >
                            {audioFile.name?.startsWith("voice-memo") ? (
                                <Mic size={24} style={{ color: "#FF453A" }} />
                            ) : (
                                <FileAudio size={24} style={{ color: "#0A84FF" }} />
                            )}
                        </div>

                        <div className="flex-1 min-w-0">
                            <p className="font-semibold text-white truncate text-[15px]">
                                {audioFile.name}
                            </p>
                            <p className="text-sm mt-0.5" style={{ color: "#52525B" }}>
                                {(audioFile.size / 1024 / 1024).toFixed(2)} MB • {audioFile.name?.startsWith("voice-memo") ? "Recorded Comms" : "Uploaded Audio"}
                            </p>
                        </div>

                        <button
                            type="button"
                            onClick={resetUpload}
                            disabled={uploading}
                            className="w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 shrink-0"
                            style={{
                                background: "rgba(255,255,255,0.05)",
                                border: "1px solid rgba(255,255,255,0.07)"
                            }}
                            onMouseEnter={e => {
                                e.currentTarget.style.background = "rgba(255,69,58,0.12)";
                                e.currentTarget.style.borderColor = "rgba(255,69,58,0.2)";
                            }}
                            onMouseLeave={e => {
                                e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                                e.currentTarget.style.borderColor = "rgba(255,255,255,0.07)";
                            }}
                        >
                            <X size={14} style={{ color: "#71717A" }} />
                        </button>
                    </div>

                    {/* Audio Player */}
                    <div className="rounded-2xl overflow-hidden"
                        style={{
                            background: "rgba(255,255,255,0.025)",
                            border: "1px solid rgba(255,255,255,0.05)"
                        }}>
                        <audio controls src={audioURL} className="w-full" style={{ height: "48px" }} />
                    </div>

                    {/* Pipeline completion tracker */}
                    <div className="flex items-start gap-0">
                        {STEPS.map((step, idx) => {
                            const StepIcon = step.icon;
                            const isDone   = activeStep >= idx;

                            return (
                                <div key={step.key} className="flex-1 flex flex-col items-center gap-2 relative">
                                    {idx < STEPS.length - 1 && (
                                        <div className="absolute top-4 left-[calc(50%+16px)] right-[calc(-50%+16px)] h-[1px]"
                                            style={{
                                                background: isDone
                                                    ? "rgba(48,209,88,0.4)"
                                                    : "rgba(255,255,255,0.06)"
                                            }} />
                                    )}

                                    <div className="w-8 h-8 rounded-full flex items-center justify-center relative z-10 transition-all duration-500"
                                        style={{
                                            background: isDone ? "rgba(48,209,88,0.12)" : "rgba(255,255,255,0.04)",
                                            border: `1px solid ${isDone ? "rgba(48,209,88,0.3)" : "rgba(255,255,255,0.06)"}`,
                                            boxShadow: isDone ? "0 0 12px rgba(48,209,88,0.15)" : "none"
                                        }}
                                    >
                                        <StepIcon size={12}
                                            style={{ color: isDone ? "#30D158" : "#3F3F46" }} />
                                    </div>
                                    <span className="text-[10px] font-medium text-center"
                                        style={{ color: isDone ? "#30D158" : "#27272A" }}>
                                        {step.label}
                                    </span>
                                </div>
                            );
                        })}
                    </div>

                    {/* Transcript block */}
                    <div className="rounded-2xl p-6"
                        style={{
                            background: "rgba(255,255,255,0.025)",
                            border: "1px solid rgba(255,255,255,0.05)"
                        }}
                    >
                        <div className="flex items-center gap-2 mb-4">
                            <Mic size={13} style={{ color: "#0A84FF" }} />
                            <p className="text-[11px] font-semibold uppercase tracking-[0.12em]"
                                style={{ color: "#52525B" }}>
                                Whisper Transcript
                            </p>
                        </div>
                        <p className="text-[14px] leading-7 whitespace-pre-wrap"
                            style={{ color: transcript ? "#D4D4D8" : "#3F3F46" }}>
                            {transcript || "Awaiting transcription…"}
                        </p>
                    </div>

                    {/* Status & Ready Button */}
                    <div className="flex items-center justify-between pt-2">
                        <p className="text-sm font-medium" style={{ color: "#52525B" }}>
                            {status}
                        </p>

                        <button
                            type="button"
                            onClick={resetUpload}
                            className="flex items-center gap-2 px-6 py-2.5 rounded-full text-[13px] font-semibold transition-all duration-200"
                            style={{
                                background: "rgba(48,209,88,0.1)",
                                border: "1px solid rgba(48,209,88,0.2)",
                                color: "#30D158"
                            }}
                        >
                            <CheckCircle2 size={14} /> New Input
                        </button>
                    </div>
                </div>

            )}

        </div>
    );
}