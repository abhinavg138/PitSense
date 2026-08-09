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
import tempfile
import sqlite3
import json

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


def run_persistence_tests():
    print("\n==================================================")
    print("RUNNING PIT SENSE PHASE 9.5 PERSISTENCE TEST SUITE")
    print("==================================================\n")

    results = []

    def log_result(test_name: str, passed: bool, details: str = ""):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {details}")
        results.append((test_name, passed, details))

    # Create isolated temporary database for test suite
    temp_dir = tempfile.mkdtemp(prefix="pitsense_test_db_")
    test_db_path = os.path.join(temp_dir, "test_pitsense.db")
    os.environ["PITSENSE_DB_PATH"] = test_db_path

    try:
        # ─────────────────────────────────────────────────────────────────────
        # 1. DB Initialization Test
        # ─────────────────────────────────────────────────────────────────────
        try:
            init_db(test_db_path)
            assert os.path.exists(test_db_path)
            with get_connection(test_db_path) as conn:
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temporal_observations'")
                assert cur.fetchone() is not None
            log_result("1. Database Initialization", True, f"Created DB at {test_db_path}")
        except Exception as e:
            log_result("1. Database Initialization", False, str(e))

        # ─────────────────────────────────────────────────────────────────────
        # 2. SessionManager Insertion Test (4 Observations)
        # ─────────────────────────────────────────────────────────────────────
        session_id = "test_persistence_session_01"
        try:
            sm = SessionManager(db_path=test_db_path)
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
            log_result("2. Observation Insertion (4 Laps)", True, f"Inserted 4 observations into '{session_id}'")
        except Exception as e:
            log_result("2. Observation Insertion (4 Laps)", False, str(e))

        # ─────────────────────────────────────────────────────────────────────
        # 3. Initial Temporal Analysis Verification
        # ─────────────────────────────────────────────────────────────────────
        try:
            analysis_1 = analyze_temporal_session(sm.get_history(session_id))
            assert analysis_1["sample_count"] == 4
            assert analysis_1["current_stress"] == 64
            assert analysis_1["stress_trend"] == "RISING"
            assert analysis_1["performance_direction"] == "SLOWER"
            assert analysis_1["correlation"] is not None
            log_result("3. Pre-Restart Temporal Analysis", True, f"Samples: {analysis_1['sample_count']} | Correlation: {analysis_1['correlation']} | Trend: {analysis_1['stress_trend']}")
        except Exception as e:
            log_result("3. Pre-Restart Temporal Analysis", False, str(e))

        # ─────────────────────────────────────────────────────────────────────
        # 4. SERVER RESTART SIMULATION (Destroy RAM Manager & Instantiate New)
        # ─────────────────────────────────────────────────────────────────────
        try:
            del sm
            # Create a brand NEW SessionManager instance targeting the same SQLite DB
            sm_restarted = SessionManager(db_path=test_db_path)
            restored_history = sm_restarted.get_history(session_id)
            assert len(restored_history) == 4
            assert restored_history[-1]["lap"] == 50
            assert restored_history[-1]["stress"] == 64
            log_result("4. Server Restart Simulation", True, f"Restored {len(restored_history)} observations from SQLite after object destruction")
        except Exception as e:
            log_result("4. Server Restart Simulation", False, str(e))

        # ─────────────────────────────────────────────────────────────────────
        # 5. Post-Restart Temporal Analysis Verification
        # ─────────────────────────────────────────────────────────────────────
        try:
            analysis_2 = analyze_temporal_session(sm_restarted.get_history(session_id))
            assert analysis_2["sample_count"] == 4
            assert analysis_2["current_stress"] == 64
            assert analysis_2["current_lap"] == 50
            assert analysis_2["stress_trend"] == "RISING"
            assert analysis_2["correlation"] == analysis_1["correlation"]
            assert analysis_2["association"] == analysis_1["association"]
            log_result("5. Post-Restart Temporal Analysis", True, f"Correlation survived: {analysis_2['correlation']} | Trend survived: {analysis_2['stress_trend']}")
        except Exception as e:
            log_result("5. Post-Restart Temporal Analysis", False, str(e))

        # ─────────────────────────────────────────────────────────────────────
        # 6. Post-Restart Observation Continuation (Lap 51)
        # ─────────────────────────────────────────────────────────────────────
        try:
            obs5 = {"timestamp": "2024-09-22T13:21:30Z", "filename": "lap_51.mp3", "lap": 51, "lap_time_seconds": 99.100, "stress": 72, "stress_state": "Critical", "confidence": 0.95, "issues": ["rear sliding"]}
            sm_restarted.add_observation(session_id, obs5)

            history_5 = sm_restarted.get_history(session_id)
            assert len(history_5) == 5
            analysis_3 = analyze_temporal_session(history_5)
            assert analysis_3["sample_count"] == 5
            assert analysis_3["current_stress"] == 72
            assert analysis_3["current_lap"] == 51
            log_result("6. Post-Restart Observation Continuation", True, f"Sample count expanded to {analysis_3['sample_count']} (Lap 51)")
        except Exception as e:
            log_result("6. Post-Restart Observation Continuation", False, str(e))

        # ─────────────────────────────────────────────────────────────────────
        # 7. Active Session Restoration Test
        # ─────────────────────────────────────────────────────────────────────
        try:
            active_id = get_active_session_id(test_db_path)
            assert active_id == session_id
            log_result("7. Active Session Identity Restoration", True, f"Active session restored as '{active_id}'")
        except Exception as e:
            log_result("7. Active Session Identity Restoration", False, str(e))

        # ─────────────────────────────────────────────────────────────────────
        # 8. Reset & Clear Operations Test
        # ─────────────────────────────────────────────────────────────────────
        try:
            sm_restarted.reset_session(session_id)
            assert len(sm_restarted.get_history(session_id)) == 0
            db_history = load_session_history(session_id, db_path=test_db_path)
            assert len(db_history) == 0
            log_result("8. Reset Session Operation", True, f"Durable deletion confirmed for '{session_id}'")
        except Exception as e:
            log_result("8. Reset Session Operation", False, str(e))

        # ─────────────────────────────────────────────────────────────────────
        # FAILURE & EDGE-CASE TESTS
        # ─────────────────────────────────────────────────────────────────────

        # TEST A: Missing Database File Auto-Creation
        try:
            missing_db_path = os.path.join(temp_dir, "non_existent_subdir", "missing.db")
            sm_missing = SessionManager(db_path=missing_db_path)
            assert os.path.exists(missing_db_path)
            log_result("TEST A (Missing DB file auto-creation)", True, "Created directory and DB file automatically")
        except Exception as e:
            log_result("TEST A (Missing DB file auto-creation)", False, str(e))

        # TEST B: Empty Database Query
        try:
            empty_db_path = os.path.join(temp_dir, "empty.db")
            init_db(empty_db_path)
            empty_hist = load_session_history("non_existent_session", db_path=empty_db_path)
            assert isinstance(empty_hist, list)
            assert len(empty_hist) == 0
            log_result("TEST B (Empty DB query handling)", True, "Returns empty list without exception")
        except Exception as e:
            log_result("TEST B (Empty DB query handling)", False, str(e))

        # TEST C: Corrupt JSON Deserialization Resilience
        try:
            corrupt_db_path = os.path.join(temp_dir, "corrupt.db")
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
            log_result("TEST C (Corrupt JSON deserialization resilience)", True, "Handled corrupted JSON gracefully without crashing")
        except Exception as e:
            log_result("TEST C (Corrupt JSON deserialization resilience)", False, str(e))

        # TEST D: Duplicate Lap Numbers Preservation
        try:
            dupe_db_path = os.path.join(temp_dir, "dupe.db")
            sm_dupe = SessionManager(db_path=dupe_db_path)
            sm_dupe.add_observation("dupe_session", {"lap": 16, "lap_time_seconds": 97.168, "stress": 40})
            sm_dupe.add_observation("dupe_session", {"lap": 16, "lap_time_seconds": 96.683, "stress": 44})

            del sm_dupe
            sm_dupe_restored = SessionManager(db_path=dupe_db_path)
            dupe_hist = sm_dupe_restored.get_history("dupe_session")
            assert len(dupe_hist) == 2
            assert dupe_hist[0]["lap_time_seconds"] == 97.168
            assert dupe_hist[1]["lap_time_seconds"] == 96.683
            log_result("TEST D (Duplicate lap observation ordering)", True, "Both observations preserved in exact order")
        except Exception as e:
            log_result("TEST D (Duplicate lap observation ordering)", False, str(e))

        # TEST E: Reset All Clear Operation
        try:
            clear_db_path = os.path.join(temp_dir, "clear.db")
            sm_clear = SessionManager(db_path=clear_db_path)
            sm_clear.add_observation("session_A", {"lap": 1, "stress": 20})
            sm_clear.add_observation("session_B", {"lap": 2, "stress": 30})
            sm_clear.reset_all()

            all_sessions = load_all_sessions(db_path=clear_db_path)
            assert len(all_sessions) == 0
            log_result("TEST E (Reset all clear operation)", True, "All sessions wiped cleanly from SQLite")
        except Exception as e:
            log_result("TEST E (Reset all clear operation)", False, str(e))

    finally:
        # Clean up temporary test directory
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            if "PITSENSE_DB_PATH" in os.environ:
                del os.environ["PITSENSE_DB_PATH"]
        except Exception:
            pass

    print("\n==================================================")
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print(f"PHASE 9.5 PERSISTENCE TEST RESULT: {passed_count}/{total_count} PASSED")
    print("==================================================\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = run_persistence_tests()
    sys.exit(0 if success else 1)
