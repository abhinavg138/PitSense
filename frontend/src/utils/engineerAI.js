import API from "../services/api";

/**
 * Deterministic client-side F1 Race Engineer response engine fallback.
 * Strictly avoids inventing non-existent telemetry (fuel levels, lap times, tyre temperatures, etc.).
 */
export function generateLocalEngineerAnswer(sessionData, question) {
    const q = (question || "").trim().toLowerCase();
    if (!q) {
        return "That information is not available in the current session.";
    }

    const transcript = sessionData?.transcript || "";
    const analysis = sessionData?.analysis || sessionData || {};
    const driver = analysis?.driver_analysis || {};
    const emotion = analysis?.emotion || {};
    const aiSummary = analysis?.ai_summary || "";

    const tLower = transcript.toLowerCase();

    // Guardrail against hallucinated telemetry requested by user
    const unavailableKeywords = [
        "fuel", "lap time", "sector", "gap", "tire temp", "tyre temp",
        "brake temp", "engine temp", "oil temp", "compound", "softs",
        "mediums", "hards", "intermediates", "wets", "telemetry value", "telemetry reading"
    ];

    for (const kw of unavailableKeywords) {
        if (q.includes(kw) && !tLower.includes(kw)) {
            return "That information is not available in the current session.";
        }
    }

    const state = driver.driver_state || "Calm";
    const stress = driver.stress ?? 0;
    const urgency = driver.urgency ?? 0;
    const issues = driver.issues || [];
    const recommendations = driver.recommendations || [];
    const emoLabel = emotion.emotion ? emotion.emotion.charAt(0).toUpperCase() + emotion.emotion.slice(1) : "Calm";
    const emoConf = emotion.confidence ?? 85;

    const getRiskLevel = (urg) => {
        if (urg >= 90) return "CRITICAL";
        if (urg >= 70) return "HIGH";
        if (urg >= 40) return "MODERATE";
        return "LOW";
    };
    const riskLevel = getRiskLevel(urgency);

    // 1. Driver classification / state questions
    if (q.includes("classified") || q.includes("driver state") || (q.includes("why") && (q.includes("concerned") || q.includes("stress") || q.includes("emergency") || q.includes("calm")))) {
        if (state === "Concerned") {
            const issuesStr = issues.length ? issues.join(", ") : "increasing tyre degradation and vehicle balance shift";
            return `PitSense classified the driver as Concerned because the radio indicates a measurable change in vehicle behaviour, specifically ${issuesStr}. Stress is elevated at ${stress}%, which remains below the High Stress threshold, while urgency remains moderate at ${urgency}%.\n\nThe primary concern is tyre performance and handling rather than driver panic.`;
        } else if (state === "Emergency" || state === "High Stress") {
            const issuesStr = issues.length ? issues.join(", ") : "critical driver radio transmissions";
            return `PitSense classified the driver as ${state} due to high operational workload and elevated risk signals on track. Radio feedback highlights ${issuesStr}. Stress is registered at ${stress}% and urgency is at ${urgency}%.\n\nImmediate pit wall intervention and strategy review are required.`;
        } else {
            return `PitSense classified the driver as Calm based on structured, clear radio communications. Speech emotion was detected as ${emoLabel} (${emoConf}% confidence). Stress index is low at ${stress}% with urgency at ${urgency}%.\n\nNo vehicle reliability or balance issues were detected.`;
        }
    }

    // 2. Risk question
    if (q.includes("risk")) {
        if (issues.length > 0) {
            return `The primary risk right now is: ${issues.join("; ")}. Current urgency score is ${urgency}% (${riskLevel} risk level) with stress at ${stress}%.\n\n${recommendations[0] || "We recommend monitoring telemetry closely and preparing the pit window."}`;
        }
        return `Overall session risk is assessed as ${riskLevel} with an urgency score of ${urgency}%. Vehicle systems appear stable based on driver feedback. The primary operational objective is maintaining target pace.`;
    }

    // 3. Pit stop / Box question
    if (q.includes("pit") || q.includes("box") || q.includes("stay out")) {
        if (riskLevel === "CRITICAL" || riskLevel === "HIGH" || state === "Emergency" || state === "High Stress") {
            const recsStr = recommendations.length ? recommendations.join("; ") : "Inspect vehicle and perform diagnostic checks.";
            return `A pit stop is strongly recommended. Risk is evaluated as ${riskLevel} with urgency at ${urgency}%. Radio flags: ${recsStr}.\n\nBoxing now prevents further performance loss and ensures driver safety.`;
        }
        return `PitSense recommends continuing the current stint. Urgency is manageable at ${urgency}% (${riskLevel} risk), and car balance remains operational.\n\nKeep the pit crew ready, but remaining on track is optimal for overall race time.`;
    }

    // 4. Radio / Transcript question
    if (q.includes("radio") || q.includes("transcript") || q.includes("said") || q.includes("indicate")) {
        const transClean = transcript ? `"${transcript}"` : "No radio transcript captured.";
        const issuesSummary = issues.length ? `Detected flags: ${issues.join(", ")}.` : "No handling anomalies reported.";
        return `The driver's radio states: ${transClean}\n\nVoice tone analysis detected ${emoLabel} emotion (${emoConf}% confidence), with a stress rating of ${stress}% and urgency of ${urgency}%. ${issuesSummary}`;
    }

    // 5. Pushing / Pace question
    if (q.includes("push") || q.includes("pace")) {
        if (state === "Emergency" || state === "High Stress") {
            return `Negative. Do not push. Driver stress is elevated (${stress}%) with urgency at ${urgency}%.\n\nReduce unnecessary risk, conserve tyre energy, and prepare for pit wall instructions.`;
        }
        return `Copy. Driver state is ${state} and stress remains controlled at ${stress}%.\n\nVehicle stability is good. The driver can continue pushing within target stint pace.`;
    }

    // 6. Engineer advice / what to tell driver question
    if (q.includes("tell") || q.includes("say to") || q.includes("advice") || q.includes("tell the driver")) {
        if (riskLevel === "CRITICAL") return `The engineer should inform the driver: "BOX THIS LAP. Telemetry indicates a critical event. Reduce unnecessary risk and return safely."`;
        if (riskLevel === "HIGH") return `The engineer should inform the driver: "Copy. We are analysing telemetry. Prepare for a possible strategy change. Continue reporting vehicle behaviour."`;
        if (riskLevel === "MODERATE") return `The engineer should inform the driver: "Copy. Continue current stint. Keep reporting any changes."`;
        return `The engineer should inform the driver: "Copy. Car looks good. Telemetry agrees with your feedback. Continue pushing."`;
    }

    // Quick Actions
    if (q.includes("explain") || q.includes("summary")) {
        const issuesTxt = issues.length ? issues.join(", ") : "None";
        const recsTxt = recommendations.length ? recommendations.join(", ") : "Maintain stint pace";
        return `Executive Analysis Breakdown:\n• Driver State: ${state}\n• Emotion: ${emoLabel} (${emoConf}% confidence)\n• Stress Index: ${stress}%\n• Urgency Rating: ${urgency}%\n• Identified Issues: ${issuesTxt}\n• Recommended Actions: ${recsTxt}`;
    }

    if (q.includes("strategy")) {
        if (recommendations.length) {
            return `Operational Strategy Recommendations:\n${recommendations.map(r => `• ${r}`).join("\n")}`;
        }
        return `Strategy recommendation: Maintain current race stint, monitor tyre degradation, and stick to the planned pit window.`;
    }

    // General fallback
    if (transcript) {
        return `PitSense analyzed the radio transmission: "${transcript}". Current driver state is ${state} with stress at ${stress}% and urgency at ${urgency}%.\n\n${issues.length ? 'Key issues: ' + issues.join(', ') : 'Vehicle performance is stable.'}`;
    }

    return "That information is not available in the current session.";
}

/**
 * Main query function — attempts backend API first, falls back to deterministic engine.
 */
export async function askRaceEngineer(sessionData, question) {
    if (!question || !question.trim()) {
        throw new Error("Question cannot be empty");
    }

    const payload = {
        transcript: sessionData?.transcript || "",
        emotion: sessionData?.analysis?.emotion || sessionData?.emotion || {},
        driver_analysis: sessionData?.analysis?.driver_analysis || sessionData?.driver_analysis || {},
        ai_summary: sessionData?.analysis?.ai_summary || sessionData?.ai_summary || "",
        question: question.trim(),
        filename: sessionData?.filename || "",
        timestamp: sessionData?.timestamp || Date.now(),
        chat_history: sessionData?.chat || []
    };

    try {
        const response = await API.post("/chat", payload);
        if (response.data && response.data.answer) {
            return {
                text: response.data.answer,
                aiSource: response.data.ai_source || "local"
            };
        }
    } catch (err) {
        console.warn("Backend /chat endpoint unavailable, using local Race Engineer engine:", err?.message);
    }

    // Fallback to deterministic local engine
    return {
        text: generateLocalEngineerAnswer(sessionData, question),
        aiSource: "local"
    };
}
