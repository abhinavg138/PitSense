from typing import Dict, Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# PitSense Actionable Engineering Insight & Recommendation Engine (Phase 5)
#
# Answers the core pit-wall question: "What does the pit wall recommend doing next?"
#
# CORE PRINCIPLES:
# 1. Deterministic generation — AI/LLM is NOT responsible for decision-making.
# 2. Strict Priority Hierarchy:
#    CRITICAL SAFETY / VEHICLE DAMAGE → PIT_NOW
#    HIGH RISK + VEHICLE CONCERN / SUSTAINED HIGH STRESS → PREPARE_PIT / PIT_NOW
#    RISING STRESS + LAP DEGRADATION → RADIO_INTERVENTION
#    RISING STRESS + STABLE LAP PERF → MONITOR / RADIO_INTERVENTION
#    ELEVATED STRESS → MONITOR
#    LOW STRESS / STABLE → NO_INTERVENTION / CONTINUE
# 3. Confidence-Aware — Low confidence lowers recommendation certainty and prompts
#    radio re-verification before escalating.
# 4. Clear 3-part structure: WHAT, WHY, PIT_WALL_ACTION.
# ─────────────────────────────────────────────────────────────────────────────

# --- Configuration & Action Constants ----------------------------------------

ACTIONS = [
    "NO_INTERVENTION",
    "CONTINUE",
    "MONITOR",
    "RADIO_INTERVENTION",
    "PREPARE_PIT",
    "PIT_NOW",
]

CATEGORIES = [
    "CRITICAL_DRIVER_STATE",
    "VEHICLE_CONCERN",
    "PERFORMANCE_DEGRADATION",
    "SUSTAINED_STRESS",
    "RISING_STRESS",
    "STABLE",
    "INSUFFICIENT_DATA",
]

