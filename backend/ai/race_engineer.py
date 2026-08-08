from datetime import datetime
from ai.llm_summary import (
    MISSING_TELEMETRY_RESPONSE,
    build_session_context,
    generate_gemini_brief,
    generate_gemini_chat_answer,
    is_missing_telemetry_question,
)


def bar(value, length=20):
    filled = int((value / 100) * length)
    return "█" * filled + "░" * (length - filled)


def emoji(state):
    if state == "Emergency":
        return "🚨"

    if state == "High Stress":
        return "🔴"

    if state == "Concerned":
        return "🟡"

    return "🟢"


def risk(urgency):

    if urgency >= 90:
        return "CRITICAL"

    if urgency >= 70:
        return "HIGH"

    if urgency >= 40:
        return "MODERATE"

    return "LOW"


def engineer_reply(level, driver_state="Calm", issues=None, recommendations=None):
    issues = issues or []
    recommendations = recommendations or []

    if level == "CRITICAL" or driver_state == "Emergency":
        if issues:
            issues_str = ", ".join(issues[:2])
            return f"Copy. We see the reported issues ({issues_str}). BOX THIS LAP. Reduce unnecessary risk and return safely."
        return (
            "BOX THIS LAP.\n"
            "Telemetry indicates a critical event.\n"
            "Reduce unnecessary risk and return safely."
        )

    if level == "HIGH" or driver_state == "High Stress":
        if issues:
            issues_str = ", ".join(issues[:2])
            return f"Copy. We see the reported vehicle issue ({issues_str}). Reduce unnecessary risk and prepare for an earlier stop."
        return (
            "Copy. We see the degradation and high workload.\n"
            "Manage the car and report if the vibration or balance worsens."
        )

    if level == "MODERATE" or driver_state == "Concerned":
        if issues:
            return f"Copy. We are monitoring {issues[0]}. Continue for now and report if the balance or vibration worsens."
        return (
            "Copy.\n"
            "Continue current stint.\n"
            "Keep reporting any changes."
        )

    return (
        "Copy.\n"
        "Car feedback is stable.\n"
        "Continue with current plan."
    )


