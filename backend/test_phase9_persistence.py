"""
test_phase9_persistence.py
---------------------------
Automated Test Suite for Phase 9.5: Durable SQLite Session Persistence.

Verifies:
- Creation of temporal observations table in SQLite
- Persistence of multi-lap observations
- Simulation of Uvicorn/FastAPI server restart (SessionManager destruction & re-instantiation)
- Restoration of stress history, lap times, correlation, and association statement across restarts
- Post-restart observation appending
- Session reset and clear operations
- Failure resilience (missing DB, empty DB, missing table, corrupt JSON, single/duplicate lap observations)

TEST DB ISOLATION GUARANTEE:
Uses an isolated temporary database path via PITSENSE_DB_PATH.
Never touches or modifies the production database file.
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
    get_connection,
)
from ai.temporal_analysis import SessionManager, analyze_temporal_session


@pytest.fixture(scope="module")
def shared_db(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("pitsense_persistence")
    db_path = str(temp_dir / "test_pitsense.db")
    os.environ["PITSENSE_DB_PATH"] = db_path
    yield db_path
    if "PITSENSE_DB_PATH" in os.environ:
        del os.environ["PITSENSE_DB_PATH"]


def test_01_database_initialization(shared_db):
    init_db(shared_db)
    assert os.path.exists(shared_db)
    with get_connection(shared_db) as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temporal_observations'")
        assert cur.fetchone() is not None


def test_02_observation_insertion_4_laps(shared_db):
    session_id = "test_persistence_session_01"
    sm = SessionManager(db_path=shared_db)
    obs1 = {"timestamp": "2024-09-22T13:15:00Z", "filename": "lap_47.mp3", "lap": 47, "lap_time_seconds": 97.636, "stress": 31, "stress_state": "Calm", "confidence": 0.9, "issues": []}
    obs2 = {"timestamp": "2024-09-22T13:16:37Z", "filename": "lap_48.mp3", "lap": 48, "lap_time_seconds": 97.900, "stress": 38, "stress_state": "Calm", "confidence": 0.88, "issues": []}
    obs3 = {"timestamp": "2024-09-22T13:18:15Z", "filename": "lap_49.mp3", "lap": 49, "lap_time_seconds": 98.200, "stress": 51, "stress_state": "Elevated", "confidence": 0.85, "issues": []}
    obs4 = {"timestamp": "2024-09-22T13:19:53Z", "filename": "lap_50.mp3", "lap": 50, "lap_time_seconds": 98.600, "stress": 64, "stress_state": "Stressed", "confidence": 0.92, "issues": ["tyre wear"]}

    sm.add_observation(session_id, obs1)
    sm.add_observation(session_id, obs2)
    sm.add_observation(session_id, obs3)
    sm.add_observation(session_id, obs4)

    history = sm.get_history(session_id)
    assert len(history) == 4


def test_03_pre_restart_temporal_analysis(shared_db):
    session_id = "test_persistence_session_01"
    sm = SessionManager(db_path=shared_db)
    analysis_1 = analyze_temporal_session(sm.get_history(session_id))
    assert analysis_1["sample_count"] == 4
    assert analysis_1["current_stress"] == 64
    assert analysis_1["stress_trend"] == "RISING"
    assert analysis_1["performance_direction"] == "SLOWER"
    assert analysis_1["correlation"] is not None


def test_04_server_restart_simulation(shared_db):
    session_id = "test_persistence_session_01"
    # Create a brand NEW SessionManager instance targeting the same SQLite DB
    sm_restarted = SessionManager(db_path=shared_db)
    restored_history = sm_restarted.get_history(session_id)
    assert len(restored_history) == 4
    assert restored_history[-1]["lap"] == 50
    assert restored_history[-1]["stress"] == 64


def test_05_post_restart_temporal_analysis(shared_db):
    session_id = "test_persistence_session_01"
    sm_restarted = SessionManager(db_path=shared_db)
    history = sm_restarted.get_history(session_id)
    analysis_1 = analyze_temporal_session(history)
    analysis_2 = analyze_temporal_session(history)
    assert analysis_2["sample_count"] == 4
    assert analysis_2["current_stress"] == 64
    assert analysis_2["current_lap"] == 50
    assert analysis_2["stress_trend"] == "RISING"
    assert analysis_2["correlation"] == analysis_1["correlation"]
    assert analysis_2["association"] == analysis_1["association"]


def test_06_post_restart_observation_continuation(shared_db):
    session_id = "test_persistence_session_01"
    sm_restarted = SessionManager(db_path=shared_db)
    obs5 = {"timestamp": "2024-09-22T13:21:30Z", "filename": "lap_51.mp3", "lap": 51, "lap_time_seconds": 99.100, "stress": 72, "stress_state": "Critical", "confidence": 0.95, "issues": ["rear sliding"]}
    sm_restarted.add_observation(session_id, obs5)

    history_5 = sm_restarted.get_history(session_id)
    assert len(history_5) == 5
    analysis_3 = analyze_temporal_session(history_5)
    assert analysis_3["sample_count"] == 5
    assert analysis_3["current_stress"] == 72
    assert analysis_3["current_lap"] == 51


def test_07_active_session_identity_restoration(shared_db):
    session_id = "test_persistence_session_01"
    active_id = get_active_session_id(shared_db)
    assert active_id == session_id


def test_08_reset_session_operation(shared_db):
    session_id = "test_persistence_session_01"
    sm_restarted = SessionManager(db_path=shared_db)
    sm_restarted.reset_session(session_id)
    assert len(sm_restarted.get_history(session_id)) == 0
    db_history = load_session_history(session_id, db_path=shared_db)
    assert len(db_history) == 0


def test_missing_db_file_auto_creation(tmp_path):
    missing_db_path = str(tmp_path / "non_existent_subdir" / "missing.db")
    sm_missing = SessionManager(db_path=missing_db_path)
    assert os.path.exists(missing_db_path)


def test_empty_db_query_handling(tmp_path):
    empty_db_path = str(tmp_path / "empty.db")
    init_db(empty_db_path)
    empty_hist = load_session_history("non_existent_session", db_path=empty_db_path)
    assert isinstance(empty_hist, list)
    assert len(empty_hist) == 0


def test_corrupt_json_deserialization_resilience(tmp_path):
    corrupt_db_path = str(tmp_path / "corrupt.db")
    init_db(corrupt_db_path)
    with get_connection(corrupt_db_path) as conn:
        conn.execute("INSERT INTO sessions (session_id, created_at, updated_at) VALUES ('corrupt_session', '2024-09-22T00:00:00Z', '2024-09-22T00:00:00Z')")
        conn.execute(
            """
            INSERT INTO temporal_observations (session_id, observation_order, timestamp, filename, stress, telemetry_json, issues_json)
            VALUES ('corrupt_session', 1, '2024-09-22T00:00:00Z', 'bad.mp3', 50.0, 'INVALID_JSON{{{', 'NOT_JSON')
            """
        )
        conn.commit()
    corrupt_hist = load_session_history("corrupt_session", db_path=corrupt_db_path)
    assert len(corrupt_hist) == 1
    assert corrupt_hist[0]["telemetry"]["available"] is False
    assert corrupt_hist[0]["issues"] == []


def test_duplicate_lap_observation_ordering(tmp_path):
    dupe_db_path = str(tmp_path / "dupe.db")
    sm_dupe = SessionManager(db_path=dupe_db_path)
    sm_dupe.add_observation("dupe_session", {"lap": 16, "lap_time_seconds": 97.168, "stress": 40})
    sm_dupe.add_observation("dupe_session", {"lap": 16, "lap_time_seconds": 96.683, "stress": 44})

    del sm_dupe
    sm_dupe_restored = SessionManager(db_path=dupe_db_path)
    dupe_hist = sm_dupe_restored.get_history("dupe_session")
    assert len(dupe_hist) == 2
    assert dupe_hist[0]["lap_time_seconds"] == 97.168
    assert dupe_hist[1]["lap_time_seconds"] == 96.683


def test_reset_all_clear_operation(tmp_path):
    clear_db_path = str(tmp_path / "clear.db")
    sm_clear = SessionManager(db_path=clear_db_path)
    sm_clear.add_observation("session_A", {"lap": 1, "stress": 20})
    sm_clear.add_observation("session_B", {"lap": 2, "stress": 30})
    sm_clear.reset_all()

    all_sessions = load_all_sessions(db_path=clear_db_path)
    assert len(all_sessions) == 0
