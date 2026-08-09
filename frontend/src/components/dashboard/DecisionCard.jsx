import { Activity, AlertTriangle, ShieldCheck, TrendingUp, Cpu, CheckCircle2, ArrowRight } from "lucide-react";

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
    if (!analysis) return null;

    const temporal = analysis.temporal_analysis || {};
    const decision = analysis.engineer_decision || {};

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
                className="p-6 rounded-2xl mb-6"
                style={{ background: `${badge.color}08`, border: `1px solid ${badge.color}20` }}
            >
                <div className="flex items-start justify-between">
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.14em] mb-1" style={{ color: "#71717A" }}>
                            Recommended Engineer Decision
                        </p>
                        <h3 className="text-2xl font-black uppercase tracking-tight" style={{ color: badge.color }}>
                            {decisionName}
                        </h3>
                        <p className="text-sm mt-2 font-medium text-zinc-200">
                            {recText}
                        </p>
                    </div>
                    <div className="text-right shrink-0 ml-4">
                        <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "#71717A" }}>Engine Confidence</p>
                        <p className="text-2xl font-extrabold tabular-nums" style={{ color: badge.color }}>
                            {Math.round((decision.confidence || 0.85) * 100)}%
                        </p>
                    </div>
                </div>

                {/* Decision Reasons (WHY?) */}
                {reasons.length > 0 && (
                    <div className="mt-4 pt-4 space-y-1.5" style={{ borderTop: `1px solid ${badge.color}15` }}>
                        <p className="text-[11px] font-extrabold uppercase tracking-wider text-zinc-300">
                            WHY? (Backend Deterministic Reasons)
                        </p>
                        {reasons.map((r, i) => (
                            <p key={i} className="text-xs flex items-center gap-2 text-zinc-300">
                                <span style={{ color: badge.color }}>•</span> {r}
                            </p>
                        ))}
                    </div>
                )}
            </div>

            {/* Temporal Metrics Grid */}
            <div className="grid grid-cols-3 gap-4">

                {/* Card A: Stress Trend */}
                <div className="p-4 rounded-2xl" style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                    <p className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "#71717A" }}>
                        Stress Trend
                    </p>
                    {sampleCount >= 2 && stressHistory.length > 0 ? (
                        <div>
                            <div className="flex items-center gap-1 text-xs font-semibold tabular-nums mb-2 text-zinc-300">
                                {stressHistory.map((s, idx) => (
                                    <span key={idx} className="flex items-center gap-1">
                                        {idx > 0 && <ArrowRight size={10} style={{ color: "#52525B" }} />}
                                        <span style={{ color: s >= 70 ? "#FF453A" : s >= 50 ? "#FF9F0A" : "#30D158" }}>
                                            {s}
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
                    <p className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "#71717A" }}>
                        Lap Time vs Baseline
                    </p>
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
                    <p className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "#71717A" }}>
                        Observed Association
                    </p>
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

            {/* Observational statement footer */}
            <p className="text-[11px] italic mt-4 pt-3 text-zinc-400" style={{ borderTop: "1px solid rgba(255, 255, 255, 0.04)" }}>
                {association}
            </p>
        </div>
    );
}
