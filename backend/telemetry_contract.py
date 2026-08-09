from typing import Any, Dict, List, Optional


def _float_or_none(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _telemetry_status(point: Dict[str, Any]) -> str:
    if not point.get("available"):
        return "UNAVAILABLE"

    has_lap_time = point.get("lap_time") is not None
    has_sectors = any(point.get(key) is not None for key in ("sector_1", "sector_2", "sector_3"))
    has_speeds = any(point.get(key) is not None for key in ("i1_speed", "i2_speed", "top_speed"))

    if has_lap_time and has_sectors and has_speeds:
        return "AVAILABLE"
    if has_lap_time or has_sectors or has_speeds or point.get("lap") is not None:
        return "PARTIAL"
    return "UNAVAILABLE"


def build_telemetry_series(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    points: List[Dict[str, Any]] = []

    for index, observation in enumerate(history):
        telemetry = observation.get("telemetry") or {}
        lap = observation.get("lap")
        if lap is None:
            lap = telemetry.get("lap")

        lap_time = observation.get("lap_time_seconds")
        if lap_time is None:
            lap_time = observation.get("lap_time")
        if lap_time is None:
            lap_time = telemetry.get("lap_time")

        point = {
            "index": index + 1,
            "timestamp": observation.get("timestamp"),
            "filename": observation.get("filename") or telemetry.get("audio_file"),
            "available": bool(telemetry.get("available")) or lap is not None or lap_time is not None,
            "lap": _int_or_none(lap),
            "lap_time": _float_or_none(lap_time),
            "stress": _float_or_none(observation.get("stress", observation.get("stress_index"))),
            "sector_1": _float_or_none(telemetry.get("sector_1")),
            "sector_2": _float_or_none(telemetry.get("sector_2")),
            "sector_3": _float_or_none(telemetry.get("sector_3")),
            "i1_speed": _int_or_none(telemetry.get("i1_speed")),
            "i2_speed": _int_or_none(telemetry.get("i2_speed")),
            "top_speed": _int_or_none(telemetry.get("top_speed")),
        }
        point["status"] = _telemetry_status(point)
        points.append(point)

    usable_points = [p for p in points if p["status"] in ("AVAILABLE", "PARTIAL")]
    if not points or not usable_points:
        status = "UNAVAILABLE"
    elif len(usable_points) < 2:
        status = "INSUFFICIENT"
    elif any(p["status"] == "AVAILABLE" for p in usable_points):
        status = "AVAILABLE"
    else:
        status = "PARTIAL"

    return {
        "available": bool(usable_points),
        "status": status,
        "sample_count": len(points),
        "point_count": len(usable_points),
        "points": points,
    }
