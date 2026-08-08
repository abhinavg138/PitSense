import Sidebar from "../components/common/Sidebar";
import UploadCard from "../components/upload/UploadCard";
import TranscriptCard from "../components/dashboard/TranscriptCard";
import EmotionCard from "../components/dashboard/EmotionCard";
import AISummary from "../components/dashboard/AISummary";
import TelemetryCard from "../components/dashboard/TelemetryCard";
import EngineerChat from "../components/engineer/EngineerChat";
import { useState, useEffect, useCallback } from "react";
import {
    Activity,
    Brain,
    Zap,
    TrendingUp,
    Radio
} from "lucide-react";
import {
    loadSessions,
    saveSessions,
    loadActiveSessionId,
    saveActiveSessionId,
    generateTitle
} from "../utils/sessions";

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

    /* Restore active session on mount — clear the ID if the session no longer exists. */
    useEffect(() => {
        if (activeSessionId) {
            const session = sessions.find(s => s.id === activeSessionId);
            if (session?.analysis) {
                setAnalysis(session.analysis);
            } else {
                // Session was deleted or storage is corrupted — don't keep a stale pointer.
                setActiveSessionId(null);
            }
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    /* Persist sessions */
    useEffect(() => {
        saveSessions(sessions);
    }, [sessions]);

    /* Persist active session ID */
    useEffect(() => {
        saveActiveSessionId(activeSessionId);
    }, [activeSessionId]);

    /* Active Session Object */
    const activeSession = sessions.find(s => s.id === activeSessionId) || null;

    /* ── Handlers ── */
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

    const emotion = analysis?.emotion;
    const driver  = analysis?.driver_analysis;

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
                            AI-Powered Race Intelligence — Real-time Driver Communication Analysis
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

                    {/* Stat cards (visible after analysis) */}
                    {analysis && (
                        <div className="grid grid-cols-4 gap-5">
                            <StatCard
                                icon={Brain}
                                label="Emotion"
                                value={emotion.emotion}
                                color="#BF5AF2"
                                delay={0}
                            />
                            <StatCard
                                icon={Activity}
                                label="Driver State"
                                value={driver.driver_state}
                                color="#0A84FF"
                                delay={60}
                            />
                            <StatCard
                                icon={Zap}
                                label="Stress"
                                value={`${driver.stress}%`}
                                color={getStatColor("stress", driver.stress)}
                                delay={120}
                            />
                            <StatCard
                                icon={TrendingUp}
                                label="Urgency"
                                value={`${driver.urgency}%`}
                                color={getStatColor("urgency", driver.urgency)}
                                delay={180}
                            />
                        </div>
                    )}

                    {/* Upload card */}
                    <UploadCard key={uploadKey} setAnalysis={handleAnalysis} />

                    {/* Driver Status + Transcript */}
                    {analysis && (
                        <div className="grid grid-cols-2 gap-6">
                            <EmotionCard analysis={analysis} />
                            <TranscriptCard analysis={analysis} />
                        </div>
                    )}

                    {/* Race Telemetry Card — always shown after first analysis */}
                    {analysis && <TelemetryCard analysis={analysis} />}

                    {/* AI Race Engineer Report */}
                    <AISummary analysis={analysis} />

                    {/* Ask the Race Engineer Chat */}
                    <EngineerChat session={activeSession} onUpdateChat={handleUpdateChat} />

                </div>

            </main>

        </div>
    );
}