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
import { Activity, Brain, Zap, TrendingUp, Sparkles, Radio, Gauge, Flag, MessageSquare } from "lucide-react";
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

function ModuleCard({ icon: Icon, title, subtitle, color, visual = "bars", status = "Online" }) {
    return (
        <div className="module-card" style={{ "--module": color }}>
            <div className="module-top"><div className="module-icon"><Icon size={19} /></div><span className="module-title">{title}</span><span className="module-status"><span />{status}</span></div>
            <div className="module-subtitle">{subtitle}</div>
            <div className="module-visual">{visual === "bars" ? <MiniBars color={color} /> : visual === "wave" ? <div className="module-wave">{Array.from({ length: 30 }).map((_, i) => <i key={i} style={{ height: `${8 + ((i * 13) % 30)}px`, background: color }} />)}</div> : <div className="module-orbit" style={{ borderColor: `${color}55`, "--module": color }}><span /></div>}</div>
        </div>
    );
}

function OverviewCard({ analysis }) {
    const stress = analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0;
    const driver = analysis?.driver_analysis?.driver_state || "Calm";
    const emotion = analysis?.emotion?.emotion || "Nominal";
    return <div className="overview-card glass-card"><div className="section-head"><span>DRIVER STATE SNAPSHOT</span><b><i /> Live</b></div><div className="driver-grid"><div className="stress-ring" style={{ "--stress": Math.max(0, Math.min(100, stress)) }}><div><strong>{Math.round(stress)}%</strong><small>Stress Level</small><em>{stress >= 80 ? "HIGH" : stress >= 50 ? "ELEVATED" : "LOW"}</em></div></div><div className="driver-metrics">{[["Stress", stress, "#ff453a", Gauge],["Focus", Math.max(0, 100 - Math.round(stress * 0.35)), "#ff9f0a", Zap],["Fatigue", Math.max(0, Math.round(stress * 0.7)), "#ffd60a", Activity],["Confidence", Math.max(0, 100 - Math.round(stress * 0.2)), "#30d158", Sparkles],["Composure", Math.max(0, 100 - Math.round(stress * 0.45)), "#0a84ff", Brain]].map(([label, value, color, Icon]) => <div className="metric-row" key={label}><Icon size={15} style={{ color }} /><span>{label}</span><div className="metric-bar"><i style={{ width: `${value}%`, background: color }} /></div><b>{value}%</b></div>)}</div></div><div className="driver-chip-row"><span className="state-chip">{driver}</span><span className="state-chip soft">{emotion}</span></div></div>;
}

function StressCard({ analysis }) {
    const stress = analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0;
    return <div className="trend-card glass-card"><div className="section-head"><span>STRESS TREND</span><select defaultValue="50"><option value="50">Last 50 Laps</option><option value="20">Last 20 Laps</option><option value="10">Last 10 Laps</option></select></div><div className="chart-wrap"><svg viewBox="0 0 520 190" preserveAspectRatio="none" className="stress-chart"><defs><linearGradient id="stressFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#ff453a" stopOpacity=".38"/><stop offset="1" stopColor="#ff453a" stopOpacity="0"/></linearGradient></defs><g stroke="rgba(255,255,255,.07)" strokeWidth="1"><line x1="0" y1="30" x2="520" y2="30"/><line x1="0" y1="92" x2="520" y2="92"/><line x1="0" y1="154" x2="520" y2="154"/></g><path d="M0 122 C28 102,44 116,63 88 S98 100,119 76 S151 92,173 69 S205 90,227 104 S262 126,284 96 S322 78,344 91 S382 72,402 83 S438 62,463 70 S491 57,520 68 L520 190 L0 190 Z" fill="url(#stressFill)"/><path d="M0 122 C28 102,44 116,63 88 S98 100,119 76 S151 92,173 69 S205 90,227 104 S262 126,284 96 S322 78,344 91 S382 72,402 83 S438 62,463 70 S491 57,520 68" fill="none" stroke="#ff453a" strokeWidth="3"/></svg><div className="chart-labels"><span>Lap 10</span><span>Lap 20</span><span>Lap 30</span><span>Lap 40</span><span>Lap 50</span><span>Now</span></div><div className="chart-current" style={{ left: "78%" }}>{Math.round(stress)}%</div></div></div>;
}

