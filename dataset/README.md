# PitSense OpenF1 Team Radio & Telemetry Dataset

This directory contains the multi-race F1 Team Radio audio files and paired OpenF1 lap telemetry used by PitSense for race engineering decision support and simulation playback.

---

## 🏎️ OpenF1 Ingestion Pipeline Architecture

The dataset is ingested dynamically via `download_dataset.py` using the official OpenF1 REST API (`https://api.openf1.org/v1/`).

```
OpenF1 API
  ├── /sessions      ──> Discover 2023–2025 Race / Qualifying / Sprint sessions
  ├── /drivers       ──> Resolve driver_number to driver_name and team_name
  ├── /team_radio    ──> Fetch radio timestamps and recording URLs
  └── /laps          ──> Fetch lap start times, lap durations, sector times, & speed traps
```

---

## ⏱️ Radio → Lap Interval Matching Algorithm

To eliminate fabricated lap associations, radio communications are matched to lap telemetry deterministically:

1. **Interval Matching (`match_method = "interval"`)**:
   - Matches when: `lap_start <= radio_time < next_lap_start`
   - Calculates exact offset: `radio_to_lap_start_seconds`
2. **Nearest Matching (`match_method = "nearest"`)**:
   - Fallback when lap boundaries are slightly shifted, provided offset is within `--max-radio-lap-offset` (default 120s).
3. **Unavailable (`match_method = "unavailable"`)**:
   - Assigned when no trustworthy lap timeline exists. Marked as `RADIO_ONLY` and excluded from default telemetry-linked simulation samples.

---

## 📊 Data Quality Classification

- **`TELEMETRY_LINKED`**: Valid audio file on disk, valid driver identity, valid radio timestamp, and verified paired lap telemetry.
- **`RADIO_ONLY`**: Valid audio file on disk and radio timestamp, but no trustworthy telemetry match.
- **`INVALID`**: Malformed payload, invalid URL, or missing core identity.

---

## 🛠️ Regeneration & Resume Commands

```bash
# Build/Expand dataset (default max 250 samples, downloading audio)
python dataset/download_dataset.py --max-samples 250

# Fast metadata-only discovery (without downloading audio files)
python dataset/download_dataset.py --no-audio

# Target specific F1 seasons and session types
python dataset/download_dataset.py --years 2024 2025 --session-types Race Qualifying --max-samples 300
```

---

## 📁 Metadata Schema (`metadata.csv`)

| Field | Description |
| :--- | :--- |
| `sample_id` | Unique sample identifier (e.g. `2024_1229_9472_63_lap_03_radio_004`) |
| `audio_file` | Local filename in `dataset/audio/` |
| `recording_url` | OpenF1 live timing audio recording URL |
| `year` | Season year (2023–2025) |
| `grand_prix` | Event name (e.g., Sakhir, Jeddah, Silverstone) |
| `driver_number` | F1 car driver number |
| `driver_name` | Resolved driver full name (e.g. George Russell) |
| `team_name` | F1 constructor team name (e.g. Mercedes, Red Bull Racing) |
| `lap` | Matched lap number |
| `lap_time` | Lap duration in seconds |
| `radio_time` | UTC timestamp of team radio communication |
| `radio_to_lap_start_seconds` | Time offset from lap start to radio broadcast |
| `match_method` | `interval` \| `nearest` \| `unavailable` |
| `data_status` | `TELEMETRY_LINKED` \| `RADIO_ONLY` \| `INVALID` |
