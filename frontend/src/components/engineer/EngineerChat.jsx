import { useState, useRef, useEffect } from "react";
import { Cpu, Radio, Sparkles, MessageSquare, AlertCircle } from "lucide-react";
import ChatMessage from "./ChatMessage";
import SuggestedQuestions from "./SuggestedQuestions";
import EngineerInput from "./EngineerInput";
import { askRaceEngineer } from "../../utils/engineerAI";

export default function EngineerChat({ session, onUpdateChat }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const messagesEndRef = useRef(null);

    const chatMessages = session?.chat || [];
    const hasMessages = chatMessages.length > 0;

    // Auto-scroll to bottom of chat when new messages arrive
    useEffect(() => {
        if (hasMessages) {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [chatMessages, loading]);

    const handleSendMessage = async (text) => {
        if (!text || loading) return;
        setError(null);

        const userMsg = {
            id: Date.now().toString(),
            sender: "user",
            text: text,
            timestamp: Date.now()
        };

        const updatedMessagesWithUser = [...chatMessages, userMsg];
        onUpdateChat?.(updatedMessagesWithUser);

        setLoading(true);

        try {
            const reply = await askRaceEngineer(session, text);

            const engineerMsg = {
                id: (Date.now() + 1).toString(),
                sender: "engineer",
                text: reply.text,
                aiSource: reply.aiSource,
                timestamp: Date.now()
            };

            onUpdateChat?.([...updatedMessagesWithUser, engineerMsg]);
        } catch (err) {
            console.error("Failed to generate engineer response:", err);
            setError("Unable to process query at this time. Please try again.");

            const fallbackMsg = {
                id: (Date.now() + 1).toString(),
                sender: "engineer",
                text: "That information is not available in the current session.",
                aiSource: "local",
                timestamp: Date.now()
            };
            onUpdateChat?.([...updatedMessagesWithUser, fallbackMsg]);
        } finally {
            setLoading(false);
        }
    };

    if (!session || !session.analysis) {
        return (
            <div
                className="rounded-3xl p-8 animate-fade-in-up"
                style={{
                    background: "rgba(255, 255, 255, 0.04)",
                    backdropFilter: "blur(24px)",
                    WebkitBackdropFilter: "blur(24px)",
                    border: "1px solid rgba(255, 255, 255, 0.05)",
                    boxShadow: "0 2px 16px rgba(0,0,0,0.2)"
                }}
            >
                <div className="flex items-center gap-3 mb-4">
                    <div
                        className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(10, 132, 255, 0.08)", border: "1px solid rgba(10, 132, 255, 0.15)" }}
                    >
                        <Radio size={18} style={{ color: "#0A84FF" }} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">Ask the Race Engineer</h2>
                        <p className="text-[11px]" style={{ color: "#52525B" }}>Ask questions about this race session.</p>
                    </div>
                </div>
                <p className="text-sm" style={{ color: "#3F3F46" }}>
                    Upload or record driver radio communications above to activate the AI Race Engineer Chat.
                </p>
            </div>
        );
    }

    return (
        <div
            className="rounded-3xl p-8 space-y-6 animate-fade-in-up transition-all duration-300"
            style={{
                background: "rgba(255, 255, 255, 0.035)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                boxShadow: "0 4px 32px rgba(0, 0, 0, 0.3)"
            }}
        >
            {/* Header section */}
            <div className="flex items-center justify-between pb-6" style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
                <div className="flex items-center gap-4">
                    <div
                        className="w-12 h-12 rounded-2xl flex items-center justify-center"
                        style={{
                            background: "rgba(10, 132, 255, 0.12)",
                            border: "1px solid rgba(10, 132, 255, 0.25)",
                            boxShadow: "0 4px 16px rgba(10, 132, 255, 0.2)"
                        }}
                    >
                        <Radio size={22} style={{ color: "#0A84FF" }} />
                    </div>
                    <div>
                        <h2 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
                            Ask the Race Engineer
                        </h2>
                        <p className="text-xs mt-0.5" style={{ color: "#71717A" }}>
                            Ask questions about this race session.
                        </p>
                    </div>
                </div>

                {/* Status Indicator */}
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full"
                    style={{
                        background: loading ? "rgba(10, 132, 255, 0.08)" : "rgba(48, 209, 88, 0.08)",
                        border: `1px solid ${loading ? "rgba(10, 132, 255, 0.2)" : "rgba(48, 209, 88, 0.2)"}`
                    }}
                >
                    <div
                        className={`w-2 h-2 rounded-full ${loading ? "animate-ping" : "animate-pulse"}`}
                        style={{
                            background: loading ? "#0A84FF" : "#30D158",
                            boxShadow: loading ? "0 0 8px #0A84FF" : "0 0 8px #30D158"
                        }}
                    />
                    <span
                        className="text-[11px] font-bold uppercase tracking-wider"
                        style={{ color: loading ? "#0A84FF" : "#30D158" }}
                    >
                        {loading ? "◌ Analysing session..." : hasMessages ? "● Analysis Ready" : "● Race Engineer Online"}
                    </span>
                </div>
            </div>

            {/* Error Notification Banner if any */}
            {error && (
                <div className="flex items-center gap-2 px-4 py-3 rounded-2xl"
                    style={{ background: "rgba(255, 69, 58, 0.1)", border: "1px solid rgba(255, 69, 58, 0.2)" }}>
                    <AlertCircle size={14} style={{ color: "#FF453A" }} />
                    <span className="text-xs text-red-400 font-medium">{error}</span>
                </div>
            )}

            {/* Chat Body Container */}
            <div className="min-h-[220px] max-h-[480px] overflow-y-auto px-2 py-2">
                {!hasMessages ? (
                    <SuggestedQuestions onSelect={handleSendMessage} disabled={loading} />
                ) : (
                    <div className="space-y-2">
                        {chatMessages.map((msg) => (
                            <ChatMessage key={msg.id} message={msg} />
                        ))}
                        {loading && (
                            <div className="flex justify-start mb-4 animate-fade-in-up">
                                <div className="flex items-center gap-3 px-4 py-3 rounded-2xl"
                                    style={{
                                        background: "rgba(255, 255, 255, 0.03)",
                                        border: "1px solid rgba(255, 255, 255, 0.06)"
                                    }}>
                                    <div className="w-2 h-2 rounded-full animate-ping" style={{ background: "#0A84FF" }} />
                                    <span className="text-xs text-zinc-400 font-medium">Engineer calculating response...</span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Input Bar */}
            <div className="pt-2" style={{ borderTop: "1px solid rgba(255, 255, 255, 0.05)" }}>
                <EngineerInput onSend={handleSendMessage} loading={loading} disabled={!session} />
            </div>
        </div>
    );
}
