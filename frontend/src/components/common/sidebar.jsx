import { useState, useRef, useEffect } from "react";
import {
    LayoutDashboard,
    History,
    Cpu,
    Network,
    Activity,
    Settings,
    Plus,
    Search,
    Pencil,
    Trash2,
    X,
    Check,
    ChevronRight,
    MessageSquare,
    FileText,
    Clock,
    Radio,
} from "lucide-react";
import { formatTimestamp } from "../../utils/sessions";

function getStateConfig(state) {
    switch (state) {
        case "Emergency":
            return { color: "#FF453A", label: "Emergency" };
        case "High Stress":
            return { color: "#FF9F0A", label: "High Stress" };
        case "Concerned":
            return { color: "#FFD60A", label: "Concerned" };
        default:
            return { color: "#30D158", label: "Calm" };
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
    activeSection = "dashboard",
    onNavigate,
}) {
    const [sessionOpen, setSessionOpen] = useState(false);
    const [expandedSessionId, setExpandedSessionId] = useState(null);
    const [editingId, setEditingId] = useState(null);
    const [editTitle, setEditTitle] = useState("");
    const editRef = useRef(null);

    useEffect(() => {
        if (editingId && editRef.current) {
            editRef.current.focus();
            editRef.current.select();
        }
    }, [editingId]);

    const filteredSessions = sessions.filter((s) => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
            s.title?.toLowerCase().includes(q) ||
            s.transcript?.toLowerCase().includes(q) ||
            s.analysis?.driver_analysis?.driver_state?.toLowerCase().includes(q)
        );
    });

    function startRename(session) {
        setEditingId(session.id);
        setEditTitle(session.title || "");
    }

    function commitRename() {
        if (editingId && editTitle.trim()) onRenameSession?.(editingId, editTitle.trim());
        setEditingId(null);
        setEditTitle("");
    }

    function cancelRename() {
        setEditingId(null);
        setEditTitle("");
    }

    const navItems = [
        { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
        { id: "ai-models", label: "AI Models", icon: Cpu },
        { id: "pipeline", label: "Pipeline", icon: Network },
        { id: "diagnostics", label: "Diagnostics", icon: Activity },
        { id: "api", label: "API Reference", icon: FileText },
        { id: "settings", label: "Settings", icon: Settings },
    ];

    return (
        <aside className="w-[292px] shrink-0 min-h-screen flex flex-col border-r border-white/[0.06] bg-[#080a0d] shadow-[12px_0_40px_rgba(0,0,0,0.28)]">
            <div className="px-5 pt-6 pb-5 border-b border-white/[0.05]">
                <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-2xl flex items-center justify-center bg-gradient-to-br from-[#ff382d] to-[#a91813] shadow-[0_8px_24px_rgba(255,56,45,0.28)]">
                        <Radio size={18} className="text-white" />
                    </div>
                    <div>
                        <div className="text-[17px] font-bold tracking-tight text-white">PitSense</div>
                        <div className="text-[11px] text-zinc-500">Race Intelligence</div>
                    </div>
                </div>
            </div>

            <div className="px-4 py-4">
                <button
                    onClick={onNewAnalysis}
                    className="w-full h-12 rounded-2xl flex items-center justify-center gap-2.5 text-[15px] font-semibold text-white transition-all"
                    style={{
                        background: "linear-gradient(135deg, rgba(255,69,58,.15), rgba(105,15,12,.18))",
                        border: "1px solid rgba(255,69,58,.42)",
                        boxShadow: "inset 0 0 30px rgba(255,69,58,.05), 0 10px 24px rgba(0,0,0,.2)",
                    }}
                >
                    <Plus size={19} />
                    New Analysis
                </button>
            </div>

            <nav className="px-4 space-y-2">
                <button
                    onClick={() => onNavigate?.("dashboard")}
                    className={`w-full h-12 rounded-2xl px-4 flex items-center gap-3 text-left text-[15px] font-semibold transition-all ${activeSection === "dashboard" ? "text-white" : "text-zinc-400 hover:text-white"}`}
                    style={activeSection === "dashboard" ? {
                        background: "linear-gradient(90deg, rgba(255,69,58,.22), rgba(80,15,18,.16))",
                        border: "1px solid rgba(255,69,58,.35)",
                        boxShadow: "inset 3px 0 0 #ff453a, 0 8px 24px rgba(255,69,58,.08)"
                    } : { border: "1px solid rgba(255,255,255,.04)" }}
                >
                    <LayoutDashboard size={20} />
                    Dashboard
                </button>

                <button
                    onClick={() => setSessionOpen((v) => !v)}
                    className={`w-full h-12 rounded-2xl px-4 flex items-center gap-3 text-left text-[15px] font-semibold transition-all ${sessionOpen ? "text-white" : "text-zinc-400 hover:text-white"}`}
                    style={sessionOpen ? {
                        background: "rgba(255,255,255,.055)",
                        border: "1px solid rgba(255,255,255,.10)"
                    } : { border: "1px solid rgba(255,255,255,.04)" }}
                >
                    <History size={20} />
                    <span className="flex-1">Session History</span>
                    <span className="text-[11px] text-zinc-500">{sessions.length}</span>
                    <ChevronRight size={18} className={`transition-transform ${sessionOpen ? "rotate-90" : ""}`} />
                </button>

                {navItems.filter((item) => item.id !== "dashboard").map(({ id, label, icon: Icon }) => (
                    <button
                        key={id}
                        onClick={() => onNavigate?.(id)}
                        className={`w-full h-12 rounded-2xl px-4 flex items-center gap-3 text-left text-[15px] font-semibold transition-all ${activeSection === id ? "text-white" : "text-zinc-400 hover:text-white"}`}
                        style={activeSection === id ? {
                            background: "rgba(255,255,255,.055)",
                            border: "1px solid rgba(255,255,255,.10)"
                        } : { border: "1px solid rgba(255,255,255,.04)" }}
                    >
                        <Icon size={20} />
                        {label}
                    </button>
                ))}
            </nav>

            {sessionOpen && (
                <div className="mt-5 px-4 pb-4 flex-1 min-h-0 flex flex-col animate-slide-in-left">
                    <div className="flex items-center justify-between mb-3 px-1">
                        <div className="text-[11px] uppercase tracking-[0.16em] text-zinc-500 font-semibold">Session History</div>
                        <div className="text-[11px] text-zinc-600">{sessions.length}</div>
                    </div>

                    <div className="flex items-center gap-2 px-3 h-10 rounded-xl bg-white/[0.035] border border-white/[0.06] mb-3">
                        <Search size={14} className="text-zinc-600" />
                        <input
                            value={searchQuery}
                            onChange={(e) => onSearchChange?.(e.target.value)}
                            placeholder="Search sessions..."
                            className="w-full bg-transparent outline-none text-[12px] text-white placeholder:text-zinc-600"
                        />
                        {searchQuery && <button onClick={() => onSearchChange?.("")}><X size={13} className="text-zinc-600" /></button>}
                    </div>

                    <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                        {filteredSessions.length ? filteredSessions.map((session) => {
                            const state = getStateConfig(session.analysis?.driver_analysis?.driver_state);
                            const isActive = activeSessionId === session.id;
                            const expanded = expandedSessionId === session.id;
                            const preview = session.transcript
                                ? `${session.transcript.slice(0, 68)}${session.transcript.length > 68 ? "…" : ""}`
                                : "No transcript available";

                            return (
                                <div key={session.id} className="rounded-2xl border border-white/[0.05] bg-white/[0.02] overflow-hidden">
                                    <button
                                        onClick={() => {
                                            onSelectSession?.(session.id);
                                            setExpandedSessionId(expanded ? null : session.id);
                                        }}
                                        className="w-full text-left px-3.5 py-3 transition-all"
                                        style={isActive ? { background: "rgba(255,255,255,.055)", borderLeft: "2px solid #0A84FF" } : {}}
                                    >
                                        <div className="flex items-center gap-2">
                                            <MessageSquare size={12} className={isActive ? "text-blue-400" : "text-zinc-600"} />
                                            <span className={`flex-1 truncate text-[12px] font-semibold ${isActive ? "text-white" : "text-zinc-300"}`}>{session.title}</span>
                                            <ChevronRight size={14} className={`text-zinc-600 transition-transform ${expanded ? "rotate-90" : ""}`} />
                                        </div>
                                        <div className="mt-1.5 pl-5 text-[10px] text-zinc-600 truncate">{preview}</div>
                                        <div className="mt-2 pl-5 flex items-center gap-2">
                                            <Clock size={10} className="text-zinc-700" />
                                            <span className="text-[10px] text-zinc-600">{formatTimestamp(session.timestamp)}</span>
                                            <span className="ml-auto px-1.5 py-0.5 rounded-full text-[9px] font-semibold" style={{ color: state.color, background: `${state.color}12` }}>{state.label}</span>
                                        </div>
                                    </button>

                                    {expanded && (
                                        <div className="px-3.5 pb-3.5 border-t border-white/[0.05] bg-black/10">
                                            <button onClick={() => onSelectSession?.(session.id)} className="w-full mt-2.5 h-9 rounded-xl bg-white/[0.04] hover:bg-white/[0.07] text-[11px] text-zinc-300 flex items-center gap-2 px-3">
                                                <MessageSquare size={13} />
                                                Open Session
                                            </button>
                                            <button className="w-full mt-2 h-9 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] text-[11px] text-zinc-400 flex items-center gap-2 px-3">
                                                <FileText size={13} />
                                                View Analysis Summary
                                            </button>
                                            <div className="flex items-center gap-2 mt-2">
                                                {editingId === session.id ? (
                                                    <>
                                                        <input
                                                            ref={editRef}
                                                            value={editTitle}
                                                            onChange={(e) => setEditTitle(e.target.value)}
                                                            onKeyDown={(e) => { if (e.key === "Enter") commitRename(); if (e.key === "Escape") cancelRename(); }}
                                                            className="flex-1 h-8 rounded-lg bg-white/[0.04] border border-white/[0.08] px-2 text-[11px] text-white outline-none"
                                                        />
                                                        <button onClick={commitRename} className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center"><Check size={13} /></button>
                                                        <button onClick={cancelRename} className="w-8 h-8 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center"><X size={13} /></button>
                                                    </>
                                                ) : (
                                                    <>
                                                        <button onClick={() => startRename(session)} className="flex-1 h-8 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] text-[11px] text-zinc-500 flex items-center justify-center gap-1.5"><Pencil size={12} /> Rename</button>
                                                        <button onClick={() => onDeleteSession?.(session.id)} className="w-9 h-8 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center"><Trash2 size={13} /></button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        }) : (
                            <div className="py-10 text-center text-[11px] text-zinc-600">{searchQuery ? "No matching sessions" : "No sessions yet"}</div>
                        )}
                    </div>
                </div>
            )}

            {!sessionOpen && <div className="flex-1" />}

            <div className="p-4 border-t border-white/[0.05]">
                <div className="rounded-2xl border border-white/[0.06] bg-white/[0.025] px-3.5 py-3 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-zinc-700/80 flex items-center justify-center text-sm font-semibold text-white">AD</div>
                    <div className="min-w-0">
                        <div className="text-[13px] font-semibold text-white truncate">Race Engineer</div>
                        <div className="text-[10px] text-zinc-500">PitSense Control</div>
                    </div>
                    <div className="ml-auto w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,.65)]" />
                </div>
            </div>
        </aside>
    );
}
