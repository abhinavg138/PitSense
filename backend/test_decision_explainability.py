import pytest
from ai.decision_engine import evaluate_engineer_decision, VALID_DECISIONS

def test_decision_engine_outcomes():
    # 1. NO_ACTION (Calm driver, low stress)
    d1 = evaluate_engineer_decision(
        driver_state={"driver_state": "Calm", "stress": 20, "urgency": 10, "issues": []},
        stress_index={"stress_index": 20, "stress_state": "CALM", "stress_signals": {"vocal": 15, "speech": 20, "transcript": 0}},
        temporal_analysis={"sample_count": 4, "stress_trend": "STABLE", "performance_direction": "STABLE", "data_quality": {"telemetry": "AVAILABLE", "correlation": "AVAILABLE"}},
        audio_emotion={"confidence": 0.90},
        transcript="All good on this lap.",
    )
    assert d1["decision"] in VALID_DECISIONS
    assert d1["decision"] == "NO_ACTION"
    assert d1["evidence"]["data_quality"]["acoustic_analysis"] == "AVAILABLE"
    assert d1["evidence"]["data_quality"]["temporal_history"] == "AVAILABLE"

    # 2. MONITOR_PERFORMANCE (Elevated stress, slower lap)
    d2 = evaluate_engineer_decision(
        driver_state={"driver_state": "Concerned", "stress": 55, "urgency": 40, "issues": []},
        stress_index={"stress_index": 55, "stress_state": "ELEVATED", "stress_signals": {"vocal": 50, "speech": 60, "transcript": 10}},
        temporal_analysis={"sample_count": 3, "stress_trend": "STABLE", "performance_direction": "SLOWER", "lap_time_delta": 0.35, "data_quality": {"telemetry": "AVAILABLE", "correlation": "AVAILABLE"}},
        audio_emotion={"confidence": 0.85},
        transcript="Struggling a bit with rear stability.",
    )
    assert d2["decision"] in VALID_DECISIONS
    assert d2["decision"] == "MONITOR_PERFORMANCE"

    # 3. MONITOR (Elevated stress, stable lap)
    d3 = evaluate_engineer_decision(
        driver_state={"driver_state": "Concerned", "stress": 50, "urgency": 30, "issues": []},
        stress_index={"stress_index": 50, "stress_state": "ELEVATED", "stress_signals": {"vocal": 45, "speech": None, "transcript": 10}},
        temporal_analysis={"sample_count": 2, "stress_trend": "RISING", "performance_direction": "STABLE", "data_quality": {"telemetry": "UNAVAILABLE", "correlation": "INSUFFICIENT"}},
        audio_emotion={"confidence": 0.80},
        transcript="Traffic ahead.",
    )
    assert d3["decision"] in VALID_DECISIONS
    assert d3["decision"] == "MONITOR"
    assert d3["evidence"]["data_quality"]["acoustic_analysis"] == "UNAVAILABLE"
    assert d3["evidence"]["data_quality"]["temporal_history"] == "AVAILABLE"

    # 4. CHECK_DRIVER (High stress, stable lap, no vehicle issue)
    d4 = evaluate_engineer_decision(
        driver_state={"driver_state": "High Stress", "stress": 72, "urgency": 60, "issues": []},
        stress_index={"stress_index": 72, "stress_state": "STRESSED", "stress_signals": {"vocal": 75, "speech": 70, "transcript": 20}},
        temporal_analysis={"sample_count": 1, "stress_trend": "STABLE", "performance_direction": "STABLE", "data_quality": {"telemetry": "UNAVAILABLE", "correlation": "UNAVAILABLE"}},
        audio_emotion={"confidence": 0.88},
        transcript="Pushing hard, lots of traffic.",
    )
    assert d4["decision"] in VALID_DECISIONS
    assert d4["decision"] == "CHECK_DRIVER"
    assert d4["evidence"]["data_quality"]["temporal_history"] == "PARTIAL"

    # 5. CHECK_VEHICLE (High stress, vehicle issue reported)
    d5 = evaluate_engineer_decision(
        driver_state={"driver_state": "High Stress", "stress": 70, "urgency": 65, "issues": ["Vibration"]},
        stress_index={"stress_index": 70, "stress_state": "STRESSED", "stress_signals": {"vocal": 70, "speech": 65, "transcript": 20}},
        temporal_analysis={"sample_count": 3, "stress_trend": "RISING", "performance_direction": "STABLE", "data_quality": {"telemetry": "PARTIAL", "correlation": "AVAILABLE"}},
        audio_emotion={"confidence": 0.82},
        transcript="I have a strange vibration in turn 4.",
    )
    assert d5["decision"] in VALID_DECISIONS
    assert d5["decision"] == "CHECK_VEHICLE"

    # 6. RADIO_INTERVENTION (Stressed & slower performance without vehicle damage)
    d6 = evaluate_engineer_decision(
        driver_state={"driver_state": "High Stress", "stress": 75, "urgency": 70, "issues": []},
        stress_index={"stress_index": 75, "stress_state": "STRESSED", "stress_signals": {"vocal": 75, "speech": 80, "transcript": 20}},
        temporal_analysis={"sample_count": 3, "stress_trend": "RISING", "performance_direction": "SLOWER", "lap_time_delta": 0.65, "data_quality": {"telemetry": "AVAILABLE", "correlation": "AVAILABLE"}},
        audio_emotion={"confidence": 0.90},
        transcript="Pushing hard, lost time in sector 2.",
    )
    assert d6["decision"] in VALID_DECISIONS
    assert d6["decision"] == "RADIO_INTERVENTION"

    # 7. PIT_AND_INSPECT (Critical stress / damage reported)
    d7 = evaluate_engineer_decision(
        driver_state={"driver_state": "Emergency", "stress": 88, "urgency": 90, "issues": ["Vehicle Damage"]},
        stress_index={"stress_index": 88, "stress_state": "CRITICAL", "stress_signals": {"vocal": 90, "speech": 85, "transcript": 40}},
        temporal_analysis={"sample_count": 4, "stress_trend": "RISING", "performance_direction": "SLOWER", "lap_time_delta": 1.25, "data_quality": {"telemetry": "AVAILABLE", "correlation": "AVAILABLE"}},
        audio_emotion={"confidence": 0.95},
        transcript="I hit something, tire is flat, box this lap!",
    )
    assert d7["decision"] in VALID_DECISIONS
    assert d7["decision"] == "PIT_AND_INSPECT"

print("All 7 decision outcomes verified successfully!")
