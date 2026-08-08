import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { QuickActionPills } from "./SuggestedQuestions";

export default function EngineerInput({ onSend, loading, disabled }) {
    const [text, setText] = useState("");
    const textareaRef = useRef(null);

    // Auto-adjust textarea height dynamically
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        }
    }, [text]);

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
        }
    };

    const submit = () => {
        if (!text.trim() || loading || disabled) return;
        onSend(text.trim());
        setText("");
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
    };

    const handleQuickActionSelect = (query) => {
        if (loading || disabled) return;
        onSend(query);
    };

    const isSendDisabled = !text.trim() || loading || disabled;

    return (
        <div className="pt-2">
            {/* Quick action pills above input */}
            <QuickActionPills onSelect={handleQuickActionSelect} disabled={loading || disabled} />

            {/* Input Bar Card */}
            <div
                className="relative flex items-end gap-3 p-2.5 rounded-2xl transition-all duration-200"
                style={{
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    backdropFilter: "blur(20px)",
                    WebkitBackdropFilter: "blur(20px)"
                }}
            >
                <textarea
                    ref={textareaRef}
                    rows={1}
                    value={text}
                    disabled={loading || disabled}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about this session..."
                    className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder-zinc-500 resize-none py-1.5 px-3 min-h-[38px] max-h-[120px] leading-relaxed"
                />

                <button
                    type="button"
                    disabled={isSendDisabled}
                    onClick={submit}
                    className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white transition-all duration-200 shrink-0 disabled:opacity-30 disabled:cursor-not-allowed"
                    style={{
                        background: isSendDisabled ? "rgba(255, 255, 255, 0.08)" : "#0A84FF",
                        boxShadow: isSendDisabled ? "none" : "0 4px 16px rgba(10, 132, 255, 0.35)"
                    }}
                    onMouseEnter={e => {
                        if (!isSendDisabled) {
                            e.currentTarget.style.background = "#1A8DFF";
                        }
                    }}
                    onMouseLeave={e => {
                        if (!isSendDisabled) {
                            e.currentTarget.style.background = "#0A84FF";
                        }
                    }}
                >
                    {loading ? (
                        <>
                            <Loader2 size={14} className="animate-spin text-white" />
                            <span>Analysing...</span>
                        </>
                    ) : (
                        <>
                            <span>Send</span>
                            <Send size={13} />
                        </>
                    )}
                </button>
            </div>
            <p className="text-[10px] text-zinc-600 mt-2 text-right font-medium">
                Press Enter to send • Shift + Enter for newline
            </p>
        </div>
    );
}
