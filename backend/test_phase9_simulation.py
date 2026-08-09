"""
test_phase9_simulation.py
--------------------------
Automated Test Suite for Phase 9:
- Race Simulation Mode & Dataset Sample Discovery
- Integration Verification across Phases 1–8
- Failure-Handling & Edge Case Resilience Tests
"""

import sys
import os
import tempfile

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app import app
from dataset_loader import get_simulation_samples, load_dataset_metadata, get_telemetry_for_file
from ai.temporal_analysis import analyze_temporal_session, session_manager
from ai.decision_engine import evaluate_engineer_decision
from ai.race_engineer import generate_summary_with_source

client = TestClient(app)


def run_phase9_tests():
    print("\n==================================================")
    print("RUNNING PIT SENSE PHASE 9 AUTOMATED TEST SUITE")
    print("==================================================\n")

    results = []

    def log_result(test_name: str, passed: bool, details: str = ""):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {details}")
        results.append((test_name, passed, details))

    # 1. Endpoint Check
    try:
        res = client.get("/simulation/samples")
        assert res.status_code == 200
        samples = res.json()
        assert isinstance(samples, list)
        log_result("1. GET /simulation/samples", True, f"Discovered {len(samples)} valid dataset samples")
    except Exception as e:
        log_result("1. GET /simulation/samples", False, str(e))

    # 2. Dynamic Discovery Verification
    try:
        discovered = get_simulation_samples()
        assert len(discovered) > 0
        first_sample = discovered[0]
        assert "filename" in first_sample
        assert "lap" in first_sample
        log_result("2. Dataset Discovery Test", True, f"First sample: {first_sample['filename']} | Lap: {first_sample['lap']}")
    except Exception as e:
        log_result("2. Dataset Discovery Test", False, str(e))

    # 3. Audio File Serving Endpoint
    try:
        if discovered:
            sample_filename = discovered[0]["filename"]
            audio_res = client.get(f"/simulation/audio/{sample_filename}")
            assert audio_res.status_code == 200
            assert len(audio_res.content) > 0
            log_result("3. Audio Serving Endpoint Test", True, f"Streamed {len(audio_res.content)} bytes for {sample_filename}")
        else:
            log_result("3. Audio Serving Endpoint Test", False, "No discovered samples to test audio serving")
    except Exception as e:
        log_result("3. Audio Serving Endpoint Test", False, str(e))

    # 4. Simulation Session Step Test
    try:
        session_manager.reset_session("test_sim_session")
        sample_audio = "lap_04.mp3"
        audio_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "audio", sample_audio)

        if os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                res = client.post(
                    "/upload",
                    files={"file": (sample_audio, f, "audio/mpeg")},
                    data={"session_id": "test_sim_session", "lap": "4", "lap_time_seconds": "99.17"}
                )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert "engineer_decision" in data
            assert "temporal_analysis" in data
            log_result("4. Simulation /upload Step Test", True, f"Decision: {data['engineer_decision']['decision']}")
        else:
            log_result("4. Simulation /upload Step Test", False, f"{sample_audio} not found on disk")
    except Exception as e:
        log_result("4. Simulation /upload Step Test", False, str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # FAILURE & EDGE-CASE HANDLING TESTS
    # ─────────────────────────────────────────────────────────────────────────

    # TEST A: Missing audio file gracefully handled by sample endpoint
    try:
        res_missing = client.get("/simulation/audio/non_existent_file_12345.mp3")
        assert res_missing.status_code == 404
        log_result("TEST A (Missing audio file 404 response)", True, "Returns HTTP 404 gracefully")
    except Exception as e:
        log_result("TEST A (Missing audio file 404 response)", False, str(e))

    # TEST B: Missing lap-time metadata
    try:
        recs_no_lap = [{"stress": 40, "confidence": 0.9}]
        temp_no_lap = analyze_temporal_session(recs_no_lap)
        assert temp_no_lap["available"] is True
        assert temp_no_lap["current_lap_time"] is None
        log_result("TEST B (Missing lap-time metadata)", True, "Lap performance gracefully marked unavailable")
    except Exception as e:
        log_result("TEST B (Missing lap-time metadata)", False, str(e))

    # TEST C: Empty transcript
    try:
        dec_empty = evaluate_engineer_decision(
            driver_state={"driver_state": "Calm", "stress": 20, "urgency": 10, "issues": []},
            stress_index={"stress_index": 20},
            temporal_analysis={"sample_count": 1, "stress_trend": "STABLE"},
            audio_emotion={"confidence": 0.8},
            transcript="",
        )
        assert dec_empty["severity"] == "CALM"
        log_result("TEST C (Empty transcript handling)", True, f"Severity: {dec_empty['severity']}")
    except Exception as e:
        log_result("TEST C (Empty transcript handling)", False, str(e))

    # TEST D: Single observation only
    try:
        recs_single = [{"lap": 10, "lap_time_seconds": 95.0, "stress": 30, "confidence": 0.9}]
        temp_single = analyze_temporal_session(recs_single)
        assert temp_single["available"] is True
        assert temp_single["sample_count"] == 1
        assert temp_single["correlation"] is None
        log_result("TEST D (Single observation correlation fallback)", True, f"Correlation: {temp_single['correlation']}")
    except Exception as e:
        log_result("TEST D (Single observation correlation fallback)", False, str(e))

    # TEST E: Multiple observations on same lap (duplicate lap handling)
    try:
        recs_dupe = [
            {"lap": 16, "lap_time_seconds": 97.168, "stress": 40, "confidence": 0.9},
            {"lap": 16, "lap_time_seconds": 96.683, "stress": 44, "confidence": 0.9},
        ]
        temp_dupe = analyze_temporal_session(recs_dupe)
        assert temp_dupe["sample_count"] == 2
        assert temp_dupe["stress_change"] == 4.0
        log_result("TEST E (Duplicate lap observations handling)", True, f"Sample count: {temp_dupe['sample_count']} | Stress change: {temp_dupe['stress_change']}")
    except Exception as e:
        log_result("TEST E (Duplicate lap observations handling)", False, str(e))

    # TEST F: Gemini unavailable / fallback to local deterministic response
    try:
        old_key = os.environ.get("GEMINI_API_KEY")
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        summary_fallback = generate_summary_with_source(
            "Box this lap",
            {"emotion": "Fear", "confidence": 90},
            {"driver_state": "High Stress", "stress": 75, "urgency": 70, "issues": [], "recommendations": []}
        )
        assert "summary" in summary_fallback
        assert summary_fallback["ai_source"] in ["deterministic_rule_engine", "gemini_flash", "local"]
        log_result("TEST F (Gemini fallback mode)", True, f"AI Source: {summary_fallback['ai_source']}")
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key
    except Exception as e:
        log_result("TEST F (Gemini fallback mode)", False, str(e))




    # TEST G: Empty dataset / missing file loader resilience
    try:
        fake_loader_res = load_dataset_metadata("non_existent_csv_path.csv")
        assert isinstance(fake_loader_res, dict)
        assert len(fake_loader_res) == 0
        log_result("TEST G (Missing dataset CSV handling)", True, "Returns empty dict without raising exception")
    except Exception as e:
        log_result("TEST G (Missing dataset CSV handling)", False, str(e))

    print("\n==================================================")
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print(f"PHASE 9 TEST SUITE RESULT: {passed_count}/{total_count} PASSED")
    print("==================================================\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = run_phase9_tests()
    sys.exit(0 if success else 1)
