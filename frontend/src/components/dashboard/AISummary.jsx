import {
    Cpu,
    FileText,
    AlertTriangle,
    CheckCircle2,
    Radio,
    Mic,
    ChevronRight,
    Sparkles,
    Target
} from "lucide-react";

/* ── Reply logic ── */
function getEngineerReply(state) {
    if (state === "Emergency")
        return "Box this lap. We've identified a critical issue. Bring the car back safely.";
    if (state === "High Stress")
        return "Copy. We're reviewing telemetry. Continue for now and report any changes immediately.";
    if (state === "Concerned")
        return "Copy. Continue pushing. We'll monitor the data closely.";
    return "Copy. Car looks good. Continue with current strategy.";
}

function getReplyAccent(state) {
    if (state === "Emergency") return "#FF453A";
    if (state === "High Stress") return "#FF9F0A";
    if (state === "Concerned") return "#FFD60A";
    return "#30D158";
}

/* ── Section card ── */
function Section({ children, className = "" }) {
    return (
        <div
            className={`rounded-3xl p-7 ${className}`}
            style={{
                background: "rgba(255,255,255,0.04)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                border: "1px solid rgba(255,255,255,0.05)",
                boxShadow: "0 2px 16px rgba(0,0,0,0.2)",
                transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)"
            }}
            onMouseEnter={e => {
                e.currentTarget.style.background = "rgba(255,255,255,0.06)";
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = "0 12px 40px rgba(0,0,0,0.3)";
            }}
            onMouseLeave={e => {
                e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 2px 16px rgba(0,0,0,0.2)";
            }}
        >
            {children}
        </div>
    );
}

function SectionHeader({ icon: Icon, label, color }) {
    return (
        <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-2xl flex items-center justify-center"
                style={{ background: `${color}0D`, border: `1px solid ${color}18` }}>
                <Icon size={16} style={{ color }} />
            </div>
            <h3 className="text-[15px] font-bold text-white tracking-tight">{label}</h3>
        </div>
    );
}