def generate_summary(transcript, emotion, driver):

    state = driver["driver_state"]

    stress = driver["stress"]

    urgency = driver["urgency"]

    issues = driver["issues"]

    recommendations = driver["recommendations"]

    report = []

    report.append("╔════════════════════════════════════════════════════════════╗")
    report.append("║                 🏎 PITSENSE AI RACE ENGINEER              ║")
    report.append("╚════════════════════════════════════════════════════════════╝")

    report.append("")

    report.append(
        f"📅 Generated : {datetime.now().strftime('%d %b %Y   %H:%M:%S')}"
    )

    report.append(f"🏁 Driver State : {emoji(state)} {state}")

    report.append(
        f"😊 Emotion : {emotion['emotion'].title()} ({emotion['confidence']}%)"
    )

    report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("📋 EXECUTIVE SUMMARY")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if state == "Emergency":

        report.append(
            "Driver communication suggests an immediate race-critical event."
        )

        report.append(
            "Rapid intervention from the pit wall is strongly recommended."
        )

    elif state == "High Stress":

        report.append(
            "Driver workload is elevated with signs of increasing pressure."
        )

        report.append(
            "Current communication indicates deteriorating operating conditions."
        )

    elif state == "Concerned":

        report.append(
            "Minor concerns have been identified from the driver's report."
        )

        report.append(
            "Vehicle remains operational but should be monitored."
        )

    else:

        report.append(
            "Driver communication is calm, structured and technically consistent."
        )

        report.append(
            "No significant operational concern was detected."
        )

    report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("🧠 DRIVER METRICS")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    report.append(
        f"Stress      {bar(stress)} {stress}%"
    )

    report.append(
        f"Urgency     {bar(urgency)} {urgency}%"
    )

    report.append(
        f"Confidence  {bar(emotion['confidence'])} {emotion['confidence']}%"
    )

    report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("🏎 VEHICLE HEALTH")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if issues:

        for issue in issues:

            report.append(f"⚠ {issue}")

    else:

        report.append("✅ Engine status appears normal.")
        report.append("✅ No obvious reliability concern detected.")
        report.append("✅ Driver reported stable vehicle behaviour.")

    report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("📡 TELEMETRY ITEMS")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    telemetry = [
        "Engine Temperature",
        "Tyre Temperature",
        "Brake Temperature",
        "Fuel Consumption",
        "ERS Deployment",
        "Lap Consistency",
        "Suspension Load",
        "Power Unit"
    ]

    for item in telemetry:

        report.append(f"☐ {item}")

        report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("🚦 RISK ASSESSMENT")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    level = risk(urgency)

    if level == "CRITICAL":
        colour = "🔴"

    elif level == "HIGH":
        colour = "🟠"

    elif level == "MODERATE":
        colour = "🟡"

    else:
        colour = "🟢"

    report.append(f"Overall Risk Level : {colour} {level}")

    report.append("")

    if level == "CRITICAL":

        report.append(
            "Driver safety has become the highest priority."
        )

        report.append(
            "Immediate engineering intervention is recommended."
        )

    elif level == "HIGH":

        report.append(
            "Performance degradation is likely affecting the lap."
        )

        report.append(
            "Telemetry should be reviewed before the next sector."
        )

    elif level == "MODERATE":

        report.append(
            "Current conditions remain manageable."
        )

        report.append(
            "Continue collecting driver feedback."
        )

    else:

        report.append(
            "Current operating conditions remain stable."
        )

        report.append(
            "No immediate engineering action required."
        )

    report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("🏁 RACE STRATEGY")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if recommendations:

        for recommendation in recommendations:

            report.append(f"▶ {recommendation}")

    else:

        if level == "LOW":

            report.append("▶ Continue current race strategy.")
            report.append("▶ Maintain target lap pace.")
            report.append("▶ Monitor tyre degradation.")

        elif level == "MODERATE":

            report.append("▶ Maintain current stint.")
            report.append("▶ Prepare contingency strategy.")
            report.append("▶ Increase telemetry monitoring.")

        elif level == "HIGH":

            report.append("▶ Evaluate pit window.")
            report.append("▶ Review vehicle telemetry.")
            report.append("▶ Prepare pit crew.")

        else:

            report.append("▶ Box this lap.")
            report.append("▶ Inspect vehicle immediately.")
            report.append("▶ Safety takes priority.")

    report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("🎧 ENGINEER RESPONSE")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    report.append("┌──────────────────────────────────────────────────────────┐")

    for line in engineer_reply(level).split("\n"):

        report.append(f"│ {line}")

    report.append("└──────────────────────────────────────────────────────────┘")

    report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("🤖 AI CONFIDENCE")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    overall = round(
        (
            emotion["confidence"] +
            stress +
            urgency
        ) / 3
    )

    report.append(
        f"Speech Analysis     {bar(emotion['confidence'])} {emotion['confidence']}%"
    )

    report.append(
        f"Driver Intelligence {bar(overall)} {overall}%"
    )

    report.append("")

    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("🚨 FINAL VERDICT")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if level == "CRITICAL":

        report.append("🔴 IMMEDIATE PIT INTERVENTION REQUIRED")

    elif level == "HIGH":

        report.append("🟠 HIGH PRIORITY - REVIEW STRATEGY")

    elif level == "MODERATE":

        report.append("🟡 CONTINUE WITH CAUTION")

    else:

        report.append("🟢 VEHICLE OPERATING NORMALLY")

    report.append("")

    report.append(
        "PitSense AI has completed a full communication,"
    )

    report.append(
        "emotion and strategy assessment based on the"
    )

    report.append(
        "available driver radio transmission."
    )

    report.append("")

    report.append("════════════════════════════════════════════════════════════")
    report.append("Generated by PitSense AI Race Engineer v2.0")
    report.append("════════════════════════════════════════════════════════════")

    return "\n".join(report)