PRIORITIES = ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def generate_actionable_insight(
    driver_state: Dict[str, Any],
    stress_index: Dict[str, Any],
    audio_emotion: Dict[str, Any],
    text_emotion: Dict[str, Any],
    temporal_analysis: Dict[str, Any],
    lap_performance: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a structured, deterministic engineering recommendation.

    Takes perception output, explainable stress index, temporal trend,
    and lap performance data to produce a single, non-contradictory recommendation.
    """
    # Extract core metrics
    state_label = driver_state.get("driver_state", "Calm")
    stress_val = stress_index.get("stress_index", driver_state.get("stress", 20))
    urgency_val = driver_state.get("urgency", 10)
    issues = driver_state.get("issues", [])

    # Perception confidence (0.0 – 1.0)
    audio_conf = audio_emotion.get("confidence", 0.0)
    text_conf = text_emotion.get("confidence", 100) / 100.0 if text_emotion.get("confidence", 0) > 1 else text_emotion.get("confidence", 1.0)
    confidence = round((audio_conf + text_conf) / 2.0, 2) if audio_conf > 0 else round(text_conf, 2)

    # Temporal metrics
    temporal_avail = temporal_analysis.get("available", False)
    trend = temporal_analysis.get("trend", "INSUFFICIENT_DATA")
    sustained = temporal_analysis.get("sustained_stress", False)
    stress_change = temporal_analysis.get("stress_change", 0)

    # Lap performance metrics
    lap_avail = lap_performance.get("available", False)
    lap_delta = lap_performance.get("lap_time_delta_seconds")
    correlation = lap_performance.get("correlation")

    # ── Rule Hierarchy ──

    # Rule 1: CRITICAL SAFETY / EMERGENCY / VEHICLE DAMAGE
    if state_label == "Emergency" or urgency_val >= 90 or "Vehicle Damage" in issues or stress_val >= 90:
        category = "CRITICAL_DRIVER_STATE"
        priority = "CRITICAL"
        action = "PIT_NOW"
        headline = "Immediate Pit Stop Required"
        
        issues_text = f" ({', '.join(issues)})" if issues else ""
        what = f"Critical driver state '{state_label}' detected{issues_text} with stress at {stress_val}%."
        why = "Driver safety and vehicle integrity are compromised. Immediate pit intervention is required."
        pit_wall_action = "Box this lap. Prepare pit crew for emergency inspection and service."
        recommendation = f"BOX THIS LAP. {what} {pit_wall_action}"

    # Rule 2: VEHICLE CONCERN / HIGH RISK
    elif issues or (sustained and stress_val >= 70):
        category = "VEHICLE_CONCERN" if issues else "SUSTAINED_STRESS"
        priority = "HIGH"
        action = "PREPARE_PIT"
        headline = f"Vehicle Issue & Workload Elevated ({', '.join(issues)})" if issues else "Sustained High Driver Workload"

        issues_text = f"Reported vehicle issues: {', '.join(issues)}." if issues else "Sustained high driver stress over consecutive laps."
        what = f"Driver stress at {stress_val}%. {issues_text}"
        why = "Potential performance degradation or mechanical failure risk during current stint."
        pit_wall_action = "Prepare pit wall for earlier pit window. Alert crew to inspect reported components."
        recommendation = f"PREPARE PIT STOP. {what} {pit_wall_action}"

    # Rule 3: RISING STRESS + LAP DEGRADATION
    elif trend == "RISING" and lap_avail and lap_delta is not None and lap_delta > 0.2:
        category = "PERFORMANCE_DEGRADATION"
        priority = "HIGH"
        action = "RADIO_INTERVENTION"
        headline = "Driver Stress Rising Alongside Slower Lap Times"

        what = f"Driver stress increased by +{stress_change}% while lap time degraded by +{lap_delta}s."
        why = "Vocal stress correlates directly with lap time degradation, indicating driver overload or tire drop-off."
        pit_wall_action = "Initiate radio communication. Check tire degradation and balance with driver."
        recommendation = f"RADIO INTERVENTION. {what} {pit_wall_action}"

    # Rule 4: RISING STRESS (General)
    elif trend == "RISING" or stress_change >= 10:
        category = "RISING_STRESS"
        priority = "MODERATE"
        action = "RADIO_INTERVENTION" if stress_val >= 60 else "MONITOR"
        headline = "Driver Stress Trend Increasing"

        what = f"Driver stress level has risen by +{stress_change}% over recent communications."
        why = "Early indicator of increasing workload or developing balance issues."
        pit_wall_action = "Query driver on car balance on the main straight. Monitor next sector split."
        recommendation = f"MONITOR / RADIO CHECK. {what} {pit_wall_action}"

    # Rule 5: SUSTAINED ELEVATED STRESS
    elif sustained:
        category = "SUSTAINED_STRESS"
        priority = "HIGH"
        action = "RADIO_INTERVENTION"
        headline = "Sustained High Driver Workload"

        what = f"Driver stress has remained consistently high ({stress_val}%) across multiple laps."
        why = "Sustained stress elevates risk of driver fatigue and operational errors."
        pit_wall_action = "Initiate radio check to confirm driver status and stint strategy."
        recommendation = f"RADIO INTERVENTION. {what} {pit_wall_action}"

    # Rule 6: STABLE / LOW STRESS
    elif stress_val < 40 and not issues:
        category = "STABLE"
        priority = "LOW"
        action = "CONTINUE" if stress_val < 25 else "NO_INTERVENTION"
        headline = "Driver Condition & Pace Stable"

        what = f"Driver stress low ({stress_val}%), communication calm and structured."
        why = "Vehicle behavior stable, lap times consistent with target pace."
        pit_wall_action = "Maintain current stint plan. No pit-wall intervention needed."
        recommendation = f"CONTINUE STINT. {what} {pit_wall_action}"

    # Rule 7: DEFAULT / MODERATE MONITORING
    else:
        category = "INSUFFICIENT_DATA" if not temporal_avail else "STABLE"
        priority = "MODERATE" if stress_val >= 50 else "LOW"
        action = "MONITOR"
        headline = "Baseline Established — Monitoring Stint"

        what = f"Driver stress at {stress_val}%, driver state '{state_label}'."
        why = "No critical vehicle issues or severe stress spikes detected."
        pit_wall_action = "Continue standard telemetry & radio monitoring."
        recommendation = f"MONITOR. {what} {pit_wall_action}"

    # ── Confidence Adjustment ──
    # If confidence is low (< 0.45) and not an explicit emergency, soften action
    if confidence < 0.45 and category != "CRITICAL_DRIVER_STATE":
        if action in ["PIT_NOW", "PREPARE_PIT"]:
            action = "RADIO_INTERVENTION"
        recommendation += f" (Note: Perception confidence is low at {int(confidence*100)}%; confirm via radio before action)."

    return {
        "category":        category,
        "priority":        priority,
        "action":          action,
        "headline":        headline,
        "reason":          why,
        "recommendation":  recommendation,
        "confidence":      confidence,
        "what":            what,
        "why":             why,
        "pit_wall_action": pit_wall_action,
    }
