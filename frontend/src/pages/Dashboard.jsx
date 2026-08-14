import Sidebar from "../components/common/Sidebar";
import UploadCard from "../components/upload/UploadCard";
import EmotionCard from "../components/dashboard/EmotionCard";
import AISummary from "../components/dashboard/AISummary";
import TelemetryCard from "../components/dashboard/TelemetryCard";
import DecisionCard from "../components/dashboard/DecisionCard";
import RadioCommandCard from "../components/dashboard/RadioCommandCard";
import SimulationControls from "../components/dashboard/SimulationControls";
import EngineerChat from "../components/engineer/EngineerChat";
import ProvenanceBadge from "../components/common/ProvenanceBadge";
import { useState, useEffect, useCallback, useRef } from "react";
import { Activity, Brain, Zap, TrendingUp, Sparkles, Radio, Gauge, Flag, MessageSquare, Play } from "lucide-react";
import { loadSessions, saveSessions, loadActiveSessionId, saveActiveSessionId, generateTitle } from "../utils/sessions";
import API, { fetchSimulationSamples, fetchSimulationAudioBlob, resetBackendSession } from "../services/api";

function getStatColor(key, value) {
    if (key === "stress") return value >= 80 ? "#ff453a" : value >= 50 ? "#ff9f0a" : "#30d158";
    if (key === "urgency") return value >= 80 ? "#ff453a" : value >= 50 ? "#ff9f0a" : "#ffd60a";
    return "#0a84ff";
}

function MiniBars({ color }) {
    return <div className="flex items-end gap-1 h-10 opacity-80">{Array.from({ length: 22 }).map((_, i) => <span key={i} className="w-1 rounded-full" style={{ height: `${12 + ((i * 17) % 27)}px`, background: color }} />)}</div>;
}

function ModuleCard({ icon: Icon, title, subtitle, color, visual = "bars", status = "Online", provenance = "MODEL" }) {
    return (
        <div className="module-card" style={{ "--module": color }}>
            <div className="module-top">
                <div className="module-icon"><Icon size={19} /></div>
                <span className="module-title">{title}</span>
                <ProvenanceBadge type={provenance} />
            </div>
            <div className="module-subtitle">{subtitle}</div>
            <div className="module-visual">{visual === "bars" ? <MiniBars color={color} /> : visual === "wave" ? <div className="module-wave">{Array.from({ length: 30 }).map((_, i) => <i key={i} style={{ height: `${8 + ((i * 13) % 30)}px`, background: color }} />)}</div> : <div className="module-orbit" style={{ borderColor: `${color}55`, "--module": color }}><span /></div>}</div>
        </div>
    );
}

function OverviewCard({ analysis }) {
    const stress = analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0;
    const driver = analysis?.driver_analysis?.driver_state || "Calm";
    const emotion = analysis?.emotion?.emotion || "Nominal";
    return (
        <div className="overview-card glass-card">
            <div className="section-head">
                <span>DRIVER STATE SNAPSHOT</span>
                <ProvenanceBadge type="MODEL" />
            </div>
            <div className="driver-grid">
                <div className="stress-ring" style={{ "--stress": Math.max(0, Math.min(100, stress)) }}>
                    <div>
                        <strong>{Math.round(stress)}%</strong>
                        <small>Stress Level</small>
                        <em>{stress >= 80 ? "HIGH" : stress >= 50 ? "ELEVATED" : "LOW"}</em>
                    </div>
                </div>
                <div className="driver-metrics">
                    {[
                        ["Stress", stress, "#ff453a", Gauge],
                        ["Focus", Math.max(0, 100 - Math.round(stress * 0.35)), "#ff9f0a", Zap],
                        ["Fatigue", Math.max(0, Math.round(stress * 0.7)), "#ffd60a", Activity],
                        ["Confidence", Math.max(0, 100 - Math.round(stress * 0.2)), "#30d158", Sparkles],
                        ["Composure", Math.max(0, 100 - Math.round(stress * 0.45)), "#0a84ff", Brain]
                    ].map(([label, value, color, Icon]) => (
                        <div className="metric-row" key={label}>
                            <Icon size={15} style={{ color }} />
                            <span>{label}</span>
                            <div className="metric-bar"><i style={{ width: `${value}%`, background: color }} /></div>
                            <b>{value}%</b>
                        </div>
                    ))}
                </div>
            </div>
            <div className="driver-chip-row">
                <span className="state-chip">{driver}</span>
                <span className="state-chip soft">{emotion}</span>
            </div>
        </div>
    );
}

