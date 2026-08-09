import { Timer, Gauge, Radio, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import PerformanceGraph from "./PerformanceGraph";
import {
    formatNumber,
    getCurrentTelemetry,
    normalizeTelemetrySeries,
} from "../../utils/telemetry";

function MetricBox({ label, value, unit = "", accent = "#0A84FF" }) {
    const hasValue = value !== null && value !== undefined;

    return (
        <div
            className="flex flex-col gap-1.5 p-4 rounded-2xl"
            style={{
                background: hasValue ? `${accent}08` : "rgba(255,255,255,0.02)",
                border: `1px solid ${hasValue ? accent + "20" : "rgba(255,255,255,0.05)"}`,
            }}
        >
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "#52525B" }}>
                {label}
            </p>
            {hasValue ? (
                <p className="text-xl font-extrabold tracking-tight tabular-nums" style={{ color: accent }}>
                    {value}
                    {unit && <span className="text-sm font-medium ml-1" style={{ color: accent + "99" }}>{unit}</span>}
                </p>
            ) : (
                <p className="text-sm font-medium" style={{ color: "#3F3F46" }}>Unavailable</p>
            )}
        </div>
    );
}

function StatusBadge({ status }) {
    const available = status === "AVAILABLE" || status === "PARTIAL";
    const insufficient = status === "INSUFFICIENT";
    const Icon = available ? CheckCircle2 : insufficient ? AlertCircle : XCircle;
    const color = available ? "#30D158" : insufficient ? "#FFD60A" : "#52525B";

    return (
        <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
            style={{
                background: available ? "rgba(48,209,88,0.07)" : insufficient ? "rgba(255,214,10,0.07)" : "rgba(255,255,255,0.04)",
                border: available ? "1px solid rgba(48,209,88,0.2)" : insufficient ? "1px solid rgba(255,214,10,0.2)" : "1px solid rgba(255,255,255,0.07)",
            }}
        >
            <Icon size={11} style={{ color }} />
            <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>
                {status || "UNAVAILABLE"}
            </span>
        </div>
    );
}

function EmptyTelemetry({ analysis, status }) {
    const title = analysis ? "Telemetry unavailable" : "Awaiting analysis";
    const body = analysis
        ? "This sample did not include matched lap telemetry. Pace values and charts are hidden until real telemetry is available."
        : "Upload or simulate a dataset audio sample to populate pace telemetry.";

    return (
        <div className="rounded-3xl p-8 animate-fade-in-up glass-card">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div
                        className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.06)" }}
                    >
                        <Gauge size={17} style={{ color: "#52525B" }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">Pace Telemetry</h2>
                        <p className="text-[11px]" style={{ color: "#3F3F46" }}>{title}</p>
                    </div>
                </div>
                {analysis && <StatusBadge status={status} />}
            </div>
            <p className="text-sm" style={{ color: "#3F3F46" }}>{body}</p>
        </div>
    );
}

export default function TelemetryCard({ analysis }) {
    const telemetry = getCurrentTelemetry(analysis);
    const series = normalizeTelemetrySeries(analysis);
    const status = series.status || telemetry.status;

    if (!analysis || !telemetry.available) {
        return <EmptyTelemetry analysis={analysis} status={status} />;
    }

    const lapTime = formatNumber(telemetry.lap_time, 3);
    const sector1 = formatNumber(telemetry.sector_1, 3);
    const sector2 = formatNumber(telemetry.sector_2, 3);
    const sector3 = formatNumber(telemetry.sector_3, 3);
    const hasSectors = sector1 !== null || sector2 !== null || sector3 !== null;
    const hasSpeeds = telemetry.i1_speed !== null || telemetry.i2_speed !== null || telemetry.top_speed !== null;

    let radioTimeStr = null;
    if (telemetry.radio_time) {
        try {
            radioTimeStr = new Date(telemetry.radio_time).toISOString().slice(11, 19) + " UTC";
        } catch {
            radioTimeStr = telemetry.radio_time;
        }
    }

    return (
        <div className="rounded-3xl p-8 animate-scale-pop glass-card">
            <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div
                        className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(10,132,255,0.1)", border: "1px solid rgba(10,132,255,0.2)" }}
                    >
                        <Gauge size={17} style={{ color: "#0A84FF" }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">Pace Telemetry</h2>
                        <p className="text-[11px]" style={{ color: "#3F3F46" }}>
                            {telemetry.audio_file || analysis.filename}
                        </p>
                    </div>
                </div>
                <StatusBadge status={status} />
            </div>

            <div
                className="flex items-center justify-between p-6 rounded-2xl mb-6"
                style={{
                    background: "rgba(10,132,255,0.06)",
                    border: "1px solid rgba(10,132,255,0.15)",
                }}
            >
                <div className="flex flex-col gap-1 min-w-[96px]">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em]" style={{ color: "#52525B" }}>
                        Lap
                    </p>
                    <p className="text-5xl font-black tabular-nums tracking-tight" style={{ color: "#0A84FF" }}>
                        {telemetry.lap ?? "N/A"}
                    </p>
                </div>

                <div className="w-px h-14 mx-6" style={{ background: "rgba(10,132,255,0.15)" }} />

                <div className="flex flex-col gap-1 flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <Timer size={13} style={{ color: "#52525B" }} />
                        <p className="text-[10px] font-semibold uppercase tracking-[0.14em]" style={{ color: "#52525B" }}>
                            Lap Time
                        </p>
                    </div>
                    <p className="text-5xl font-black tabular-nums tracking-tight" style={{ color: "#FFFFFF" }}>
                        {lapTime ?? "N/A"}
                        {lapTime && <span className="text-xl font-semibold ml-2" style={{ color: "#52525B" }}>s</span>}
                    </p>
                </div>

                {telemetry.is_pit_out_lap === true && (
                    <div
                        className="px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                        style={{ background: "rgba(255,159,10,0.12)", border: "1px solid rgba(255,159,10,0.25)", color: "#FF9F0A" }}
                    >
                        Pit Out
                    </div>
                )}
            </div>

            <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "#52525B" }}>
                        Pace Trend
                    </p>
                    <p className="text-[11px] tabular-nums" style={{ color: "#52525B" }}>
                        {series.point_count} telemetry point{series.point_count === 1 ? "" : "s"}
                    </p>
                </div>
                <PerformanceGraph series={series} />
            </div>

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

            {hasSpeeds && (
                <div className="mb-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.12em] mb-3" style={{ color: "#52525B" }}>
                        Speed Traps
                    </p>
                    <div className="grid grid-cols-3 gap-3">
                        <MetricBox label="I1 Speed" value={telemetry.i1_speed} unit="km/h" accent="#FF9F0A" />
                        <MetricBox label="I2 Speed" value={telemetry.i2_speed} unit="km/h" accent="#FF9F0A" />
                        <MetricBox label="Top Speed" value={telemetry.top_speed} unit="km/h" accent="#FF9F0A" />
                    </div>
                </div>
            )}

            {radioTimeStr && (
                <div className="flex items-center gap-2 mt-4 pt-4" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                    <Radio size={12} style={{ color: "#52525B" }} />
                    <p className="text-[11px] tabular-nums" style={{ color: "#52525B" }}>
                        Radio transmitted: <span className="text-white font-medium">{radioTimeStr}</span>
                    </p>
                </div>
            )}
        </div>
    );
}
