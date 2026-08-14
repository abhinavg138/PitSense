"""
test_session_isolation.py
-------------------------
Automated Test Suite for Fresh Session Isolation & Multi-Session Independence.

Verifies:
1. Fresh sessions start with 0 observations and return INSUFFICIENT_DATA temporal status.
2. Previous session observations do NOT leak into a new fresh session ID.
3. Stress history, stress trends, lap performance history, and correlation do NOT carry over across sessions.
4. Old sessions remain preserved and fully restorable from SQLite.
5. Race Simulation sessions operate in isolated session IDs without contaminating manual sessions.
6. Targeted session reset only clears the specified session.
"""

import sys
import os
from pathlib import Path
import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database.db import (
    init_db,
    save_observation,
    load_session_history,
    load_all_sessions,
    delete_session_history,
    clear_all_session_history,
    get_active_session_id,
    set_active_session_id,
)
from ai.temporal_analysis import SessionManager, analyze_temporal_session, analyze_lap_performance


@pytest.fixture(scope="module")
def isolation_db(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("pitsense_session_isolation")
    db_path = str(temp_dir / "test_isolation.db")
    os.environ["PITSENSE_DB_PATH"] = db_path
    init_db(db_path)
    yield db_path
    if "PITSENSE_DB_PATH" in os.environ:
        del os.environ["PITSENSE_DB_PATH"]


def test_01_fresh_session_initializes_empty(isolation_db):
    sm = SessionManager(db_path=isolation_db)
    fresh_session_id = "session_fresh_test_01"
    
    # History must be completely empty
    history = sm.get_history(fresh_session_id)
    assert len(history) == 0

    # Temporal analysis on fresh empty session
    temporal = analyze_temporal_session(history)
    assert temporal["available"] is False
    assert temporal["sample_count"] == 0
    assert temporal["trend"] == "INSUFFICIENT_DATA"
    assert temporal["stress_trend"] == "STABLE"


def test_02_session_isolation_no_data_leakage(isolation_db):
    sm = SessionManager(db_path=isolation_db)
    session_a = "session_driver_verstappen_stint1"
    session_b = "session_fresh_analysis_stint2"

    # Add 3 high-stress deteriorating observations to Session A
    obs_a1 = {
        "timestamp": "2026-05-24T14:01:00",
        "filename": "lap_01.mp3",
        "stress": 75.0,
        "stress_state": "High Stress",
        "confidence": 0.92,
        "lap": 10,
        "lap_time_seconds": 92.5,
        "telemetry": {"available": True, "speed": 310},
        "issues": ["Oversteer in turn 4"],
    }
    obs_a2 = {
        "timestamp": "2026-05-24T14:02:30",
        "filename": "lap_02.mp3",
        "stress": 85.0,
        "stress_state": "High Stress",
        "confidence": 0.95,
        "lap": 11,
        "lap_time_seconds": 93.8,
        "telemetry": {"available": True, "speed": 305},
        "issues": ["Braking instability"],
    }
    obs_a3 = {
        "timestamp": "2026-05-24T14:04:00",
        "filename": "lap_03.mp3",
        "stress": 92.0,
        "stress_state": "Emergency",
        "confidence": 0.98,
        "lap": 12,
        "lap_time_seconds": 95.2,
        "telemetry": {"available": True, "speed": 298},
        "issues": ["Tyre degradation"],
    }

    sm.add_observation(session_a, obs_a1)
    sm.add_observation(session_a, obs_a2)
    sm.add_observation(session_a, obs_a3)

    # Verify Session A temporal metrics
    history_a = sm.get_history(session_a)
    assert len(history_a) == 3
    temporal_a = analyze_temporal_session(history_a)
    assert temporal_a["sample_count"] == 3
    assert temporal_a["stress_trend"] == "RISING"
    assert temporal_a["sustained_stress"] is True
    assert temporal_a["performance_trend"] in ("DETERIORATING", "SLOWER")

    # Now verify Fresh Session B before any uploads
    history_b = sm.get_history(session_b)
    assert len(history_b) == 0

    # Add 1 calm observation to Fresh Session B
    obs_b1 = {
        "timestamp": "2026-05-24T15:00:00",
        "filename": "fresh_lap_01.mp3",
        "stress": 22.0,
        "stress_state": "Calm",
        "confidence": 0.88,
        "lap": 1,
        "lap_time_seconds": 90.1,
        "telemetry": {"available": True, "speed": 320},
        "issues": [],
    }
    sm.add_observation(session_b, obs_b1)

    # Verify Session B temporal analysis is 100% isolated:
    # 1. Observation count must be exactly 1
    # 2. Previous rising stress from Session A must NOT carry over
    # 3. Sustained stress must be False
    # 4. Correlation must be None / insufficient data
    history_b_after = sm.get_history(session_b)
    assert len(history_b_after) == 1
    temporal_b = analyze_temporal_session(history_b_after)
    assert temporal_b["sample_count"] == 1
    assert temporal_b["stress_trend"] == "STABLE"
    assert temporal_b["sustained_stress"] is False
    assert temporal_b["correlation"] is None
    assert temporal_b["performance_trend"] == "STABLE"

    # Verify Session A is STILL intact with all 3 observations
    history_a_recheck = sm.get_history(session_a)
    assert len(history_a_recheck) == 3
    assert history_a_recheck[-1]["stress"] == 92.0


def test_03_simulation_session_isolation(isolation_db):
    sm = SessionManager(db_path=isolation_db)
    user_session = "manual_analysis_session_01"
    sim_session = "sim_session_replay_01"

    # Add manual user observation
    obs_user = {
        "timestamp": "2026-05-24T16:00:00",
        "filename": "manual_radio.wav",
        "stress": 45.0,
        "stress_state": "Calm",
        "confidence": 0.90,
        "lap": 5,
        "lap_time_seconds": 91.5,
    }
    sm.add_observation(user_session, obs_user)

    # Add simulation observation
    obs_sim = {
        "timestamp": "2026-05-24T16:05:00",
        "filename": "lap_04.mp3",
        "stress": 80.0,
        "stress_state": "High Stress",
        "confidence": 0.95,
        "lap": 4,
        "lap_time_seconds": 99.17,
    }
    sm.add_observation(sim_session, obs_sim)

    assert len(sm.get_history(user_session)) == 1
    assert len(sm.get_history(sim_session)) == 1
    assert sm.get_history(user_session)[0]["filename"] == "manual_radio.wav"
    assert sm.get_history(sim_session)[0]["filename"] == "lap_04.mp3"


def test_04_targeted_session_reset_preserves_other_sessions(isolation_db):
    sm = SessionManager(db_path=isolation_db)
    session_to_reset = "session_temp_throwaway"
    session_to_keep = "session_valuable_history"

    sm.add_observation(session_to_reset, {"filename": "temp.mp3", "stress": 50, "lap": 1})
    sm.add_observation(session_to_keep, {"filename": "keep.mp3", "stress": 30, "lap": 1})

    assert len(sm.get_history(session_to_reset)) == 1
    assert len(sm.get_history(session_to_keep)) == 1

    # Reset ONLY the temporary session
    sm.reset_session(session_to_reset)

    assert len(sm.get_history(session_to_reset)) == 0
    assert len(sm.get_history(session_to_keep)) == 1
    assert load_session_history(session_to_keep, db_path=isolation_db)[0]["filename"] == "keep.mp3"