/* ── Main Component ── */
export default function AISummary({ analysis }) {

    if (!analysis) {
        return (
            <div className="rounded-3xl p-8 animate-fade-in-up"
                style={{
                    background: "rgba(255,255,255,0.04)",
                    backdropFilter: "blur(24px)",
                    WebkitBackdropFilter: "blur(24px)",
                    border: "1px solid rgba(255,255,255,0.05)",
                    boxShadow: "0 2px 16px rgba(0,0,0,0.2)"
                }}
            >
                <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(10,132,255,0.08)", border: "1px solid rgba(10,132,255,0.15)" }}>
                        <Cpu size={17} style={{ color: "#0A84FF" }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">AI Race Engineer</h2>
                        <p className="text-[11px]" style={{ color: "#3F3F46" }}>Awaiting analysis</p>
                    </div>
                </div>
                <p className="text-sm" style={{ color: "#3F3F46" }}>
                    Upload an audio file to generate AI-powered race engineer recommendations.
                </p>
            </div>
        );
    }

    const driver = analysis.driver_analysis;
    const emotion = analysis.emotion;
    const replyAccent = getReplyAccent(driver.driver_state);

    return (
        <div className="space-y-5 animate-fade-in-up">

            {/* ── Hero header ── */}
            <div className="rounded-3xl p-8 relative overflow-hidden"
                style={{
                    background: "linear-gradient(135deg, rgba(10,132,255,0.1) 0%, rgba(90,200,250,0.05) 100%)",
                    border: "1px solid rgba(10,132,255,0.12)",
                    boxShadow: "0 4px 24px rgba(0,0,0,0.3)"
                }}
            >
                <div className="absolute top-0 right-0 w-72 h-72 rounded-full pointer-events-none"
                    style={{
                        background: "radial-gradient(circle, rgba(10,132,255,0.08) 0%, transparent 65%)",
                        transform: "translate(25%, -35%)"
                    }} />

                <div className="relative flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-3xl flex items-center justify-center"
                            style={{
                                background: "rgba(10,132,255,0.12)",
                                border: "1px solid rgba(10,132,255,0.2)",
                                boxShadow: "0 4px 20px rgba(10,132,255,0.2)"
                            }}
                        >
                            <Cpu size={24} style={{ color: "#0A84FF" }} />
                        </div>
                        <div>
                            <h2 className="text-2xl font-extrabold text-white tracking-tight">
                                AI Race Engineer
                            </h2>
                            <p className="text-[13px] mt-0.5" style={{ color: "#5AC8FA" }}>
                                Automated Driver Communication Analysis
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-2 rounded-full"
                        style={{
                            background: "rgba(48,209,88,0.08)",
                            border: "1px solid rgba(48,209,88,0.15)"
                        }}
                    >
                        <div className="w-1.5 h-1.5 rounded-full animate-pulse"
                            style={{ background: "#30D158" }} />
                        <span className="text-[11px] font-bold" style={{ color: "#30D158" }}>COMPLETE</span>
                    </div>
                </div>
            </div>

            {/* ── Two-column: Summary + Issues ── */}
            <div className="grid grid-cols-2 gap-5">

                {/* Executive Summary */}
                <Section>
                    <SectionHeader icon={FileText} label="Executive Summary" color="#0A84FF" />

                    <div className="space-y-0">
                        {[
                            { label: "Driver State", value: driver.driver_state, color: "#FFFFFF" },
                            { label: "Emotion",      value: emotion.emotion,     color: "#FFFFFF" },
                            { label: "Stress",       value: `${driver.stress}%`, color: "#FF453A" },
                            { label: "Urgency",      value: `${driver.urgency}%`,color: "#FF9F0A" },
                        ].map(({ label, value, color }, idx) => (
                            <div key={label}
                                className="flex items-center justify-between py-3.5"
                                style={{
                                    borderBottom: idx < 3 ? "1px solid rgba(255,255,255,0.04)" : "none"
                                }}>
                                <span className="text-[13px]" style={{ color: "#52525B" }}>{label}</span>
                                <span className="text-[13px] font-bold capitalize" style={{ color }}>{value}</span>
                            </div>
                        ))}
                    </div>
                </Section>

                {/* Detected Issues */}
                <Section>
                    <SectionHeader icon={AlertTriangle} label="Detected Issues" color="#FF453A" />

                    {driver.issues.length ? (
                        <div className="space-y-2.5">
                            {driver.issues.map((issue, idx) => (
                                <div key={idx}
                                    className="flex items-start gap-3 px-4 py-3.5 rounded-2xl"
                                    style={{
                                        background: "rgba(255,69,58,0.05)",
                                        border: "1px solid rgba(255,69,58,0.08)"
                                    }}
                                >
                                    <AlertTriangle size={13} className="mt-0.5 shrink-0"
                                        style={{ color: "#FF453A" }} />
                                    <span className="text-[13px] leading-relaxed" style={{ color: "#D4D4D8" }}>
                                        {issue}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="flex items-center gap-3 px-4 py-3.5 rounded-2xl"
                            style={{
                                background: "rgba(48,209,88,0.05)",
                                border: "1px solid rgba(48,209,88,0.08)"
                            }}
                        >
                            <CheckCircle2 size={13} style={{ color: "#30D158" }} />
                            <span className="text-[13px]" style={{ color: "#52525B" }}>No issues detected</span>
                        </div>
                    )}
                </Section>

            </div>

            {/* ── Strategy Recommendations ── */}
            <Section>
                <SectionHeader icon={Target} label="Strategy Recommendations" color="#30D158" />

                {driver.recommendations.length ? (
                    <div className="space-y-2.5">
                        {driver.recommendations.map((item, idx) => (
                            <div key={idx}
                                className="flex items-start gap-3 px-4 py-3.5 rounded-2xl transition-all duration-200 group cursor-default"
                                style={{
                                    background: "rgba(48,209,88,0.04)",
                                    border: "1px solid rgba(48,209,88,0.07)"
                                }}
                                onMouseEnter={e => {
                                    e.currentTarget.style.background = "rgba(48,209,88,0.07)";
                                    e.currentTarget.style.borderColor = "rgba(48,209,88,0.12)";
                                }}
                                onMouseLeave={e => {
                                    e.currentTarget.style.background = "rgba(48,209,88,0.04)";
                                    e.currentTarget.style.borderColor = "rgba(48,209,88,0.07)";
                                }}
                            >
                                <CheckCircle2 size={13} className="mt-0.5 shrink-0"
                                    style={{ color: "#30D158" }} />
                                <span className="text-[13px] leading-relaxed" style={{ color: "#D4D4D8" }}>
                                    {item}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-[13px]" style={{ color: "#3F3F46" }}>No recommendations available.</p>
                )}
            </Section>

            {/* ── Suggested Engineer Reply ── */}
            <Section>
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-9 h-9 rounded-2xl flex items-center justify-center"
                        style={{ background: `${replyAccent}0D`, border: `1px solid ${replyAccent}18` }}>
                        <Radio size={16} style={{ color: replyAccent }} />
                    </div>
                    <h3 className="text-[15px] font-bold text-white tracking-tight">Suggested Engineer Reply</h3>
                    <div className="ml-auto flex items-center gap-1.5 px-3 py-1 rounded-full"
                        style={{
                            background: `${replyAccent}08`,
                            border: `1px solid ${replyAccent}12`
                        }}>
                        <Mic size={10} style={{ color: replyAccent }} className="animate-pulse-glow" />
                        <span className="text-[10px] font-semibold uppercase tracking-wider"
                            style={{ color: replyAccent }}>
                            Radio
                        </span>
                    </div>
                </div>

                <div className="px-6 py-5 rounded-2xl"
                    style={{
                        background: `${replyAccent}06`,
                        border: `1px solid ${replyAccent}10`
                    }}
                >
                    <p className="text-[15px] italic leading-8 font-medium text-white">
                        "{getEngineerReply(driver.driver_state)}"
                    </p>
                </div>
            </Section>

        </div>
    );
}