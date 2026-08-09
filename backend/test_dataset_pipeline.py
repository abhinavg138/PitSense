"""
test_dataset_pipeline.py
-------------------------
Pytest suite for the PitSense multi-race telemetry + team-radio dataset.

Covers:
- OpenF1 ISO datetime parsing
- Radio -> lap interval matching
- Maximum offset rejection
- Existing metadata preservation
- Dataset loader compatibility
- /simulation/samples endpoint
- Idempotent metadata deduplication

The tests are intentionally compatible with the current frozen dataset and
do not depend on the legacy lap_04.mp3 fixture.
"""

import csv
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
AUDIO_DIR = DATASET_DIR / "audio"
METADATA_CSV = DATASET_DIR / "metadata.csv"

# Make backend + dataset modules importable when pytest is run from root.
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(DATASET_DIR))


# ---------------------------------------------------------------------------
# Application imports
# ---------------------------------------------------------------------------

from app import app
from dataset_loader import (
    get_simulation_samples,
    get_telemetry_for_file,
    load_dataset_metadata,
)
from download_dataset import (
    FIELDNAMES,
    load_existing_metadata,
    match_radio_to_lap,
    parse_iso_datetime,
)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_real_telemetry_sample():
    """
    Find a real audio sample from the current frozen dataset that:
    - exists in dataset/audio/
    - has telemetry metadata
    - is marked TELEMETRY_LINKED when that field is available

    Returns:
        (audio_filename, metadata_row)
    """
    assert METADATA_CSV.exists(), f"metadata.csv not found: {METADATA_CSV}"

    with METADATA_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows, "metadata.csv contains no rows"

    # Prefer telemetry-linked samples with audio actually present.
    candidates = [
        row
        for row in rows
        if row.get("audio_file")
        and (AUDIO_DIR / row["audio_file"]).exists()
        and row.get("data_status") == "TELEMETRY_LINKED"
    ]

    # Fall back to any real audio sample if status metadata is unavailable.
    if not candidates:
        candidates = [
            row
            for row in rows
            if row.get("audio_file")
            and (AUDIO_DIR / row["audio_file"]).exists()
        ]

    assert candidates, "No metadata row has a corresponding audio file on disk."

    row = candidates[0]
    return row["audio_file"], row


# ---------------------------------------------------------------------------
# 1. ISO datetime parsing
# ---------------------------------------------------------------------------

def test_parse_iso_datetime():
    dt = parse_iso_datetime("2024-03-02T15:07:32.513000+00:00")

    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 3
    assert dt.day == 2
    assert dt.hour == 15
    assert dt.minute == 7
    assert dt.second == 32


# ---------------------------------------------------------------------------
# 2. Radio -> lap interval matching
# ---------------------------------------------------------------------------

def test_radio_lap_interval_matching():
    laps_mock = [
        {
            "lap_number": 1,
            "date_start": "2024-03-02T15:00:00.000Z",
            "lap_duration": 96.0,
        },
        {
            "lap_number": 2,
            "date_start": "2024-03-02T15:01:36.000Z",
            "lap_duration": 96.5,
        },
        {
            "lap_number": 3,
            "date_start": "2024-03-02T15:03:12.500Z",
            "lap_duration": 97.0,
        },
    ]

    radio_dt = datetime.fromisoformat(
        "2024-03-02T15:02:10.000+00:00"
    )

    matched, method, offset = match_radio_to_lap(
        radio_dt,
        laps_mock,
        max_offset=120.0,
    )

    assert matched is not None
    assert matched["lap_number"] == 2
    assert method == "interval"
    assert offset == 34.0


# ---------------------------------------------------------------------------
# 3. Maximum radio -> lap offset rejection
# ---------------------------------------------------------------------------

def test_max_offset_rejection():
    laps_mock = [
        {
            "lap_number": 1,
            "date_start": "2024-03-02T15:00:00.000Z",
            "lap_duration": 96.0,
        },
    ]

    radio_far_dt = datetime.fromisoformat(
        "2024-03-02T16:00:00.000+00:00"
    )

    matched, method, offset = match_radio_to_lap(
        radio_far_dt,
        laps_mock,
        max_offset=120.0,
    )

    assert matched is None
    assert method == "unavailable"


# ---------------------------------------------------------------------------
# 4. Existing metadata preservation
# ---------------------------------------------------------------------------

