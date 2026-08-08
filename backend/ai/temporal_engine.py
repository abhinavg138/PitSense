import math
from datetime import datetime
from typing import Dict, List, Optional, Any

# ─────────────────────────────────────────────────────────────────────────────
# PitSense Temporal & Lap Correlation Engine (Phases 3 & 4)
#
# Tracks driver stress over time within a session and correlates stress
# against actual lap performance data when available.
#
# DATA INTEGRITY GUARANTEE:
# Never fabricates lap numbers, lap times, or historical observations.
# If data is missing or insufficient, explicit availability flags are returned.
# ─────────────────────────────────────────────────────────────────────────────

# --- Configuration -----------------------------------------------------------

STRESS_CHANGE_THRESHOLD = 10     # abs(change) >= 10 triggers RISING or FALLING
RECENT_WINDOW_SIZE = 3           # size of recent_stress observation window
MIN_SUSTAINED_OBSERVATIONS = 3   # consecutive observations required for sustained stress
SUSTAINED_STRESS_THRESHOLD = 60  # minimum stress level to count as elevated
MIN_CORRELATION_POINTS = 3       # minimum paired (stress, lap_time) points for Pearson correlation


class SessionManager:
    """In-memory session history store."""

    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])

    def add_observation(self, session_id: str, observation: Dict[str, Any]):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(observation)

    def reset_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id] = []

    def reset_all(self):
        self._sessions.clear()


# Global in-memory session manager
session_manager = SessionManager()


# --- Phase 3: Temporal Stress Analysis ----------------------------------------