function RecommendationCard({ analysis }) {
    const recommendation = analysis?.engineering_recommendation || analysis?.engineer_decision?.recommendation || analysis?.ai_summary || "Monitor driver stress and review the latest radio communication.";
    const confidence = analysis?.engineer_decision?.confidence ?? analysis?.stress_index?.confidence ?? 92;
    return <div className="recommend-card glass-card"><div className="section-head"><span>RECOMMENDATION</span></div><div className="recommend-icon"><Flag size={24} /></div><div className="priority-pill">◆ HIGH PRIORITY</div><h3>{String(recommendation).replace(/\s+/g, " ").slice(0, 120)}</h3><div className="confidence-row"><span>Confidence</span><b>{Math.round(confidence)}%</b></div><div className="confidence-bar"><i style={{ width: `${Math.max(0, Math.min(100, confidence))}%` }} /></div><div className="recommend-meta"><span>Category <b>Strategy</b></span><span>Timing <b>Immediate</b></span></div></div>;
}

export default function Dashboard() {
    const [sessions, setSessions] = useState(() => loadSessions());
    const [activeSessionId, setActiveSessionId] = useState(() => loadActiveSessionId());
    const [analysis, setAnalysis] = useState(null);
    const [uploadKey, setUploadKey] = useState(0);
    const [searchQuery, setSearchQuery] = useState("");
    const [mode, setMode] = useState("manual");
    const [samples, setSamples] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [simulationState, setSimulationState] = useState("idle");
    const [delaySeconds, setDelaySeconds] = useState(2);
    const [isProcessing, setIsProcessing] = useState(false);
    const [activeSection, setActiveSection] = useState("dashboard");
    const timerRef = useRef(null);

    useEffect(() => { if (mode === "simulation" && samples.length === 0) fetchSimulationSamples().then(data => setSamples(data || [])).catch(console.error); }, [mode, samples.length]);
    useEffect(() => { if (activeSessionId) { const session = sessions.find(s => s.id === activeSessionId); if (session?.analysis) setAnalysis(session.analysis); else setActiveSessionId(null); } }, []);
    useEffect(() => { saveSessions(sessions); }, [sessions]);
    useEffect(() => { saveActiveSessionId(activeSessionId); }, [activeSessionId]);

    const activeSession = sessions.find(s => s.id === activeSessionId) || null;
    const handleAnalysis = useCallback((data) => { const session = { id: Date.now().toString(), title: generateTitle(data.transcript), timestamp: Date.now(), transcript: data.transcript || "", analysis: data, chat: [] }; setAnalysis(data); setSessions(prev => [session, ...prev]); setActiveSessionId(session.id); }, []);
    const handleNewAnalysis = useCallback(() => { setAnalysis(null); setActiveSessionId(null); setUploadKey(k => k + 1); setActiveSection("dashboard"); }, []);
    const handleSelectSession = useCallback((sessionId) => { const session = sessions.find(s => s.id === sessionId); if (session?.analysis) { setAnalysis(session.analysis); setActiveSessionId(sessionId); setUploadKey(k => k + 1); setActiveSection("dashboard"); } }, [sessions]);
    const handleDeleteSession = useCallback((sessionId) => { setSessions(prev => prev.filter(s => s.id !== sessionId)); if (activeSessionId === sessionId) { setAnalysis(null); setActiveSessionId(null); setUploadKey(k => k + 1); } }, [activeSessionId]);
    const handleRenameSession = useCallback((sessionId, newTitle) => setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s)), []);
    const handleUpdateChat = useCallback((newChatMessages) => { if (!activeSessionId) return; setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, chat: newChatMessages } : s)); }, [activeSessionId]);

    const processSampleAtIndex = useCallback(async (idx, sampleList) => { const targetList = sampleList || samples; if (!targetList || idx < 0 || idx >= targetList.length) { setSimulationState("completed"); return null; } setIsProcessing(true); const sample = targetList[idx]; try { const blob = await fetchSimulationAudioBlob(sample.filename); const formData = new FormData(); formData.append("file", blob, sample.filename); formData.append("session_id", "simulation_session"); if (sample.lap != null) formData.append("lap", sample.lap.toString()); if (sample.lap_time != null) formData.append("lap_time_seconds", sample.lap_time.toString()); const res = await API.post("/upload", formData, { headers: { "Content-Type": "multipart/form-data" } }); const data = res.data; setAnalysis(data); const sessionObj = { id: `sim_${Date.now()}_${idx}`, title: `[Sim] Lap ${sample.lap || idx + 1} - ${sample.driver_name || sample.filename}`, timestamp: Date.now(), transcript: data.transcript || "", analysis: data, chat: [] }; setSessions(prev => [sessionObj, ...prev.filter(s => s.id !== sessionObj.id)]); setActiveSessionId(sessionObj.id); return data; } catch (err) { console.error(`Simulation processing error on sample ${sample.filename}:`, err); return null; } finally { setIsProcessing(false); } }, [samples]);
    const clearSimTimer = useCallback(() => { if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null; } }, []);
    const handleStartSimulation = useCallback(async () => { clearSimTimer(); let currentSamples = samples; if (!currentSamples.length) { try { currentSamples = await fetchSimulationSamples(); setSamples(currentSamples); } catch (err) { console.error(err); return; } } if (simulationState === "paused") setSimulationState("running"); else { await resetBackendSession("simulation_session"); setCurrentIndex(0); setSimulationState("running"); await processSampleAtIndex(0, currentSamples); } }, [clearSimTimer, processSampleAtIndex, samples, simulationState]);
    const handlePauseSimulation = useCallback(() => { clearSimTimer(); setSimulationState("paused"); }, [clearSimTimer]);
    const handleNextSimulation = useCallback(async () => { clearSimTimer(); if (currentIndex + 1 < samples.length) { const nextIdx = currentIndex + 1; setCurrentIndex(nextIdx); await processSampleAtIndex(nextIdx, samples); } else setSimulationState("completed"); }, [clearSimTimer, currentIndex, processSampleAtIndex, samples]);
    const handleResetSimulation = useCallback(async () => { clearSimTimer(); await resetBackendSession("simulation_session"); setCurrentIndex(0); setSimulationState("idle"); setAnalysis(null); }, [clearSimTimer]);
    useEffect(() => { if (simulationState === "running" && !isProcessing && samples.length > 0) { if (currentIndex < samples.length - 1) timerRef.current = setTimeout(async () => { const nextIdx = currentIndex + 1; setCurrentIndex(nextIdx); await processSampleAtIndex(nextIdx, samples); }, delaySeconds * 1000); else setSimulationState("completed"); } return () => clearSimTimer(); }, [simulationState, isProcessing, currentIndex, samples, delaySeconds, processSampleAtIndex, clearSimTimer]);

    const emotion = analysis?.emotion;
    const driver = analysis?.driver_analysis;
    const currentSample = samples[currentIndex] || null;

    const renderSection = () => {
        if (activeSection !== "dashboard") {
            return <div className="content-wrap"><div className="section-title"><span /> {activeSection.replace("ai-models", "AI MODELS").replace("api", "API REFERENCE").toUpperCase()}</div><div className="glass-card" style={{ borderRadius: 18, padding: 28, minHeight: 420 }}><h2 style={{ marginTop: 0 }}>{activeSection === "ai-models" ? "AI Models" : activeSection === "api" ? "API Reference" : activeSection[0].toUpperCase() + activeSection.slice(1)}</h2><p style={{ color: "#87909d", maxWidth: 720 }}>This section is ready for the corresponding PitSense control surface.</p></div></div>;
        }

        return <>
            <section className="hero-panel"><div className="hero-bg" /><div className="hero-overlay" /><div className="hero-topbar"><span className="live-pill"><i /> Pipeline Active</span><div className="hero-time"><b>21:45:32 IST</b><small>May 24, 2025</small></div><button className="icon-btn" aria-label="Theme"><Sparkles size={18} /></button></div><div className="hero-content"><div className="hero-copy"><div className="brand-wordmark"><span>PIT</span>SENSE</div><div className="hero-kicker">AI-Powered Race Intelligence</div><p>Transforming driver radio into real-time<br />insights, emotional intelligence, and<br />winning strategies.</p><div className="hero-actions"><button className="primary-btn" onClick={handleNewAnalysis}><Radio size={18} /> Start New Analysis</button><button className="secondary-btn" onClick={() => setActiveSection("dashboard")}><MessageSquare size={17} /> View Sessions</button></div></div><div className="live-insight glass-card"><div className="section-head"><span>Live Insight</span><b>{analysis ? "● LIVE" : "● STANDBY"}</b></div><div className={`waveform ${analysis ? "" : "muted"}`}>{Array.from({ length: 42 }).map((_, i) => <i key={i} style={{ height: `${analysis ? 10 + ((i * 17) % 42) : 8 + ((i * 11) % 26)}px` }} />)}</div><p>“{String(analysis?.transcript || analysis?.engineer_reply || "Upload a radio clip to see PitSense turn driver communication into actionable race intelligence.").slice(0, 90)}”</p><div className="live-stress"><span>Driver Stress</span><b>{analysis ? `${Math.round(analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0)}%` : "--"}</b></div><div className="live-progress"><i style={{ width: `${analysis ? Math.min(100, analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0) : 8}%` }} /></div></div></div></section>
            <div className="content-wrap"><section className="section-block"><div className="section-title"><span /> SYSTEM OVERVIEW</div><div className="module-grid"><ModuleCard icon={Activity} title="ASR Engine" subtitle="Parakeet TDT 0.6B" color="#1490ff" visual="wave" /><ModuleCard icon={Radio} title="Audio Emotion" subtitle="Wav2Vec2 XLSR" color="#8b4dff" /><ModuleCard icon={Brain} title="Text Emotion" subtitle="DistilRoBERTa" color="#ff8a00" visual="wave" /><ModuleCard icon={Gauge} title="Driver State" subtitle="Intelligence Engine" color="#18b8da" visual="orbit" /><ModuleCard icon={Flag} title="Recommendations" subtitle="Race Engineer AI" color="#3cd05f" visual="wave" /><ModuleCard icon={Sparkles} title="Gemini AI" subtitle="Strategic Advisor" color="#ff2093" visual="wave" /></div></section>
            {analysis && driver && emotion && <div className="four-stat-row">{[[Brain,"Emotion",emotion.emotion||"Nominal","#bf5af2"],[Activity,"Driver State",driver.driver_state||"Calm","#0a84ff"],[Zap,"Stress",`${driver.stress||analysis?.stress_index?.stress_index||0}%`,getStatColor("stress",driver.stress||analysis?.stress_index?.stress_index||0)],[TrendingUp,"Urgency",`${driver.urgency||0}%`,getStatColor("urgency",driver.urgency||0)]].map(([Icon,label,value,color])=><div className="compact-stat glass-card" key={label}><span className="compact-label">{label}</span><span className="compact-icon" style={{ color, background:`${color}13`, borderColor:`${color}28` }}><Icon size={17}/></span><strong style={{ color }}>{value}</strong></div>)}</div>}
            {!analysis && <div className="analysis-placeholder glass-card"><UploadCard key={uploadKey} setAnalysis={handleAnalysis} /></div>}
            {mode === "simulation" && <SimulationControls mode={mode} setMode={setMode} simulationState={simulationState} onStart={handleStartSimulation} onPause={handlePauseSimulation} onNext={handleNextSimulation} onReset={handleResetSimulation} delaySeconds={delaySeconds} setDelaySeconds={setDelaySeconds} currentIndex={currentIndex} totalSamples={samples.length} currentSample={currentSample} isProcessing={isProcessing} />}
            {analysis && <div className="analysis-grid"><OverviewCard analysis={analysis}/><StressCard analysis={analysis}/><RecommendationCard analysis={analysis}/></div>}
            {analysis && <div className="support-grid"><EmotionCard analysis={analysis}/><TranscriptCard analysis={analysis}/></div>}
            {analysis && <><TelemetryCard analysis={analysis}/><DecisionCard analysis={analysis}/></>}
            <AISummary analysis={analysis}/><div id="sessions-anchor"><EngineerChat session={activeSession} onUpdateChat={handleUpdateChat}/></div>
            <section className="metrics-strip glass-card"><div><span>Lap Time</span><b>1:24.532</b></div><div><span>Best Lap</span><b>1:22.847</b></div><div><span>Current Lap</span><b>32 / 58</b></div><div><span>Gap to Leader</span><b className="warn">+4.532s</b></div><div><span>Tyre Condition</span><b className="danger">23%</b></div><div><span>Fuel Load</span><b className="danger">18.6 L</b></div><div><span>Track Temp</span><b className="danger">42°C</b></div><div><span>Air Temp</span><b>28°C</b></div></section></div>
        </>;
    };

    return <div className="dashboard-shell"><Sidebar sessions={sessions} activeSessionId={activeSessionId} searchQuery={searchQuery} onSearchChange={setSearchQuery} onNewAnalysis={handleNewAnalysis} onSelectSession={handleSelectSession} onDeleteSession={handleDeleteSession} onRenameSession={handleRenameSession} activeSection={activeSection} onNavigate={setActiveSection} /><main className="dashboard-main">{renderSection()}</main></div>;
}
