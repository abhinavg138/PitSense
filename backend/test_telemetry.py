import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app

client = TestClient(app)
SAMPLE_AUDIO = backend_dir.parent / "dataset" / "audio" / "lap_04.mp3"


def test_dataset_validate():
    r = client.get("/dataset/validate")
    assert r.status_code == 200
    val = r.json()
    assert val["overall_status"] == "PASS"


def test_upload_lap_04_telemetry():
    assert SAMPLE_AUDIO.exists(), f"Sample audio missing at {SAMPLE_AUDIO}"
    with open(SAMPLE_AUDIO, "rb") as f:
        res = client.post(
            "/upload",
            files={"file": ("lap_04.mp3", f, "audio/mp3")}
        )

    assert res.status_code == 200
    data = res.json()
    tel = data.get("telemetry", {})
    assert tel.get("available") is True
    assert tel.get("lap") == 4

    series = data.get("telemetry_series", {})
    assert series.get("available") is True
    assert series.get("status") in {"INSUFFICIENT", "PARTIAL", "AVAILABLE"}
    assert series.get("point_count", 0) >= 1
    assert isinstance(series.get("points"), list)
    assert series["points"][-1]["lap"] == 4
    assert abs(series["points"][-1]["lap_time"] - 99.17) < 1e-3
