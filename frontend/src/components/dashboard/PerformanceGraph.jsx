import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Filler,
    Tooltip,
    Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { Gauge } from "lucide-react";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

function EmptyGraph({ status, pointCount }) {
    const message = pointCount > 0
        ? "Need at least two telemetry samples to draw a trend."
        : "No lap telemetry points available for this sample.";

    return (
        <div
            className="h-64 rounded-2xl flex flex-col items-center justify-center gap-3"
            style={{
                background: "rgba(255,255,255,0.025)",
                border: "1px solid rgba(255,255,255,0.06)",
            }}
        >
            <Gauge size={22} style={{ color: "#52525B" }} />
            <div className="text-center">
                <p className="text-xs font-semibold uppercase tracking-[0.12em]" style={{ color: "#71717A" }}>
                    {status || "UNAVAILABLE"}
                </p>
                <p className="text-sm mt-1" style={{ color: "#3F3F46" }}>
                    {message}
                </p>
            </div>
        </div>
    );
}

export default function PerformanceGraph({ series }) {
    const points = series?.usablePoints || [];
    const pointCount = points.length;

    if (pointCount < 2) {
        return <EmptyGraph status={series?.status} pointCount={pointCount} />;
    }

    const labels = points.map((point) => (
        point.lap !== null && point.lap !== undefined ? `L${point.lap}` : `S${point.index}`
    ));

    const chartData = {
        labels,
        datasets: [
            {
                label: "Lap time",
                data: points.map(point => point.lap_time),
                borderColor: "#0A84FF",
                backgroundColor: "rgba(10,132,255,0.14)",
                pointBackgroundColor: "#0A84FF",
                pointBorderColor: "#09090B",
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                tension: 0.35,
                yAxisID: "y",
                fill: true,
            },
            {
                label: "Stress",
                data: points.map(point => point.stress),
                borderColor: "#FF9F0A",
                backgroundColor: "rgba(255,159,10,0.08)",
                pointBackgroundColor: "#FF9F0A",
                pointBorderColor: "#09090B",
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                tension: 0.35,
                yAxisID: "y1",
                fill: false,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: "index",
            intersect: false,
        },
        plugins: {
            legend: {
                position: "top",
                align: "end",
                labels: {
                    color: "#A1A1AA",
                    boxWidth: 10,
                    boxHeight: 10,
                    usePointStyle: true,
                    font: { size: 11, weight: 600 },
                },
            },
            tooltip: {
                backgroundColor: "rgba(9,9,11,0.95)",
                titleColor: "#FFFFFF",
                bodyColor: "#D4D4D8",
                borderColor: "rgba(255,255,255,0.12)",
                borderWidth: 1,
                callbacks: {
                    label(context) {
                        const suffix = context.dataset.yAxisID === "y" ? " s" : "%";
                        return `${context.dataset.label}: ${context.parsed.y}${suffix}`;
                    },
                },
            },
        },
        scales: {
            x: {
                grid: { color: "rgba(255,255,255,0.04)" },
                ticks: { color: "#71717A", font: { size: 11 } },
            },
            y: {
                type: "linear",
                position: "left",
                grid: { color: "rgba(10,132,255,0.08)" },
                ticks: {
                    color: "#0A84FF",
                    font: { size: 11 },
                    callback: value => `${Number(value).toFixed(1)}s`,
                },
                title: {
                    display: true,
                    text: "Lap time",
                    color: "#0A84FF",
                    font: { size: 11, weight: 700 },
                },
            },
            y1: {
                type: "linear",
                position: "right",
                min: 0,
                max: 100,
                grid: { drawOnChartArea: false },
                ticks: {
                    color: "#FF9F0A",
                    font: { size: 11 },
                    callback: value => `${value}%`,
                },
                title: {
                    display: true,
                    text: "Stress",
                    color: "#FF9F0A",
                    font: { size: 11, weight: 700 },
                },
            },
        },
    };

    return (
        <div className="h-72">
            <Line data={chartData} options={options} />
        </div>
    );
}
