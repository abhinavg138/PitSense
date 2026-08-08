import { useState, useRef, useEffect } from "react";
import {
    LayoutDashboard,
    History,
    Cpu,
    Activity,
    Zap,
    Radio,
    TrendingUp,
    AlertCircle,
    CheckCircle2,
    Clock,
    Plus,
    Search,
    Pencil,
    Trash2,
    X,
    Check,
    MessageSquare
} from "lucide-react";
import { formatTimestamp } from "../../utils/sessions";

/* ── State → config ── */
function getStateConfig(state) {
    switch (state) {
        case "Emergency":
            return { color: "#FF453A", icon: AlertCircle };
        case "High Stress":
            return { color: "#FF9F0A", icon: TrendingUp };
        case "Concerned":
            return { color: "#FFD60A", icon: Activity };
        default:
            return { color: "#30D158", icon: CheckCircle2 };
    }
}

export default function Sidebar({
    sessions = [],
    activeSessionId,
    searchQuery = "",
    onSearchChange,
    onNewAnalysis,
    onSelectSession,
    onDeleteSession,
    onRenameSession,
}) {
    const [editingId, setEditingId] = useState(null);
    const [editTitle, setEditTitle] = useState("");
    const editRef = useRef(null);

    useEffect(() => {
        if (editingId && editRef.current) {
            editRef.current.focus();
            editRef.current.select();
        }
    }, [editingId]);

    function startRename(session) {
        setEditingId(session.id);
        setEditTitle(session.title);
    }

    function commitRename() {
        if (editingId && editTitle.trim()) {
            onRenameSession?.(editingId, editTitle.trim());
        }
        setEditingId(null);
        setEditTitle("");
    }

    function cancelRename() {
        setEditingId(null);
        setEditTitle("");
    }

    /* Filter sessions by search query */
    const filteredSessions = sessions.filter(s => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
            s.title?.toLowerCase().includes(q) ||
            s.transcript?.toLowerCase().includes(q) ||
            s.analysis?.driver_analysis?.driver_state?.toLowerCase().includes(q)
        );
    });

    return (
        <aside
            className="w-72 shrink-0 flex flex-col min-h-screen"
            style={{
                background: "#0F0F10",
                borderRight: "1px solid rgba(255,255,255,0.05)",
                boxShadow: "2px 0 32px rgba(0,0,0,0.4)"
            }}
        >

            {/* ── Logo ── */}
            <div className="px-5 pt-7 pb-2">
                <div className="flex items-center gap-3">
                    <div
                        className="w-9 h-9 rounded-2xl flex items-center justify-center shrink-0"
                        style={{
                            background: "linear-gradient(135deg, #0A84FF, #5AC8FA)",
                            boxShadow: "0 4px 16px rgba(10,132,255,0.35)"
                        }}
                    >
                        <Radio size={16} className="text-white" />
                    </div>
                    <div>
                        <span className="text-white font-bold text-base tracking-tight">PitSense</span>
                        <p className="text-xs" style={{ color: "#52525B", marginTop: "-1px" }}>Race Intelligence</p>
                    </div>
                </div>
            </div>

            {/* ── New Analysis button ── */}
            <div className="px-4 pt-5 pb-2">
                <button
                    onClick={onNewAnalysis}
                    className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 rounded-2xl text-sm font-semibold transition-all duration-200"
                    style={{
                        background: "rgba(10,132,255,0.12)",
                        border: "1px solid rgba(10,132,255,0.2)",
                        color: "#0A84FF"
                    }}
                    onMouseEnter={e => {
                        e.currentTarget.style.background = "rgba(10,132,255,0.2)";
                        e.currentTarget.style.borderColor = "rgba(10,132,255,0.35)";
                    }}
                    onMouseLeave={e => {
                        e.currentTarget.style.background = "rgba(10,132,255,0.12)";
                        e.currentTarget.style.borderColor = "rgba(10,132,255,0.2)";
                    }}
                >
                    <Plus size={16} strokeWidth={2.5} />
                    New Analysis
                </button>
            </div>

            {/* ── Navigation ── */}
            <nav className="px-3 pt-3 pb-1 space-y-0.5">
                <button className="w-full flex items-center gap-3 px-4 py-2 rounded-xl text-left text-[13px] font-medium transition-all duration-200"
                    style={{
                        background: "rgba(255,255,255,0.06)",
                        color: "#FFFFFF"
                    }}
                >
                    <LayoutDashboard size={15} />
                    <span>Dashboard</span>
                </button>

                <button className="w-full flex items-center gap-3 px-4 py-2 rounded-xl text-left text-[13px] font-medium transition-all duration-200"
                    style={{ color: "#52525B" }}
                    onMouseEnter={e => {
                        e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                        e.currentTarget.style.color = "#A1A1AA";
                    }}
                    onMouseLeave={e => {
                        e.currentTarget.style.background = "transparent";
                        e.currentTarget.style.color = "#52525B";
                    }}
                >
                    <History size={15} />
                    <span>Session History</span>
                </button>

                <button className="w-full flex items-center gap-3 px-4 py-2 rounded-xl text-left text-[13px] font-medium transition-all duration-200"
                    style={{ color: "#52525B" }}
                    onMouseEnter={e => {
                        e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                        e.currentTarget.style.color = "#A1A1AA";
                    }}
                    onMouseLeave={e => {
                        e.currentTarget.style.background = "transparent";
                        e.currentTarget.style.color = "#52525B";
                    }}
                >
                    <Cpu size={15} />
                    <span>AI Models</span>
                </button>
            </nav>

            {/* ── Sessions section ── */}
            <div className="flex-1 flex flex-col min-h-0 mt-4">

                {/* Search */}
                <div className="px-4 pb-3">
                    <div className="flex items-center gap-2 px-3 py-2 rounded-xl"
                        style={{
                            background: "rgba(255,255,255,0.04)",
                            border: "1px solid rgba(255,255,255,0.05)"
                        }}
                    >
                        <Search size={13} style={{ color: "#3F3F46" }} />
                        <input
                            type="text"
                            placeholder="Search sessions…"
                            value={searchQuery}
                            onChange={e => onSearchChange?.(e.target.value)}
                            className="bg-transparent border-none outline-none text-xs text-white placeholder-zinc-600 w-full"
                        />
                        {searchQuery && (
                            <button onClick={() => onSearchChange?.("")}
                                className="shrink-0">
                                <X size={12} style={{ color: "#52525B" }} />
                            </button>
                        )}
                    </div>
                </div>

                {/* Label */}
                <p className="px-6 text-[10px] font-semibold uppercase tracking-[0.15em] mb-2"
                    style={{ color: "#3F3F46" }}>
                    Sessions
                    {sessions.length > 0 && (
                        <span className="ml-2 text-[10px] font-normal" style={{ color: "#27272A" }}>
                            {sessions.length}
                        </span>
                    )}
                </p>

                {/* Session list */}
                <div className="flex-1 overflow-y-auto px-3 space-y-1 pb-3">
                    {filteredSessions.length > 0 ? (
                        filteredSessions.map((session, idx) => {
                            const cfg = getStateConfig(
                                session.analysis?.driver_analysis?.driver_state
                            );
                            const StateIcon = cfg.icon;
                            const isActive = activeSessionId === session.id;
                            const isEditing = editingId === session.id;
                            const preview = session.transcript
                                ? session.transcript.substring(0, 55) + (session.transcript.length > 55 ? "…" : "")
                                : "No transcript";

                            return (
                                <div
                                    key={session.id}
                                    className="group rounded-xl px-3 py-2.5 cursor-pointer transition-all duration-200 animate-slide-in-left"
                                    style={{
                                        animationDelay: `${idx * 30}ms`,
                                        background: isActive
                                            ? "rgba(255,255,255,0.07)"
                                            : "transparent",
                                        borderLeft: isActive
                                            ? "2px solid #0A84FF"
                                            : "2px solid transparent",
                                    }}
                                    onClick={() => !isEditing && onSelectSession?.(session.id)}
                                    onMouseEnter={e => {
                                        if (!isActive) e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                                    }}
                                    onMouseLeave={e => {
                                        if (!isActive) e.currentTarget.style.background = "transparent";
                                    }}
                                >
                                    {/* Title row */}
                                    <div className="flex items-center gap-2 mb-1">
                                        <MessageSquare size={11} style={{ color: isActive ? "#0A84FF" : "#3F3F46" }} className="shrink-0" />

                                        {isEditing ? (
                                            <input
                                                ref={editRef}
                                                type="text"
                                                value={editTitle}
                                                onChange={e => setEditTitle(e.target.value)}
                                                onKeyDown={e => {
                                                    if (e.key === "Enter") commitRename();
                                                    if (e.key === "Escape") cancelRename();
                                                }}
                                                onBlur={commitRename}
                                                onClick={e => e.stopPropagation()}
                                                className="flex-1 bg-transparent border-none outline-none text-xs font-medium text-white min-w-0"
                                                style={{ padding: "0" }}
                                            />
                                        ) : (
                                            <span className="flex-1 text-xs font-medium truncate"
                                                style={{ color: isActive ? "#FFFFFF" : "#A1A1AA" }}>
                                                {session.title}
                                            </span>
                                        )}

                                        {/* Hover actions */}
                                        {!isEditing && (
                                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150 shrink-0">
                                                <button
                                                    onClick={e => { e.stopPropagation(); startRename(session); }}
                                                    className="w-5 h-5 rounded-md flex items-center justify-center transition-colors"
                                                    onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.1)"}
                                                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                                                >
                                                    <Pencil size={10} style={{ color: "#71717A" }} />
                                                </button>
                                                <button
                                                    onClick={e => { e.stopPropagation(); onDeleteSession?.(session.id); }}
                                                    className="w-5 h-5 rounded-md flex items-center justify-center transition-colors"
                                                    onMouseEnter={e => e.currentTarget.style.background = "rgba(255,69,58,0.15)"}
                                                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                                                >
                                                    <Trash2 size={10} style={{ color: "#71717A" }} />
                                                </button>
                                            </div>
                                        )}

                                        {isEditing && (
                                            <div className="flex items-center gap-1 shrink-0">
                                                <button onClick={e => { e.stopPropagation(); commitRename(); }}
                                                    className="w-5 h-5 rounded-md flex items-center justify-center"
                                                    style={{ background: "rgba(48,209,88,0.15)" }}>
                                                    <Check size={10} style={{ color: "#30D158" }} />
                                                </button>
                                                <button onClick={e => { e.stopPropagation(); cancelRename(); }}
                                                    className="w-5 h-5 rounded-md flex items-center justify-center"
                                                    style={{ background: "rgba(255,69,58,0.15)" }}>
                                                    <X size={10} style={{ color: "#FF453A" }} />
                                                </button>
                                            </div>
                                        )}
                                    </div>

                                    {/* Preview */}
                                    <p className="text-[11px] leading-relaxed truncate pl-[19px]"
                                        style={{ color: "#3F3F46" }}>
                                        {preview}
                                    </p>

                                    {/* Bottom row: timestamp + state badge */}
                                    <div className="flex items-center gap-2 mt-1.5 pl-[19px]">
                                        <span className="text-[10px]" style={{ color: "#27272A" }}>
                                            {formatTimestamp(session.timestamp)}
                                        </span>
                                        {session.analysis?.driver_analysis?.driver_state && (
                                            <span className="ml-auto flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                                                style={{
                                                    background: cfg.color + "12",
                                                    color: cfg.color
                                                }}>
                                                <StateIcon size={8} />
                                                {session.analysis.driver_analysis.driver_state}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    ) : (
                        <div className="px-3 py-8 text-center">
                            <Clock size={20} className="mx-auto mb-3" style={{ color: "#27272A" }} />
                            <p className="text-xs" style={{ color: "#3F3F46" }}>
                                {searchQuery ? "No matching sessions" : "No sessions yet"}
                            </p>
                            <p className="text-[10px] mt-1" style={{ color: "#27272A" }}>
                                {searchQuery ? "Try a different search" : "Upload an audio file to begin"}
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* ── AI Pipeline footer ── */}
            <div className="p-3 mt-auto">
                <div className="rounded-2xl p-4"
                    style={{
                        background: "rgba(255,255,255,0.03)",
                        border: "1px solid rgba(255,255,255,0.05)"
                    }}
                >
                    <div className="flex items-center gap-2 mb-2">
                        <Zap size={12} style={{ color: "#0A84FF" }} />
                        <span className="text-[11px] font-semibold text-white">AI Pipeline</span>
                        <span className="ml-auto w-1.5 h-1.5 rounded-full animate-pulse-glow"
                            style={{ background: "#30D158", boxShadow: "0 0 6px #30D158" }} />
                    </div>
                    <p className="text-[10px] leading-relaxed" style={{ color: "#3F3F46" }}>
                        HF Parakeet → Emotion AI → Driver Intelligence → Recommendations
                    </p>
                </div>
            </div>

        </aside>
    );
}