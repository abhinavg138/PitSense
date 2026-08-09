"""
decision_engine.py
------------------
Phase 8 — Engineer Decision & Support Engine

Determines structured race-engineering state, severity, decision, and explainable reasons.
Runs deterministically BEFORE Gemini natural-language synthesis.

Vocabulary:
  Severity: CALM | ELEVATED | STRESSED | CRITICAL
  Priority: LOW | MODERATE | HIGH | CRITICAL
  Decision: NO_ACTION | MONITOR | MONITOR_PERFORMANCE | CHECK_DRIVER | CHECK_VEHICLE | RADIO_INTERVENTION | PIT_AND_INSPECT
"""

from typing import Dict, Any, List, Optional


VALID_DECISIONS = [
    "NO_ACTION",
    "MONITOR",
    "MONITOR_PERFORMANCE",
    "CHECK_DRIVER",
    "CHECK_VEHICLE",
    "RADIO_INTERVENTION",
    "PIT_AND_INSPECT",
]

VALID_SEVERITIES = ["CALM", "ELEVATED", "STRESSED", "CRITICAL"]


def evaluate_engineer_decision(
    driver_state: Dict[str, Any],
    stress_index: Dict[str, Any],
    temporal_analysis: Dict[str, Any],
    audio_emotion: Dict[str, Any],
    transcript: str = "",
) -> Dict[str, Any]:
    """
    Evaluates multi-signal telemetry, stress metrics, trends, and transcript cues
    to produce a deterministic Engineer Decision.
    """
    stress_val = float(stress_index.get("stress_index", driver_state.get("stress", 0)))
    urgency_val = float(driver_state.get("urgency", 0))
    driver_label = str(driver_state.get("driver_state", "Calm"))
    issues = driver_state.get("issues", [])
    t_lower = (transcript or "").lower()

    # Temporal signals
    sample_count = temporal_analysis.get("sample_count", 1)
    stress_trend = temporal_analysis.get("stress_trend", "STABLE")
    perf_direction = temporal_analysis.get("performance_direction", "STABLE")
    perf_trend = temporal_analysis.get("performance_trend", "STABLE")
    stress_change = temporal_analysis.get("stress_change", 0)
    lap_delta = temporal_analysis.get("lap_time_delta")
    correlation = temporal_analysis.get("correlation")

    # Transcript vehicle concern signals
    vehicle_keywords = ["tyre", "tire", "vibration", "puncture", "wing", "brake", "engine", "smoke", "gearbox", "damage", "balance"]
    has_vehicle_issue_in_transcript = any(kw in t_lower for kw in vehicle_keywords)

    reasons: List[str] = []

    # 1. Determine Severity
    if (
        stress_val >= 85
        or urgency_val >= 85
        or driver_label == "Emergency"
        or ("Vehicle Damage" in issues and stress_val >= 70)
        or (has_vehicle_issue_in_transcript and stress_val >= 75 and perf_direction == "SLOWER")
    ):
        severity = "CRITICAL"
        priority = "CRITICAL"
        reasons.append(f"Driver stress is critically elevated ({int(stress_val)}/100).")
        if urgency_val >= 80:
            reasons.append(f"Urgency score is critical ({int(urgency_val)}/100).")
        if issues:
            reasons.append(f"Reported vehicle issues: {', '.join(issues)}.")
        if perf_direction == "SLOWER":
            reasons.append(f"Lap times are slower than baseline (+{lap_delta}s).")

    elif (
        stress_val >= 65
        or driver_label == "High Stress"
        or (stress_trend == "RISING" and perf_direction == "SLOWER")
    ):
        severity = "STRESSED"
        priority = "HIGH"
        reasons.append(f"Sustained high driver workload (stress: {int(stress_val)}/100).")
        if stress_trend == "RISING":
            reasons.append(f"Stress has increased (+{stress_change} pts over recent laps).")
        if perf_direction == "SLOWER":
            reasons.append(f"Performance is deteriorating (+{lap_delta}s vs baseline).")

    elif (
        stress_trend == "RISING"
        or (45 <= stress_val < 65)
        or perf_direction == "SLOWER"
        or driver_label == "Concerned"
    ):
        severity = "ELEVATED"
        priority = "MODERATE"
        reasons.append(f"Driver stress is elevated ({int(stress_val)}/100).")
        if stress_trend == "RISING":
            reasons.append("Stress trend is rising across recent communications.")
        if perf_direction == "SLOWER":
            reasons.append("Lap time is slightly slower than baseline.")

    else:
        severity = "CALM"
        priority = "LOW"
        reasons.append("Driver stress is low and communication is structured.")
        reasons.append("No active vehicle or performance anomalies detected.")

    # 2. Determine Decision & Recommendation
    if severity == "CRITICAL":
        if issues or has_vehicle_issue_in_transcript:
            decision = "PIT_AND_INSPECT"
            recommendation = "Box this lap. Prepare pit crew for vehicle inspection and service."
        else:
            decision = "RADIO_INTERVENTION"
            recommendation = "Initiate immediate radio contact. Confirm driver status and stint strategy."

    elif severity == "STRESSED":
        if perf_direction == "SLOWER":
            decision = "RADIO_INTERVENTION"
            recommendation = "Query driver on vehicle balance and tire drop-off on straight."
        elif issues:
            decision = "CHECK_VEHICLE"
            recommendation = "Monitor vehicle diagnostic telemetry and verify reported concerns."
        else:
            decision = "CHECK_DRIVER"
            recommendation = "Maintain radio check. Monitor driver workload and sector pace."

    elif severity == "ELEVATED":
        if perf_direction == "SLOWER":
            decision = "MONITOR_PERFORMANCE"
            recommendation = "Monitor lap time degradation and next sector split."
        else:
            decision = "MONITOR"
            recommendation = "Continue standard stint monitoring. Baseline operational."

    else:
        decision = "NO_ACTION"
        recommendation = "Maintain current stint plan. No pit-wall intervention needed."

    # 3. Transparent Confidence Calculation
    base_conf = float(audio_emotion.get("confidence", 85.0)) / 100.0 if float(audio_emotion.get("confidence", 85.0)) > 1.0 else float(audio_emotion.get("confidence", 0.85))

    if sample_count <= 1:
        calc_confidence = min(0.55, base_conf)
    elif sample_count < 3:
        calc_confidence = min(0.75, base_conf * 1.1)
    else:
        calc_confidence = min(0.88, base_conf * 1.15)
        if correlation is not None and abs(correlation) >= 0.7:
            calc_confidence = min(0.95, calc_confidence + 0.07)

    confidence = round(max(0.40, calc_confidence), 2)

    return {
        "severity": severity,
        "priority": priority,
        "decision": decision,
        "recommendation": recommendation,
        "reasons": reasons,
        "confidence": confidence,
    }
