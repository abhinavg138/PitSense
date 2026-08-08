import { Cpu, User, Radio } from "lucide-react";

function formatTime(timestamp) {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function ChatMessage({ message }) {
    const isUser = message.sender === "user";
    const timeStr = formatTime(message.timestamp);

    if (isUser) {
        return (
            <div className="flex justify-end mb-4 animate-fade-in-up">
                <div className="max-w-[80%] flex items-end gap-2">
                    <div className="flex flex-col items-end">
                        <div
                            className="rounded-2xl rounded-tr-xs px-5 py-3.5 text-sm text-white font-normal shadow-sm leading-relaxed"
                            style={{
                                background: "rgba(10, 132, 255, 0.18)",
                                border: "1px solid rgba(10, 132, 255, 0.3)",
                                backdropFilter: "blur(12px)",
                                WebkitBackdropFilter: "blur(12px)",
                                boxShadow: "0 4px 20px rgba(10, 132, 255, 0.15)"
                            }}
                        >
                            {message.text}
                        </div>
                        {timeStr && (
                            <span className="text-[10px] mt-1 pr-1 font-medium" style={{ color: "#52525B" }}>
                                {timeStr}
                            </span>
                        )}
                    </div>
                    <div
                        className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mb-4"
                        style={{
                            background: "rgba(10, 132, 255, 0.2)",
                            border: "1px solid rgba(10, 132, 255, 0.3)"
                        }}
                    >
                        <User size={13} style={{ color: "#0A84FF" }} />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex justify-start mb-5 animate-fade-in-up">
            <div className="max-w-[85%] flex items-start gap-3">
                <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-0.5"
                    style={{
                        background: "rgba(10, 132, 255, 0.12)",
                        border: "1px solid rgba(10, 132, 255, 0.22)",
                        boxShadow: "0 2px 10px rgba(10, 132, 255, 0.2)"
                    }}
                >
                    <Cpu size={15} style={{ color: "#0A84FF" }} />
                </div>

                <div className="flex flex-col">
                    <div
                        className="rounded-2xl rounded-tl-xs p-5 transition-all duration-200"
                        style={{
                            background: "rgba(255, 255, 255, 0.035)",
                            backdropFilter: "blur(20px)",
                            WebkitBackdropFilter: "blur(20px)",
                            border: "1px solid rgba(255, 255, 255, 0.07)",
                            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.2)"
                        }}
                    >
                        {/* Header badge inside bubble */}
                        <div className="flex items-center gap-2 mb-2.5 pb-2" style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
                            <Radio size={11} style={{ color: "#0A84FF" }} />
                            <span className="text-[11px] font-bold tracking-wider uppercase" style={{ color: "#0A84FF" }}>
                                PitSense Engineer
                            </span>
                            <span className="ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full"
                                style={{
                                    background: "rgba(48, 209, 88, 0.08)",
                                    color: "#30D158",
                                    border: "1px solid rgba(48, 209, 88, 0.15)"
                                }}
                            >
                                TELEMETRY VERIFIED
                            </span>
                        </div>

                        {/* Message text */}
                        <p className="text-[14px] leading-relaxed text-zinc-200 whitespace-pre-wrap font-normal">
                            {message.text}
                        </p>
                    </div>

                    {timeStr && (
                        <span className="text-[10px] mt-1 pl-1 font-medium" style={{ color: "#52525B" }}>
                            {timeStr}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
