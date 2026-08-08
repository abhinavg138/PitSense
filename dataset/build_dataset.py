"""
build_dataset.py
----------------
Automated, reusable F1 dataset collection pipeline using the OpenF1 API.

Usage:
  python dataset/build_dataset.py
  python dataset/build_dataset.py --years 2024 --session-types Race Qualifying --drivers 63 --max-samples 100

Features:
- Dynamically queries OpenF1 sessions, team radio, laps, stints, weather.
- Matches team radio recordings to laps using actual timestamps (radio_time vs date_start).
- Deduplicates recordings by recording_url, audio_file, and sample_id to prevent re-downloads.
- Preserves existing samples in metadata.csv.
- Caches raw API responses in dataset/raw/ to avoid unnecessary API requests.
- Implements rate limiting and exponential backoff retry logic for OpenF1 API.
- Evaluates a Quality Score (0-100) for each sample.
"""

import os
import sys
import csv
import json
import time
import hashlib
import logging
import argparse
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Set, Tuple

import requests

# Ensure stdout handles UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Paths ───────────────────────────────────────────────────────────────────
DATASET_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(DATASET_DIR, "audio")
RAW_DIR = os.path.join(DATASET_DIR, "raw")
LOGS_DIR = os.path.join(DATASET_DIR, "logs")
METADATA_CSV = os.path.join(DATASET_DIR, "metadata.csv")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ── Logging Setup ───────────────────────────────────────────────────────────
log_file_path = os.path.join(LOGS_DIR, "build_dataset.log")
logger = logging.getLogger("build_dataset")
logger.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(ch)

# File handler
fh = logging.FileHandler(log_file_path, encoding="utf-8")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(fh)


# ── Metadata Schema ─────────────────────────────────────────────────────────
CSV_FIELDNAMES = [
    "sample_id",
    "audio_file",
    "recording_url",
    "year",
    "grand_prix",
    "country",
    "location",
    "meeting_key",
    "session_key",
    "session_type",
    "session_name",
    "driver_number",
    "driver_name",
    "team_name",
    "lap",
    "lap_time",
    "sector_1",
    "sector_2",
    "sector_3",
    "i1_speed",
    "i2_speed",
    "top_speed",
    "is_pit_out_lap",
    "radio_time",
    "lap_start_time",
    "radio_to_lap_start_seconds",
    "tyre_compound",
    "tyre_age",
    "stint_number",
    "position",
    "gap_to_leader",
    "interval",
    "air_temperature",
    "track_temperature",
    "humidity",
    "wind_speed",
    "rainfall",
    "quality_score",
]


# ── OpenF1 API Client with Cache & Retry ────────────────────────────────────
class OpenF1Client:
    BASE_URL = "https://api.openf1.org/v1"

    def __init__(self, raw_dir: str, refresh: bool = False):
        self.raw_dir = raw_dir
        self.refresh = refresh
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PitSense-Dataset-Builder/2.0"})

    def _get_cache_path(self, endpoint: str, params: Dict[str, Any]) -> str:
        sub_dir = os.path.join(self.raw_dir, endpoint.strip("/"))
        os.makedirs(sub_dir, exist_ok=True)
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode("utf-8")).hexdigest()[:10]
        return os.path.join(sub_dir, f"{param_hash}.json")

    def fetch(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        params = params or {}
        cache_path = self._get_cache_path(endpoint, params)

        if not self.refresh and os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Cache read error for {cache_path}: {e}")

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        max_retries = 4
        backoff = 1.0

        for attempt in range(1, max_retries + 1):
            try:
                time.sleep(0.15)  # Respectful rate-limit delay
                resp = self.session.get(url, params=params, timeout=20)

                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                    except Exception as e:
                        logger.warning(f"Failed to write API cache {cache_path}: {e}")
                    return data
                elif resp.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"API HTTP {resp.status_code} for {url} (Attempt {attempt}/{max_retries}). Backing off {backoff:.1f}s...")
                    time.sleep(backoff)
                    backoff *= 2.0
                else:
                    logger.error(f"API HTTP {resp.status_code} for {url}: {resp.text[:200]}")
                    return []
            except (requests.RequestException, Exception) as exc:
                logger.warning(f"Network error on {url} (Attempt {attempt}/{max_retries}): {exc}")
                time.sleep(backoff)
                backoff *= 2.0

        logger.error(f"Failed to fetch {url} after {max_retries} attempts.")
        return []


