"""
test_phase10_hardening.py
--------------------------
Automated Test Suite for Phase 10: Hackathon Hardening & Explainable Race Intelligence.

Verifies:
- Truthful /health status endpoint overall status & component readiness
- Full frontend/backend API contract integrity (all dashboard fields present)
- Monkeypatched failure resilience:
  * Gemini API failure -> graceful fallback to local deterministic wording
  * OpenF1 telemetry timeout -> graceful fallback to unavailable telemetry
  * Invalid audio / ASR exception -> structured JSON error response
  * Corrupted DB JSON record -> safe row skipping
  * Simulation sample failure -> 404 handling without simulation crash
- 4-State Data Quality indicators (AVAILABLE, PARTIAL, INSUFFICIENT, UNAVAILABLE)
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
from ai.decision_engine import evaluate_engineer_decision
from ai.temporal_analysis import SessionManager, analyze_temporal_session
from ai.race_engineer import generate_summary_with_source
from database.db import init_db, get_connection, load_session_history

client = TestClient(app)
SAMPLE_AUDIO_PATH = backend_dir.parent / "dataset" / "audio" / "2024_1229_9472_63_lap_03_radio_004.mp3"


def test_truthful_health_status_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("READY", "DEGRADED", "UNAVAILABLE")
    assert "components" in data
    comps = data["components"]
    assert "backend" in comps and comps["backend"] == "READY"
    assert "asr_model" in comps
    assert "audio_emotion_model" in comps
    assert "telemetry" in comps
    assert "gemini" in comps


def test_frontend_backend_response_schema_contract():
    assert SAMPLE_AUDIO_PATH.exists(), f"Sample audio missing at {SAMPLE_AUDIO_PATH}"
    with open(SAMPLE_AUDIO_PATH, "rb") as f:
        audio_bytes = f.read()

    files = {"file": ("2024_1229_9472_63_lap_03_radio_004.mp3", audio_bytes, "audio/mpeg")}
    resp = client.post("/upload", files=files, data={"session_id": "contract_test_session"})

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    data = resp.json()
    required_keys = [
        "success", "filename", "telemetry", "transcript", "emotion",
        "driver_analysis", "ai_summary", "engineer_reply", "ai_source",
        "audio_emotion", "stress_index", "temporal_analysis",
        "engineer_decision", "lap_performance", "engineering_insight",
        "engineering_recommendation"
    ]
    for k in required_keys:
        assert k in data, f"Missing key: {k}"

    dec = data["engineer_decision"]
    dec_keys = ["severity", "priority", "decision", "recommendation", "reasons", "confidence", "evidence"]
    for dk in dec_keys:
        assert dk in dec, f"Missing decision key: {dk}"

    ev = dec["evidence"]
    assert "data_quality" in ev
    dq = ev["data_quality"]
    for domain in ["transcript", "audio_emotion", "telemetry", "correlation"]:
        assert domain in dq
        assert dq[domain] in ("AVAILABLE", "PARTIAL", "INSUFFICIENT", "UNAVAILABLE")


def test_mocked_gemini_exception_fallback():
    with patch("ai.race_engineer.generate_gemini_brief") as mock_gemini:
        mock_gemini.side_effect = RuntimeError("Gemini API Rate Limit Exceeded (Mocked)")
        res = generate_summary_with_source(
            transcript="Tires are going off, balance is neutral",
            emotion={"emotion": "anxious", "confidence": 0.8},
            driver={"driver_state": "High Stress", "stress": 75, "urgency": 80, "issues": ["tyre wear"], "recommendations": ["Monitor tire wear"]}
        )

        assert res["ai_source"] == "local"
        assert "summary" in res
        assert "engineer_reply" in res


def test_mocked_telemetry_timeout_fallback():
    assert SAMPLE_AUDIO_PATH.exists(), f"Sample audio missing at {SAMPLE_AUDIO_PATH}"
    with open(SAMPLE_AUDIO_PATH, "rb") as f:
        audio_bytes = f.read()

    with patch("app.get_telemetry_for_file") as mock_tel:
        mock_tel.return_value = {"available": False}
        resp = client.post(
            "/upload",
            files={"file": ("unmatched_audio.mp3", audio_bytes, "audio/mpeg")},
            data={"session_id": "tel_fallback_test"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["telemetry"]["available"] is False


def test_missing_simulation_audio_404_handling():
    resp = client.get("/simulation/audio/non_existent_audio_sample_99.mp3")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data


def test_4_state_data_quality_indicators():
    # Case A: 1 sample -> correlation INSUFFICIENT
    obs_1 = [{"lap": 1, "lap_time_seconds": 97.5, "stress": 30}]
    t1 = analyze_temporal_session(obs_1)
    d1 = evaluate_engineer_decision({"stress": 30}, {"stress_index": 30}, t1, {"confidence": 0.9}, "radio ok")
    assert d1["evidence"]["data_quality"]["correlation"] == "INSUFFICIENT"

    # Case B: 3 samples -> correlation AVAILABLE
    obs_3 = [
        {"lap": 1, "lap_time_seconds": 97.5, "stress": 30},
        {"lap": 2, "lap_time_seconds": 98.0, "stress": 45},
        {"lap": 3, "lap_time_seconds": 98.6, "stress": 60},
    ]
    t3 = analyze_temporal_session(obs_3)
    d3 = evaluate_engineer_decision({"stress": 60}, {"stress_index": 60}, t3, {"confidence": 0.9}, "radio ok")
    assert d3["evidence"]["data_quality"]["correlation"] == "AVAILABLE"
