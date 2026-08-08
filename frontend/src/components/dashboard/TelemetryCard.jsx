import { Timer, Gauge, Zap, Radio, CheckCircle2, XCircle } from "lucide-react";

/* ── Helpers ── */
function fmt(val, decimals = 3) {
    if (val === null || val === undefined) return null;
    return typeof val === "number" ? val.toFixed(decimals) : val;
}

function MetricBox({ label, value, unit = "", accent = "#0A84FF", wide = false }) {
    const hasValue = value !== null && value !== undefined;
    return (
        <div
            className={`flex flex-col gap-1.5 p-4 rounded-2xl${wide ? " col-span-2" : ""}`}
            style={{
                background: hasValue ? `${accent}08` : "rgba(255,255,255,0.02)",
                border: `1px solid ${hasValue ? accent + "20" : "rgba(255,255,255,0.05)"}`,
            }}
        >
            <p
                className="text-[10px] font-semibold uppercase tracking-[0.12em]"
                style={{ color: "#52525B" }}
            >
                {label}
            </p>
            {hasValue ? (
                <p className="text-xl font-extrabold tracking-tight tabular-nums" style={{ color: accent }}>
                    {value}
                    {unit && (
                        <span className="text-sm font-medium ml-1" style={{ color: accent + "99" }}>
                            {unit}
                        </span>
                    )}
                </p>
            ) : (
                <p className="text-sm font-medium" style={{ color: "#3F3F46" }}>
                    N/A
                </p>
            )}
        </div>
    );
}