# ── Audio Downloader ────────────────────────────────────────────────────────
def download_audio_file(url: str, dest_path: str) -> bool:
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return True

    temp_path = dest_path + ".tmp"
    max_retries = 3
    backoff = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=30, stream=True)
            if resp.status_code == 200:
                with open(temp_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)

                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1000:
                    os.replace(temp_path, dest_path)
                    return True
                else:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            time.sleep(backoff)
            backoff *= 2.0
        except Exception as exc:
            logger.warning(f"Audio download attempt {attempt} failed for {url}: {exc}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            time.sleep(backoff)
            backoff *= 2.0

    return False


# ── Metadata DB Management (Safe Read/Append/Deduplication) ─────────────────
def load_existing_metadata(csv_path: str) -> Tuple[List[Dict[str, Any]], Set[str], Set[str], Set[str]]:
    rows: List[Dict[str, Any]] = []
    urls: Set[str] = set()
    files: Set[str] = set()
    ids: Set[str] = set()

    if not os.path.exists(csv_path):
        return rows, urls, files, ids

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                audio_file = str(row.get("audio_file", "")).strip()
                recording_url = str(row.get("recording_url", "")).strip()
                sample_id = str(row.get("sample_id", "")).strip()

                if audio_file:
                    files.add(audio_file.lower())
                if recording_url:
                    urls.add(recording_url.strip())
                if sample_id:
                    ids.add(sample_id.strip())

                # Fill all schema keys for existing rows
                full_row = {field: row.get(field, "") for field in CSV_FIELDNAMES}
                if not full_row["sample_id"] and audio_file:
                    full_row["sample_id"] = os.path.splitext(audio_file)[0]
                rows.append(full_row)
    except Exception as exc:
        logger.error(f"Error reading existing metadata CSV: {exc}")

    return rows, urls, files, ids


def save_metadata(csv_path: str, rows: List[Dict[str, Any]]):
    temp_csv = csv_path + ".tmp"
    try:
        with open(temp_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        os.replace(temp_csv, csv_path)
    except Exception as exc:
        logger.error(f"Failed to save metadata CSV: {exc}")
        if os.path.exists(temp_csv):
            os.remove(temp_csv)


# ── Timestamp Parser ────────────────────────────────────────────────────────
def parse_iso_time(ts_str: str) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None


# ── Radio → Lap Matching Algorithm ──────────────────────────────────────────
def match_radio_to_lap(radio_date_str: str, laps: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[float], str]:
    """
    Matches radio timestamp to the best lap for the driver.
    Returns (best_lap_dict, radio_to_lap_start_seconds, match_reason)
    """
    radio_dt = parse_iso_time(radio_date_str)
    if not radio_dt:
        return None, None, "Invalid radio timestamp"

    valid_laps = []
    for lap in laps:
        date_start_str = lap.get("date_start")
        if not date_start_str:
            continue
        start_dt = parse_iso_time(date_start_str)
        if not start_dt:
            continue
        duration = lap.get("lap_duration")

        valid_laps.append({
            "lap": lap,
            "start_dt": start_dt,
            "duration": float(duration) if duration is not None else None
        })

    if not valid_laps:
        return None, None, "No valid laps with start timestamp found"

    # Sort laps by start time
    valid_laps.sort(key=lambda x: x["start_dt"])

    # 1. Try strict interval match: start <= radio <= start + duration
    for item in valid_laps:
        start = item["start_dt"]
        dur = item["duration"]
        if dur is not None and dur > 0:
            end = start + timedelta(seconds=dur)
            if start <= radio_dt <= end:
                diff_sec = round((radio_dt - start).total_seconds(), 3)
                return item["lap"], diff_sec, "Inside lap duration"

    # 2. Nearest lap start match within threshold (max 120s)
    best_item = None
    min_dist = float("inf")

    for item in valid_laps:
        dist = abs((radio_dt - item["start_dt"]).total_seconds())
        if dist < min_dist:
            min_dist = dist
            best_item = item

    if best_item and min_dist <= 120.0:
        diff_sec = round((radio_dt - best_item["start_dt"]).total_seconds(), 3)
        return best_item["lap"], diff_sec, f"Nearest lap start ({min_dist:.1f}s diff)"

    return None, None, f"No lap start within threshold (closest was {min_dist:.1f}s)"


# ── Quality Score Evaluator ─────────────────────────────────────────────────
def calculate_quality_score(sample: Dict[str, Any]) -> int:
    score = 50  # Base for valid audio + lap match

    if sample.get("lap_time") is not None and float(sample.get("lap_time") or 0) > 0:
        score += 15

    radio_diff = sample.get("radio_to_lap_start_seconds")
    lap_time = sample.get("lap_time")
    if radio_diff is not None and lap_time is not None:
        if 0 <= float(radio_diff) <= float(lap_time):
            score += 15  # Radio occurred strictly inside the lap

    s1 = sample.get("sector_1")
    s2 = sample.get("sector_2")
    s3 = sample.get("sector_3")
    if s1 is not None and s2 is not None and s3 is not None:
        score += 10

    top_speed = sample.get("top_speed")
    if top_speed is not None:
        score += 5

    if sample.get("tyre_compound") or sample.get("air_temperature") is not None:
        score += 5

    if sample.get("is_pit_out_lap") is True:
        score -= 15

    return max(0, min(100, score))


# ── Main Collection Pipeline ────────────────────────────────────────────────
def build_dataset(
    years: List[int],
    session_types: List[str],
    drivers_filter: Optional[List[int]],
    limit_sessions: int,
    max_samples: int,
    refresh: bool,
):
    logger.info("==================================================")
    logger.info("Starting PitSense Automated Dataset Collection Pipeline")
    logger.info(f"Years: {years} | Session Types: {session_types}")
    if drivers_filter:
        logger.info(f"Filter Drivers: {drivers_filter}")
    logger.info(f"Target Max New Samples: {max_samples}")
    logger.info("==================================================")

    client = OpenF1Client(RAW_DIR, refresh=refresh)

    # 1. Load existing metadata to deduplicate
    rows, existing_urls, existing_files, existing_ids = load_existing_metadata(METADATA_CSV)
    logger.info(f"Loaded {len(rows)} existing samples from metadata.csv")

    collected_count = 0

    # 2. Fetch Sessions
    all_sessions = []
    for y in years:
        for st in session_types:
            sess_list = client.fetch("sessions", {"year": y, "session_name": st})
            if not sess_list:
                sess_list = client.fetch("sessions", {"year": y, "session_type": st})
            all_sessions.extend(sess_list)

    # Deduplicate sessions by session_key
    unique_sessions = {s["session_key"]: s for s in all_sessions if "session_key" in s}
    sessions_to_process = list(unique_sessions.values())[:limit_sessions]
    logger.info(f"Found {len(sessions_to_process)} target sessions to process.")

    for sess_idx, sess in enumerate(sessions_to_process, 1):
        if collected_count >= max_samples:
            logger.info(f"[TARGET REACHED] Collected max target samples ({max_samples}). Stopping.")
            break

        session_key = sess["session_key"]
        meeting_key = sess.get("meeting_key", 0)
        gp_name = sess.get("circuit_short_name") or sess.get("country_name") or "GrandPrix"
        year = sess.get("year", 2024)
        sess_name = sess.get("session_name", "Race")
        sess_type = sess.get("session_type", sess_name)
        country = sess.get("country_name", "")
        location = sess.get("location", "")

        logger.info(f"\n[SESSION {sess_idx}/{len(sessions_to_process)}] {year} {gp_name} {sess_name} (key: {session_key})")

        # Fetch Team Radio for this session
        radio_items = client.fetch("team_radio", {"session_key": session_key})
        if not radio_items:
            logger.info(f"  [RADIO] No team radio recordings found for session {session_key}.")
            continue

        # Filter by driver if specified
        if drivers_filter:
            radio_items = [r for r in radio_items if r.get("driver_number") in drivers_filter]

        logger.info(f"  [RADIO] Found {len(radio_items)} radio recordings.")

        # Cache driver info & weather info for the session
        drivers_info = {d.get("driver_number"): d for d in client.fetch("drivers", {"session_key": session_key})}
        weather_info = client.fetch("weather", {"session_key": session_key})

        # Process each radio recording
        for radio_idx, radio in enumerate(radio_items, 1):
            if collected_count >= max_samples:
                break

            rec_url = str(radio.get("recording_url", "")).strip()
            if not rec_url:
                continue

            driver_num = radio.get("driver_number")
            radio_date = radio.get("date")

            if not driver_num or not radio_date:
                continue

            # Deduplication Check 1: recording_url
            if rec_url in existing_urls:
                logger.info(f"  [SKIP] Already downloaded recording URL: {rec_url}")
                continue

            # Fetch laps for driver in this session
            laps = client.fetch("laps", {"session_key": session_key, "driver_number": driver_num})
            matched_lap, radio_diff_sec, match_reason = match_radio_to_lap(radio_date, laps)

            if not matched_lap:
                logger.info(f"  [REJECT] Driver {driver_num} Radio at {radio_date} -> {match_reason}")
                continue

            lap_num = matched_lap.get("lap_number")
            lap_duration = matched_lap.get("lap_duration")

            if lap_num is None or lap_duration is None:
                logger.info(f"  [REJECT] Driver {driver_num} Lap {lap_num} has null lap_duration")
                continue

            # Construct collision-safe sample filename
            audio_filename = f"{year}_{meeting_key}_{session_key}_{driver_num}_lap_{lap_num:02d}_radio_{radio_idx:03d}.mp3"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            sample_id = os.path.splitext(audio_filename)[0]

            # Deduplication Check 2: audio_file or sample_id
            if audio_filename.lower() in existing_files or sample_id in existing_ids:
                logger.info(f"  [SKIP] Already present in dataset: {audio_filename}")
                existing_urls.add(rec_url)
                continue

            # Download Audio MP3
            logger.info(f"  [DOWNLOAD] Downloading radio recording -> {audio_filename}")
            download_success = download_audio_file(rec_url, audio_path)

            if not download_success:
                logger.warning(f"  [REJECT] Audio download failed for {rec_url}")
                continue

            # Stint lookup
            stint_info = client.fetch("stints", {"session_key": session_key, "driver_number": driver_num})
            tyre_compound = None
            tyre_age = None
            stint_num = None
            for st in stint_info:
                st_start = st.get("lap_start")
                st_end = st.get("lap_end")
                if st_start is not None and st_end is not None and st_start <= lap_num <= st_end:
                    tyre_compound = st.get("compound")
                    stint_num = st.get("stint_number")
                    start_age = st.get("tyre_age_at_start", 0)
                    tyre_age = start_age + (lap_num - st_start)
                    break

            # Closest Weather lookup
            air_temp = None
            track_temp = None
            humidity = None
            wind_speed = None
            rainfall = None

            if weather_info:
                radio_dt = parse_iso_time(radio_date)
                if radio_dt:
                    best_w = None
                    best_w_diff = float("inf")
                    for w in weather_info:
                        w_dt = parse_iso_time(w.get("date"))
                        if w_dt:
                            diff = abs((radio_dt - w_dt).total_seconds())
                            if diff < best_w_diff:
                                best_w_diff = diff
                                best_w = w
                    if best_w:
                        air_temp = best_w.get("air_temperature")
                        track_temp = best_w.get("track_temperature")
                        humidity = best_w.get("humidity")
                        wind_speed = best_w.get("wind_speed")
                        rainfall = best_w.get("rainfall")

            # Driver name & team lookup
            d_info = drivers_info.get(driver_num, {})
            driver_name = d_info.get("full_name") or d_info.get("broadcast_name") or f"Driver {driver_num}"
            team_name = d_info.get("team_name") or ""

            # Build record
            record = {
                "sample_id": sample_id,
                "audio_file": audio_filename,
                "recording_url": rec_url,
                "year": year,
                "grand_prix": gp_name,
                "country": country,
                "location": location,
                "meeting_key": meeting_key,
                "session_key": session_key,
                "session_type": sess_type,
                "session_name": sess_name,
                "driver_number": driver_num,
                "driver_name": driver_name,
                "team_name": team_name,
                "lap": lap_num,
                "lap_time": float(lap_duration),
                "sector_1": matched_lap.get("duration_sector_1"),
                "sector_2": matched_lap.get("duration_sector_2"),
                "sector_3": matched_lap.get("duration_sector_3"),
                "i1_speed": matched_lap.get("i1_speed"),
                "i2_speed": matched_lap.get("i2_speed"),
                "top_speed": matched_lap.get("st_speed"),
                "is_pit_out_lap": matched_lap.get("is_pit_out_lap"),
                "radio_time": radio_date,
                "lap_start_time": matched_lap.get("date_start"),
                "radio_to_lap_start_seconds": radio_diff_sec,
                "tyre_compound": tyre_compound,
                "tyre_age": tyre_age,
                "stint_number": stint_num,
                "position": None,
                "gap_to_leader": None,
                "interval": None,
                "air_temperature": air_temp,
                "track_temperature": track_temp,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "rainfall": rainfall,
                "quality_score": 0,
            }

            record["quality_score"] = calculate_quality_score(record)

            # Log match success
            logger.info(f"  [MATCH] Radio {radio_date[11:19]} -> Lap {lap_num} ({match_reason})")
            logger.info(f"  [TELEMETRY] Lap {lap_num} -> {record['lap_time']:.3f}s (Quality Score: {record['quality_score']}/100)")
            logger.info(f"  [SAVE] Saved sample {sample_id}")

            rows.append(record)
            existing_urls.add(rec_url)
            existing_files.add(audio_filename.lower())
            existing_ids.add(sample_id)

            collected_count += 1

            # Periodically write to CSV every 5 new samples so progress isn't lost
            if collected_count % 5 == 0:
                save_metadata(METADATA_CSV, rows)

    # Final save
    save_metadata(METADATA_CSV, rows)

    logger.info("==================================================")
    logger.info(f"Dataset build run finished.")
    logger.info(f"New samples added in this run: {collected_count}")
    logger.info(f"Total dataset size: {len(rows)} samples.")
    logger.info("==================================================")


# ── Main Entrypoint ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="PitSense Automated F1 Dataset Collector")
    parser.add_argument("--years", nargs="+", type=int, default=[2024], help="Years to query (e.g. 2023 2024 2025)")
    parser.add_argument("--session-types", nargs="+", type=str, default=["Race", "Qualifying"], help="Session types (e.g. Race Qualifying Sprint)")
    parser.add_argument("--drivers", nargs="+", type=int, default=None, help="Filter specific driver numbers (e.g. 63 1 44)")
    parser.add_argument("--limit", type=int, default=50, help="Max sessions to process")
    parser.add_argument("--max-samples", type=int, default=150, help="Max new samples to collect in this run")
    parser.add_argument("--refresh", action="store_true", help="Force refresh API caches")

    args = parser.parse_args()

    build_dataset(
        years=args.years,
        session_types=args.session_types,
        drivers_filter=args.drivers,
        limit_sessions=args.limit,
        max_samples=args.max_samples,
        refresh=args.refresh,
    )


if __name__ == "__main__":
    main()
