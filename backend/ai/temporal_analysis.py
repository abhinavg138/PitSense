"""
temporal_analysis.py
--------------------
Consolidated PitSense Temporal & Lap Correlation Engine

Tracks driver stress over time within a session, calculates multi-lap stress trends,
correlates driver stress against actual lap performance data, and produces explainable
decision support metrics.

DATA INTEGRITY GUARANTEE:
Never fabricates lap numbers, lap times, or historical observations.
If data is missing or insufficient, explicit availability flags are returned.
"""

import math
from typing import Dict, List, Optional, Any

# Configurable Thresholds
STRESS_TREND_THRESHOLD = 5          # abs(stress_change) >= 5 triggers RISING/FALLING
PERFORMANCE_TREND_THRESHOLD = 0.2    # abs(lap_delta) >= 0.2s triggers SLOWER/FASTER
MIN_CORRELATION_POINTS = 3          # minimum paired observations for Pearson correlation
SUSTAINED_STRESS_THRESHOLD = 60     # minimum stress level for sustained elevated stress


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


# Global in-memory session manager instance
session_manager = SessionManager()


def pearson_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """
    Computes Pearson correlation coefficient r between two numeric series.
    Returns None if n < 2 or variance is zero.
    """
    n = len(x)
    if n < 2 or len(y) != n:
        return None

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    if var_x < 1e-9 or var_y < 1e-9:
        return None

    covariance = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    r = covariance / (math.sqrt(var_x) * math.sqrt(var_y))
    return round(max(-1.0, min(1.0, r)), 3)


