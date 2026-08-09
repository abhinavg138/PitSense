"""
temporal_analysis.py
--------------------
Phase 7 — Temporal Stress & Lap-Time Correlation Engine

Calculates:
- Current vs previous stress & 3-lap stress change
- Rolling stress average & stress trend (RISING / FALLING / STABLE)
- Consecutive rising stress count
- Rolling lap-time baseline & lap-time delta vs baseline (+0.42s = SLOWER)
- Performance direction (SLOWER / FASTER / STABLE) & performance trend (DETERIORATING / IMPROVING / STABLE)
- Consecutive deteriorating performance count
- Pearson correlation coefficient & strength (STRONG / MODERATE / WEAK / NONE)
- Observational association statement (strictly non-causal language)
"""

import math
from typing import Dict, List, Optional, Any

# Configurable Thresholds
STRESS_TREND_THRESHOLD = 5       # abs(stress_change) >= 5 triggers RISING/FALLING
PERFORMANCE_TREND_THRESHOLD = 0.2 # abs(lap_delta) >= 0.2s triggers SLOWER/FASTER
MIN_CORRELATION_POINTS = 3       # minimum paired observations for Pearson correlation


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
    Performs Phase 7 temporal analysis across a session's history records.

    Each record expects:
    - lap (int or None)
    - lap_time_seconds (float or None) or lap_time
    - stress (int/float)
    - confidence (float)
    - timestamp (str)
    """
    sample_count = len(records)

    if sample_count == 0:
        return {
            "available": False,
            "sample_count": 0,
            "reason": "Building temporal picture…",
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
        "current_lap": current_lap,
        "current_stress": current_stress,
        "previous_stress": previous_stress,
        "stress_change": stress_change,
        "stress_change_3_laps": stress_change_3_laps,
        "rolling_stress": rolling_stress,
        "stress_trend": stress_trend,
        "consecutive_rising_stress": consecutive_rising_stress,
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
