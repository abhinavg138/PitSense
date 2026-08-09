from telemetry_contract import build_telemetry_series


def test_build_telemetry_series_marks_two_real_points_available():
    history = [
        {
            "timestamp": "2026-08-09T10:00:00",
            "filename": "lap_04.mp3",
            "lap": 4,
            "lap_time_seconds": 99.17,
            "stress": 33,
            "telemetry": {
                "available": True,
                "lap": 4,
                "lap_time": 99.17,
                "sector_1": 29.464,
                "sector_2": 42.067,
                "top_speed": 284,
                "audio_file": "lap_04.mp3",
            },
        },
        {
            "timestamp": "2026-08-09T10:01:40",
            "filename": "lap_33.mp3",
            "lap": 33,
            "lap_time_seconds": 97.449,
            "stress": 48,
            "telemetry": {
                "available": True,
                "lap": 33,
                "lap_time": 97.449,
                "sector_1": 28.8,
                "sector_2": 41.9,
                "top_speed": 289,
                "audio_file": "lap_33.mp3",
            },
        },
    ]

    series = build_telemetry_series(history)

    assert series["available"] is True
    assert series["status"] == "AVAILABLE"
    assert series["sample_count"] == 2
    assert series["point_count"] == 2
    assert series["points"][0]["lap"] == 4
    assert series["points"][1]["lap_time"] == 97.449
    assert series["points"][1]["stress"] == 48.0


def test_build_telemetry_series_reports_insufficient_single_point():
    series = build_telemetry_series([
        {
            "filename": "lap_04.mp3",
            "lap": 4,
            "lap_time_seconds": 99.17,
            "stress": 33,
            "telemetry": {"available": True, "lap": 4, "lap_time": 99.17},
        }
    ])

    assert series["available"] is True
    assert series["status"] == "INSUFFICIENT"
    assert series["point_count"] == 1


def test_build_telemetry_series_keeps_unavailable_explicit():
    series = build_telemetry_series([
        {
            "filename": "custom_upload.mp3",
            "stress": 28,
            "telemetry": {"available": False},
        }
    ])

    assert series["available"] is False
    assert series["status"] == "UNAVAILABLE"
    assert series["sample_count"] == 1
    assert series["point_count"] == 0
    assert series["points"][0]["status"] == "UNAVAILABLE"