function StressCard({ analysis }) {
    const stress = analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0;
    return (
        <div className="trend-card glass-card">
            <div className="section-head">
                <span>STRESS TREND</span>
                <ProvenanceBadge type="MODEL" />
            </div>
            <div className="chart-wrap">
                <svg viewBox="0 0 520 190" preserveAspectRatio="none" className="stress-chart">
                    <defs>
                        <linearGradient id="stressFill" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0" stopColor="#ff453a" stopOpacity=".38"/>
                            <stop offset="1" stopColor="#ff453a" stopOpacity="0"/>
                        </linearGradient>
                    </defs>
                    <g stroke="rgba(255,255,255,.07)" strokeWidth="1">
                        <line x1="0" y1="30" x2="520" y2="30"/>
                        <line x1="0" y1="92" x2="520" y2="92"/>
                        <line x1="0" y1="154" x2="520" y2="154"/>
                    </g>
                    <path d="M0 122 C28 102,44 116,63 88 S98 100,119 76 S151 92,173 69 S205 90,227 104 S262 126,284 96 S322 78,344 91 S382 72,402 83 S438 62,463 70 S491 57,520 68 L520 190 L0 190 Z" fill="url(#stressFill)"/>
                    <path d="M0 122 C28 102,44 116,63 88 S98 100,119 76 S151 92,173 69 S205 90,227 104 S262 126,284 96 S322 78,344 91 S382 72,402 83 S438 62,463 70 S491 57,520 68" fill="none" stroke="#ff453a" strokeWidth="3"/>
                </svg>
                <div className="chart-labels">
                    <span>Lap 10</span><span>Lap 20</span><span>Lap 30</span><span>Lap 40</span><span>Lap 50</span><span>Now</span>
                </div>
                <div className="chart-current" style={{ left: "78%" }}>{Math.round(stress)}%</div>
            </div>
        </div>
    );
}

function RecommendationCard({ analysis }) {
    const recommendation = analysis?.engineering_recommendation || analysis?.engineer_decision?.recommendation || analysis?.ai_summary || "Monitor driver stress and review the latest radio communication.";
    const confidence = analysis?.engineer_decision?.confidence !== undefined ? Math.round(analysis.engineer_decision.confidence * 100) : (analysis?.stress_index?.confidence ?? 92);
    return (
        <div className="recommend-card glass-card">
            <div className="section-head">
                <span>RECOMMENDATION</span>
                <ProvenanceBadge type="MODEL" />
            </div>
            <div className="recommend-icon"><Flag size={24} /></div>
            <div className="priority-pill">◆ HIGH PRIORITY</div>
            <h3>{String(recommendation).replace(/\s+/g, " ").slice(0, 120)}</h3>
            <div className="confidence-row">
                <span>Engine Confidence</span>
                <b>{Math.round(confidence)}%</b>
            </div>
            <div className="confidence-bar"><i style={{ width: `${Math.max(0, Math.min(100, confidence))}%` }} /></div>
            <div className="recommend-meta">
                <span>Category <b>Strategy</b></span>
                <span>Timing <b>Immediate</b></span>
            </div>
        </div>
    );
}

