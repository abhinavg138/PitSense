import { FileText, Mic } from "lucide-react";

export default function TranscriptCard({ analysis }) {

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
                        <FileText size={17} style={{ color: "#52525B" }} />
                    </div>
                    <h2 className="text-lg font-bold text-white tracking-tight">Transcript</h2>
                </div>
                <p className="text-sm" style={{ color: "#3F3F46" }}>
                    Waiting for uploaded race radio…
                </p>
            </div>
        );
    }

    return (
        <div className="rounded-3xl p-8 transition-all duration-300 animate-scale-pop"
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

            {/* Header */}
            <div className="flex items-center gap-3 mb-8">
                <div className="w-10 h-10 rounded-2xl flex items-center justify-center"
                    style={{ background: "rgba(10,132,255,0.08)", border: "1px solid rgba(10,132,255,0.15)" }}>
                    <FileText size={17} style={{ color: "#0A84FF" }} />
                </div>
                <div>
                    <h2 className="text-lg font-bold text-white tracking-tight">Transcript</h2>
                    <p className="text-[11px] mt-0.5" style={{ color: "#3F3F46" }}>NVIDIA Parakeet TDT 0.6B v3</p>
                </div>
                <div className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-full"
                    style={{
                        background: "rgba(48,209,88,0.06)",
                        border: "1px solid rgba(48,209,88,0.1)"
                    }}>
                    <Mic size={10} style={{ color: "#30D158" }} />
                    <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "#30D158" }}>
                        Transcribed
                    </span>
                </div>
            </div>

            {/* Transcript body — Notion-style clean reading experience */}
            <div className="rounded-2xl p-6"
                style={{
                    background: "rgba(255,255,255,0.025)",
                    border: "1px solid rgba(255,255,255,0.04)"
                }}
            >
                <p className="text-[15px] leading-8 whitespace-pre-wrap"
                    style={{
                        color: "#D4D4D8",
                        fontFamily: "'Inter', -apple-system, sans-serif"
                    }}>
                    {analysis.transcript}
                </p>
            </div>

        </div>
    );
}