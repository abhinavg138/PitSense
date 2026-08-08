import requests
import csv
import os
from datetime import datetime

SESSION = 9606
DRIVER = 63

OUT = "dataset"
AUDIO = os.path.join(OUT, "audio")

os.makedirs(AUDIO, exist_ok=True)

laps = requests.get(
    f"https://api.openf1.org/v1/laps?session_key={SESSION}&driver_number={DRIVER}"
).json()

radio = requests.get(
    f"https://api.openf1.org/v1/team_radio?session_key={SESSION}&driver_number={DRIVER}"
).json()

rows = []

for r in radio:
    radio_time = datetime.fromisoformat(r["date"])

    for i, lap in enumerate(laps[:-1]):
        start = datetime.fromisoformat(lap["date_start"])
        end = datetime.fromisoformat(laps[i + 1]["date_start"])

        if start <= radio_time < end and lap.get("lap_duration"):

            filename = f"lap_{lap['lap_number']:02d}.mp3"
            filepath = os.path.join(AUDIO, filename)

            print(f"Lap {lap['lap_number']} → {lap['lap_duration']}s")

            response = requests.get(r["recording_url"])

            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)

                rows.append({
                    "lap": lap["lap_number"],
                    "audio_file": filename,
                    "lap_time": lap["lap_duration"],
                    "radio_time": r["date"]
                })

            break

with open(
    os.path.join(OUT, "metadata.csv"),
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=["lap", "audio_file", "lap_time", "radio_time"]
    )

    writer.writeheader()
    writer.writerows(rows)

print(f"\nDONE — {len(rows)} samples created.")