def analyze_temporal_stress(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze stress trend across historical observations in a session.

    Requires at least 2 observations for temporal metrics.
    Never fabricates missing observations.
    """
    count = len(history)

    if count < 2:
        return {
            "available": False,
            "reason": "Insufficient session history",
        }

    current_obs = history[-1]
    previous_obs = history[-2]

    current_stress = current_obs["stress"]
    previous_stress = previous_obs["stress"]
    stress_change = current_stress - previous_stress

    # Determine trend category
    if stress_change >= STRESS_CHANGE_THRESHOLD:
        trend = "RISING"
    elif stress_change <= -STRESS_CHANGE_THRESHOLD:
        trend = "FALLING"
    else:
        trend = "STABLE"

    # Extract recent window of stress values
    window = history[-RECENT_WINDOW_SIZE:]
    recent_stress = [obs["stress"] for obs in window]

    # Detect sustained elevated stress
    # Requires at least MIN_SUSTAINED_OBSERVATIONS consecutive readings >= SUSTAINED_STRESS_THRESHOLD
    sustained_stress = False
    if count >= MIN_SUSTAINED_OBSERVATIONS:
        last_n = history[-MIN_SUSTAINED_OBSERVATIONS:]
        sustained_stress = all(obs["stress"] >= SUSTAINED_STRESS_THRESHOLD for obs in last_n)

    return {
        "available": True,
        "observation_count": count,
        "current_stress": current_stress,
        "previous_stress": previous_stress,
        "stress_change": stress_change,
        "trend": trend,
        "recent_stress": recent_stress,
        "sustained_stress": sustained_stress,
    }


# --- Phase 4: Lap Performance Correlation ------------------------------------

def _pearson_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """Calculate Pearson correlation coefficient between two lists of numbers.

    Returns None if variance in x or y is zero.
    """
    n = len(x)
    if n < 2:
        return None

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    if var_x == 0 or var_y == 0:
        return None

    covariance = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    return round(covariance / (math.sqrt(var_x) * math.sqrt(var_y)), 2)


def analyze_lap_performance(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Correlate stress against actual lap performance data when available.

    Only uses observations that contain explicit lap & lap_time_seconds.
    Never fabricates lap numbers or times.
    """
    # Filter observations with valid lap time data
    lap_obs = [
        obs for obs in history
        if obs.get("lap") is not None and obs.get("lap_time_seconds") is not None
    ]

    if not lap_obs:
        return {
            "available": False,
            "reason": "No lap-time data available for this session",
        }

    laps_summary = [
        {
            "lap": obs["lap"],
            "lap_time_seconds": obs["lap_time_seconds"],
            "stress": obs["stress"],
        }
        for obs in lap_obs
    ]

    # Calculate lap time delta if at least 2 lap observations exist
    lap_time_delta_seconds = None
    stress_change = None
    if len(lap_obs) >= 2:
        curr = lap_obs[-1]
        prev = lap_obs[-2]
        lap_time_delta_seconds = round(curr["lap_time_seconds"] - prev["lap_time_seconds"], 3)
        stress_change = curr["stress"] - prev["stress"]

    # Calculate Pearson correlation if at least MIN_CORRELATION_POINTS exist
    stresses = [obs["stress"] for obs in lap_obs]
    lap_times = [obs["lap_time_seconds"] for obs in lap_obs]

    correlation = None
    correlation_available = False
    corr_reason = None

    if len(lap_obs) >= MIN_CORRELATION_POINTS:
        r = _pearson_correlation(stresses, lap_times)
        if r is not None:
            correlation = r
            correlation_available = True
        else:
            corr_reason = "Zero variance in stress or lap time observations"
    else:
        corr_reason = "Insufficient paired observations"

    # Deterministic interpretation
    interpretation = _generate_interpretation(
        stress_change=stress_change,
        lap_time_delta=lap_time_delta_seconds,
        correlation=correlation,
        correlation_available=correlation_available
    )

    result = {
        "available": True,
        "laps": laps_summary,
        "lap_time_delta_seconds": lap_time_delta_seconds,
        "stress_change": stress_change,
        "correlation": correlation,
        "correlation_available": correlation_available,
        "interpretation": interpretation,
    }

    if not correlation_available:
        result["reason"] = corr_reason

    return result


def _generate_interpretation(
    stress_change: Optional[int],
    lap_time_delta: Optional[float],
    correlation: Optional[float],
    correlation_available: bool,
) -> str:
    """Generate a deterministic interpretation based strictly on actual data."""

    if stress_change is not None and lap_time_delta is not None:
        if stress_change > 0 and lap_time_delta > 0.1:
            return "Stress increased alongside slower lap times."
        elif stress_change > 0 and abs(lap_time_delta) <= 0.1:
            return "Stress increased, but no corresponding lap-time deterioration was observed."
        elif stress_change < 0 and lap_time_delta < -0.1:
            return "Lower stress coincided with improved lap performance."
        elif stress_change < 0 and lap_time_delta > 0.1:
            return "Driver stress decreased while lap times slowed."

    if correlation_available and correlation is not None:
        if abs(correlation) < 0.3:
            return "No strong association between stress and lap time was observed."
        elif correlation >= 0.7:
            return "Strong positive correlation observed: higher stress corresponds with slower lap times."
        elif correlation <= -0.7:
            return "Strong negative correlation observed: higher stress corresponds with faster lap times."

    return "Insufficient lap performance history to establish a clear trend."


# --- Decision Support: Engineering Insight -----------------------------------

def generate_engineering_insight(
    temporal: Dict[str, Any],
    lap_perf: Dict[str, Any],
    driver_state: Dict[str, Any],
) -> str:
    """Generate a deterministic decision support insight for the race engineer.

    Combines temporal stress trends, lap performance deltas, and vehicle issues.
    This is decision support, not proof of causality.
    """
    trend = temporal.get("trend", "INSUFFICIENT_DATA")
    sustained = temporal.get("sustained_stress", False)
    issues = driver_state.get("issues", [])
    lap_delta = lap_perf.get("lap_time_delta_seconds")

    # Priority 1: Sustained High Stress + Vehicle Issue
    if (sustained or driver_state.get("stress", 0) >= 70) and issues:
        issues_str = ", ".join(issues[:2])
        return f"Sustained high driver stress coincides with reported vehicle concerns ({issues_str}). Consider pit-wall intervention."

    # Priority 2: Rising Stress + Slower Lap Times
    if trend == "RISING" and lap_delta is not None and lap_delta > 0.2:
        return "Sustained stress increased alongside slower lap times. Consider radio intervention."

    # Priority 3: High Stress + Stable Lap Time
    if (sustained or driver_state.get("stress", 0) >= 60) and (lap_delta is None or abs(lap_delta) <= 0.2):
        return "Driver stress is elevated, but lap performance remains stable. Continue monitoring."

    # Priority 4: Low/Stable Stress + Stable Performance
    if driver_state.get("stress", 0) < 40 and (lap_delta is None or lap_delta <= 0.1):
        return "Driver stress and lap performance remain stable. No intervention recommended."

    # Default fallback based on trend
    if trend == "RISING":
        return "Driver stress trend is rising across recent communications. Monitor closely."
    elif trend == "FALLING":
        return "Driver stress levels are stabilizing. Maintain stint plan."

    return "Session data baseline established. Awaiting further driver communications."
