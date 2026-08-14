import React from "react";
import {
    Activity,
    AlertTriangle,
    ShieldCheck,
    TrendingUp,
    Gauge,
    Flame,
    ArrowRight,
    CheckCircle2,
    XCircle,
    AlertCircle,
    FileText,
    Mic,
    Radio,
    Clock,
    Zap,
    Info
} from "lucide-react";
import ProvenanceBadge from "../common/ProvenanceBadge";

function getSeverityBadge(severity) {
    switch (severity) {
        case "CRITICAL":
            return { color: "#FF453A", bg: "rgba(255, 69, 58, 0.12)", border: "rgba(255, 69, 58, 0.25)", label: "CRITICAL INTERVENTION" };
        case "STRESSED":
            return { color: "#FF9F0A", bg: "rgba(255, 159, 10, 0.12)", border: "rgba(255, 159, 10, 0.25)", label: "STRESSED WORKLOAD" };
        case "ELEVATED":
            return { color: "#FFD60A", bg: "rgba(255, 214, 10, 0.10)", border: "rgba(255, 214, 10, 0.20)", label: "ELEVATED ATTENTION" };
        default:
            return { color: "#30D158", bg: "rgba(48, 209, 88, 0.10)", border: "rgba(48, 209, 88, 0.20)", label: "CALM / NOMINAL" };
    }
}

function DataQualityBadge({ domain, state }) {
    let color = "#71717A";
    let bg = "rgba(113, 113, 122, 0.12)";
    let border = "rgba(113, 113, 122, 0.25)";
    let Icon = XCircle;

    if (state === "AVAILABLE") {
        color = "#30D158";
        bg = "rgba(48, 209, 88, 0.12)";
        border = "rgba(48, 209, 88, 0.25)";
        Icon = CheckCircle2;
    } else if (state === "PARTIAL") {
        color = "#FF9F0A";
        bg = "rgba(255, 159, 10, 0.12)";
        border = "rgba(255, 159, 10, 0.25)";
        Icon = AlertCircle;
    } else if (state === "INSUFFICIENT") {
        color = "#FFD60A";
        bg = "rgba(255, 214, 10, 0.12)";
        border = "rgba(255, 214, 10, 0.25)";
        Icon = AlertCircle;
    }

    return (
        <div
            className="flex items-center justify-between p-3 rounded-xl"
            style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.05)" }}
        >
            <span className="text-xs font-semibold text-zinc-300">{domain}</span>
            <span
                className="flex items-center gap-1.5 text-[10px] font-extrabold px-2 py-0.5 rounded uppercase tracking-wider"
                style={{ color, background: bg, border: `1px solid ${border}` }}
            >
                <Icon size={11} style={{ color }} />
                {state}
            </span>
        </div>
    );
}

function generateNaturalLanguageWhy(decision, driverState, stressVal, issues, perfDir, lapDelta, stressTrend) {
    const parts = [];

    if (stressVal >= 70) {
        parts.push(`High driver stress (${Math.round(stressVal)}/100)`);
    } else if (stressVal >= 50) {
        parts.push(`Elevated driver stress (${Math.round(stressVal)}/100)`);
    }

    if (issues && issues.length > 0) {
        parts.push(`reported vehicle concerns (${issues.join(", ")})`);
    }

    if (perfDir === "SLOWER" && lapDelta !== null && lapDelta !== undefined) {
        parts.push(`deteriorating lap performance (+${Number(lapDelta).toFixed(2)}s vs baseline)`);
    } else if (stressTrend === "RISING") {
        parts.push(`a rising stress trend across recent laps`);
    }

    const decisionTitle = (decision.decision || "NO_ACTION").replace(/_/g, " ");

    if (parts.length === 0) {
        return `Nominal driver state and stable lap telemetry confirmed the ${decisionTitle} status.`;
    }

    if (parts.length === 1) {
        return `${parts[0].charAt(0).toUpperCase() + parts[0].slice(1)} triggered the ${decisionTitle} recommendation.`;
    }

    const last = parts.pop();
    return `${parts.join(", ")} and ${last} together triggered the ${decisionTitle} recommendation.`;
}

