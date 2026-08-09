import Sidebar from "../components/common/Sidebar";
import UploadCard from "../components/upload/UploadCard";
import TranscriptCard from "../components/dashboard/TranscriptCard";
import EmotionCard from "../components/dashboard/EmotionCard";
import AISummary from "../components/dashboard/AISummary";
import TelemetryCard from "../components/dashboard/TelemetryCard";
import DecisionCard from "../components/dashboard/DecisionCard";
import SimulationControls from "../components/dashboard/SimulationControls";
import EngineerChat from "../components/engineer/EngineerChat";
import { useState, useEffect, useCallback, useRef } from "react";
import {
    Activity,
    Brain,
    Zap,
    TrendingUp,
} from "lucide-react";
import {
    loadSessions,
    saveSessions,
    loadActiveSessionId,
    saveActiveSessionId,
    generateTitle
} from "../utils/sessions";
import API, {
    fetchSimulationSamples,
    fetchSimulationAudioBlob,
    resetBackendSession,
} from "../services/api";

/* ── Stat color helper ── */
function getStatColor(key, value) {
    if (key === "stress")  return value >= 80 ? "#FF453A" : value >= 50 ? "#FF9F0A" : "#30D158";
    if (key === "urgency") return value >= 80 ? "#FF453A" : value >= 50 ? "#FF9F0A" : "#FFD60A";
    return "#0A84FF";
}

/* ── Stat Card ── */
function StatCard({ icon: Icon, label, value, color, delay = 0 }) {
    return (
        <div
            className="rounded-3xl p-6 cursor-default animate-fade-in-up"
            style={{
                background: "rgba(255,255,255,0.04)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                border: "1px solid rgba(255,255,255,0.05)",
                boxShadow: "0 2px 16px rgba(0,0,0,0.25)",
                animationDelay: `${delay}ms`,
                transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)"
            }}
            onMouseEnter={e => {
                e.currentTarget.style.background = "rgba(255,255,255,0.07)";
                e.currentTarget.style.transform = "translateY(-3px)";
                e.currentTarget.style.boxShadow = `0 12px 40px rgba(0,0,0,0.35), 0 0 0 1px ${color}15`;
            }}
            onMouseLeave={e => {
                e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 2px 16px rgba(0,0,0,0.25)";
            }}
        >
            <div className="flex items-center justify-between mb-5">
                <p className="text-[11px] font-medium uppercase tracking-[0.12em]"
                    style={{ color: "#52525B" }}>
                    {label}
                </p>
                <div className="w-9 h-9 rounded-2xl flex items-center justify-center"
                    style={{ background: `${color}12`, border: `1px solid ${color}20` }}>
                    <Icon size={15} style={{ color }} />
                </div>
            </div>
            <p className="text-3xl font-extrabold tracking-tight capitalize"
                style={{ color }}>
                {value}
            </p>
        </div>
    );
}