def analyze_temporal_session(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Performs comprehensive temporal analysis across a session's history records.

    Each record expects:
    - lap (int or None)
    - lap_time_seconds (float or None) or lap_time
    - stress (int/float) or stress_index
    - confidence (float)
    - timestamp (str)
    """
    sample_count = len(records)

    if sample_count == 0:
        return {
            "available": False,
            "sample_count": 0,
            "observation_count": 0,
            "reason": "Building temporal picture…",
            "trend": "INSUFFICIENT_DATA",
            "stress_trend": "STABLE",
            "sustained_stress": False,
            "association": "Building temporal picture…",
        }

    # Extract stress timeline
    stresses = [float(r.get("stress", r.get("stress_index", 0))) for r in records]
    current_stress = stresses[-1]
    previous_stress = stresses[-2] if sample_count >= 2 else None

    stress_change = round(current_stress - previous_stress, 1) if previous_stress is not None else 0.0

    if sample_count >= 3:
        stress_change_3_laps = round(current_stress - stresses[-3], 1)
    else:
        stress_change_3_laps = stress_change

    rolling_stress = round(sum(stresses) / sample_count, 1)

    # Determine Stress Trend
    if stress_change >= STRESS_TREND_THRESHOLD:
        stress_trend = "RISING"
    elif stress_change <= -STRESS_TREND_THRESHOLD:
        stress_trend = "FALLING"
    else:
        stress_trend = "STABLE"

    # Consecutive rising stress
    consecutive_rising_stress = 0
    for i in range(sample_count - 1, 0, -1):
        if stresses[i] > stresses[i - 1]:
            consecutive_rising_stress += 1
        else:
            break

    # Sustained stress detection
    sustained_stress = False
    if sample_count >= 3:
        sustained_stress = all(s >= SUSTAINED_STRESS_THRESHOLD for s in stresses[-3:])
    elif sample_count >= 2:
        sustained_stress = (consecutive_rising_stress >= 2 and current_stress >= SUSTAINED_STRESS_THRESHOLD)

    # Extract lap performance timeline (filter non-null lap times)
    lap_records = []
    for r in records:
        lt = r.get("lap_time_seconds")
        if lt is None:
            lt = r.get("lap_time")
        if lt is not None and float(lt) > 0:
            lap_records.append({
                "lap": r.get("lap"),
                "lap_time": float(lt),
                "stress": float(r.get("stress", r.get("stress_index", 0))),
            })

    current_lap = records[-1].get("lap")
    current_lap_time = None
    previous_lap_time = None
    rolling_lap_time = None
    lap_time_delta = None
    performance_direction = "STABLE"
    performance_trend = "STABLE"
    consecutive_deteriorating_performance = 0

    if lap_records:
        current_lap_time = lap_records[-1]["lap_time"]
        if len(lap_records) >= 2:
            previous_lap_time = lap_records[-2]["lap_time"]

        lap_times_all = [lr["lap_time"] for lr in lap_records]
        rolling_lap_time = round(sum(lap_times_all) / len(lap_times_all), 3)

        if current_lap_time is not None and rolling_lap_time is not None:
            lap_time_delta = round(current_lap_time - rolling_lap_time, 3)

            if lap_time_delta > PERFORMANCE_TREND_THRESHOLD:
                performance_direction = "SLOWER"
            elif lap_time_delta < -PERFORMANCE_TREND_THRESHOLD:
                performance_direction = "FASTER"
            else:
                performance_direction = "STABLE"

        # Performance trend over recent lap observations
        if len(lap_records) >= 2:
            last_delta = lap_records[-1]["lap_time"] - lap_records[-2]["lap_time"]
            if last_delta > 0.1:
                performance_trend = "DETERIORATING"
            elif last_delta < -0.1:
                performance_trend = "IMPROVING"
            else:
                performance_trend = "STABLE"

        # Consecutive deteriorating performance
        for i in range(len(lap_records) - 1, 0, -1):
            if lap_records[i]["lap_time"] > lap_records[i - 1]["lap_time"]:
                consecutive_deteriorating_performance += 1
            else:
                break

    # Correlation Analysis
    correlation = None
    correlation_strength = None
    association = "Building temporal picture…"

    paired_stresses = [lr["stress"] for lr in lap_records]
    paired_laps = [lr["lap_time"] for lr in lap_records]

    if len(paired_stresses) >= MIN_CORRELATION_POINTS:
        r = pearson_correlation(paired_stresses, paired_laps)
        if r is not None:
            correlation = r
            abs_r = abs(r)
            if abs_r >= 0.7:
                correlation_strength = "STRONG"
            elif abs_r >= 0.4:
                correlation_strength = "MODERATE"
            elif abs_r >= 0.2:
                correlation_strength = "WEAK"
            else:
                correlation_strength = "NONE"

            if r > 0.3:
                association = "Observed association: Stress and slower lap times are moving together in the observed samples."
            elif r < -0.3:
                association = "Observed association: Stress and faster lap times are moving together in the observed samples."
            else:
                association = "Observed association: No linear trend observed between stress and lap times."
        else:
            association = "Insufficient variance across samples to compute correlation."
    else:
        association = f"Insufficient paired data ({len(paired_stresses)}/{MIN_CORRELATION_POINTS} required) for correlation."

    return {
        "available": True,
        "sample_count": sample_count,
        "observation_count": sample_count,
        "current_lap": current_lap,
        "current_stress": current_stress,
        "previous_stress": previous_stress,
        "stress_change": stress_change,
        "stress_change_3_laps": stress_change_3_laps,
        "rolling_stress": rolling_stress,
        "stress_trend": stress_trend,
        "trend": stress_trend,  # Backward compatible key for recommendation engine
        "consecutive_rising_stress": consecutive_rising_stress,
        "sustained_stress": sustained_stress,
        "recent_stress": stresses[-3:],
        "current_lap_time": current_lap_time,
        "previous_lap_time": previous_lap_time,
        "rolling_lap_time": rolling_lap_time,
        "lap_time_delta": lap_time_delta,
        "performance_direction": performance_direction,
        "performance_trend": performance_trend,
        "consecutive_deteriorating_performance": consecutive_deteriorating_performance,
        "correlation": correlation,
        "correlation_strength": correlation_strength,
        "association": association,
        "stress_history": stresses[-4:],
    }


def analyze_temporal_stress(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Wrapper calling analyze_temporal_session for stress analysis."""
    return analyze_temporal_session(history)


def analyze_lap_performance(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Correlate stress against actual lap performance data when available."""
    lap_obs = [
        obs for obs in history
        if obs.get("lap") is not None and (obs.get("lap_time_seconds") is not None or obs.get("lap_time") is not None)
    ]

    if not lap_obs:
        return {
            "available": False,
            "reason": "No lap-time data available for this session",
        }

    laps_summary = []
    for obs in lap_obs:
        lt = obs.get("lap_time_seconds") if obs.get("lap_time_seconds") is not None else obs.get("lap_time")
        laps_summary.append({
            "lap": obs.get("lap"),
            "lap_time_seconds": float(lt) if lt is not None else None,
            "stress": obs.get("stress", obs.get("stress_index", 0)),
        })

    lap_time_delta_seconds = None
    stress_change = None
    if len(lap_obs) >= 2:
        curr_lt = lap_obs[-1].get("lap_time_seconds", lap_obs[-1].get("lap_time"))
        prev_lt = lap_obs[-2].get("lap_time_seconds", lap_obs[-2].get("lap_time"))
        if curr_lt is not None and prev_lt is not None:
            lap_time_delta_seconds = round(float(curr_lt) - float(prev_lt), 3)
        curr_s = lap_obs[-1].get("stress", lap_obs[-1].get("stress_index", 0))
        prev_s = lap_obs[-2].get("stress", lap_obs[-2].get("stress_index", 0))
        stress_change = curr_s - prev_s

    stresses = [obs.get("stress", obs.get("stress_index", 0)) for obs in lap_obs]
    lap_times = [float(obs.get("lap_time_seconds", obs.get("lap_time", 0))) for obs in lap_obs]

    correlation = None
    correlation_available = False
    corr_reason = None

    if len(lap_obs) >= MIN_CORRELATION_POINTS:
        r = pearson_correlation(stresses, lap_times)
        if r is not None:
            correlation = r
            correlation_available = True
        else:
            corr_reason = "Zero variance in stress or lap time observations"
    else:
        corr_reason = "Insufficient paired observations"

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
    stress_change: Optional[float],
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


def generate_engineering_insight(
    temporal: Dict[str, Any],
    lap_perf: Dict[str, Any],
    driver_state: Dict[str, Any],
) -> str:
    """Generate a deterministic decision support insight for the race engineer."""
    trend = temporal.get("trend", temporal.get("stress_trend", "INSUFFICIENT_DATA"))
    sustained = temporal.get("sustained_stress", False)
    issues = driver_state.get("issues", [])
    lap_delta = lap_perf.get("lap_time_delta_seconds") or temporal.get("lap_time_delta")

    if (sustained or driver_state.get("stress", 0) >= 70) and issues:
        issues_str = ", ".join(issues[:2])
        return f"Sustained high driver stress coincides with reported vehicle concerns ({issues_str}). Consider pit-wall intervention."

    if trend == "RISING" and lap_delta is not None and lap_delta > 0.2:
        return "Sustained stress increased alongside slower lap times. Consider radio intervention."

    if (sustained or driver_state.get("stress", 0) >= 60) and (lap_delta is None or abs(lap_delta) <= 0.2):
        return "Driver stress is elevated, but lap performance remains stable. Continue monitoring."

    if driver_state.get("stress", 0) < 40 and (lap_delta is None or lap_delta <= 0.1):
        return "Driver stress and lap performance remain stable. No intervention recommended."

    if trend == "RISING":
        return "Driver stress trend is rising across recent communications. Monitor closely."
    elif trend == "FALLING":
        return "Driver stress levels are stabilizing. Maintain stint plan."

    return "Session data baseline established. Awaiting further driver communications."
