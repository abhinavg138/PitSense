from app import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test 1: dataset/validate
r = client.get("/dataset/validate")
val = r.json()
passed = val["passed"]
total = val["total"]
overall = val["overall_status"]
print(f"Validate: {overall} ({passed}/{total})")

# Test 2: upload lap_04.mp3
with open("../dataset/audio/lap_04.mp3", "rb") as f:
    res = client.post("/upload", files={"file": ("lap_04.mp3", f, "audio/mp3")})

data = res.json()
tel = data.get("telemetry", {})
print(f"HTTP status: {res.status_code}")
print(f"available:   {tel.get('available')}")
print(f"lap:         {tel.get('lap')}")
print(f"lap_time:    {tel.get('lap_time')}")
print(f"sector_1:    {tel.get('sector_1')}")
print(f"sector_2:    {tel.get('sector_2')}")
print(f"sector_3:    {tel.get('sector_3')}")
print(f"top_speed:   {tel.get('top_speed')}")
ctx = data.get("telemetry_context", "")
print(f"context:\n{ctx}")
