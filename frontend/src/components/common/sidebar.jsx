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
        case "Emergency": return { color: "#FF453A", label: "Emergency" };
        case "High Stress": return { color: "#FF9F0A", label: "High Stress" };
        case "Concerned": return { color: "#FFD60A", label: "Concerned" };
        default: return { color: "#30D158", label: "Calm" };
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
        return s.title?.toLowerCase().includes(q)
            || s.transcript?.toLowerCase().includes(q)
            || s.analysis?.driver_analysis?.driver_state?.toLowerCase().includes(q);
    });

    const startRename = (session) => {
        setEditingId(session.id);
        setEditTitle(session.title || "");
    };

    const commitRename = () => {
        if (editingId && editTitle.trim()) onRenameSession?.(editingId, editTitle.trim());
        setEditingId(null);
        setEditTitle("");
    };

    const cancelRename = () => {
        setEditingId(null);
        setEditTitle("");
    };

    const navItems = [
        { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
        { id: "ai-models", label: "AI Models", icon: Cpu },
        { id: "pipeline", label: "Pipeline", icon: Network },
        { id: "diagnostics", label: "Diagnostics", icon: Activity },
        { id: "api", label: "API Reference", icon: FileText },
        { id: "settings", label: "Settings", icon: Settings },
    ];

    return (
        <aside className="sidebar-new">
            <div className="sidebar-brand-row">
                <div className="sidebar-brand-mark"><Radio size={20} /></div>
                <div>
                    <div className="sidebar-brand-title">PitSense</div>
                    <div className="sidebar-brand-subtitle">Race Intelligence</div>
                </div>
            </div>

            <div className="sidebar-divider" />

            <div className="sidebar-nav-block">
                <button className="sidebar-new-analysis" onClick={onNewAnalysis}>
                    <Plus size={20} />
                    <span>New Analysis</span>
                </button>

                <div className="sidebar-nav-list">
                    {navItems.map(({ id, label, icon: Icon }) => {
                        const active = activeSection === id;
                        return (
                            <button
                                key={id}
                                onClick={() => onNavigate?.(id)}
                                className={`sidebar-nav-item ${active ? "active" : ""}`}
                            >
                                <Icon size={22} />
                                <span>{label}</span>
                                {id === "dashboard" && active && <span className="nav-accent-dot" />}
                            </button>
                        );
                    })}
                </div>
            </div>

            <button
                className={`sidebar-session-launch ${sessionOpen ? "open" : ""}`}
                onClick={() => setSessionOpen((v) => !v)}
            >
                <div className="sidebar-session-icon"><History size={21} /></div>
                <div className="sidebar-session-copy">
                    <span>Session History</span>
                    <small>{sessions.length} saved analyses</small>
                </div>
                <ChevronRight size={20} className={`sidebar-chevron ${sessionOpen ? "rotate" : ""}`} />
            </button>

            {sessionOpen && (
                <section className="sidebar-sessions-panel">
                    <div className="sidebar-session-panel-head">
                        <span>Recent Sessions</span>
                        <span>{sessions.length}</span>
                    </div>
                    <div className="sidebar-search">
                        <Search size={15} />
                        <input
                            value={searchQuery}
                            onChange={(e) => onSearchChange?.(e.target.value)}
                            placeholder="Search sessions..."
                        />
                        {searchQuery && <button onClick={() => onSearchChange?.("")}><X size={14} /></button>}
                    </div>

                    <div className="sidebar-session-list">
                        {filteredSessions.length ? filteredSessions.map((session) => {
                            const state = getStateConfig(session.analysis?.driver_analysis?.driver_state);
                            const isActive = activeSessionId === session.id;
                            const expanded = expandedSessionId === session.id;
                            const preview = session.transcript
                                ? `${session.transcript.slice(0, 64)}${session.transcript.length > 64 ? "…" : ""}`
                                : "No transcript available";

                            return (
                                <div key={session.id} className={`session-entry ${isActive ? "active" : ""}`}>
                                    <button
                                        className="session-entry-main"
                                        onClick={() => {
                                            onSelectSession?.(session.id);
                                            setExpandedSessionId(expanded ? null : session.id);
                                        }}
                                    >
                                        <div className="session-entry-top">
                                            <MessageSquare size={13} />
                                            <span className="session-entry-title">{session.title}</span>
                                            <ChevronRight size={15} className={expanded ? "rotate" : ""} />
                                        </div>
                                        <p>{preview}</p>
                                        <div className="session-entry-bottom">
                                            <span><Clock size={11} /> {formatTimestamp(session.timestamp)}</span>
                                            <b style={{ color: state.color, background: `${state.color}14` }}>{state.label}</b>
                                        </div>
                                    </button>

                                    {expanded && (
                                        <div className="session-entry-details">
                                            <button onClick={() => onSelectSession?.(session.id)}><MessageSquare size={14} /> Open Session</button>
                                            <button><FileText size={14} /> View Analysis Summary</button>
                                            <div className="session-edit-row">
                                                {editingId === session.id ? (
                                                    <>
                                                        <input
                                                            ref={editRef}
                                                            value={editTitle}
                                                            onChange={(e) => setEditTitle(e.target.value)}
                                                            onKeyDown={(e) => {
                                                                if (e.key === "Enter") commitRename();
                                                                if (e.key === "Escape") cancelRename();
                                                            }}
                                                        />
                                                        <button className="confirm" onClick={commitRename}><Check size={13} /></button>
                                                        <button className="danger" onClick={cancelRename}><X size={13} /></button>
                                                    </>
                                                ) : (
                                                    <>
                                                        <button onClick={() => startRename(session)}><Pencil size={13} /> Rename</button>
                                                        <button className="danger" onClick={() => onDeleteSession?.(session.id)}><Trash2 size={13} /></button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        }) : (
                            <div className="sidebar-empty">{searchQuery ? "No matching sessions" : "No sessions yet"}</div>
                        )}
                    </div>
                </section>
            )}

            <div className="sidebar-spacer" />

            <div className="sidebar-footer">
                <div className="sidebar-status-card">
                    <div className="sidebar-status-dot" />
                    <div>
                        <b>Pipeline Active</b>
                        <span>Local race intelligence</span>
                    </div>
                </div>
                <div className="sidebar-profile">
                    <div className="sidebar-avatar">AD</div>
                    <div>
                        <b>Race Engineer</b>
                        <span>PitSense Control</span>
                    </div>
                    <div className="sidebar-profile-live" />
                </div>
            </div>
        </aside>
    );
}