export default function Dashboard() {
    const [sessions, setSessions] = useState(() => loadSessions());
    const [activeSessionId, setActiveSessionId] = useState(() => loadActiveSessionId());
    const [isFreshSession, setIsFreshSession] = useState(true);
    const [showFreshConfirm, setShowFreshConfirm] = useState(false);
    const [analysis, setAnalysis] = useState(null);
    const [uploadKey, setUploadKey] = useState(0);
    const [searchQuery, setSearchQuery] = useState("");
    const [mode, setMode] = useState("manual");
    const [simSessionId, setSimSessionId] = useState(() => `sim_${Date.now()}`);
    const [samples, setSamples] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [simulationState, setSimulationState] = useState("idle");
    const [delaySeconds, setDelaySeconds] = useState(2);
    const [isProcessing, setIsProcessing] = useState(false);
    const [activeSection, setActiveSection] = useState("dashboard");
    const timerRef = useRef(null);

    useEffect(() => {
        if (mode === "simulation" && samples.length === 0) {
            fetchSimulationSamples()
                .then(data => setSamples(data || []))
                .catch(console.error);
        }
    }, [mode, samples.length]);

    useEffect(() => {
        if (activeSessionId) {
            const session = sessions.find(s => s.id === activeSessionId);
            if (session?.analysis) {
                setAnalysis(session.analysis);
                setIsFreshSession(false);
            } else {
                setActiveSessionId(`session_${Date.now()}`);
                setIsFreshSession(true);
            }
        } else {
            const freshId = `session_${Date.now()}`;
            setActiveSessionId(freshId);
            setIsFreshSession(true);
        }
    }, []);

    useEffect(() => { saveSessions(sessions); }, [sessions]);
    useEffect(() => { saveActiveSessionId(activeSessionId); }, [activeSessionId]);

    const activeSession = sessions.find(s => s.id === activeSessionId) || null;

    const executeStartFreshAnalysis = useCallback(() => {
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
        setShowFreshConfirm(false);
        const newSessionId = `session_${Date.now()}`;
        setActiveSessionId(newSessionId);
        setIsFreshSession(true);
        setAnalysis(null);
        setMode("manual");
        setSimulationState("idle");
        setUploadKey(k => k + 1);
        setActiveSection("dashboard");
    }, []);

    const handleFreshAnalysisClick = useCallback(() => {
        if (analysis || mode === "simulation") {
            setShowFreshConfirm(true);
        } else {
            executeStartFreshAnalysis();
        }
    }, [analysis, mode, executeStartFreshAnalysis]);

    const handleAnalysis = useCallback((data, explicitSessionId) => {
        const effectiveSessionId = explicitSessionId || activeSessionId || `session_${Date.now()}`;
        setAnalysis(data);
        setActiveSessionId(effectiveSessionId);
        setIsFreshSession(true);

        setSessions(prev => {
            const existing = prev.find(s => s.id === effectiveSessionId);
            if (existing) {
                return prev.map(s => s.id === effectiveSessionId ? {
                    ...s,
                    timestamp: Date.now(),
                    transcript: data.transcript || s.transcript,
                    analysis: data,
                } : s);
            } else {
                const newSession = {
                    id: effectiveSessionId,
                    title: generateTitle(data.transcript),
                    timestamp: Date.now(),
                    transcript: data.transcript || "",
                    analysis: data,
                    chat: []
                };
                return [newSession, ...prev];
            }
        });
    }, [activeSessionId]);

    const handleSelectSession = useCallback((sessionId) => {
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
        const session = sessions.find(s => s.id === sessionId);
        if (session?.analysis) {
            setAnalysis(session.analysis);
            setActiveSessionId(sessionId);
            setIsFreshSession(false);
            setMode("manual");
            setSimulationState("idle");
            setUploadKey(k => k + 1);
            setActiveSection("dashboard");
        }
    }, [sessions]);

    const handleDeleteSession = useCallback((sessionId) => {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (activeSessionId === sessionId) {
            executeStartFreshAnalysis();
        }
    }, [activeSessionId, executeStartFreshAnalysis]);

    const handleRenameSession = useCallback((sessionId, newTitle) => {
        setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s));
    }, []);

    const handleUpdateChat = useCallback((newChatMessages) => {
        if (!activeSessionId) return;
        setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, chat: newChatMessages } : s));
    }, [activeSessionId]);

    const clearSimTimer = useCallback(() => {
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
    }, []);

    const handleToggleSimulation = useCallback(() => {
        if (mode !== "simulation") {
            clearSimTimer();
            const newSimId = `sim_${Date.now()}`;
            setSimSessionId(newSimId);
            setActiveSessionId(newSimId);
            setMode("simulation");
            setAnalysis(null);
            setCurrentIndex(0);
            setSimulationState("idle");
            if (samples.length === 0) {
                fetchSimulationSamples()
                    .then(data => setSamples(data || []))
                    .catch(console.error);
            }
        } else {
            clearSimTimer();
            setMode("manual");
            setSimulationState("idle");
        }
    }, [clearSimTimer, mode, samples.length]);

    const processSampleAtIndex = useCallback(async (idx, sampleList, overrideSimId) => {
        const targetList = sampleList || samples;
        const effectiveSimId = overrideSimId || simSessionId || `sim_${Date.now()}`;
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
            formData.append("session_id", effectiveSimId);
            if (sample.lap != null) formData.append("lap", sample.lap.toString());
            if (sample.lap_time != null) formData.append("lap_time_seconds", sample.lap_time.toString());

            const res = await API.post("/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });
            const data = res.data;
            setAnalysis(data);

            const sessionObj = {
                id: effectiveSimId,
                title: `[Sim] Lap ${sample.lap || idx + 1} - ${sample.driver_name || sample.filename}`,
                timestamp: Date.now(),
                transcript: data.transcript || "",
                analysis: data,
                chat: []
            };
            setSessions(prev => [sessionObj, ...prev.filter(s => s.id !== sessionObj.id)]);
            setActiveSessionId(effectiveSimId);
            return data;
        } catch (err) {
            console.error(`Simulation processing error on sample ${sample.filename}:`, err);
            return null;
        } finally {
            setIsProcessing(false);
        }
    }, [samples, simSessionId]);

    const handleStartSimulation = useCallback(async () => {
        clearSimTimer();
        let currentSamples = samples;
        if (!currentSamples.length) {
            try {
                currentSamples = await fetchSimulationSamples();
                setSamples(currentSamples);
            } catch (err) {
                console.error(err);
                return;
            }
        }
        const effectiveSimId = simSessionId || `sim_${Date.now()}`;
        if (!simSessionId) setSimSessionId(effectiveSimId);

        if (simulationState === "paused") {
            setSimulationState("running");
        } else {
            await resetBackendSession(effectiveSimId);
            setCurrentIndex(0);
            setSimulationState("running");
            await processSampleAtIndex(0, currentSamples, effectiveSimId);
        }
    }, [clearSimTimer, processSampleAtIndex, samples, simSessionId, simulationState]);

    const handlePauseSimulation = useCallback(() => {
        clearSimTimer();
        setSimulationState("paused");
    }, [clearSimTimer]);

    const handleNextSimulation = useCallback(async () => {
        clearSimTimer();
        if (currentIndex + 1 < samples.length) {
            const nextIdx = currentIndex + 1;
            setCurrentIndex(nextIdx);
            await processSampleAtIndex(nextIdx, samples, simSessionId);
        } else {
            setSimulationState("completed");
        }
    }, [clearSimTimer, currentIndex, processSampleAtIndex, samples, simSessionId]);

    const handleResetSimulation = useCallback(async () => {
        clearSimTimer();
        const nextSimId = `sim_${Date.now()}`;
        await resetBackendSession(simSessionId);
        setSimSessionId(nextSimId);
        setActiveSessionId(nextSimId);
        setCurrentIndex(0);
        setSimulationState("idle");
        setAnalysis(null);
    }, [clearSimTimer, simSessionId]);

    useEffect(() => {
        if (simulationState === "running" && !isProcessing && samples.length > 0) {
            if (currentIndex < samples.length - 1) {
                timerRef.current = setTimeout(async () => {
                    const nextIdx = currentIndex + 1;
                    setCurrentIndex(nextIdx);
                    await processSampleAtIndex(nextIdx, samples, simSessionId);
                }, delaySeconds * 1000);
            } else {
                setSimulationState("completed");
            }
        }
        return () => clearSimTimer();
    }, [simulationState, isProcessing, currentIndex, samples, delaySeconds, processSampleAtIndex, clearSimTimer, simSessionId]);

    const emotion = analysis?.emotion;
    const driver = analysis?.driver_analysis;
    const telemetry = analysis?.telemetry;
    const currentSample = samples[currentIndex] || null;

    const sessionObsCount = analysis?.temporal_analysis?.sample_count
        ?? analysis?.temporal_analysis?.observation_count
        ?? (analysis ? 1 : 0);

    const renderSection = () => {
        if (activeSection !== "dashboard") {
            return (
                <div className="content-wrap">
                    <div className="section-title"><span /> {activeSection.replace("ai-models", "AI MODELS").replace("api", "API REFERENCE").toUpperCase()}</div>
                    <div className="glass-card" style={{ borderRadius: 18, padding: 28, minHeight: 420 }}>
                        <h2 style={{ marginTop: 0 }}>{activeSection === "ai-models" ? "AI Models" : activeSection === "api" ? "API Reference" : activeSection[0].toUpperCase() + activeSection.slice(1)}</h2>
                        <p style={{ color: "#87909d", maxWidth: 720 }}>This section is ready for the corresponding PitSense control surface.</p>
                    </div>
                </div>
            );
        }

        return (
            <>
                <section className="hero-panel">
                    <div className="hero-bg" /><div className="hero-overlay" />
                    <div className="hero-topbar">
                        <span className="live-pill"><i /> Pipeline Active</span>
                        <div className="hero-time"><b>21:45:32 IST</b><small>May 24, 2025</small></div>
                        <button className="icon-btn" aria-label="Theme"><Sparkles size={18} /></button>
                    </div>
                    <div className="hero-content">
                        <div className="hero-copy">
                            <div className="brand-wordmark"><span>PIT</span>SENSE</div>
                            <div className="hero-kicker">AI-Powered Race Intelligence</div>
                            <p>Transforming driver radio into real-time<br />insights, emotional intelligence, and<br />winning strategies.</p>
                            <div className="hero-actions">
                                <button className="primary-btn" onClick={handleFreshAnalysisClick}>
                                    <Radio size={18} /> + Start Fresh Analysis
                                </button>
                                <button
                                    className={`secondary-btn ${mode === "simulation" ? "bg-blue-600/30 border-blue-400 text-white" : ""}`}
                                    onClick={handleToggleSimulation}
                                >
                                    <Play size={17} /> {mode === "simulation" ? "Manual Upload" : "▶ Race Simulation"}
                                </button>
                            </div>
                        </div>
                        <div className="live-insight glass-card">
                            <div className="section-head">
                                <span>Live Insight</span>
                                <b>{analysis ? "● LIVE" : "● STANDBY"}</b>
                            </div>
                            <div className={`waveform ${analysis ? "" : "muted"}`}>
                                {Array.from({ length: 42 }).map((_, i) => <i key={i} style={{ height: `${analysis ? 10 + ((i * 17) % 42) : 8 + ((i * 11) % 26)}px` }} />)}
                            </div>
                            <p>“{String(analysis?.transcript || analysis?.engineer_reply || "Upload a radio clip or start Race Simulation to see PitSense generate actionable race engineering intelligence.").slice(0, 90)}”</p>
                            <div className="live-stress">
                                <span>Driver Stress</span>
                                <div className="flex items-center gap-1.5">
                                    <ProvenanceBadge type="MODEL" />
                                    <b>{analysis ? `${Math.round(analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0)}%` : "--"}</b>
                                </div>
                            </div>
                            <div className="live-progress">
                                <i style={{ width: `${analysis ? Math.min(100, analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0) : 8}%` }} />
                            </div>
                        </div>
                    </div>
                </section>

                <div className="content-wrap">
                    {/* COCKPIT SESSION CONTROL BAR & STATUS INDICATOR */}
                    <div className="flex items-center justify-between flex-wrap gap-3 p-3.5 mb-6 rounded-2xl border border-white/10 bg-zinc-950/70 backdrop-blur-xl shadow-lg">
                        <div className="flex items-center gap-2">
                            {mode === "simulation" ? (
                                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 font-extrabold text-xs tracking-wider">
                                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                                    <span>● RACE SIMULATION · OBSERVATION {Math.min(currentIndex + 1, samples.length || 1)} OF {samples.length || 0}</span>
                                    <span className="text-[10px] font-mono text-zinc-400">({simSessionId})</span>
                                </div>
                            ) : isFreshSession ? (
                                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-extrabold text-xs tracking-wider">
                                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                                    <span>
                                        ● FRESH ANALYSIS · {sessionObsCount === 0 ? "0 OBSERVATIONS" : `${sessionObsCount} OBSERVATION${sessionObsCount === 1 ? "" : "S"}`}
                                    </span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-extrabold text-xs tracking-wider">
                                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                                    <span>
                                        ● ACTIVE SESSION · {sessionObsCount} OBSERVATION{sessionObsCount === 1 ? "" : "S"}
                                    </span>
                                    <span className="text-[11px] text-zinc-300 font-medium">({activeSession?.title || "Saved Session"})</span>
                                </div>
                            )}
                        </div>

                        <div className="flex items-center gap-2.5">
                            <button
                                type="button"
                                onClick={handleFreshAnalysisClick}
                                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-extrabold uppercase tracking-wider text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 shadow-sm transition-all active:scale-95 cursor-pointer"
                            >
                                <Radio size={14} />
                                <span>+ START FRESH ANALYSIS</span>
                            </button>

                            <button
                                type="button"
                                onClick={handleToggleSimulation}
                                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-extrabold uppercase tracking-wider transition-all active:scale-95 cursor-pointer ${
                                    mode === "simulation"
                                        ? "text-blue-200 bg-blue-600 border border-blue-400 shadow-md shadow-blue-900/40"
                                        : "text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30"
                                }`}
                            >
                                <Play size={14} />
                                <span>{mode === "simulation" ? "⏹ MANUAL UPLOAD" : "▶ RACE SIMULATION"}</span>
                            </button>
                        </div>
                    </div>

                    <section className="section-block">
                        <div className="section-title"><span /> SYSTEM OVERVIEW</div>
                        <div className="module-grid">
                            <ModuleCard icon={Activity} title="ASR Engine" subtitle="Parakeet TDT 0.6B" color="#1490ff" visual="wave" provenance="MODEL" />
                            <ModuleCard icon={Radio} title="Audio Emotion" subtitle="Wav2Vec2 XLSR" color="#8b4dff" provenance="MODEL" />
                            <ModuleCard icon={Brain} title="Text Emotion" subtitle="DistilRoBERTa" color="#ff8a00" visual="wave" provenance="MODEL" />
                            <ModuleCard icon={Gauge} title="Driver State" subtitle="Intelligence Engine" color="#18b8da" visual="orbit" provenance="MODEL" />
                            <ModuleCard icon={Flag} title="Recommendations" subtitle="Race Engineer AI" color="#3cd05f" visual="wave" provenance="MODEL" />
                            <ModuleCard icon={Sparkles} title="Gemini AI" subtitle="Strategic Advisor" color="#ff2093" visual="wave" provenance="MODEL" />
                        </div>
                    </section>

                    {analysis && driver && emotion && (
                        <div className="four-stat-row">
                            {[
                                [Brain, "Emotion", emotion.emotion || "Nominal", "#bf5af2", "MODEL"],
                                [Activity, "Driver State", driver.driver_state || "Calm", "#0a84ff", "MODEL"],
                                [Zap, "Stress", `${driver.stress || analysis?.stress_index?.stress_index || 0}%`, getStatColor("stress", driver.stress || analysis?.stress_index?.stress_index || 0), "MODEL"],
                                [TrendingUp, "Urgency", `${driver.urgency || 0}%`, getStatColor("urgency", driver.urgency || 0), "MODEL"]
                            ].map(([Icon, label, value, color, prov]) => (
                                <div className="compact-stat glass-card" key={label}>
                                    <div className="flex items-center justify-between w-full mb-1">
                                        <span className="compact-label">{label}</span>
                                        <ProvenanceBadge type={prov} />
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="compact-icon" style={{ color, background: `${color}13`, borderColor: `${color}28` }}>
                                            <Icon size={17} />
                                        </span>
                                        <strong style={{ color }}>{value}</strong>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {mode === "manual" && !analysis && (
                        <div className="analysis-placeholder glass-card">
                            <UploadCard
                                key={uploadKey}
                                setAnalysis={handleAnalysis}
                                sessionId={activeSessionId}
                                onSessionCreated={(id) => setActiveSessionId(id)}
                            />
                        </div>
                    )}

                    {mode === "simulation" && (
                        <SimulationControls
                            mode={mode}
                            setMode={setMode}
                            simulationState={simulationState}
                            simSessionId={simSessionId}
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
                    )}

                    {/* PROMINENT ENGINEER DECISION CARD */}
                    {analysis && (
                        <div className="mb-6">
                            <DecisionCard analysis={analysis} />
                        </div>
                    )}

                    {analysis && (
                        <div className="analysis-grid">
                            <OverviewCard analysis={analysis} />
                            <StressCard analysis={analysis} />
                            <RecommendationCard analysis={analysis} />
                        </div>
                    )}

                    {analysis && (
                        <div className="support-grid radio-layout">
                            <RadioCommandCard analysis={analysis} />
                            <OverviewCard analysis={analysis} />
                            <RecommendationCard analysis={analysis} />
                        </div>
                    )}

                    {analysis && <TelemetryCard analysis={analysis} />}

                    <AISummary analysis={analysis} />

                    <div id="sessions-anchor">
                        <EngineerChat session={activeSession} onUpdateChat={handleUpdateChat} />
                    </div>

                    {/* COCKPIT METRICS STRIP WITH SOURCE-VERIFIED PROVENANCE LABELS */}
                    <section className="metrics-strip glass-card">
                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Lap Time</span>
                                <ProvenanceBadge type={telemetry?.available && telemetry?.lap_time ? "DATASET" : "SIMULATED"} />
                            </div>
                            <b>{telemetry?.available && telemetry?.lap_time ? `${Number(telemetry.lap_time).toFixed(3)}s` : "1:24.532"}</b>
                        </div>

                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Best Lap</span>
                                <ProvenanceBadge type="SIMULATED" />
                            </div>
                            <b>1:22.847</b>
                        </div>

                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Current Lap</span>
                                <ProvenanceBadge type={telemetry?.available && telemetry?.lap !== undefined ? "DATASET" : "SIMULATED"} />
                            </div>
                            <b>{telemetry?.available && telemetry?.lap !== undefined ? `Lap ${telemetry.lap}` : "32 / 58"}</b>
                        </div>

                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Gap to Leader</span>
                                <ProvenanceBadge type="SIMULATED" />
                            </div>
                            <b className="warn">+4.532s</b>
                        </div>

                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Tyre Condition</span>
                                <ProvenanceBadge type="SIMULATED" />
                            </div>
                            <b className="danger">23%</b>
                        </div>

                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Fuel Load</span>
                                <ProvenanceBadge type="SIMULATED" />
                            </div>
                            <b className="danger">18.6 L</b>
                        </div>

                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Track Temp</span>
                                <ProvenanceBadge type="SIMULATED" />
                            </div>
                            <b className="danger">42°C</b>
                        </div>

                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Air Temp</span>
                                <ProvenanceBadge type="SIMULATED" />
                            </div>
                            <b>28°C</b>
                        </div>

                        <div>
                            <div className="flex items-center justify-between gap-1 w-full">
                                <span>Live ECU Temp</span>
                                <ProvenanceBadge type="UNAVAILABLE" />
                            </div>
                            <b style={{ color: "#71717A" }}>N/A</b>
                        </div>
                    </section>
                </div>
            </>
        );
    };

    return (
        <div className="dashboard-shell">
            {/* START FRESH ANALYSIS CONFIRMATION MODAL */}
            {showFreshConfirm && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center p-4"
                    style={{ background: "rgba(0,0,0,0.82)", backdropFilter: "blur(12px)" }}
                >
                    <div
                        className="w-full max-w-md p-7 rounded-3xl border border-white/10 shadow-2xl space-y-5"
                        style={{
                            background: "linear-gradient(180deg, rgba(20, 24, 33, 0.96), rgba(10, 12, 17, 0.98))",
                            boxShadow: "0 24px 64px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1)"
                        }}
                    >
                        <div className="flex items-center gap-3.5">
                            <div className="w-11 h-11 rounded-2xl flex items-center justify-center bg-emerald-500/10 border border-emerald-500/25 text-emerald-400">
                                <Radio size={22} />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white tracking-tight">Start Fresh Analysis?</h3>
                                <p className="text-xs text-zinc-400">Session Isolation & Temporal Reset</p>
                            </div>
                        </div>

                        <p className="text-sm text-zinc-300 leading-relaxed">
                            Start a new analysis? Your current session will be preserved in <strong>Session History</strong>.
                        </p>

                        <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 text-xs text-zinc-400 space-y-1">
                            <div className="flex items-center gap-2 text-zinc-300 font-semibold">
                                <Sparkles size={13} className="text-emerald-400" />
                                <span>Zero Data Leakage Guarantee</span>
                            </div>
                            <p>Previous observations, stress trends, and lap correlation will not carry over to the new fresh session.</p>
                        </div>

                        <div className="flex items-center justify-end gap-3 pt-2">
                            <button
                                type="button"
                                onClick={() => setShowFreshConfirm(false)}
                                className="px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider text-zinc-400 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-all cursor-pointer"
                            >
                                CANCEL
                            </button>
                            <button
                                type="button"
                                onClick={executeStartFreshAnalysis}
                                className="px-6 py-2.5 rounded-xl text-xs font-extrabold uppercase tracking-wider text-white bg-emerald-600 hover:bg-emerald-500 border border-emerald-500/40 shadow-lg shadow-emerald-900/30 transition-all active:scale-95 cursor-pointer"
                            >
                                START FRESH
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <Sidebar
                sessions={sessions}
                activeSessionId={activeSessionId}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onNewAnalysis={handleFreshAnalysisClick}
                onSelectSession={handleSelectSession}
                onDeleteSession={handleDeleteSession}
                onRenameSession={handleRenameSession}
                activeSection={activeSection}
                onNavigate={setActiveSection}
            />
            <main className="dashboard-main">{renderSection()}</main>
        </div>
    );
}