def answer_engineer_question(
    transcript: str,
    emotion: dict,
    driver_analysis: dict,
    ai_summary: str = "",
    question: str = "",
    filename: str = "",
    timestamp: str = ""
) -> str:
    """
    Generates a professional, operational F1 Race Engineer response based ONLY on current session context.
    Strictly avoids hallucinating unavailable telemetry data (fuel level, lap times, tyre temps, etc.).
    """
    q = (question or "").strip().lower()
    if not q:
        return "That information is not available in the current session."

    # Explicit telemetry check guardrails for missing data
    unavailable_keywords = [
        "fuel", "lap time", "sector", "gap", "tire temp", "tyre temp",
        "brake temp", "engine temp", "oil temp", "compound", "softs",
        "mediums", "hards", "intermediates", "wets", "telemetry value", "telemetry reading"
    ]

    # Check if question asks about specific metrics that aren't mentioned in the transcript
    t_lower = (transcript or "").lower()
    for kw in unavailable_keywords:
        if kw in q and kw not in t_lower:
            return "That information is not available in the current session."

    state = driver_analysis.get("driver_state", "Calm")
    stress = driver_analysis.get("stress", 0)
    urgency = driver_analysis.get("urgency", 0)
    issues = driver_analysis.get("issues", [])
    recommendations = driver_analysis.get("recommendations", [])
    emo_label = emotion.get("emotion", "calm").title()
    emo_conf = emotion.get("confidence", 85)

    risk_lvl = risk(urgency)

    # 1. Driver classification / state question
    # Parens are required here — `and` binds tighter than `or`.
    if "classified" in q or "driver state" in q or ("why" in q and ("concerned" in q or "stress" in q or "emergency" in q or "calm" in q)):
        if state == "Concerned":
            issues_str = ", ".join(issues) if issues else "reported handling and performance variations"
            return (
                f"PitSense classified the driver as Concerned because the radio indicates a measurable change in vehicle behaviour, "
                f"specifically {issues_str}. Stress is elevated at {stress}%, which remains below the High Stress threshold, while urgency is at {urgency}%. "
                f"The primary concern is vehicle operational feedback rather than driver panic."
            )
        elif state in ["High Stress", "Emergency"]:
            issues_str = ", ".join(issues) if issues else "critical driver radio comms"
            return (
                f"PitSense classified the driver as {state} due to high operational workload on track. "
                f"Detected radio signals indicate {issues_str}. Stress level is registered at {stress}% with urgency at {urgency}%. "
                f"Immediate engineering support and pit wall intervention are advised."
            )
        else:
            return (
                f"PitSense classified the driver as Calm based on structured and consistent radio communication. "
                f"Speech emotion was detected as {emo_label} ({emo_conf}% confidence). Stress is low at {stress}% and urgency is at {urgency}%. "
                f"No vehicle reliability concerns were detected."
            )

    # 2. Risk question
    if "risk" in q:
        if issues:
            issues_str = "; ".join(issues)
            return (
                f"The primary risk right now is: {issues_str}. Current urgency score is {urgency}% ({risk_lvl} risk level), "
                f"with driver stress at {stress}%. {recommendations[0] if recommendations else 'Telemetry should be monitored closely to prevent stint time loss.'}"
            )
        else:
            return (
                f"Overall session risk is assessed as {risk_lvl} with an urgency level of {urgency}%. "
                f"No active vehicle issues have been identified in the transcript. The main focus is maintaining stint consistency and managing tyre wear."
            )

    # 3. Pit stop / Box question
    if "pit" in q or "box" in q or "stay out" in q:
        if risk_lvl in ["CRITICAL", "HIGH"] or state in ["Emergency", "High Stress"]:
            recs_str = "; ".join(recommendations) if recommendations else "Inspect vehicle and address driver reported issues."
            return (
                f"A pit stop is advised because risk is rated at {risk_lvl} with urgency at {urgency}%. "
                f"Driver communication flags: {recs_str}. Bringing the car in reduces mechanical risk and protects track position."
            )
        else:
            return (
                f"PitSense recommends continuing the current stint. Urgency is manageable at {urgency}% ({risk_lvl} risk), "
                f"and vehicle status remains operational. Pit crew should remain standby, but staying out is optimal for race pace."
            )

    # 4. Radio / Transcript question
    if "radio" in q or "transcript" in q or "said" in q or "say" in q:
        trans_clean = transcript if transcript else "No transcript captured."
        return (
            f"The driver's radio message recorded: \"{trans_clean}\". "
            f"Tone analysis indicates emotion '{emo_label}' ({emo_conf}% confidence), stress index of {stress}%, and urgency of {urgency}%. "
            f"{'Detected issues: ' + ', '.join(issues) if issues else 'No vehicle anomalies reported.'}"
        )

    # 5. Pushing question
    if "push" in q or "pushing" in q or "pace" in q:
        if state in ["Emergency", "High Stress"]:
            return (
                f"Negative. Do not push. Driver stress ({stress}%) and urgency ({urgency}%) are elevated. "
                f"Focus on vehicle control, managing tyre energy, and stabilizing lap time."
            )
        else:
            return (
                f"Copy. Telemetry and driver state ({state}) indicate car stability is high. "
                f"Stress is low ({stress}%). Driver can continue pushing within stint targets."
            )

    # 6. Engineer advice question
    if "tell" in q or "say to" in q or "advice" in q or "message" in q:
        reply_txt = engineer_reply(risk_lvl)
        return f"The engineer should relay the following message: \"{reply_txt}\""

    # Quick Action: Explain Analysis
    if "explain" in q or "summary" in q or "overview" in q:
        issues_txt = ", ".join(issues) if issues else "None"
        recs_txt = ", ".join(recommendations) if recommendations else "Continue current stint"
        return (
            f"Session Analysis Summary: Driver state is '{state}' with emotion '{emo_label}' ({emo_conf}% confidence). "
            f"Stress is {stress}% and Urgency is {urgency}%. Detected issues: {issues_txt}. Key strategy recommendation: {recs_txt}."
        )

    # Quick Action: Strategy
    if "strategy" in q or "recommend" in q:
        if recommendations:
            recs_fmt = "; ".join(recommendations)
            return f"Current operational strategy recommendations for this session: {recs_fmt}."
        return f"Current strategy is to maintain lap pace, monitor tyre wear, and execute the baseline pit window."

    # General fallback using session context
    if transcript:
        return (
            f"Based on session radio \"{transcript}\", driver state is {state} (Stress: {stress}%, Urgency: {urgency}%). "
            f"Primary operational verdict: {engineer_reply(risk_lvl)}"
        )

    return "That information is not available in the current session."