/* ── Main Component ── */
export default function TelemetryCard({ analysis }) {
    const telemetry = analysis?.telemetry;
    const available = telemetry?.available === true;

    /* ── Empty / unavailable state ── */
    if (!analysis) {
        return (
            <div
                className="rounded-3xl p-8 animate-fade-in-up"
                style={{
                    background: "rgba(255,255,255,0.03)",
                    backdropFilter: "blur(24px)",
                    WebkitBackdropFilter: "blur(24px)",
                    border: "1px solid rgba(255,255,255,0.05)",
                    boxShadow: "0 2px 16px rgba(0,0,0,0.2)",
                }}
            >
                <div className="flex items-center gap-3 mb-4">
                    <div
                        className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.06)" }}
                    >
                        <Gauge size={17} style={{ color: "#52525B" }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">Race Telemetry</h2>
                        <p className="text-[11px]" style={{ color: "#3F3F46" }}>Awaiting analysis</p>
                    </div>
                </div>
                <p className="text-sm" style={{ color: "#3F3F46" }}>
                    Upload a dataset audio file to see lap telemetry.
                </p>
            </div>
        );
    }

    /* ── No dataset match ── */
    if (!available) {
        return (
            <div
                className="rounded-3xl p-8 animate-scale-pop"
                style={{
                    background: "rgba(255,255,255,0.03)",
                    backdropFilter: "blur(24px)",
                    WebkitBackdropFilter: "blur(24px)",
                    border: "1px solid rgba(255,255,255,0.05)",
                    boxShadow: "0 2px 16px rgba(0,0,0,0.2)",
                }}
            >
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div
                            className="w-10 h-10 rounded-2xl flex items-center justify-center"
                            style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.06)" }}
                        >
                            <Gauge size={17} style={{ color: "#52525B" }} />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-white tracking-tight">Race Telemetry</h2>
                            <p className="text-[11px]" style={{ color: "#3F3F46" }}>No dataset match</p>
                        </div>
                    </div>
                    <div
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
                        style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
                    >
                        <XCircle size={11} style={{ color: "#52525B" }} />
                        <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "#52525B" }}>
                            Telemetry Unavailable
                        </span>
                    </div>
                </div>
                <p className="text-sm" style={{ color: "#3F3F46" }}>
                    This audio file was not found in the dataset. Telemetry is only available for matched lap recordings.
                </p>
            </div>
        );
    }

    /* ── Dataset match — full card ── */
    const lap      = telemetry.lap;
    const lapTime  = fmt(telemetry.lap_time, 3);
    const sector1  = fmt(telemetry.sector_1, 3);
    const sector2  = fmt(telemetry.sector_2, 3);
    const sector3  = fmt(telemetry.sector_3, 3);
    const i1Speed  = telemetry.i1_speed;
    const i2Speed  = telemetry.i2_speed;
    const topSpeed = telemetry.top_speed;
    const isPitOut = telemetry.is_pit_out_lap;

    // Format radio_time as HH:MM:SS UTC
    let radioTimeStr = null;
    if (telemetry.radio_time) {
        try {
            const d = new Date(telemetry.radio_time);
            radioTimeStr = d.toISOString().slice(11, 19) + " UTC";
        } catch {
            radioTimeStr = telemetry.radio_time;
        }
    }

    const hasSectors  = sector1 !== null || sector2 !== null || sector3 !== null;
    const hasSpeeds   = i1Speed !== null || i2Speed !== null || topSpeed !== null;

    return (
        <div
            className="rounded-3xl p-8 animate-scale-pop"
            style={{
                background: "rgba(255,255,255,0.04)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                border: "1px solid rgba(255,255,255,0.06)",
                boxShadow: "0 2px 16px rgba(0,0,0,0.2)",
                transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
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
            {/* ── Header ── */}
            <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div
                        className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(10,132,255,0.1)", border: "1px solid rgba(10,132,255,0.2)" }}
                    >
                        <Gauge size={17} style={{ color: "#0A84FF" }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">Race Telemetry</h2>
                        <p className="text-[11px]" style={{ color: "#3F3F46" }}>
                            {telemetry.audio_file}
                        </p>
                    </div>
                </div>

                {/* Available badge */}
                <div
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
                    style={{ background: "rgba(48,209,88,0.07)", border: "1px solid rgba(48,209,88,0.2)" }}
                >
                    <CheckCircle2 size={11} style={{ color: "#30D158" }} />
                    <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "#30D158" }}>
                        Telemetry Available
                    </span>
                </div>
            </div>

            {/* ── Primary hero: Lap + Lap Time ── */}
            <div
                className="flex items-center justify-between p-6 rounded-2xl mb-6"
                style={{
                    background: "rgba(10,132,255,0.06)",
                    border: "1px solid rgba(10,132,255,0.15)",
                }}
            >
                {/* Lap number */}
                <div className="flex flex-col gap-1">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em]" style={{ color: "#52525B" }}>
                        Lap
                    </p>
                    <p className="text-5xl font-black tabular-nums tracking-tight" style={{ color: "#0A84FF" }}>
                        {lap ?? "—"}
                    </p>
                </div>

                {/* Divider */}
                <div className="w-px h-14 mx-6" style={{ background: "rgba(10,132,255,0.15)" }} />

                {/* Lap time (primary value) */}
                <div className="flex flex-col gap-1 flex-1">
                    <div className="flex items-center gap-2">
                        <Timer size={13} style={{ color: "#52525B" }} />
                        <p className="text-[10px] font-semibold uppercase tracking-[0.14em]" style={{ color: "#52525B" }}>
                            Lap Time
                        </p>
                    </div>
                    <p className="text-5xl font-black tabular-nums tracking-tight" style={{ color: "#FFFFFF" }}>
                        {lapTime ?? "—"}
                        <span className="text-xl font-semibold ml-2" style={{ color: "#52525B" }}>s</span>
                    </p>
                </div>

                {/* Pit out badge (if applicable) */}
                {isPitOut === true && (
                    <div
                        className="px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                        style={{ background: "rgba(255,159,10,0.12)", border: "1px solid rgba(255,159,10,0.25)", color: "#FF9F0A" }}
                    >
                        Pit Out
                    </div>
                )}
            </div>

            {/* ── Sectors ── */}
            {hasSectors && (
                <div className="mb-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.12em] mb-3" style={{ color: "#52525B" }}>
                        Sector Times
                    </p>
                    <div className="grid grid-cols-3 gap-3">
                        <MetricBox label="Sector 1" value={sector1} unit="s" accent="#BF5AF2" />
                        <MetricBox label="Sector 2" value={sector2} unit="s" accent="#BF5AF2" />
                        <MetricBox label="Sector 3" value={sector3} unit="s" accent="#BF5AF2" />
                    </div>
                </div>
            )}

            {/* ── Speeds ── */}
            {hasSpeeds && (
                <div className="mb-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.12em] mb-3" style={{ color: "#52525B" }}>
                        Speed Traps
                    </p>
                    <div className="grid grid-cols-3 gap-3">
                        <MetricBox label="I1 Speed"  value={i1Speed}  unit="km/h" accent="#FF9F0A" />
                        <MetricBox label="I2 Speed"  value={i2Speed}  unit="km/h" accent="#FF9F0A" />
                        <MetricBox label="Top Speed" value={topSpeed} unit="km/h" accent="#FF9F0A" />
                    </div>
                </div>
            )}

            {/* ── Radio time footer ── */}
            {radioTimeStr && (
                <div
                    className="flex items-center gap-2 mt-4 pt-4"
                    style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
                >
                    <Radio size={12} style={{ color: "#52525B" }} />
                    <p className="text-[11px] tabular-nums" style={{ color: "#52525B" }}>
                        Radio transmitted: <span className="text-white font-medium">{radioTimeStr}</span>
                    </p>
                </div>
            )}
        </div>
    );
}
