"""
dataset_loader.py
-----------------
Loads metadata.csv + openf1_extended.json to produce a normalised telemetry
dict for every uploaded audio file that exists in the dataset.

Returned structure (available=True):
{
    "available":     True,
    "lap":           4,
    "lap_time":      99.170,
    "sector_1":      29.464,   # or null
    "sector_2":      42.067,   # or null
    "sector_3":      27.639,   # or null
    "i1_speed":      286,      # or null
    "i2_speed":      258,      # or null
    "top_speed":     284,      # or null  (= st_speed in OpenF1)
    "is_pit_out_lap": False,   # or null
    "radio_time":    "2024-09-22T12:09:14.327000+00:00",
    "audio_file":    "lap_04.mp3"
}

Returned structure (available=False):
{
    "available": False
}
"""

import csv
import json
import os
import sys
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Ensure stdout handles UTF-8 gracefully on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Configurable paths ──────────────────────────────────────────────────────
_HERE = os.path.dirname(__file__)
_DATASET_DIR = os.path.abspath(os.path.join(_HERE, "..", "dataset"))

DEFAULT_METADATA_PATH = os.path.join(_DATASET_DIR, "metadata.csv")
DEFAULT_EXTENDED_PATH = os.path.join(_DATASET_DIR, "openf1_extended.json")


def get_metadata_csv_path() -> str:
    path = os.environ.get("DATASET_METADATA_PATH", DEFAULT_METADATA_PATH)
    return os.path.abspath(path)


def get_extended_json_path() -> str:
    path = os.environ.get("DATASET_EXTENDED_PATH", DEFAULT_EXTENDED_PATH)
    return os.path.abspath(path)


# ── Internal loaders ────────────────────────────────────────────────────────

