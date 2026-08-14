import { useMemo } from "react";
import { MessageSquare, Play, Radio, Send, Sparkles } from "lucide-react";
import ProvenanceBadge from "../common/ProvenanceBadge";

export default function RadioCommandCard({ analysis }) {
    const transcript = analysis?.transcript || analysis?.engineer_reply || "Awaiting driver radio communication.";
    const emotion = analysis?.emotion?.emotion || "Nominal";
    const stress = Math.round(analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress ?? 0);
    const urgency = Math.round(analysis?.driver_analysis?.urgency ?? 0);
    const confidence = analysis?.engineer_decision?.confidence !== undefined ? Math.round(analysis.engineer_decision.confidence * 100) : Math.round(analysis?.stress_index?.confidence ?? 91);

    const interpretation = useMemo(() => {
        if (analysis?.ai_summary) return String(analysis.ai_summary).replace(/\s+/g, " ").slice(0, 180);
        if (stress >= 70) return "Driver communication indicates elevated pressure. Stress is high, so the next response should prioritize composure and clear instructions.";
        return "Driver communication appears stable. Continue monitoring tone, stress and urgency across the next radio exchange.";
    }, [analysis, stress]);

    const suggestedResponse = stress >= 70
        ? "Copy. Stay focused. Give me two clean laps and we'll reassess the balance."
        : "Copy. Keep the pace consistent and report any change in balance.";

    return (
        <div className="radio-command-card glass-card">
            <div className="radio-command-head">
                <div className="section-head">
                    <span>RADIO COMMAND</span>
                    <b>● LIVE</b>
                </div>
                <span className="radio-command-live"><Radio size={12} /> LIVE</span>
            </div>
            <div className="radio-command-wave-row">
                <button type="button" className="radio-play" aria-label="Play latest radio"><Play size={16} fill="currentColor" /></button>
                <div className="radio-command-wave">{Array.from({ length: 44 }).map((_, i) => <i key={i} style={{ height: `${8 + ((i * 17) % 24)}px` }} />)}</div>
                <span className="radio-duration">0:12</span>
            </div>
            <div className="radio-command-transcript">“{String(transcript).replace(/\s+/g, " ").slice(0, 155)}”</div>
            <div className="radio-command-label flex items-center justify-between">
                <span className="flex items-center gap-1.5"><Sparkles size={13} /> AI INTERPRETATION</span>
                <ProvenanceBadge type="MODEL" />
            </div>
            <div className="radio-command-interpretation">{interpretation}</div>
            <div className="radio-command-signals">
                <span><MessageSquare size={12} /> Emotion <b>{emotion}</b></span>
                <span><i className="sig-dot stress" /> Stress <b>{stress}%</b></span>
                <span><i className="sig-dot urgency" /> Urgency <b>{urgency}%</b></span>
                <span><i className="sig-dot confidence" /> Confidence <b>{confidence}%</b></span>
            </div>
            <div className="radio-command-label flex items-center justify-between">
                <span>SUGGESTED ENGINEER RESPONSE</span>
                <ProvenanceBadge type="MODEL" />
            </div>
            <div className="radio-response-row">
                <div className="radio-response-copy">{suggestedResponse}</div>
                <button type="button" className="radio-send"><Send size={14} /> Send Response</button>
            </div>
        </div>
    );
}
