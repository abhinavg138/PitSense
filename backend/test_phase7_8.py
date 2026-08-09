"""
test_phase7_8.py
----------------
Automated Test Suite for Phase 7 (Temporal Analysis) & Phase 8 (Decision Engine).
"""

import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.temporal_analysis import analyze_temporal_session
from ai.decision_engine import evaluate_engineer_decision
from dataset_loader import load_dataset_metadata, get_telemetry_for_file
from app import app
from fastapi.testclient import TestClient


def run_tests():
    print("\n==================================================")
    print("RUNNING PIT SENSE PHASE 7 & 8 AUTOMATED TEST SUITE")
    print("==================================================\n")

    results = []

    def log_result(test_name: str, passed: bool, details: str = ""):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {details}")
        results.append((test_name, passed, details))

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Backend import test
    # ─────────────────────────────────────────────────────────────────────────
    try:
        from app import app
        log_result("1. Backend Import Test", True, "app.py and all AI modules import cleanly")
    except Exception as e:
        log_result("1. Backend Import Test", False, f"Import error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Dataset loader test
    # ─────────────────────────────────────────────────────────────────────────
    try:
        meta = load_dataset_metadata()
        sample_tel = get_telemetry_for_file("lap_04.mp3")
        is_valid = sample_tel is not None and sample_tel.get("lap") == 4 and abs(sample_tel.get("lap_time", 0) - 99.17) < 1e-3
        log_result("2. Dataset Loader Test", is_valid, f"Loaded {len(meta)} metadata rows; lap_04 telemetry: {sample_tel.get('lap_time')}s")
    except Exception as e:
        log_result("2. Dataset Loader Test", False, f"Dataset error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Decision Engine Unit Tests (TEST A to TEST G)
    # ─────────────────────────────────────────────────────────────────────────

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
    passed_a = dec_a["severity"] == "CALM" and dec_a["decision"] == "NO_ACTION"
    log_result("TEST A (Low stress + stable pace)", passed_a, f"Severity: {dec_a['severity']} | Decision: {dec_a['decision']}")

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
    passed_b = dec_b["severity"] == "ELEVATED" and dec_b["decision"] in ["MONITOR", "MONITOR_PERFORMANCE"]
    log_result("TEST B (Moderate rising stress)", passed_b, f"Severity: {dec_b['severity']} | Decision: {dec_b['decision']}")

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
    passed_c = dec_c["severity"] == "STRESSED" and dec_c["decision"] == "RADIO_INTERVENTION"
    log_result("TEST C (High sustained stress + slower laps)", passed_c, f"Severity: {dec_c['severity']} | Decision: {dec_c['decision']}")

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
    passed_d = dec_d["severity"] == "CRITICAL" and dec_d["decision"] == "PIT_AND_INSPECT"
    log_result("TEST D (Critical stress + vehicle concern)", passed_d, f"Severity: {dec_d['severity']} | Decision: {dec_d['decision']}")

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
    passed_e = temp_e["available"] is True and dec_e["severity"] in ["CALM", "ELEVATED"]
    log_result("TEST E (Missing lap-time data)", passed_e, f"Available: {temp_e['available']} | Severity: {dec_e['severity']}")

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
    passed_f = temp_f["correlation"] is None and dec_f["confidence"] <= 0.55
    log_result("TEST F (Single sample confidence cap)", passed_f, f"Correlation: {temp_f['correlation']} | Confidence: {dec_f['confidence']}")

    # TEST G: duplicate lap numbers -> handles gracefully
    records_g = [
        {"lap": 52, "lap_time_seconds": 97.299, "stress": 60, "confidence": 0.85},
        {"lap": 52, "lap_time_seconds": 97.299, "stress": 64, "confidence": 0.85},
    ]
    temp_g = analyze_temporal_session(records_g)
    passed_g = temp_g["available"] is True and temp_g["sample_count"] == 2
    log_result("TEST G (Duplicate lap number handling)", passed_g, f"Sample count: {temp_g['sample_count']} | Stress change: {temp_g['stress_change']}")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Full API POST /upload Integration Test
    # ─────────────────────────────────────────────────────────────────────────
    try:
        client = TestClient(app)
        audio_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset", "audio", "lap_04.mp3"))
        with open(audio_path, "rb") as f:
            res = client.post("/upload", files={"file": ("lap_04.mp3", f, "audio/mp3")})

        data = res.json()

        req_keys = [
            "success", "filename", "telemetry", "transcript", "emotion",
            "driver_analysis", "ai_summary", "engineer_reply", "ai_source",
            "audio_emotion", "stress_index", "temporal_analysis",
            "engineer_decision", "lap_performance", "engineering_insight"
        ]

        missing_keys = [k for k in req_keys if k not in data]
        passed_api = (res.status_code == 200) and (len(missing_keys) == 0)

        details_api = f"HTTP {res.status_code} | Decision: {data.get('engineer_decision', {}).get('decision')} | Severity: {data.get('engineer_decision', {}).get('severity')}"
        if missing_keys:
            details_api += f" | Missing keys: {missing_keys}"

        log_result("4. Full /upload API Test", passed_api, details_api)
    except Exception as e:
        log_result("4. Full /upload API Test", False, f"API test error: {e}")

    # Summary
    total_passed = sum(1 for _, p, _ in results if p)
    total_tests = len(results)
    overall_status = "ALL PASS" if total_passed == total_tests else "FAILURES DETECTED"

    print("\n==================================================")
    print(f"FINAL RESULT: {overall_status} ({total_passed}/{total_tests} passed)")
    print("==================================================\n")

    return total_passed == total_tests


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