def _load_csv() -> Dict[str, Dict[str, Any]]:
    """
    Returns {lowercased_filename: {lap, audio_file, lap_time, radio_time}}.
    Never crashes — returns {} on any error.
    """
    target = get_metadata_csv_path()
    result: Dict[str, Dict[str, Any]] = {}

    if not os.path.exists(target):
        logger.warning(f"[TELEMETRY] metadata.csv not found at: {target}")
        return result

    try:
        with open(target, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                audio_file = str(row.get("audio_file", "")).strip()
                if not audio_file:
                    continue
                try:
                    key = os.path.basename(audio_file).lower()
                    if key not in result:            # first row wins on duplicate
                        lap_str = str(row.get("lap", "")).strip()
                        lap_time_str = str(row.get("lap_time", "")).strip()

                        lap_val = int(lap_str) if lap_str and lap_str.isdigit() else None
                        lap_time_val = float(lap_time_str) if lap_time_str else None

                        result[key] = {
                            "lap":        lap_val,
                            "lap_time":   lap_time_val,
                            "radio_time": str(row.get("radio_time", "")).strip(),
                            "audio_file": audio_file,
                        }
                except (ValueError, KeyError) as err:
                    logger.warning(f"[TELEMETRY] Skipping malformed CSV row {row}: {err}")

    except Exception as exc:
        logger.error(f"[TELEMETRY] Error reading metadata.csv: {exc}")

    return result


def _load_extended() -> Dict[str, Dict[str, Any]]:
    """
    Returns {lowercased_filename: openf1 field dict}.
    Never crashes — returns {} on any error.
    """
    target = get_extended_json_path()

    if not os.path.exists(target):
        logger.info(f"[TELEMETRY] openf1_extended.json not found at: {target} (optional)")
        return {}

    try:
        with open(target, "r", encoding="utf-8") as f:
            raw: Dict[str, Any] = json.load(f)
        return {k.lower(): v for k, v in raw.items()}
    except Exception as exc:
        logger.error(f"[TELEMETRY] Error reading openf1_extended.json: {exc}")
        return {}


# ── Public API ───────────────────────────────────────────────────────────────

def load_dataset_metadata(csv_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Back-compat function used by tests and validation.
    Returns the raw CSV map {filename_key -> {lap, lap_time, radio_time, audio_file}}.
    """
    if csv_path:
        # If a custom path is given, load only that CSV (no side-file merging)
        result: Dict[str, Dict[str, Any]] = {}
        if not os.path.exists(csv_path):
            return result
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    audio_file = str(row.get("audio_file", "")).strip()
                    if not audio_file:
                        continue
                    try:
                        key = os.path.basename(audio_file).lower()
                        if key not in result:
                            result[key] = {
                                "lap":        int(row["lap"]),
                                "lap_time":   float(row["lap_time"]),
                                "radio_time": str(row["radio_time"]).strip(),
                                "audio_file": audio_file,
                            }
                    except (ValueError, KeyError):
                        pass
        except Exception:
            pass
        return result
    return _load_csv()


def get_telemetry_for_file(
    filename: str,
    csv_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Given an uploaded filename, returns a normalised telemetry dict or None.

    When a match is found the dict has `available=True` and all fields.
    When no match is found returns None (caller should treat as available=False).
    """
    if not filename:
        return None

    key = os.path.basename(filename).strip().lower()

    csv_map = load_dataset_metadata(csv_path)
    csv_row = csv_map.get(key)
    if not csv_row:
        logger.info(f"[TELEMETRY] No dataset match for: {key}")
        return None

    # Merge extended OpenF1 fields if available
    ext_map = _load_extended()
    ext = ext_map.get(key, {})

    def _f(v) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v) -> Optional[int]:
        if v is None or v == "":
            return None
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    def _b(v) -> Optional[bool]:
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("true", "1", "t", "yes")

    def _get_field(ext_val, csv_val, parser):
        v = parser(ext_val)
        if v is not None:
            return v
        return parser(csv_val)

    telemetry: Dict[str, Any] = {
        "available":      True,
        "lap":            csv_row["lap"],
        "lap_time":       _f(csv_row.get("lap_time")),
        "sector_1":       _get_field(ext.get("duration_sector_1"), csv_row.get("sector_1"), _f),
        "sector_2":       _get_field(ext.get("duration_sector_2"), csv_row.get("sector_2"), _f),
        "sector_3":       _get_field(ext.get("duration_sector_3"), csv_row.get("sector_3"), _f),
        "i1_speed":       _get_field(ext.get("i1_speed"), csv_row.get("i1_speed"), _i),
        "i2_speed":       _get_field(ext.get("i2_speed"), csv_row.get("i2_speed"), _i),
        "top_speed":      _get_field(ext.get("st_speed"), csv_row.get("top_speed"), _i),
        "is_pit_out_lap": _get_field(ext.get("is_pit_out_lap"), csv_row.get("is_pit_out_lap"), _b),
        "radio_time":     csv_row.get("radio_time", ""),
        "audio_file":     csv_row.get("audio_file", ""),
    }

    lap_time_str = f"{telemetry['lap_time']:.3f}s" if telemetry["lap_time"] is not None else "?"
    msg = f"[TELEMETRY] Match: {csv_row['audio_file']} -> Lap {csv_row['lap']} -> {lap_time_str}"
    logger.info(msg)
    print(msg)

    return telemetry


def build_telemetry_context_string(telemetry: Optional[Dict[str, Any]]) -> str:
    """
    Returns a human-readable block that can be injected into Race Engineer prompts.
    Returns empty string when telemetry is unavailable.
    """
    if not telemetry or not telemetry.get("available"):
        return ""

    lines = [
        "RACE TELEMETRY:",
        f"  Lap:       {telemetry.get('lap', 'N/A')}",
        f"  Lap Time:  {telemetry.get('lap_time', 'N/A')} s",
    ]
    if telemetry.get("sector_1") is not None:
        lines.append(f"  Sector 1:  {telemetry['sector_1']} s")
    if telemetry.get("sector_2") is not None:
        lines.append(f"  Sector 2:  {telemetry['sector_2']} s")
    if telemetry.get("sector_3") is not None:
        lines.append(f"  Sector 3:  {telemetry['sector_3']} s")
    if telemetry.get("i1_speed") is not None:
        lines.append(f"  I1 Speed:  {telemetry['i1_speed']} km/h")
    if telemetry.get("i2_speed") is not None:
        lines.append(f"  I2 Speed:  {telemetry['i2_speed']} km/h")
    if telemetry.get("top_speed") is not None:
        lines.append(f"  Top Speed: {telemetry['top_speed']} km/h")

    return "\n".join(lines)


# ── Simulation Sample Discovery ──────────────────────────────────────────────

def get_simulation_samples(csv_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Dynamically discovers available audio observations from metadata.csv and dataset/audio/.
    Does not hardcode sample lists; reads metadata dynamically and verifies audio file existence.
    Sorts chronologically using radio_time or lap number.
    """
    target = csv_path or get_metadata_csv_path()
    audio_dir = os.path.join(_DATASET_DIR, "audio")
    samples: List[Dict[str, Any]] = []

    if not os.path.exists(target):
        logger.warning(f"[SIMULATION] metadata.csv not found at: {target}")
        return samples

    try:
        with open(target, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                audio_file = str(row.get("audio_file", "")).strip()
                if not audio_file:
                    continue

                # Check if audio file exists in dataset/audio/ or uploads/
                audio_path = os.path.join(audio_dir, audio_file)
                if not os.path.exists(audio_path):
                    alt_path = os.path.join(_HERE, "uploads", audio_file)
                    if not os.path.exists(alt_path):
                        logger.debug(f"[SIMULATION] Audio file missing for row: {audio_file}")
                        continue


                def _parse_int(val):
                    try:
                        return int(val) if val is not None and val != "" else None
                    except (ValueError, TypeError):
                        return None

                def _parse_float(val):
                    try:
                        return float(val) if val is not None and val != "" else None
                    except (ValueError, TypeError):
                        return None

                data_status = str(row.get("data_status", "")).strip()
                if data_status == "INVALID":
                    continue

                samples.append({
                    "sample_id": str(row.get("sample_id", "")).strip() or audio_file,
                    "audio_file": audio_file,
                    "filename": audio_file,
                    "lap": _parse_int(row.get("lap")),
                    "lap_time": _parse_float(row.get("lap_time")),
                    "radio_time": str(row.get("radio_time", "")).strip(),
                    "driver_number": _parse_int(row.get("driver_number")),
                    "driver_name": str(row.get("driver_name", "")).strip(),
                    "team_name": str(row.get("team_name", "")).strip(),
                    "grand_prix": str(row.get("grand_prix", "")).strip(),
                    "year": _parse_int(row.get("year")),
                    "match_method": str(row.get("match_method", "interval")).strip(),
                    "data_status": data_status or ("TELEMETRY_LINKED" if row.get("lap_time") else "RADIO_ONLY"),
                    "radio_to_lap_start_seconds": _parse_float(row.get("radio_to_lap_start_seconds")),
                })

        # Sort samples chronologically: radio_time (ISO str) -> lap -> filename
        def _sort_key(s):
            rt = s.get("radio_time") or ""
            lap = s.get("lap") or 0
            return (rt, lap, s.get("audio_file") or "")

        samples.sort(key=_sort_key)

    except Exception as exc:
        logger.error(f"[SIMULATION] Error discovering dataset samples: {exc}")

    return samples


# ── Validation ───────────────────────────────────────────────────────────────

def run_dataset_validation(csv_path: Optional[str] = None) -> Dict[str, Any]:
    """
    PASS/FAIL check for all expected dataset samples.
    """
    expected = [
        ("lap_04.mp3", 99.170),
        ("lap_33.mp3", 97.449),
        ("lap_44.mp3", 97.701),
        ("lap_47.mp3", 97.636),
        ("lap_52.mp3", 97.299),
    ]

    results = []
    passed = 0

    print("\n--- PitSense Dataset Loader Validation ---")
    for audio_file, expected_lap_time in expected:
        telemetry = get_telemetry_for_file(audio_file, csv_path=csv_path)
        actual_lap_time = telemetry.get("lap_time") if telemetry else None
        is_match = actual_lap_time is not None and abs(actual_lap_time - expected_lap_time) < 1e-3
        status = "PASS" if is_match else "FAIL"
        if is_match:
            passed += 1

        actual_str = f"{actual_lap_time:.3f}" if actual_lap_time is not None else "None"
        print(f"  {audio_file} -> {actual_str} (expected {expected_lap_time}): {status}")

        results.append({
            "audio_file":        audio_file,
            "expected_lap_time": expected_lap_time,
            "actual_lap_time":   actual_lap_time,
            "status":            status,
        })

    total = len(expected)
    overall = "PASS" if passed == total else "FAIL"
    print(f"Overall: {overall} ({passed}/{total} passed)\n")

    return {
        "overall_status": overall,
        "passed":         passed,
        "total":          total,
        "results":        results,
    }


if __name__ == "__main__":
    run_dataset_validation()