export default function WhyDecisionPanel({ analysis, onClose }) {
    if (!analysis) return null;

    const temporal = analysis.temporal_analysis || {};
    const decision = analysis.engineer_decision || {};
    const driver = analysis.driver_analysis || {};
    const stressIndex = analysis.stress_index || {};

    const severity = decision.severity || "CALM";
    const priority = decision.priority || "LOW";
    const decisionName = (decision.decision || "NO_ACTION").replace(/_/g, " ");
    const recText = decision.recommendation || "Maintain current stint plan.";
    const confidence = Math.round((decision.confidence || 0.85) * 100);
    const badge = getSeverityBadge(severity);

    const stressVal = stressIndex.stress_index ?? driver.stress ?? 0;
    const urgencyVal = driver.urgency;
    const driverStateLabel = driver.driver_state || "Calm";
    const issues = driver.issues || [];

    const stressTrend = temporal.stress_trend || temporal.trend || "STABLE";
    const stressHistory = temporal.stress_history || temporal.recent_stress || [];
    const lapTime = temporal.current_lap_time;
    const lapDelta = temporal.lap_time_delta;
    const perfDir = temporal.performance_direction || "STABLE";
    const sustainedStress = temporal.sustained_stress;
    const correlation = temporal.correlation;
    const association = temporal.association || "Building temporal picture…";

    const evidenceDataQuality = decision.evidence?.data_quality || temporal.data_quality || {};

    const acousticSignalAvailable = (stressIndex.stress_signals || {}).speech !== undefined && (stressIndex.stress_signals || {}).speech !== null;

    const dataQualityMap = {
        "Transcript": evidenceDataQuality.transcript || (analysis.transcript ? "AVAILABLE" : "UNAVAILABLE"),
        "Audio Emotion": evidenceDataQuality.audio_emotion || (analysis.audio_emotion?.confidence ? "AVAILABLE" : "UNAVAILABLE"),
        "Acoustic Analysis": evidenceDataQuality.acoustic_analysis || (acousticSignalAvailable ? "AVAILABLE" : "UNAVAILABLE"),
        "Telemetry": evidenceDataQuality.telemetry || (analysis.telemetry?.available ? "AVAILABLE" : "UNAVAILABLE"),
        "Temporal History": evidenceDataQuality.temporal_history || ((temporal.sample_count || 1) >= 2 ? "AVAILABLE" : (temporal.sample_count === 1 ? "PARTIAL" : "UNAVAILABLE")),
        "Correlation": evidenceDataQuality.correlation || ((temporal.sample_count || 0) < 1 ? "UNAVAILABLE" : (temporal.sample_count < 3 ? "INSUFFICIENT" : "AVAILABLE")),
    };

    const naturalWhy = generateNaturalLanguageWhy(decision, driver, stressVal, issues, perfDir, lapDelta, stressTrend);

    return (
        <div
            className="mt-6 p-6 rounded-2xl animate-fade-in-up"
            style={{
                background: "rgba(18, 18, 22, 0.95)",
                border: `1px solid ${badge.color}35`,
                boxShadow: `0 12px 32px rgba(0, 0, 0, 0.5), 0 0 20px ${badge.color}10`,
            }}
        >
            {/* Header bar */}
            <div className="flex items-center justify-between pb-4 mb-6" style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
                <div className="flex items-center gap-2.5">
                    <div className="w-3 h-3 rounded-full" style={{ background: badge.color }} />
                    <h3 className="text-sm font-extrabold uppercase tracking-wider text-white flex items-center gap-2">
                        ENGINEERING DECISION EXPLAINABILITY AUDIT
                    </h3>
                    <ProvenanceBadge type="MODEL" />
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-xs font-bold px-3 py-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
                    >
                        Close Panel ✕
                    </button>
                )}
            </div>

            {/* 1. DECISION SUMMARY */}
            <div className="mb-6 p-4 rounded-xl" style={{ background: `${badge.color}0A`, border: `1px solid ${badge.color}20` }}>
                <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Severity:</span>
                            <span className="text-xs font-black uppercase tracking-wider" style={{ color: badge.color }}>{severity}</span>
                            <span className="text-zinc-600">•</span>
                            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Priority:</span>
                            <span className="text-xs font-extrabold uppercase text-zinc-200">{priority}</span>
                        </div>
                        <h4 className="text-xl font-black text-white uppercase tracking-tight">{decisionName}</h4>
                        <p className="text-xs mt-1.5 font-medium text-zinc-300">{recText}</p>
                    </div>

                    <div className="text-right shrink-0 ml-4">
                        <div className="flex items-center gap-1.5 justify-end">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Engine Confidence</span>
                            <ProvenanceBadge type="MODEL" />
                        </div>
                        <p className="text-2xl font-black tabular-nums mt-0.5" style={{ color: badge.color }}>
                            {confidence}%
                        </p>
                        <p className="text-[9px] text-zinc-500 mt-1 max-w-[150px] leading-tight">
                            Consensus weighted score across active signals. Not probability.
                        </p>
                    </div>
                </div>
            </div>

            {/* 2. KEY EVIDENCE */}
            <div className="mb-6">
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
                    <span>KEY EVIDENCE</span>
                    <span className="text-[9px] font-semibold text-zinc-500 lowercase">(observed values)</span>
                </p>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {/* Driver Stress */}
                    <div className="p-3 rounded-xl glass-card">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Driver Stress</p>
                        <p className="text-lg font-black text-white tabular-nums mt-0.5 flex items-center gap-1">
                            {Math.round(stressVal)}/100
                            {stressTrend === "RISING" && <span className="text-red-400 text-xs">↑</span>}
                            {stressTrend === "FALLING" && <span className="text-emerald-400 text-xs">↓</span>}
                        </p>
                        <div className="mt-1 flex items-center gap-1">
                            <ProvenanceBadge type="MODEL" />
                        </div>
                    </div>

                    {/* Driver State */}
                    <div className="p-3 rounded-xl glass-card">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Driver State</p>
                        <p className="text-sm font-extrabold text-white mt-1">{driverStateLabel}</p>
                        <div className="mt-1.5 flex items-center gap-1">
                            <ProvenanceBadge type="MODEL" />
                        </div>
                    </div>

                    {/* Urgency */}
                    {urgencyVal !== undefined && urgencyVal !== null && (
                        <div className="p-3 rounded-xl glass-card">
                            <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Urgency Level</p>
                            <p className="text-lg font-black text-white tabular-nums mt-0.5">{Math.round(urgencyVal)}/100</p>
                            <div className="mt-1 flex items-center gap-1">
                                <ProvenanceBadge type="MODEL" />
                            </div>
                        </div>
                    )}

                    {/* Vehicle Issues */}
                    <div className="p-3 rounded-xl glass-card">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Transcript Vehicle Issue</p>
                        <p className="text-xs font-bold text-zinc-200 mt-1">
                            {issues && issues.length > 0 ? issues.join(", ") : "None Detected"}
                        </p>
                        <div className="mt-1 flex items-center gap-1">
                            <ProvenanceBadge type="MODEL" />
                        </div>
                    </div>

                    {/* Lap Delta */}
                    {lapTime !== null && lapTime !== undefined && (
                        <div className="p-3 rounded-xl glass-card">
                            <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Lap Delta vs Baseline</p>
                            <p className="text-sm font-black tabular-nums mt-1" style={{ color: perfDir === "SLOWER" ? "#FF453A" : perfDir === "FASTER" ? "#30D158" : "#FFFFFF" }}>
                                {lapDelta !== null && lapDelta !== undefined ? `${lapDelta > 0 ? "+" : ""}${Number(lapDelta).toFixed(3)}s` : "Baseline"}
                            </p>
                            <div className="mt-1 flex items-center gap-1">
                                <ProvenanceBadge type="DATASET" />
                            </div>
                        </div>
                    )}

                    {/* Stress Trend */}
                    <div className="p-3 rounded-xl glass-card">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Stress Trend</p>
                        <p className="text-xs font-black uppercase mt-1" style={{ color: stressTrend === "RISING" ? "#FF453A" : "#30D158" }}>
                            {stressTrend}
                        </p>
                        <div className="mt-1 flex items-center gap-1">
                            <ProvenanceBadge type="MODEL" />
                        </div>
                    </div>

                    {/* Sustained Stress */}
                    <div className="p-3 rounded-xl glass-card">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Sustained Stress</p>
                        <p className="text-xs font-extrabold uppercase mt-1" style={{ color: sustainedStress ? "#FF9F0A" : "#71717A" }}>
                            {sustainedStress ? "DETECTED" : "NOT DETECTED"}
                        </p>
                        <div className="mt-1 flex items-center gap-1">
                            <ProvenanceBadge type="MODEL" />
                        </div>
                    </div>
                </div>
            </div>

            {/* 3. TEMPORAL EVIDENCE */}
            <div className="mb-6">
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
                    <span>TEMPORAL EVIDENCE & PATTERNS</span>
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Stress History Timeline */}
                    <div className="p-4 rounded-xl glass-card">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-2">
                            Stress Trajectory History
                        </p>
                        {stressHistory.length > 0 ? (
                            <div className="flex items-center gap-2 py-1">
                                {stressHistory.map((s, idx) => (
                                    <React.Fragment key={idx}>
                                        {idx > 0 && <ArrowRight size={12} className="text-zinc-600" />}
                                        <span
                                            className="px-2.5 py-1 rounded-lg text-xs font-black tabular-nums"
                                            style={{
                                                background: s >= 70 ? "rgba(255,69,58,0.15)" : s >= 50 ? "rgba(255,159,10,0.15)" : "rgba(48,209,88,0.15)",
                                                color: s >= 70 ? "#FF453A" : s >= 50 ? "#FF9F0A" : "#30D158",
                                                border: `1px solid ${s >= 70 ? "rgba(255,69,58,0.3)" : s >= 50 ? "rgba(255,159,10,0.3)" : "rgba(48,209,88,0.3)"}`,
                                            }}
                                        >
                                            {Math.round(s)}
                                        </span>
                                    </React.Fragment>
                                ))}
                                <span className="ml-2 text-[10px] font-extrabold uppercase px-2 py-0.5 rounded text-zinc-400 bg-zinc-800">
                                    {stressTrend}
                                </span>
                            </div>
                        ) : (
                            <p className="text-xs italic text-zinc-500">Insufficient observation history.</p>
                        )}
                    </div>

                    {/* Correlation & Association */}
                    <div className="p-4 rounded-xl glass-card">
                        <div className="flex items-center justify-between mb-1">
                            <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                                Stress-Pace Correlation
                            </p>
                            <ProvenanceBadge type="MODEL" />
                        </div>
                        {correlation !== null && correlation !== undefined ? (
                            <div>
                                <p className="text-sm font-extrabold text-blue-400 tabular-nums">
                                    r = {correlation > 0 ? "+" : ""}{correlation} ({temporal.correlation_strength || "MODERATE"})
                                </p>
                                <p className="text-[11px] text-zinc-400 mt-1 leading-snug">{association}</p>
                                <p className="text-[9px] text-zinc-500 mt-1.5 italic">
                                    Note: Observed correlation across sample points does not imply direct physical causation.
                                </p>
                            </div>
                        ) : (
                            <p className="text-xs italic text-zinc-500 mt-1">
                                {association}
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* 4. DETERMINISTIC REASONING ("WHY?") */}
            <div className="mb-6 p-4 rounded-xl" style={{ background: "rgba(10, 132, 255, 0.06)", border: "1px solid rgba(10, 132, 255, 0.18)" }}>
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-blue-400 mb-2 flex items-center gap-1.5">
                    <Info size={14} /> DETERMINISTIC DECISION REASONING
                </p>
                <p className="text-sm font-semibold text-zinc-100 leading-relaxed">
                    “{naturalWhy}”
                </p>
                {decision.reasons && decision.reasons.length > 0 && (
                    <div className="mt-3 pt-3 space-y-1" style={{ borderTop: "1px solid rgba(255, 255, 255, 0.06)" }}>
                        <p className="text-[10px] font-extrabold uppercase tracking-wider text-zinc-400 mb-1">Backend Engineering Rules Triggered:</p>
                        {decision.reasons.map((r, idx) => (
                            <p key={idx} className="text-xs text-zinc-300 flex items-center gap-2">
                                <span className="text-blue-400 font-bold">•</span> {r}
                            </p>
                        ))}
                    </div>
                )}
            </div>

            {/* 5. DATA QUALITY / EVIDENCE AVAILABILITY */}
            <div>
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-zinc-400 mb-3">
                    DATA QUALITY & SIGNAL AVAILABILITY AUDIT
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {Object.entries(dataQualityMap).map(([domain, state]) => (
                        <DataQualityBadge key={domain} domain={domain} state={state} />
                    ))}
                </div>
            </div>
        </div>
    );
}
