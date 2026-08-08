import {
    HelpCircle,
    FileText,
    ShieldAlert,
    Target,
    Activity,
    ChevronRight,
    Sparkles
} from "lucide-react";

export const SUGGESTED_QUESTIONS = [
    "Why was the driver classified as Concerned?",
    "What is the biggest risk right now?",
    "Why did you recommend a pit stop?",
    "What does the driver's radio indicate?",
    "Should we continue pushing?",
    "What should the engineer tell the driver?"
];

export const QUICK_ACTIONS = [
    { label: "Explain Analysis", icon: FileText, query: "Explain Analysis overview for this session" },
    { label: "Risk Assessment", icon: ShieldAlert, query: "What is the overall Risk Assessment right now?" },
    { label: "Strategy", icon: Target, query: "What is the recommended race Strategy?" },
    { label: "Driver State", icon: Activity, query: "Explain the Driver State and emotion levels" }
];

export function QuickActionPills({ onSelect, disabled }) {
    return (
        <div className="flex flex-wrap items-center gap-2 mb-3">
            {QUICK_ACTIONS.map((action) => {
                const Icon = action.icon;
                return (
                    <button
                        key={action.label}
                        type="button"
                        disabled={disabled}
                        onClick={() => onSelect(action.query)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 disabled:opacity-40"
                        style={{
                            background: "rgba(255, 255, 255, 0.04)",
                            border: "1px solid rgba(255, 255, 255, 0.08)",
                            color: "#D4D4D8"
                        }}
                        onMouseEnter={e => {
                            if (!disabled) {
                                e.currentTarget.style.background = "rgba(10, 132, 255, 0.12)";
                                e.currentTarget.style.borderColor = "rgba(10, 132, 255, 0.25)";
                                e.currentTarget.style.color = "#0A84FF";
                            }
                        }}
                        onMouseLeave={e => {
                            if (!disabled) {
                                e.currentTarget.style.background = "rgba(255, 255, 255, 0.04)";
                                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
                                e.currentTarget.style.color = "#D4D4D8";
                            }
                        }}
                    >
                        <Icon size={12} className="shrink-0 text-blue-400" />
                        <span>{action.label}</span>
                    </button>
                );
            })}
        </div>
    );
}

export default function SuggestedQuestions({ onSelect, disabled }) {
    return (
        <div className="py-6 px-4 text-center animate-fade-in-up">
            <div className="w-12 h-12 mx-auto rounded-2xl flex items-center justify-center mb-4"
                style={{
                    background: "rgba(10, 132, 255, 0.08)",
                    border: "1px solid rgba(10, 132, 255, 0.15)"
                }}
            >
                <Sparkles size={22} style={{ color: "#0A84FF" }} />
            </div>

            <p className="text-sm font-semibold text-zinc-300 mb-1">
                Ask PitSense anything about this session.
            </p>
            <p className="text-xs text-zinc-500 mb-6 max-w-md mx-auto">
                Select a suggested question below or enter a custom query. Responses rely strictly on live session radio & driver analysis.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto text-left">
                {SUGGESTED_QUESTIONS.map((question) => (
                    <button
                        key={question}
                        type="button"
                        disabled={disabled}
                        onClick={() => onSelect(question)}
                        className="group flex items-center justify-between p-3.5 rounded-2xl text-xs font-medium text-zinc-300 transition-all duration-200 disabled:opacity-40"
                        style={{
                            background: "rgba(255, 255, 255, 0.03)",
                            border: "1px solid rgba(255, 255, 255, 0.06)"
                        }}
                        onMouseEnter={e => {
                            if (!disabled) {
                                e.currentTarget.style.background = "rgba(10, 132, 255, 0.08)";
                                e.currentTarget.style.borderColor = "rgba(10, 132, 255, 0.2)";
                                e.currentTarget.style.transform = "translateY(-1px)";
                            }
                        }}
                        onMouseLeave={e => {
                            if (!disabled) {
                                e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
                                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.06)";
                                e.currentTarget.style.transform = "translateY(0)";
                            }
                        }}
                    >
                        <div className="flex items-center gap-2.5 pr-2">
                            <HelpCircle size={14} className="shrink-0 text-zinc-500 group-hover:text-blue-400 transition-colors" />
                            <span className="leading-snug">{question}</span>
                        </div>
                        <ChevronRight size={14} className="shrink-0 text-zinc-600 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all" />
                    </button>
                ))}
            </div>
        </div>
    );
}