def generate_summary_with_source(transcript, emotion, driver):
    deterministic_summary = generate_summary(transcript, emotion, driver)
    context = build_session_context(
        transcript=transcript,
        emotion=emotion,
        driver=driver,
        ai_summary=deterministic_summary
    )

    gemini_brief = generate_gemini_brief(context)
    if gemini_brief:
        enhanced_summary = "\n\n".join([
            deterministic_summary,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "AI ENHANCED BRIEF",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            gemini_brief["summary"],
        ])
        return {
            "summary": enhanced_summary,
            "engineer_reply": gemini_brief["radio_response"],
            "ai_source": "gemini",
        }

    return {
        "summary": deterministic_summary,
        "engineer_reply": engineer_reply(
            risk(driver.get("urgency", 0)),
            driver_state=driver.get("driver_state", "Calm"),
            issues=driver.get("issues", []),
            recommendations=driver.get("recommendations", [])
        ),
        "ai_source": "local",
    }


def answer_engineer_question_with_source(
    transcript: str,
    emotion: dict,
    driver_analysis: dict,
    ai_summary: str = "",
    question: str = "",
    filename: str = "",
    timestamp: str = ""
):
    deterministic_answer = answer_engineer_question(
        transcript=transcript,
        emotion=emotion,
        driver_analysis=driver_analysis,
        ai_summary=ai_summary,
        question=question,
        filename=filename,
        timestamp=timestamp
    )

    if deterministic_answer == MISSING_TELEMETRY_RESPONSE or is_missing_telemetry_question(question):
        return {
            "answer": MISSING_TELEMETRY_RESPONSE,
            "ai_source": "local",
        }

    context = build_session_context(
        transcript=transcript,
        emotion=emotion,
        driver=driver_analysis,
        ai_summary=ai_summary
    )
    gemini_answer = generate_gemini_chat_answer(context, question)
    if gemini_answer:
        return {
            "answer": gemini_answer,
            "ai_source": "gemini",
        }

    return {
        "answer": deterministic_answer,
        "ai_source": "local",
    }
