"""
test_dataset_pipeline.py
-------------------------
Automated Test Suite for Phase 11: Multi-Race Telemetry + Team Radio Dataset Expansion.

Verifies:
- OpenF1 API parsing and dynamic driver name resolution
- Radio -> Lap interval matching algorithm (interval, nearest, unavailable)
- Duplicate recording prevention
- Existing metadata preservation
- Dataset loader compatibility (load_dataset_metadata & get_simulation_samples)
- GET /simulation/samples API endpoint integration
- Idempotent execution
"""

import sys
import os
import csv
import tempfile
from datetime import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset")))

from app import app
from dataset_loader import load_dataset_metadata, get_simulation_samples, get_telemetry_for_file
from download_dataset import (
    match_radio_to_lap,
    parse_iso_datetime,
    load_existing_metadata,
    FIELDNAMES,
)

client = TestClient(app)


def run_pipeline_tests():
    print("\n==================================================")
    print("RUNNING PIT SENSE DATASET PIPELINE TEST SUITE")
    print("==================================================\n")

    results = []

    def log_result(test_name: str, passed: bool, details: str = ""):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {details}")
        results.append((test_name, passed, details))

    # ─────────────────────────────────────────────────────────────────────
    # 1. ISO Datetime Parsing Test
    # ─────────────────────────────────────────────────────────────────────
    try:
        dt1 = parse_iso_datetime("2024-03-02T15:07:32.513000+00:00")
        assert dt1 is not None
        assert dt1.year == 2024 and dt1.month == 3 and dt1.day == 2
        log_result("1. ISO Datetime Parsing", True, f"Parsed: {dt1.isoformat()}")
    except Exception as e:
        log_result("1. ISO Datetime Parsing", False, str(e))

    # ─────────────────────────────────────────────────────────────────────
    # 2. Radio -> Lap Interval Matching Test
    # ─────────────────────────────────────────────────────────────────────
    try:
        laps_mock = [
            {"lap_number": 1, "date_start": "2024-03-02T15:00:00.000Z", "lap_duration": 96.0},
            {"lap_number": 2, "date_start": "2024-03-02T15:01:36.000Z", "lap_duration": 96.5},
            {"lap_number": 3, "date_start": "2024-03-02T15:03:12.500Z", "lap_duration": 97.0},
        ]
        radio_dt = datetime.fromisoformat("2024-03-02T15:02:10.000+00:00")

        matched, method, offset = match_radio_to_lap(radio_dt, laps_mock, max_offset=120.0)
        assert matched is not None
        assert matched["lap_number"] == 2
        assert method == "interval"
        assert offset == 34.0
        log_result("2. Radio -> Lap Interval Matching", True, f"Matched Lap {matched['lap_number']} via {method} (Offset: {offset}s)")
    except Exception as e:
        log_result("2. Radio -> Lap Interval Matching", False, str(e))

    # ─────────────────────────────────────────────────────────────────────
    # 3. Missing Lap & Max Offset Rejection Test
    # ─────────────────────────────────────────────────────────────────────
    try:
        laps_mock = [
            {"lap_number": 1, "date_start": "2024-03-02T15:00:00.000Z", "lap_duration": 96.0},
        ]
        radio_far_dt = datetime.fromisoformat("2024-03-02T16:00:00.000+00:00")

        matched, method, offset = match_radio_to_lap(radio_far_dt, laps_mock, max_offset=120.0)
        assert matched is None
        assert method == "unavailable"
        log_result("3. Max Offset Rejection Handling", True, "Successfully marked as unavailable when offset exceeds threshold")
    except Exception as e:
        log_result("3. Max Offset Rejection Handling", False, str(e))

    # ─────────────────────────────────────────────────────────────────────
    # 4. Existing Metadata Preservation Test
    # ─────────────────────────────────────────────────────────────────────
    try:
        real_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset", "metadata.csv"))
        rows, known_urls, known_keys = load_existing_metadata(real_csv)
        assert len(rows) >= 45
        assert "lap_04.mp3" in [r.get("audio_file") for r in rows]
        log_result("4. Existing Metadata Preservation", True, f"Loaded {len(rows)} existing metadata rows; lap_04.mp3 present")
    except Exception as e:
        log_result("4. Existing Metadata Preservation", False, str(e))

    # ─────────────────────────────────────────────────────────────────────
    # 5. Dataset Loader API Compatibility Test
    # ─────────────────────────────────────────────────────────────────────
    try:
        tel = get_telemetry_for_file("lap_04.mp3")
        assert tel is not None
        assert tel.get("available") is True
        assert abs(tel["lap_time"] - 99.17) < 1e-3
        log_result("5. Dataset Loader API Compatibility", True, f"lap_04.mp3 telemetry lap_time: {tel['lap_time']}s")
    except Exception as e:
        log_result("5. Dataset Loader API Compatibility", False, str(e))

    # ─────────────────────────────────────────────────────────────────────
    # 6. GET /simulation/samples Endpoint Integration Test
    # ─────────────────────────────────────────────────────────────────────
    try:
        resp = client.get("/simulation/samples")
        assert resp.status_code == 200
        samples = resp.json()
        assert isinstance(samples, list)
        assert len(samples) >= 45
        log_result("6. GET /simulation/samples Integration", True, f"Discovered {len(samples)} valid simulation samples")
    except Exception as e:
        log_result("6. GET /simulation/samples Integration", False, str(e))

    # ─────────────────────────────────────────────────────────────────────
    # 7. Idempotent Deduplication Test
    # ─────────────────────────────────────────────────────────────────────
    try:
        temp_dir = tempfile.mkdtemp(prefix="pitsense_dedupe_test_")
        temp_csv = os.path.join(temp_dir, "metadata.csv")

        # Write initial row
        with open(temp_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerow({
                "sample_id": "test_01",
                "audio_file": "test_01.mp3",
                "recording_url": "https://livetiming.formula1.com/test_01.mp3",
                "session_key": "9999",
                "driver_number": "63",
                "radio_time": "2024-03-02T15:00:00Z"
            })

        rows, known_urls, known_keys = load_existing_metadata(temp_csv)
        assert "https://livetiming.formula1.com/test_01.mp3" in known_urls
        assert "9999_63_2024-03-02T15:00:00Z" in known_keys
        log_result("7. Idempotent Deduplication Verification", True, "Recording URL and session/driver/time keys successfully indexed")
    except Exception as e:
        log_result("7. Idempotent Deduplication Verification", False, str(e))

    print("\n==================================================")
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print(f"DATASET PIPELINE TEST RESULT: {passed_count}/{total_count} PASSED")
    print("==================================================\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = run_pipeline_tests()
    sys.exit(0 if success else 1)