def test_existing_metadata_preservation():
    assert METADATA_CSV.exists(), f"Missing dataset metadata: {METADATA_CSV}"

    rows, known_urls, known_keys = load_existing_metadata(
        str(METADATA_CSV)
    )

    assert len(rows) >= 1
    assert len(known_urls) >= 1
    assert len(known_keys) >= 1


def test_dataset_loader_compatibility():
    """Verify the loader can resolve a real telemetry-linked audio sample."""

    assert METADATA_CSV.exists(), f"metadata.csv not found: {METADATA_CSV}"

    with METADATA_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    candidates = [
        row
        for row in rows
        if row.get("audio_file")
        and (AUDIO_DIR / row["audio_file"]).exists()
        and row.get("data_status") == "TELEMETRY_LINKED"
    ]

    assert candidates, "No TELEMETRY_LINKED audio samples found."

    row = candidates[0]
    audio_filename = row["audio_file"]

    telemetry = get_telemetry_for_file(audio_filename)

    assert telemetry is not None
    assert telemetry.get("available") is True
    assert telemetry.get("audio_file") == audio_filename

    if row.get("lap") not in (None, ""):
        assert telemetry.get("lap") is not None

    if row.get("lap_time") not in (None, ""):
        assert telemetry.get("lap_time") is not None
        assert float(telemetry["lap_time"]) > 0

def test_dataset_loader_compatibility():
    """Verify the loader can resolve a real telemetry-linked audio sample."""

    assert METADATA_CSV.exists(), f"metadata.csv not found: {METADATA_CSV}"

    with METADATA_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    candidates = [
        row
        for row in rows
        if row.get("audio_file")
        and (AUDIO_DIR / row["audio_file"]).exists()
        and row.get("data_status") == "TELEMETRY_LINKED"
    ]

    assert candidates, "No TELEMETRY_LINKED audio samples found."

    row = candidates[0]
    audio_filename = row["audio_file"]

    telemetry = get_telemetry_for_file(audio_filename)

    assert telemetry is not None
    assert telemetry.get("available") is True
    assert telemetry.get("audio_file") == audio_filename

    if row.get("lap") not in (None, ""):
        assert telemetry.get("lap") is not None

    if row.get("lap_time") not in (None, ""):
        assert telemetry.get("lap_time") is not None
        assert float(telemetry["lap_time"]) > 0

def test_simulation_samples_endpoint():
    """Verify /simulation/samples exposes real dataset samples."""

    response = client.get("/simulation/samples")

    assert response.status_code == 200

    samples = response.json()

    assert isinstance(samples, list)
    assert len(samples) > 0

    for sample in samples:
        assert isinstance(sample, dict)
        assert sample.get("filename")
        assert "lap" in sample

    existing_samples = [
        sample
        for sample in samples
        if sample.get("filename")
        and (AUDIO_DIR / sample["filename"]).exists()
    ]

    assert existing_samples


def test_idempotent_deduplication():
    """Verify duplicate recording/session identities are indexed correctly."""

    with tempfile.TemporaryDirectory(
        prefix="pitsense_dedupe_test_"
    ) as temp_dir:

        temp_csv = os.path.join(temp_dir, "metadata.csv")

        row = {field: "" for field in FIELDNAMES}

        row.update({
            "sample_id": "test_01",
            "audio_file": "test_01.mp3",
            "recording_url": (
                "https://livetiming.formula1.com/test_01.mp3"
            ),
            "session_key": "9999",
            "driver_number": "63",
            "radio_time": "2024-03-02T15:00:00Z",
        })

        with open(
            temp_csv,
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=FIELDNAMES,
            )
            writer.writeheader()
            writer.writerow(row)

        rows, known_urls, known_keys = load_existing_metadata(
            temp_csv
        )

        assert len(rows) == 1

        assert (
            "https://livetiming.formula1.com/test_01.mp3"
            in known_urls
        )

        assert (
            "9999_63_2024-03-02T15:00:00Z"
            in known_keys
        )

        # Loading again must remain idempotent.
        rows_again, known_urls_again, known_keys_again = (
            load_existing_metadata(temp_csv)
        )

        assert len(rows_again) == 1
        assert known_urls_again == known_urls
        assert known_keys_again == known_keys


def test_frozen_dataset_contains_audio_samples():
    """Basic sanity check for the currently frozen dataset."""

    assert METADATA_CSV.exists()
    assert AUDIO_DIR.exists()

    audio_files = [
        path
        for path in AUDIO_DIR.iterdir()
        if path.is_file()
    ]

    assert len(audio_files) > 0

    metadata = load_dataset_metadata()

    assert metadata