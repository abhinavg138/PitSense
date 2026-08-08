const SESSIONS_KEY = "pitsense_sessions";
const ACTIVE_KEY = "pitsense_active_session_id";

export function loadSessions() {
    try {
        const data = localStorage.getItem(SESSIONS_KEY);
        const list = data ? JSON.parse(data) : [];
        return list.map(s => ({
            ...s,
            chat: Array.isArray(s.chat) ? s.chat : []
        }));
    } catch {
        return [];
    }
}

export function saveSessions(sessions) {
    try {
        localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
    } catch (e) {
        console.warn("Failed to save sessions:", e);
    }
}


export function loadActiveSessionId() {
    return localStorage.getItem(ACTIVE_KEY) || null;
}

export function saveActiveSessionId(id) {
    if (id) {
        localStorage.setItem(ACTIVE_KEY, id);
    } else {
        localStorage.removeItem(ACTIVE_KEY);
    }
}

export function generateTitle(transcript) {
    if (!transcript) return "New Analysis";
    const clean = transcript.trim().replace(/\s+/g, " ");
    const words = clean.split(" ").slice(0, 6).join(" ");
    if (words.length > 50) return words.substring(0, 47) + "…";
    return words || "New Analysis";
}

export function formatTimestamp(ts) {
    const now = Date.now();
    const diff = now - ts;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days === 1) return "Yesterday";
    if (days < 7) return `${days}d ago`;

    return new Date(ts).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
    });
}
