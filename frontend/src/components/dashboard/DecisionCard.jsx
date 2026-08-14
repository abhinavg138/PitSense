import { useState } from "react";
import { Activity, AlertTriangle, ShieldCheck, TrendingUp, Cpu, CheckCircle2, ArrowRight, HelpCircle, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import WhyDecisionPanel from "./WhyDecisionPanel";
import ProvenanceBadge from "../common/ProvenanceBadge";

/* ── Severity Helpers ── */
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

export default function DecisionCard({ analysis }) {
    const [showWhyPanel, setShowWhyPanel] = useState(false);

    if (!analysis) return null;

    const temporal = analysis.temporal_analysis || {};
    const decision = analysis.engineer_decision || {};
    const dataQuality = (decision.evidence && decision.evidence.data_quality) || (temporal.data_quality) || {};

    const sampleCount = temporal.sample_count || temporal.observation_count || 1;
    const badge = getSeverityBadge(decision.severity || "CALM");
    const reasons = decision.reasons || [];
    const recText = decision.recommendation || "Maintain current stint plan.";
    const decisionName = (decision.decision || "NO_ACTION").replace(/_/g, " ");

    const stressTrend = temporal.stress_trend || temporal.trend || "STABLE";
    const stressHistory = temporal.stress_history || temporal.recent_stress || [];
    const lapTime = temporal.current_lap_time;
    const lapDelta = temporal.lap_time_delta;
    const perfDir = temporal.performance_direction || "STABLE";
    const correlation = temporal.correlation;
    const corrStrength = temporal.correlation_strength;
    const association = temporal.association || "Building temporal picture…";

    return (
        <div
            className="rounded-3xl p-8 animate-fade-in-up"
            style={{
                background: "rgba(255, 255, 255, 0.035)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                boxShadow: "0 4px 24px rgba(0, 0, 0, 0.3)",
            }}
        >
            {/* Header */}
            <div className="flex items-center justify-between pb-6 mb-6" style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
                <div className="flex items-center gap-3">
                    <div
                        className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: `${badge.color}15`, border: `1px solid ${badge.color}30` }}
                    >
                        <Cpu size={18} style={{ color: badge.color }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                            Engineer Decision Support Engine
                            <ProvenanceBadge type="MODEL" />
                        </h2>
                        <p className="text-[11px]" style={{ color: "#71717A" }}>
                            Phase 8 — Authoritative Deterministic Race Engineering
                        </p>
                    </div>
                </div>

                <div
                    className="flex items-center gap-2 px-3.5 py-1.5 rounded-full"
                    style={{ background: badge.bg, border: `1px solid ${badge.border}` }}
                >
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: badge.color }} />
                    <span className="text-[11px] font-extrabold uppercase tracking-wider" style={{ color: badge.color }}>
                        {badge.label}
                    </span>
                </div>
            </div>

            {/* Decision Hero Block */}
            <div
                className="p-6 rounded-2xl mb-6 relative overflow-hidden"
                style={{ background: `${badge.color}08`, border: `1px solid ${badge.color}20` }}
            >
                <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <p className="text-[10px] font-bold uppercase tracking-[0.14em]" style={{ color: "#71717A" }}>
                                Recommended Engineer Decision
                            </p>
                            <ProvenanceBadge type="MODEL" />
                        </div>
                        <h3 className="text-2xl font-black uppercase tracking-tight" style={{ color: badge.color }}>
                            {decisionName}
                        </h3>
                        <p className="text-sm mt-2 font-medium text-zinc-200">
                            {recText}
                        </p>
                    </div>
                    <div className="text-right shrink-0 ml-4">
                        <div className="flex items-center justify-end gap-1.5 mb-1">
                            <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "#71717A" }}>Engine Confidence</p>
                            <ProvenanceBadge type="MODEL" />
                        </div>
                        <p className="text-2xl font-extrabold tabular-nums" style={{ color: badge.color }}>
                            {Math.round((decision.confidence || 0.85) * 100)}%
                        </p>
                    </div>
                </div>

                {/* PROMINENT "WHY THIS DECISION?" BUTTON */}
                <div className="mt-5 pt-4 flex items-center justify-between" style={{ borderTop: `1px solid ${badge.color}18` }}>
                    <button
                        type="button"
                        onClick={() => setShowWhyPanel(!showWhyPanel)}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200"
                        style={{
                            background: showWhyPanel ? badge.color : `${badge.color}20`,
                            color: showWhyPanel ? "#000000" : "#FFFFFF",
                            border: `1px solid ${badge.color}40`,
                            boxShadow: showWhyPanel ? `0 0 16px ${badge.color}40` : "none",
                        }}
                    >
                        <HelpCircle size={15} />
                        WHY THIS DECISION?
                        {showWhyPanel ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                    </button>

                    <span className="text-[11px] font-medium text-zinc-400 flex items-center gap-1.5">
                        <Sparkles size={12} className="text-blue-400" />
                        Deterministic Rule-Based Evidence
                    </span>
                </div>
            </div>

            {/* Expandable Why This Decision Panel */}
            {showWhyPanel && (
                <WhyDecisionPanel
                    analysis={analysis}
                    onClose={() => setShowWhyPanel(false)}
                />
            )}

            {/* Temporal Metrics Grid */}
            <div className="grid grid-cols-3 gap-4 mt-6">

                {/* Card A: Stress Trend */}
                <div className="p-4 rounded-2xl" style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "#71717A" }}>
                            Stress Trend
                        </p>
                        <ProvenanceBadge type="MODEL" />
                    </div>
                    {sampleCount >= 2 && stressHistory.length > 0 ? (
                        <div>
                            <div className="flex items-center gap-1 text-xs font-semibold tabular-nums mb-2 text-zinc-300">
                                {stressHistory.map((s, idx) => (
                                    <span key={idx} className="flex items-center gap-1">
                                        {idx > 0 && <ArrowRight size={10} style={{ color: "#52525B" }} />}
                                        <span style={{ color: s >= 70 ? "#FF453A" : s >= 50 ? "#FF9F0A" : "#30D158" }}>
                                            {Math.round(s)}
                                        </span>
                                    </span>
                                ))}
                            </div>
                            <span
                                className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full"
                                style={{
                                    background: stressTrend === "RISING" ? "rgba(255,69,58,0.15)" : "rgba(48,209,88,0.15)",
                                    color: stressTrend === "RISING" ? "#FF453A" : "#30D158",
                                }}
                            >
                                {stressTrend}
                            </span>
                        </div>
                    ) : (
                        <p className="text-xs font-medium italic" style={{ color: "#52525B" }}>Building temporal picture…</p>
                    )}
                </div>

                {/* Card B: Lap Time Delta */}
                <div className="p-4 rounded-2xl" style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "#71717A" }}>
                            Lap Time vs Baseline
                        </p>
                        <ProvenanceBadge type={lapTime !== null && lapTime !== undefined ? "DATASET" : "UNAVAILABLE"} />
                    </div>
                    {lapTime !== null && lapTime !== undefined ? (
                        <div>
                            <p className="text-base font-extrabold text-white tabular-nums">
                                {Number(lapTime).toFixed(3)} s
                            </p>
                            <p className="text-xs font-semibold mt-1" style={{ color: perfDir === "SLOWER" ? "#FF453A" : perfDir === "FASTER" ? "#30D158" : "#A1A1AA" }}>
                                {lapDelta !== null && lapDelta !== undefined ? `${lapDelta > 0 ? "+" : ""}${Number(lapDelta).toFixed(3)}s` : "Baseline"} ({perfDir})
                            </p>
                        </div>
                    ) : (
                        <p className="text-xs font-medium italic" style={{ color: "#52525B" }}>Building temporal picture…</p>
                    )}
                </div>

                {/* Card C: Observed Association */}
                <div className="p-4 rounded-2xl" style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "#71717A" }}>
                            Observed Association
                        </p>
                        <ProvenanceBadge type={correlation !== null && correlation !== undefined ? "MODEL" : "UNAVAILABLE"} />
                    </div>
                    {correlation !== null && correlation !== undefined ? (
                        <div>
                            <p className="text-base font-extrabold tabular-nums" style={{ color: "#0A84FF" }}>
                                r = {correlation > 0 ? "+" : ""}{correlation}
                            </p>
                            <p className="text-[10px] font-bold uppercase tracking-wider mt-1 text-zinc-400">
                                {corrStrength || "MODERATE"} CORRELATION
                            </p>
                        </div>
                    ) : (
                        <p className="text-xs font-medium italic" style={{ color: "#52525B" }}>
                            {sampleCount < 3 ? `Need 3+ samples (${sampleCount}/3)` : "Building temporal picture…"}
                        </p>
                    )}
                </div>

            </div>

            {/* Domain Data Quality Badges */}
            <div className="mt-4 pt-3 flex items-center justify-between" style={{ borderTop: "1px solid rgba(255, 255, 255, 0.04)" }}>
                <p className="text-[11px] italic text-zinc-400">
                    {association}
                </p>
                <div className="flex items-center gap-2 shrink-0">
                    {Object.entries({
                        Transcript: dataQuality.transcript || "AVAILABLE",
                        Emotion: dataQuality.audio_emotion || "AVAILABLE",
                        Telemetry: dataQuality.telemetry || (analysis.telemetry?.available ? "AVAILABLE" : "UNAVAILABLE"),
                        Correlation: dataQuality.correlation || (sampleCount < 3 ? "INSUFFICIENT" : "AVAILABLE")
                    }).map(([domain, state]) => {
                        const style = state === "AVAILABLE" ? { color: "#30D158", bg: "rgba(48, 209, 88, 0.12)" }
                            : state === "PARTIAL" ? { color: "#FF9F0A", bg: "rgba(255, 159, 10, 0.12)" }
                            : state === "INSUFFICIENT" ? { color: "#FFD60A", bg: "rgba(255, 214, 10, 0.12)" }
                            : { color: "#71717A", bg: "rgba(113, 113, 122, 0.12)" };
                        return (
                            <span key={domain} className="text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-wider" style={{ color: style.color, background: style.bg }}>
                                {domain}: {state}
                            </span>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
