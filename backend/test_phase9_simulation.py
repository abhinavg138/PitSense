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
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app import app
from dataset_loader import get_simulation_samples, load_dataset_metadata, get_telemetry_for_file
from ai.temporal_analysis import analyze_temporal_session, session_manager
from ai.decision_engine import evaluate_engineer_decision
from ai.race_engineer import generate_summary_with_source

client = TestClient(app)


def test_simulation_samples_endpoint():
    # 1. Endpoint Check
    res = client.get("/simulation/samples")
    assert res.status_code == 200
    samples = res.json()
    assert isinstance(samples, list)


def test_dataset_discovery():
    # 2. Dynamic Discovery Verification
    discovered = get_simulation_samples()
    assert len(discovered) > 0
    first_sample = discovered[0]
    assert "filename" in first_sample
    assert "lap" in first_sample


def test_audio_serving_endpoint():
    # 3. Audio File Serving Endpoint
    discovered = get_simulation_samples()
    assert len(discovered) > 0, "No discovered samples to test audio serving"
    sample_filename = discovered[0]["filename"]
    audio_res = client.get(f"/simulation/audio/{sample_filename}")
    assert audio_res.status_code == 200
    assert len(audio_res.content) > 0


def test_simulation_upload_step():
    # 4. Simulation Session Step Test
    session_manager.reset_session("test_sim_session")
    sample_audio = "lap_04.mp3"
    audio_path = backend_dir.parent / "dataset" / "audio" / sample_audio

    assert audio_path.exists(), f"{sample_audio} not found on disk at {audio_path}"
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


def test_missing_audio_file_404_response():
    # TEST A: Missing audio file gracefully handled by sample endpoint
    res_missing = client.get("/simulation/audio/non_existent_file_12345.mp3")
    assert res_missing.status_code == 404


def test_missing_lap_time_metadata():
    # TEST B: Missing lap-time metadata
    recs_no_lap = [{"stress": 40, "confidence": 0.9}]
    temp_no_lap = analyze_temporal_session(recs_no_lap)
    assert temp_no_lap["available"] is True
    assert temp_no_lap["current_lap_time"] is None


def test_empty_transcript_handling():
    # TEST C: Empty transcript
    dec_empty = evaluate_engineer_decision(
        driver_state={"driver_state": "Calm", "stress": 20, "urgency": 10, "issues": []},
        stress_index={"stress_index": 20},
        temporal_analysis={"sample_count": 1, "stress_trend": "STABLE"},
        audio_emotion={"confidence": 0.8},
        transcript="",
    )
    assert dec_empty["severity"] == "CALM"


def test_single_observation_correlation_fallback():
    # TEST D: Single observation only
    recs_single = [{"lap": 10, "lap_time_seconds": 95.0, "stress": 30, "confidence": 0.9}]
    temp_single = analyze_temporal_session(recs_single)
    assert temp_single["available"] is True
    assert temp_single["sample_count"] == 1
    assert temp_single["correlation"] is None


def test_duplicate_lap_observations_handling():
    # TEST E: Multiple observations on same lap (duplicate lap handling)
    recs_dupe = [
        {"lap": 16, "lap_time_seconds": 97.168, "stress": 40, "confidence": 0.9},
        {"lap": 16, "lap_time_seconds": 96.683, "stress": 44, "confidence": 0.9},
    ]
    temp_dupe = analyze_temporal_session(recs_dupe)
    assert temp_dupe["sample_count"] == 2
    assert temp_dupe["stress_change"] == 4.0


def test_gemini_fallback_mode():
    # TEST F: Gemini unavailable / fallback to local deterministic response
    old_key = os.environ.get("GEMINI_API_KEY")
    try:
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        summary_fallback = generate_summary_with_source(
            "Box this lap",
            {"emotion": "Fear", "confidence": 90},
            {"driver_state": "High Stress", "stress": 75, "urgency": 70, "issues": [], "recommendations": []}
        )
        assert "summary" in summary_fallback
        assert summary_fallback["ai_source"] in ["deterministic_rule_engine", "gemini_flash", "local"]
    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key


def test_missing_dataset_csv_handling():
    # TEST G: Empty dataset / missing file loader resilience
    fake_loader_res = load_dataset_metadata("non_existent_csv_path.csv")
    assert isinstance(fake_loader_res, dict)
    assert len(fake_loader_res) == 0
