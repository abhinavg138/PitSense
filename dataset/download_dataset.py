"""
download_dataset.py
-------------------
Multi-Race Telemetry + Team Radio Dataset Ingestion Pipeline for PitSense.

Automatically discovers, matches, and downloads multi-season (2023–2025) F1 Team Radio
recordings paired with OpenF1 lap telemetry while ensuring 100% backward compatibility,
idempotency, driver balance, and robust error resilience.

Usage:
    python dataset/download_dataset.py [OPTIONS]

Examples:
    python dataset/download_dataset.py --max-samples 250
    python dataset/download_dataset.py --years 2024 2025 --no-audio
"""

import os
import sys
import csv
import time
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import requests

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OPENF1_BASE_URL = "https://api.openf1.org/v1"

# Standard Metadata Schema Fields
FIELDNAMES = [
    "sample_id", "audio_file", "recording_url", "year", "grand_prix", "country", "location",
    "meeting_key", "session_key", "session_type", "session_name", "driver_number", "driver_name",
    "team_name", "lap", "lap_time", "sector_1", "sector_2", "sector_3", "i1_speed", "i2_speed",
    "top_speed", "is_pit_out_lap", "radio_time", "lap_start_time", "radio_to_lap_start_seconds",
    "match_method", "data_status", "tyre_compound", "tyre_age", "stint_number", "position",
    "gap_to_leader", "interval", "air_temperature", "track_temperature", "humidity", "wind_speed",
    "rainfall", "quality_score"
]


