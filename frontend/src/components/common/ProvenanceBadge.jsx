import React, { useState } from "react";

const PROVENANCE_CONFIG = {
    DATASET: {
        label: "DATASET",
        color: "#0A84FF",
        bg: "rgba(10, 132, 255, 0.10)",
        border: "rgba(10, 132, 255, 0.22)",
        tooltip: "Value comes from the supplied demonstration dataset.",
    },
    MODEL: {
        label: "MODEL",
        color: "#BF5AF2",
        bg: "rgba(191, 90, 242, 0.10)",
        border: "rgba(191, 90, 242, 0.22)",
        tooltip: "Value is calculated by a PitSense model or intelligence component.",
    },
    SIMULATED: {
        label: "SIMULATED",
        color: "#FF9F0A",
        bg: "rgba(255, 159, 10, 0.10)",
        border: "rgba(255, 159, 10, 0.22)",
        tooltip: "Presentation value used for the current hackathon demonstration. It is not live vehicle telemetry.",
    },
    UNAVAILABLE: {
        label: "UNAVAILABLE",
        color: "#71717A",
        bg: "rgba(113, 113, 122, 0.10)",
        border: "rgba(113, 113, 122, 0.22)",
        tooltip: "No corresponding data is currently available.",
    },
    PARTIAL: {
        label: "PARTIAL",
        color: "#FFD60A",
        bg: "rgba(255, 214, 10, 0.10)",
        border: "rgba(255, 214, 10, 0.22)",
        tooltip: "Some telemetry information is available, but the complete signal is not.",
    },
};

export default function ProvenanceBadge({ type = "MODEL", customTooltip, className = "" }) {
    const [showTooltip, setShowTooltip] = useState(false);
    const key = (type || "MODEL").toUpperCase();
    const config = PROVENANCE_CONFIG[key] || PROVENANCE_CONFIG.MODEL;
    const tooltipText = customTooltip || config.tooltip;

    return (
        <span
            className={`relative inline-flex items-center cursor-help select-none ${className}`}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            onFocus={() => setShowTooltip(true)}
            onBlur={() => setShowTooltip(false)}
            tabIndex={0}
            role="note"
            aria-label={`${config.label} data source provenance: ${tooltipText}`}
        >
            <span
                className="text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase tracking-wider transition-all duration-150"
                style={{
                    color: config.color,
                    background: config.bg,
                    border: `1px solid ${config.border}`,
                    lineHeight: 1,
                }}
            >
                {config.label}
            </span>

            {showTooltip && (
                <span
                    className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium text-zinc-200 pointer-events-none z-50 whitespace-normal max-w-[220px] text-center shadow-xl animate-fade-in"
                    style={{
                        background: "#18181B",
                        border: "1px solid rgba(255, 255, 255, 0.12)",
                        boxShadow: "0 8px 24px rgba(0, 0, 0, 0.5)",
                    }}
                >
                    {tooltipText}
                </span>
            )}
        </span>
    );
}
