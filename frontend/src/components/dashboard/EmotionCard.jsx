import {
    AlertCircle,
    TrendingUp,
    Activity,
    CheckCircle2,
    Brain,
    Smile,
    Frown,
    Meh,
    Zap,
    Heart
} from "lucide-react";

/* ── Progress helpers ── */
function getProgressConfig(value) {
    if (value >= 80) return { color: "#FF453A", label: "Critical" };
    if (value >= 60) return { color: "#FF9F0A", label: "High" };
    if (value >= 40) return { color: "#FFD60A", label: "Moderate" };
    return { color: "#30D158", label: "Low" };
}

function AnimatedProgressBar({ value, delay = 0 }) {
    const cfg = getProgressConfig(value);
    return (
        <div className="relative w-full h-1.5 rounded-full overflow-hidden"
            style={{ background: "rgba(255,255,255,0.05)" }}>
            <div
                className="h-full rounded-full"
                style={{
                    width: `${value}%`,
                    background: cfg.color,
                    boxShadow: `0 0 10px ${cfg.color}40`,
                    transition: `width 1s cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms`
                }}
            />
        </div>
    );
}

/* ── Icon/color maps ── */
function getEmotionIcon(emotion) {
    const map = {
        happy: Smile, sad: Frown, angry: Zap,
        fearful: AlertCircle, neutral: Meh, disgusted: Frown, surprised: Heart,
    };
    return map[emotion?.toLowerCase()] || Meh;
}

function getEmotionColor(emotion) {
    const map = {
        angry: "#FF453A", fearful: "#FF9F0A", sad: "#0A84FF",
        happy: "#30D158", neutral: "#A1A1AA", disgusted: "#FF9F0A", surprised: "#BF5AF2",
    };
    return map[emotion?.toLowerCase()] || "#A1A1AA";
}

function getBadgeConfig(state) {
    switch (state) {
        case "Emergency":
            return { color: "#FF453A", bg: "rgba(255,69,58,0.08)", icon: AlertCircle, label: "Emergency" };
        case "High Stress":
            return { color: "#FF9F0A", bg: "rgba(255,159,10,0.08)", icon: TrendingUp, label: "High Stress" };
        case "Concerned":
            return { color: "#FFD60A", bg: "rgba(255,214,10,0.07)", icon: Activity, label: "Concerned" };
        default:
            return { color: "#30D158", bg: "rgba(48,209,88,0.07)", icon: CheckCircle2, label: "Nominal" };
    }
}

/* ── Metric Row ── */
function MetricRow({ label, metricValue, delay = 0 }) {
    const cfg = getProgressConfig(metricValue);
    return (
        <div className="animate-fade-in-up" style={{ animationDelay: `${delay}ms` }}>
            <div className="flex justify-between items-center mb-2.5">
                <span className="text-[13px] font-medium" style={{ color: "#71717A" }}>{label}</span>
                <div className="flex items-center gap-2.5">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider"
                        style={{ background: cfg.color + "12", color: cfg.color }}>
                        {cfg.label}
                    </span>
                    <span className="text-[13px] font-bold text-white tabular-nums">{metricValue}%</span>
                </div>
            </div>
            <AnimatedProgressBar value={metricValue} delay={delay} />
        </div>
    );
}

/* ── Main Component ── */
export default function EmotionCard({ analysis }) {

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
                        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <Brain size={17} style={{ color: "#52525B" }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">Driver Status</h2>
                        <p className="text-[11px]" style={{ color: "#3F3F46" }}>Awaiting analysis</p>
                    </div>
                </div>
                <p className="text-sm" style={{ color: "#3F3F46" }}>
                    Upload an audio file to see driver emotion and stress metrics.
                </p>
            </div>
        );
    }

    const emotion = analysis.emotion;
    const driver  = analysis.driver_analysis;
    const badge   = getBadgeConfig(driver.driver_state);
    const BadgeIcon = badge.icon;
    const EmotionIcon = getEmotionIcon(emotion.emotion);
    const emotionColor = getEmotionColor(emotion.emotion);

    return (
        <div className="rounded-3xl p-8 animate-scale-pop"
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

            {/* Header + badge */}
            <div className="flex items-start justify-between mb-8">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(10,132,255,0.08)", border: "1px solid rgba(10,132,255,0.15)" }}>
                        <Brain size={17} style={{ color: "#0A84FF" }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">Driver Status</h2>
                        <p className="text-[11px]" style={{ color: "#3F3F46" }}>Real-time analysis</p>
                    </div>
                </div>

                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full"
                    style={{
                        background: badge.bg,
                        border: `1px solid ${badge.color}20`
                    }}
                >
                    <BadgeIcon size={12} style={{ color: badge.color }} />
                    <span className="text-[11px] font-semibold" style={{ color: badge.color }}>
                        {badge.label}
                    </span>
                </div>
            </div>

            {/* Emotion display */}
            <div className="flex items-center gap-4 mb-8 p-5 rounded-2xl"
                style={{
                    background: `${emotionColor}08`,
                    border: `1px solid ${emotionColor}15`
                }}
            >
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0"
                    style={{ background: `${emotionColor}12`, border: `1px solid ${emotionColor}20` }}>
                    <EmotionIcon size={24} style={{ color: emotionColor }} />
                </div>
                <div>
                    <p className="text-[11px] font-medium mb-0.5" style={{ color: "#71717A" }}>Detected Emotion</p>
                    <h3 className="text-2xl font-extrabold capitalize text-white tracking-tight">
                        {emotion.emotion}
                    </h3>
                </div>
                <div className="ml-auto text-right">
                    <p className="text-[11px] mb-0.5" style={{ color: "#71717A" }}>Confidence</p>
                    <p className="text-2xl font-extrabold tabular-nums" style={{ color: emotionColor }}>
                        {emotion.confidence}%
                    </p>
                </div>
            </div>

            {/* Metrics */}
            <div className="space-y-6">
                <MetricRow label="Confidence" metricValue={emotion.confidence} delay={0} />
                <MetricRow label="Stress Level" metricValue={driver.stress} delay={100} />
                <MetricRow label="Urgency" metricValue={driver.urgency} delay={200} />
            </div>

        </div>
    );
}