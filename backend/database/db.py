"""
db.py
-----
Durable SQLite persistence layer for PitSense temporal session observations.

Persists raw session observations to SQLite so temporal stress trends,
lap performance histories, correlation matrices, and decision context survive
Uvicorn/FastAPI server restarts.

Database Location:
  Default: backend/data/pitsense.db
  Override: PITSENSE_DB_PATH environment variable
"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Default Database Paths
_HERE = os.path.dirname(__file__)
DEFAULT_DB_DIR = os.path.abspath(os.path.join(_HERE, "..", "data"))
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "pitsense.db")


def get_db_path() -> str:
    """Returns the effective SQLite database path, supporting environment override."""
    path = os.environ.get("PITSENSE_DB_PATH", DEFAULT_DB_PATH)
    return os.path.abspath(path)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Creates and returns a context-managed SQLite connection.
    Ensures parent directory exists and enables WAL mode.
    """
    target = db_path or get_db_path()
    db_dir = os.path.dirname(target)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(target, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception as exc:
        logger.warning(f"[DB] PRAGMA setup warning: {exc}")
    return conn


def init_db(db_path: Optional[str] = None):
    """
    Initializes SQLite tables and indexes. Safe to run on every application startup.
    """
    target = db_path or get_db_path()
    try:
        with get_connection(target) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    updated_at TEXT,
                    status TEXT DEFAULT 'active',
                    is_active INTEGER DEFAULT 0
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS temporal_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    observation_order INTEGER NOT NULL,
                    timestamp TEXT,
                    filename TEXT,
                    stress REAL,
                    stress_state TEXT,
                    confidence REAL,
                    lap INTEGER,
                    lap_time_seconds REAL,
                    telemetry_json TEXT,
                    issues_json TEXT,
                    extra_json TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_obs_session_order 
                ON temporal_observations(session_id, observation_order);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_obs_session_lap 
                ON temporal_observations(session_id, lap);
            """)
            conn.commit()
            logger.info(f"[DB] Initialized database cleanly at: {target}")
    except Exception as exc:
        logger.error(f"[DB] Error initializing database at {target}: {exc}")


def get_active_session_id(db_path: Optional[str] = None) -> Optional[str]:
    """Returns the most recent active session ID from SQLite."""
    target = db_path or get_db_path()
    try:
        with get_connection(target) as conn:
            cur = conn.execute(
                "SELECT session_id FROM sessions WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                return row["session_id"]
    except Exception as exc:
        logger.warning(f"[DB] Error reading active session ID: {exc}")
    return None


def set_active_session_id(session_id: str, db_path: Optional[str] = None):
    """Marks session_id as the active session in SQLite."""
    if not session_id:
        return
    target = db_path or get_db_path()
    now_str = datetime.now().isoformat()
    try:
        with get_connection(target) as conn:
            conn.execute("UPDATE sessions SET is_active = 0")
            conn.execute(
                """
                INSERT INTO sessions (session_id, created_at, updated_at, status, is_active)
                VALUES (?, ?, ?, 'active', 1)
                ON CONFLICT(session_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    is_active = 1
                """,
                (session_id, now_str, now_str)
            )
            conn.commit()
    except Exception as exc:
        logger.warning(f"[DB] Error setting active session ID '{session_id}': {exc}")


def save_observation(
    session_id: str,
    observation: Dict[str, Any],
    observation_order: int,
    db_path: Optional[str] = None
) -> bool:
    """
    Persists a single observation dictionary to SQLite under session_id.
    """
    if not session_id or not observation:
        return False

    target = db_path or get_db_path()
    now_str = observation.get("timestamp") or datetime.now().isoformat()

    # Extract core columns
    filename = observation.get("filename", "")
    stress = float(observation.get("stress", 0.0))
    stress_state = str(observation.get("stress_state", "Calm"))
    confidence = float(observation.get("confidence", 0.0))

    lap = observation.get("lap")
    lap_val = int(lap) if lap is not None and str(lap).isdigit() else None

    lap_time = observation.get("lap_time_seconds")
    if lap_time is None:
        lap_time = observation.get("lap_time")
    try:
        lap_time_val = float(lap_time) if lap_time is not None else None
    except (ValueError, TypeError):
        lap_time_val = None

    # JSON serialization
    try:
        telemetry_json = json.dumps(observation.get("telemetry", {}))
    except Exception:
        telemetry_json = "{}"

    try:
        issues_json = json.dumps(observation.get("issues", []))
    except Exception:
        issues_json = "[]"

    # Known keys
    known_keys = {
        "timestamp", "filename", "stress", "stress_state", "confidence",
        "lap", "lap_time_seconds", "lap_time", "telemetry", "issues"
    }
    extra = {k: v for k, v in observation.items() if k not in known_keys}
    try:
        extra_json = json.dumps(extra)
    except Exception:
        extra_json = "{}"

    try:
        with get_connection(target) as conn:
            # Ensure session row exists
            conn.execute(
                """
                INSERT INTO sessions (session_id, created_at, updated_at, status, is_active)
                VALUES (?, ?, ?, 'active', 1)
                ON CONFLICT(session_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    is_active = 1
                """,
                (session_id, now_str, now_str)
            )

            # Insert observation
            conn.execute(
                """
                INSERT INTO temporal_observations (
                    session_id, observation_order, timestamp, filename,
                    stress, stress_state, confidence, lap, lap_time_seconds,
                    telemetry_json, issues_json, extra_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    observation_order,
                    now_str,
                    filename,
                    stress,
                    stress_state,
                    confidence,
                    lap_val,
                    lap_time_val,
                    telemetry_json,
                    issues_json,
                    extra_json,
                )
            )
            conn.commit()
            return True
    except Exception as exc:
        logger.error(f"[DB] Failed to save observation for session '{session_id}': {exc}")
        return False


def load_session_history(session_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Restores the observation history list for session_id from SQLite.
    Skipping any individual corrupted row gracefully.
    """
    if not session_id:
        return []

    target = db_path or get_db_path()
    results: List[Dict[str, Any]] = []

    try:
        with get_connection(target) as conn:
            cur = conn.execute(
                """
                SELECT timestamp, filename, stress, stress_state, confidence,
                       lap, lap_time_seconds, telemetry_json, issues_json, extra_json
                FROM temporal_observations
                WHERE session_id = ?
                ORDER BY observation_order ASC
                """,
                (session_id,)
            )
            rows = cur.fetchall()
            for r in rows:
                try:
                    # Deserialize JSON
                    try:
                        telemetry = json.loads(r["telemetry_json"]) if r["telemetry_json"] else {"available": False}
                    except Exception:
                        telemetry = {"available": False}

                    try:
                        issues = json.loads(r["issues_json"]) if r["issues_json"] else []
                    except Exception:
                        issues = []

                    try:
                        extra = json.loads(r["extra_json"]) if r["extra_json"] else {}
                    except Exception:
                        extra = {}

                    obs = {
                        "timestamp": r["timestamp"],
                        "filename": r["filename"],
                        "stress": r["stress"],
                        "stress_state": r["stress_state"],
                        "confidence": r["confidence"],
                        "lap": r["lap"],
                        "lap_time_seconds": r["lap_time_seconds"],
                        "telemetry": telemetry,
                        "issues": issues,
                    }
                    if extra and isinstance(extra, dict):
                        obs.update(extra)

                    results.append(obs)
                except Exception as row_exc:
                    logger.warning(f"[DB] Skipping corrupted observation row in session '{session_id}': {row_exc}")
    except Exception as exc:
        logger.error(f"[DB] Failed to load history for session '{session_id}': {exc}")

    return results


def load_all_sessions(db_path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Restores all sessions and their observation histories into a dictionary.
    """
    target = db_path or get_db_path()
    sessions_map: Dict[str, List[Dict[str, Any]]] = {}

    try:
        with get_connection(target) as conn:
            cur = conn.execute("SELECT DISTINCT session_id FROM temporal_observations")
            session_rows = cur.fetchall()
            for s_row in session_rows:
                sid = s_row["session_id"]
                history = load_session_history(sid, db_path=target)
                if history:
                    sessions_map[sid] = history
    except Exception as exc:
        logger.error(f"[DB] Failed to load all sessions from database: {exc}")

    return sessions_map


def delete_session_history(session_id: str, db_path: Optional[str] = None) -> bool:
    """
    Deletes all observations for session_id from SQLite.
    """
    if not session_id:
        return False

    target = db_path or get_db_path()
    try:
        with get_connection(target) as conn:
            conn.execute("DELETE FROM temporal_observations WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return True
    except Exception as exc:
        logger.error(f"[DB] Failed to delete session '{session_id}': {exc}")
        return False


def clear_all_session_history(db_path: Optional[str] = None) -> bool:
    """
    Deletes all sessions and observations from SQLite.
    """
    target = db_path or get_db_path()
    try:
        with get_connection(target) as conn:
            conn.execute("DELETE FROM temporal_observations")
            conn.execute("DELETE FROM sessions")
            conn.commit()
            return True
    except Exception as exc:
        logger.error(f"[DB] Failed to clear all sessions: {exc}")
        return False