def fetch_openf1(endpoint: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Any:
    """
    Executes an HTTP GET request against the OpenF1 API with timeout and exponential backoff retry.
    Returns parsed JSON data or [] on failure.
    """
    url = f"{OPENF1_BASE_URL}/{endpoint.lstrip('/')}"
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=12.0)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                logger.warning(f"[OPENF1] Rate limited (429). Waiting {attempt * 2}s...")
                time.sleep(attempt * 2)
            else:
                logger.warning(f"[OPENF1] HTTP {resp.status_code} for {url}: {resp.text[:100]}")
        except Exception as exc:
            logger.warning(f"[OPENF1] Connection attempt {attempt}/{max_retries} failed: {exc}")
            time.sleep(attempt * 1.5)
    return []


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Safely parses ISO format datetime string into Python datetime object."""
    if not dt_str:
        return None
    try:
        clean_str = str(dt_str).strip()
        if clean_str.endswith("Z"):
            clean_str = clean_str[:-1] + "+00:00"
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None


def download_audio_file(url: str, dest_path: str, max_retries: int = 3) -> bool:
    """
    Downloads audio file from URL to dest_path if missing or empty.
    Returns True if valid file exists on disk.
    """
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return True

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=15.0, stream=True)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                return True
        except Exception as exc:
            logger.warning(f"[AUDIO] Download attempt {attempt}/{max_retries} failed for {url}: {exc}")
            time.sleep(1.0)
    return False


def load_existing_metadata(csv_path: str) -> Tuple[List[Dict[str, Any]], set, set]:
    """
    Reads existing metadata.csv rows.
    Returns (rows, known_urls_set, known_keys_set).
    """
    rows: List[Dict[str, Any]] = []
    known_urls: set = set()
    known_keys: set = set()

    if not os.path.exists(csv_path):
        return rows, known_urls, known_keys

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
                url = str(r.get("recording_url", "")).strip()
                if url:
                    known_urls.add(url)
                
                sk = str(r.get("session_key", "")).strip()
                dn = str(r.get("driver_number", "")).strip()
                rt = str(r.get("radio_time", "")).strip()
                if sk and dn and rt:
                    known_keys.add(f"{sk}_{dn}_{rt}")
    except Exception as exc:
        logger.error(f"[METADATA] Error loading existing metadata: {exc}")

    return rows, known_urls, known_keys


def match_radio_to_lap(
    radio_dt: datetime,
    laps: List[Dict[str, Any]],
    max_offset: float = 120.0
) -> Tuple[Optional[Dict[str, Any]], str, Optional[float]]:
    """
    Deterministically matches a radio timestamp against driver lap records.
    Returns (matched_lap_dict, match_method, radio_to_lap_start_seconds).
    """
    if not radio_dt or not laps:
        return None, "unavailable", None

    # Parse and sort laps by start time
    valid_laps = []
    for l in laps:
        st = parse_iso_datetime(l.get("date_start"))
        dur = l.get("lap_duration")
        num = l.get("lap_number")
        if st and num is not None:
            valid_laps.append({"lap_dict": l, "start_dt": st, "duration": dur, "number": num})

    valid_laps.sort(key=lambda x: x["start_dt"])
    if not valid_laps:
        return None, "unavailable", None

    # 1. Interval Matching: lap_start <= radio_time < next_lap_start
    for i in range(len(valid_laps) - 1):
        curr_l = valid_laps[i]
        next_l = valid_laps[i + 1]
        if curr_l["start_dt"] <= radio_dt < next_l["start_dt"]:
            offset = round((radio_dt - curr_l["start_dt"]).total_seconds(), 3)
            if offset <= max_offset and curr_l["duration"] is not None:
                return curr_l["lap_dict"], "interval", offset

    # Check last lap interval (approximate using lap duration if available)
    last_l = valid_laps[-1]
    if last_l["start_dt"] <= radio_dt:
        offset = round((radio_dt - last_l["start_dt"]).total_seconds(), 3)
        lap_dur = float(last_l["duration"]) if last_l["duration"] else 120.0
        if offset <= (lap_dur + 10.0) and offset <= max_offset:
            return last_l["lap_dict"], "interval", offset

    # 2. Nearest Matching Fallback
    best_lap = None
    min_dist = float("inf")
    best_offset = None

    for vl in valid_laps:
        dist = abs((radio_dt - vl["start_dt"]).total_seconds())
        if dist < min_dist:
            min_dist = dist
            best_lap = vl["lap_dict"]
            best_offset = round((radio_dt - vl["start_dt"]).total_seconds(), 3)

    if min_dist <= max_offset and best_lap and best_lap.get("lap_duration") is not None:
        return best_lap, "nearest", best_offset

    return None, "unavailable", None


def run_pipeline(args):
    dataset_dir = os.path.abspath(args.output_dir)
    audio_dir = os.path.join(dataset_dir, "audio")
    metadata_path = os.path.join(dataset_dir, "metadata.csv")

    os.makedirs(audio_dir, exist_ok=True)

    logger.info("==================================================")
    logger.info("STARTING PIT SENSE DATASET PIPELINE")
    logger.info(f"Years: {args.years} | Session Types: {args.session_types}")
    logger.info(f"Target Max Samples: {args.max_samples} | Download Audio: {args.download_audio}")
    logger.info("==================================================")

    existing_rows, known_urls, known_keys = load_existing_metadata(metadata_path)
    logger.info(f"[METADATA] Loaded {len(existing_rows)} existing rows from metadata.csv")

    driver_counts: Dict[str, int] = {}
    season_counts: Dict[int, int] = {}
    session_counts: Dict[str, int] = {}

    # Initialize stats from existing metadata
    for r in existing_rows:
        dname = r.get("driver_name", "Unknown")
        yr = r.get("year")
        gp = r.get("grand_prix", "Unknown")
        if dname:
            driver_counts[dname] = driver_counts.get(dname, 0) + 1
        if yr and str(yr).isdigit():
            season_counts[int(yr)] = season_counts.get(int(yr), 0) + 1
        if gp:
            session_counts[gp] = session_counts.get(gp, 0) + 1

    sessions_scanned = 0
    radio_discovered = 0
    downloaded_files = 0
    reused_files = 0
    telemetry_linked = 0
    radio_only = 0
    failed_downloads = 0
    skipped_duplicates = 0
    new_rows: List[Dict[str, Any]] = []

    # Iterate over Target Years & Session Types
    for year in args.years:
        if len(existing_rows) + len(new_rows) >= args.max_samples:
            break

        for stype in args.session_types:
            if len(existing_rows) + len(new_rows) >= args.max_samples:
                break

            logger.info(f"[DISCOVERY] Fetching OpenF1 sessions for {year} {stype}...")
            sessions = fetch_openf1("sessions", params={"year": year, "session_type": stype})
            if not isinstance(sessions, list) or not sessions:
                continue

            for sess in sessions:
                if len(existing_rows) + len(new_rows) >= args.max_samples:
                    break

                sessions_scanned += 1
                session_key = sess.get("session_key")
                meeting_key = sess.get("meeting_key")
                gp_name = sess.get("circuit_short_name") or sess.get("location") or sess.get("country_name") or "Grand Prix"
                country = sess.get("country_name", "")
                location = sess.get("location", "")
                session_name = sess.get("session_name", stype)

                if not session_key:
                    continue

                # Fetch Drivers for Session
                drivers_raw = fetch_openf1("drivers", params={"session_key": session_key})
                drivers_map: Dict[int, Dict[str, str]] = {}
                if isinstance(drivers_raw, list):
                    for d in drivers_raw:
                        num = d.get("driver_number")
                        if num is not None:
                            full_name = d.get("full_name") or f"{d.get('first_name', '')} {d.get('last_name', '')}".strip() or f"Driver {num}"
                            team_name = d.get("team_name") or "Formula 1 Team"
                            drivers_map[int(num)] = {"driver_name": full_name, "team_name": team_name}

                # Fetch Team Radio for Session
                radio_records = fetch_openf1("team_radio", params={"session_key": session_key})
                if not isinstance(radio_records, list) or not radio_records:
                    continue

                radio_discovered += len(radio_records)

                # Group radio records by driver_number
                driver_radio_map: Dict[int, List[Dict[str, Any]]] = {}
                for r in radio_records:
                    dn = r.get("driver_number")
                    if dn is not None:
                        if dn not in driver_radio_map:
                            driver_radio_map[dn] = []
                        driver_radio_map[dn].append(r)

                # Process radio records per driver
                for dn, r_list in driver_radio_map.items():
                    if len(existing_rows) + len(new_rows) >= args.max_samples:
                        break

                    d_info = drivers_map.get(int(dn), {"driver_name": f"Driver {dn}", "team_name": "Formula 1 Team"})
                    d_name = d_info["driver_name"]
                    t_name = d_info["team_name"]

                    # Balance check
                    if driver_counts.get(d_name, 0) >= 35:
                        continue

                    # Fetch Laps for Driver in Session
                    laps = fetch_openf1("laps", params={"session_key": session_key, "driver_number": dn})
                    if not isinstance(laps, list):
                        laps = []

                    radio_index = 0
                    for r in r_list:
                        if len(existing_rows) + len(new_rows) >= args.max_samples:
                            break

                        url = str(r.get("recording_url", "")).strip()
                        r_date_str = str(r.get("date", "")).strip()
                        key_str = f"{session_key}_{dn}_{r_date_str}"

                        if url in known_urls or key_str in known_keys:
                            skipped_duplicates += 1
                            continue

                        radio_dt = parse_iso_datetime(r_date_str)
                        if not radio_dt:
                            continue

                        radio_index += 1
                        matched_lap, match_method, offset = match_radio_to_lap(
                            radio_dt, laps, max_offset=args.max_radio_lap_offset
                        )

                        lap_num = matched_lap.get("lap_number") if matched_lap else None
                        lap_time = matched_lap.get("lap_duration") if matched_lap else None
                        lap_start_time = matched_lap.get("date_start") if matched_lap else ""

                        s1 = matched_lap.get("duration_sector_1") if matched_lap else None
                        s2 = matched_lap.get("duration_sector_2") if matched_lap else None
                        s3 = matched_lap.get("duration_sector_3") if matched_lap else None
                        i1 = matched_lap.get("i1_speed") if matched_lap else None
                        i2 = matched_lap.get("i2_speed") if matched_lap else None
                        st = matched_lap.get("st_speed") if matched_lap else None
                        is_pit_out = matched_lap.get("is_pit_out_lap") if matched_lap else None

                        # Deterministic audio filename
                        lap_suffix = f"{int(lap_num):02d}" if lap_num is not None else "00"
                        audio_filename = f"{year}_{meeting_key}_{session_key}_{dn}_lap_{lap_suffix}_radio_{radio_index:03d}.mp3"
                        audio_filepath = os.path.join(audio_dir, audio_filename)
                        sample_id = audio_filename.replace(".mp3", "")

                        # Audio Download Handling
                        audio_ok = False
                        if args.download_audio and url:
                            audio_ok = download_audio_file(url, audio_filepath)
                            if audio_ok:
                                downloaded_files += 1
                            else:
                                failed_downloads += 1
                        elif not args.download_audio and os.path.exists(audio_filepath):
                            audio_ok = True
                            reused_files += 1

                        # Classification
                        if match_method in ("interval", "nearest") and lap_num is not None and lap_time is not None:
                            if args.download_audio and not audio_ok:
                                data_status = "INVALID"
                            else:
                                data_status = "TELEMETRY_LINKED"
                                telemetry_linked += 1
                        elif audio_ok or not args.download_audio:
                            data_status = "RADIO_ONLY"
                            radio_only += 1
                        else:
                            data_status = "INVALID"

                        if data_status == "INVALID":
                            continue

                        row_dict = {
                            "sample_id": sample_id,
                            "audio_file": audio_filename,
                            "recording_url": url,
                            "year": year,
                            "grand_prix": gp_name,
                            "country": country,
                            "location": location,
                            "meeting_key": meeting_key,
                            "session_key": session_key,
                            "session_type": stype,
                            "session_name": session_name,
                            "driver_number": dn,
                            "driver_name": d_name,
                            "team_name": t_name,
                            "lap": lap_num if lap_num is not None else "",
                            "lap_time": lap_time if lap_time is not None else "",
                            "sector_1": s1 if s1 is not None else "",
                            "sector_2": s2 if s2 is not None else "",
                            "sector_3": s3 if s3 is not None else "",
                            "i1_speed": i1 if i1 is not None else "",
                            "i2_speed": i2 if i2 is not None else "",
                            "top_speed": st if st is not None else "",
                            "is_pit_out_lap": is_pit_out if is_pit_out is not None else "",
                            "radio_time": r_date_str,
                            "lap_start_time": lap_start_time,
                            "radio_to_lap_start_seconds": offset if offset is not None else "",
                            "match_method": match_method,
                            "data_status": data_status,
                            "tyre_compound": "",
                            "tyre_age": "",
                            "stint_number": "",
                            "position": "",
                            "gap_to_leader": "",
                            "interval": "",
                            "air_temperature": "",
                            "track_temperature": "",
                            "humidity": "",
                            "wind_speed": "",
                            "rainfall": "",
                            "quality_score": 100 if data_status == "TELEMETRY_LINKED" else 75,
                        }

                        new_rows.append(row_dict)
                        known_urls.add(url)
                        known_keys.add(key_str)

                        driver_counts[d_name] = driver_counts.get(d_name, 0) + 1
                        season_counts[year] = season_counts.get(year, 0) + 1
                        session_counts[gp_name] = session_counts.get(gp_name, 0) + 1

    # Write Combined metadata.csv (preserving original + newly added rows)
    combined_rows = existing_rows + new_rows
    with open(metadata_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for r in combined_rows:
            # Ensure required legacy fields exist
            normalized = {k: r.get(k, "") for k in FIELDNAMES}
            if not normalized.get("data_status"):
                normalized["data_status"] = "TELEMETRY_LINKED" if normalized.get("lap_time") else "RADIO_ONLY"
            if not normalized.get("match_method"):
                normalized["match_method"] = "interval" if normalized.get("lap_time") else "unavailable"
            writer.writerow(normalized)

    # Print Summary Table
    logger.info("\n==================================================")
    logger.info("PITSENSE DATASET BUILD SUMMARY")
    logger.info("==================================================")
    logger.info(f"Sessions Scanned:            {sessions_scanned}")
    logger.info(f"Radio Recordings Discovered: {radio_discovered}")
    logger.info(f"Audio Files Downloaded:      {downloaded_files}")
    logger.info(f"Existing Files Reused:       {reused_files}")
    logger.info(f"Telemetry-Linked Samples:    {telemetry_linked}")
    logger.info(f"Radio-Only Samples:          {radio_only}")
    logger.info(f"Failed Downloads:            {failed_downloads}")
    logger.info(f"Skipped Duplicates:          {skipped_duplicates}")
    logger.info(f"Total Dataset Rows:          {len(combined_rows)}")
    logger.info("--------------------------------------------------")
    logger.info("Breakdown by Season:")
    for y, count in sorted(season_counts.items()):
        logger.info(f"  {y}: {count} samples")
    logger.info("--------------------------------------------------")
    logger.info("Top Drivers Represented:")
    for d, count in sorted(driver_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {d}: {count} samples")
    logger.info("==================================================\n")


def parse_args():
    parser = argparse.ArgumentParser(description="PitSense OpenF1 Team Radio & Telemetry Ingestion Pipeline")
    parser.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025], help="Target F1 seasons")
    parser.add_argument("--session-types", nargs="+", type=str, default=["Race", "Qualifying", "Sprint"], help="Session types")
    parser.add_argument("--max-samples", type=int, default=250, help="Maximum total dataset samples")
    parser.add_argument("--min-samples-per-driver", type=int, default=5, help="Minimum samples target per driver")
    parser.add_argument("--download-audio", action="store_true", default=True, help="Download audio files")
    parser.add_argument("--no-audio", action="store_false", dest="download_audio", help="Metadata discovery mode without downloading audio")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume and preserve existing dataset")
    parser.add_argument("--max-radio-lap-offset", type=float, default=120.0, help="Maximum matching window in seconds")
    parser.add_argument("--output-dir", type=str, default="dataset", help="Output directory")
    return parser.parse_args()


if __name__ == "__main__":
    run_pipeline(parse_args())