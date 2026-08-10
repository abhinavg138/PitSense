"""
test_phase7_8.py
----------------
Pytest suite for Phase 7 (Temporal Analysis) & Phase 8 (Decision Engine).
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ai.temporal_analysis import analyze_temporal_session
from ai.decision_engine import evaluate_engineer_decision
from dataset_loader import load_dataset_metadata, get_telemetry_for_file
from app import app
from fastapi.testclient import TestClient

SAMPLE_AUDIO_PATH = backend_dir.parent / "dataset" / "audio" / "lap_04.mp3"


def test_backend_import():
    from app import app as loaded_app
    assert loaded_app is not None


def test_dataset_loader():
    meta = load_dataset_metadata()
    sample_tel = get_telemetry_for_file("lap_04.mp3")
    assert sample_tel is not None
    assert sample_tel.get("lap") == 4
    assert abs(sample_tel.get("lap_time", 0) - 99.17) < 1e-3
    assert len(meta) >= 1


def test_decision_engine_low_stress_stable_pace():
    # TEST A: low stress + stable lap times -> CALM / NO_ACTION
    records_a = [
        {"lap": 1, "lap_time_seconds": 95.0, "stress": 20, "confidence": 0.9},
        {"lap": 2, "lap_time_seconds": 95.1, "stress": 22, "confidence": 0.9},
    ]
    temp_a = analyze_temporal_session(records_a)
    dec_a = evaluate_engineer_decision(
        driver_state={"driver_state": "Calm", "stress": 22, "urgency": 10, "issues": []},
        stress_index={"stress_index": 22},
        temporal_analysis=temp_a,
        audio_emotion={"confidence": 90},
    )
    assert dec_a["severity"] == "CALM"
    assert dec_a["decision"] == "NO_ACTION"


def test_decision_engine_moderate_rising_stress():
    # TEST B: moderate rising stress -> ELEVATED / MONITOR
    records_b = [
        {"lap": 10, "lap_time_seconds": 92.0, "stress": 30, "confidence": 0.85},
        {"lap": 11, "lap_time_seconds": 92.2, "stress": 55, "confidence": 0.85},
    ]
    temp_b = analyze_temporal_session(records_b)
    dec_b = evaluate_engineer_decision(
        driver_state={"driver_state": "Concerned", "stress": 55, "urgency": 40, "issues": []},
        stress_index={"stress_index": 55},
        temporal_analysis=temp_b,
        audio_emotion={"confidence": 85},
    )
    assert dec_b["severity"] == "ELEVATED"
    assert dec_b["decision"] in ["MONITOR", "MONITOR_PERFORMANCE"]


def test_decision_engine_high_sustained_stress():
    # TEST C: high sustained stress + slower laps -> STRESSED / RADIO_INTERVENTION
    records_c = [
        {"lap": 20, "lap_time_seconds": 90.0, "stress": 55, "confidence": 0.88},
        {"lap": 21, "lap_time_seconds": 90.5, "stress": 65, "confidence": 0.88},
        {"lap": 22, "lap_time_seconds": 91.2, "stress": 75, "confidence": 0.88},
    ]
    temp_c = analyze_temporal_session(records_c)
    dec_c = evaluate_engineer_decision(
        driver_state={"driver_state": "High Stress", "stress": 75, "urgency": 65, "issues": []},
        stress_index={"stress_index": 75},
        temporal_analysis=temp_c,
        audio_emotion={"confidence": 88},
    )
    assert dec_c["severity"] == "STRESSED"
    assert dec_c["decision"] == "RADIO_INTERVENTION"


def test_decision_engine_critical_stress():
    # TEST D: critical stress + deteriorating lap + vehicle concern -> CRITICAL / PIT_AND_INSPECT
    records_d = [
        {"lap": 40, "lap_time_seconds": 95.0, "stress": 60, "confidence": 0.9},
        {"lap": 41, "lap_time_seconds": 96.5, "stress": 78, "confidence": 0.9},
        {"lap": 42, "lap_time_seconds": 98.2, "stress": 89, "confidence": 0.9},
    ]
    temp_d = analyze_temporal_session(records_d)
    dec_d = evaluate_engineer_decision(
        driver_state={"driver_state": "Emergency", "stress": 89, "urgency": 92, "issues": ["Severe Tyre Vibration"]},
        stress_index={"stress_index": 89},
        temporal_analysis=temp_d,
        audio_emotion={"confidence": 90},
        transcript="I have a terrible vibration on the front right tire",
    )
    assert dec_d["severity"] == "CRITICAL"
    assert dec_d["decision"] == "PIT_AND_INSPECT"


def test_decision_engine_missing_lap_time_data():
    # TEST E: missing lap-time data -> pipeline still works
    records_e = [
        {"lap": None, "lap_time_seconds": None, "stress": 40, "confidence": 0.8},
        {"lap": None, "lap_time_seconds": None, "stress": 48, "confidence": 0.8},
    ]
    temp_e = analyze_temporal_session(records_e)
    dec_e = evaluate_engineer_decision(
        driver_state={"driver_state": "Calm", "stress": 48, "urgency": 20, "issues": []},
        stress_index={"stress_index": 48},
        temporal_analysis=temp_e,
        audio_emotion={"confidence": 80},
    )
    assert temp_e["available"] is True
    assert dec_e["severity"] in ["CALM", "ELEVATED"]


def test_decision_engine_single_sample_confidence_cap():
    # TEST F: only one sample -> no fake correlation & capped confidence
    records_f = [
        {"lap": 4, "lap_time_seconds": 99.17, "stress": 33, "confidence": 0.9},
    ]
    temp_f = analyze_temporal_session(records_f)
    dec_f = evaluate_engineer_decision(
        driver_state={"driver_state": "Calm", "stress": 33, "urgency": 10, "issues": []},
        stress_index={"stress_index": 33},
        temporal_analysis=temp_f,
        audio_emotion={"confidence": 90},
    )
    assert temp_f["correlation"] is None
    assert dec_f["confidence"] <= 0.55


def test_decision_engine_duplicate_lap_handling():
    # TEST G: duplicate lap numbers -> handles gracefully
    records_g = [
        {"lap": 52, "lap_time_seconds": 97.299, "stress": 60, "confidence": 0.85},
        {"lap": 52, "lap_time_seconds": 97.299, "stress": 64, "confidence": 0.85},
    ]
    temp_g = analyze_temporal_session(records_g)
    assert temp_g["available"] is True
    assert temp_g["sample_count"] == 2


def test_full_upload_api():
    client = TestClient(app)
    assert SAMPLE_AUDIO_PATH.exists(), f"Sample audio missing at {SAMPLE_AUDIO_PATH}"
    with open(SAMPLE_AUDIO_PATH, "rb") as f:
        res = client.post("/upload", files={"file": ("lap_04.mp3", f, "audio/mp3")})

    assert res.status_code == 200
    data = res.json()

    req_keys = [
        "success", "filename", "telemetry", "transcript", "emotion",
        "driver_analysis", "ai_summary", "engineer_reply", "ai_source",
        "audio_emotion", "stress_index", "temporal_analysis",
        "engineer_decision", "lap_performance", "engineering_insight"
    ]

    missing_keys = [k for k in req_keys if k not in data]
    assert len(missing_keys) == 0, f"Missing required keys: {missing_keys}"