export default function Dashboard() {

    /* ── Session state ── */
    const [sessions, setSessions]             = useState(() => loadSessions());
    const [activeSessionId, setActiveSessionId] = useState(() => loadActiveSessionId());
    const [analysis, setAnalysis]             = useState(null);
    const [uploadKey, setUploadKey]           = useState(0);
    const [searchQuery, setSearchQuery]       = useState("");

    /* ── Race Simulation state ── */
    const [mode, setMode]                     = useState("manual"); // "manual" | "simulation"
    const [samples, setSamples]               = useState([]);
    const [currentIndex, setCurrentIndex]     = useState(0);
    const [simulationState, setSimulationState] = useState("idle"); // "idle" | "running" | "paused" | "completed"
    const [delaySeconds, setDelaySeconds]     = useState(2);
    const [isProcessing, setIsProcessing]     = useState(false);
    const timerRef                            = useRef(null);

    /* Fetch simulation samples when entering simulation mode */
    useEffect(() => {
        if (mode === "simulation" && samples.length === 0) {
            fetchSimulationSamples()
                .then(data => {
                    setSamples(data || []);
                })
                .catch(err => {
                    console.error("Failed to load simulation samples:", err);
                });
        }
    }, [mode, samples.length]);

    /* Restore active session on mount */
    useEffect(() => {
        if (activeSessionId) {
            const session = sessions.find(s => s.id === activeSessionId);
            if (session?.analysis) {
                setAnalysis(session.analysis);
            } else {
                setActiveSessionId(null);
            }
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    /* Persist sessions & activeSessionId */
    useEffect(() => {
        saveSessions(sessions);
    }, [sessions]);

    useEffect(() => {
        saveActiveSessionId(activeSessionId);
    }, [activeSessionId]);

    /* Active Session Object */
    const activeSession = sessions.find(s => s.id === activeSessionId) || null;

    /* Handlers for manual mode */
    const handleAnalysis = useCallback((data) => {
        setAnalysis(data);

        const session = {
            id: Date.now().toString(),
            title: generateTitle(data.transcript),
            timestamp: Date.now(),
            transcript: data.transcript || "",
            analysis: data,
            chat: []
        };

        setSessions(prev => [session, ...prev]);
        setActiveSessionId(session.id);
    }, []);

    const handleNewAnalysis = useCallback(() => {
        setAnalysis(null);
        setActiveSessionId(null);
        setUploadKey(k => k + 1);
    }, []);

    const handleSelectSession = useCallback((sessionId) => {
        const session = sessions.find(s => s.id === sessionId);
        if (session?.analysis) {
            setAnalysis(session.analysis);
            setActiveSessionId(sessionId);
            setUploadKey(k => k + 1);
        }
    }, [sessions]);

    const handleDeleteSession = useCallback((sessionId) => {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (activeSessionId === sessionId) {
            setAnalysis(null);
            setActiveSessionId(null);
            setUploadKey(k => k + 1);
        }
    }, [activeSessionId]);

    const handleRenameSession = useCallback((sessionId, newTitle) => {
        setSessions(prev =>
            prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s)
        );
    }, []);

    const handleUpdateChat = useCallback((newChatMessages) => {
        if (!activeSessionId) return;
        setSessions(prev =>
            prev.map(s => s.id === activeSessionId ? { ...s, chat: newChatMessages } : s)
        );
    }, [activeSessionId]);

    /* ── Simulation processing engine ── */
    const processSampleAtIndex = useCallback(async (idx, sampleList) => {
        const targetList = sampleList || samples;
        if (!targetList || idx < 0 || idx >= targetList.length) {
            setSimulationState("completed");
            return null;
        }

        setIsProcessing(true);
        const sample = targetList[idx];

        try {
            const blob = await fetchSimulationAudioBlob(sample.filename);
            const formData = new FormData();
            formData.append("file", blob, sample.filename);
            formData.append("session_id", "simulation_session");
            if (sample.lap !== null && sample.lap !== undefined) {
                formData.append("lap", sample.lap.toString());
            }
            if (sample.lap_time !== null && sample.lap_time !== undefined) {
                formData.append("lap_time_seconds", sample.lap_time.toString());
            }

            const res = await API.post("/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });

            const data = res.data;
            setAnalysis(data);

            // Record as session item for sidebar
            const sessionObj = {
                id: `sim_${Date.now()}_${idx}`,
                title: `[Sim] Lap ${sample.lap || idx + 1} - ${sample.driver_name || sample.filename}`,
                timestamp: Date.now(),
                transcript: data.transcript || "",
                analysis: data,
                chat: []
            };

            setSessions(prev => [sessionObj, ...prev.filter(s => s.id !== sessionObj.id)]);
            setActiveSessionId(sessionObj.id);
            return data;
        } catch (err) {
            console.error(`Simulation processing error on sample ${sample.filename}:`, err);
            return null;
        } finally {
            setIsProcessing(false);
        }
    }, [samples]);

    /* Clear simulation timer */
    const clearSimTimer = useCallback(() => {
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
    }, []);

    /* Simulation Control Callbacks */
    const handleStartSimulation = useCallback(async () => {
        clearSimTimer();
        let currentSamples = samples;
        if (currentSamples.length === 0) {
            try {
                currentSamples = await fetchSimulationSamples();
                setSamples(currentSamples);
            } catch (err) {
                console.error("Failed to load simulation samples:", err);
                return;
            }
        }

        if (simulationState === "paused") {
            setSimulationState("running");
            // Schedule next step from current index + 1
            if (currentIndex + 1 < currentSamples.length) {
                timerRef.current = setTimeout(async () => {
                    const nextIdx = currentIndex + 1;
                    setCurrentIndex(nextIdx);
                    await processSampleAtIndex(nextIdx, currentSamples);
                }, delaySeconds * 1000);
            } else {
                setSimulationState("completed");
            }
        } else {
            // Fresh start or restart
            await resetBackendSession("simulation_session");
            setCurrentIndex(0);
            setSimulationState("running");
            await processSampleAtIndex(0, currentSamples);
        }
    }, [clearSimTimer, currentIndex, delaySeconds, processSampleAtIndex, samples, simulationState]);

    const handlePauseSimulation = useCallback(() => {
        clearSimTimer();
        setSimulationState("paused");
    }, [clearSimTimer]);

    const handleNextSimulation = useCallback(async () => {
        clearSimTimer();
        if (currentIndex + 1 < samples.length) {
            const nextIdx = currentIndex + 1;
            setCurrentIndex(nextIdx);
            await processSampleAtIndex(nextIdx, samples);
        } else {
            setSimulationState("completed");
        }
    }, [clearSimTimer, currentIndex, processSampleAtIndex, samples]);

    const handleResetSimulation = useCallback(async () => {
        clearSimTimer();
        await resetBackendSession("simulation_session");
        setCurrentIndex(0);
        setSimulationState("idle");
        setAnalysis(null);
    }, [clearSimTimer]);

    /* Auto-advance effect when simulationState === "running" and processing completes */
    useEffect(() => {
        if (simulationState === "running" && !isProcessing && samples.length > 0) {
            if (currentIndex < samples.length - 1) {
                timerRef.current = setTimeout(async () => {
                    const nextIdx = currentIndex + 1;
                    setCurrentIndex(nextIdx);
                    await processSampleAtIndex(nextIdx, samples);
                }, delaySeconds * 1000);
            } else {
                setSimulationState("completed");
            }
        }
        return () => clearSimTimer();
    }, [simulationState, isProcessing, currentIndex, samples, delaySeconds, processSampleAtIndex, clearSimTimer]);

    const emotion = analysis?.emotion;
    const driver  = analysis?.driver_analysis;
    const currentSample = samples[currentIndex] || null;

    return (
        <div className="flex min-h-screen" style={{ background: "#09090B" }}>

            <Sidebar
                sessions={sessions}
                activeSessionId={activeSessionId}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onNewAnalysis={handleNewAnalysis}
                onSelectSession={handleSelectSession}
                onDeleteSession={handleDeleteSession}
                onRenameSession={handleRenameSession}
            />

            <main className="flex-1 min-w-0 overflow-y-auto">

                {/* ── Top bar ── */}
                <div className="sticky top-0 z-10 px-12 py-6 flex items-center justify-between"
                    style={{
                        background: "rgba(9,9,11,0.85)",
                        backdropFilter: "blur(24px)",
                        WebkitBackdropFilter: "blur(24px)",
                        borderBottom: "1px solid rgba(255,255,255,0.04)"
                    }}
                >
                    <div>
                        <h1 className="text-2xl font-extrabold text-white tracking-tight">
                            PitSense
                        </h1>
                        <p className="text-[13px] mt-0.5" style={{ color: "#52525B" }}>
                            AI-Powered Race Intelligence — Driver Communication & Telemetry Analysis
                        </p>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-2 rounded-full"
                        style={{
                            background: "rgba(48,209,88,0.06)",
                            border: "1px solid rgba(48,209,88,0.1)"
                        }}
                    >
                        <div className="w-1.5 h-1.5 rounded-full animate-pulse"
                            style={{ background: "#30D158", boxShadow: "0 0 6px #30D158" }} />
                        <span className="text-[11px] font-semibold" style={{ color: "#30D158" }}>
                            Pipeline Active
                        </span>
                    </div>
                </div>

                {/* ── Content ── */}
                <div className="px-12 py-10 space-y-8">

                    {/* Simulation Controls Component */}
                    <SimulationControls
                        mode={mode}
                        setMode={setMode}
                        simulationState={simulationState}
                        onStart={handleStartSimulation}
                        onPause={handlePauseSimulation}
                        onNext={handleNextSimulation}
                        onReset={handleResetSimulation}
                        delaySeconds={delaySeconds}
                        setDelaySeconds={setDelaySeconds}
                        currentIndex={currentIndex}
                        totalSamples={samples.length}
                        currentSample={currentSample}
                        isProcessing={isProcessing}
                    />

                    {/* Stat cards (visible after analysis) */}
                    {analysis && driver && emotion && (
                        <div className="grid grid-cols-4 gap-5">
                            <StatCard
                                icon={Brain}
                                label="Emotion"
                                value={emotion.emotion || "Nominal"}
                                color="#BF5AF2"
                                delay={0}
                            />
                            <StatCard
                                icon={Activity}
                                label="Driver State"
                                value={driver.driver_state || "Calm"}
                                color="#0A84FF"
                                delay={60}
                            />
                            <StatCard
                                icon={Zap}
                                label="Stress"
                                value={`${driver.stress || 0}%`}
                                color={getStatColor("stress", driver.stress || 0)}
                                delay={120}
                            />
                            <StatCard
                                icon={TrendingUp}
                                label="Urgency"
                                value={`${driver.urgency || 0}%`}
                                color={getStatColor("urgency", driver.urgency || 0)}
                                delay={180}
                            />
                        </div>
                    )}

                    {/* Upload card (Manual Mode) */}
                    {mode === "manual" && (
                        <UploadCard key={uploadKey} setAnalysis={handleAnalysis} />
                    )}

                    {/* Driver Status + Transcript */}
                    {analysis && (
                        <div className="grid grid-cols-2 gap-6">
                            <EmotionCard analysis={analysis} />
                            <TranscriptCard analysis={analysis} />
                        </div>
                    )}

                    {/* Race Telemetry Card */}
                    {analysis && <TelemetryCard analysis={analysis} />}

                    {/* Engineer Decision Support Engine Card */}
                    {analysis && <DecisionCard analysis={analysis} />}

                    {/* AI Race Engineer Report */}
                    <AISummary analysis={analysis} />

                    {/* Ask the Race Engineer Chat */}
                    <EngineerChat session={activeSession} onUpdateChat={handleUpdateChat} />

                </div>

            </main>

        </div>
    );
}