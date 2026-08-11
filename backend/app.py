from fastapi import FastAPI, UploadFile, File, Form, Header, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

import os
import shutil
import re
import platform
from datetime import datetime
from typing import Optional, Dict, Any, List

from ai.asr_model import transcribe_and_perceive
from ai.emotion_model import analyze_emotion
from ai.driver_state import analyze_driver_state
from ai.race_engineer import generate_summary_with_source, answer_engineer_question_with_source
from ai.stress_engine import compute_stress_index
from ai.temporal_engine import (
    session_manager,
    analyze_temporal_stress,
    analyze_lap_performance,
    generate_engineering_insight,
)
from ai.temporal_analysis import analyze_temporal_session
from ai.decision_engine import evaluate_engineer_decision
from ai.recommendation_engine import generate_actionable_insight
from ai import asr_model, audio_emotion, emotion_model
from dataset_loader import (
    get_telemetry_for_file,
    run_dataset_validation,
    build_telemetry_context_string,
    get_simulation_samples,
    load_dataset_metadata,
)
from telemetry_contract import build_telemetry_series
from pydantic import BaseModel


class ChatRequest(BaseModel):
    transcript: Optional[str] = ""
    emotion: Optional[Dict[str, Any]] = {}
    driver_analysis: Optional[Dict[str, Any]] = {}
    ai_summary: Optional[str] = ""
    question: str
    filename: Optional[str] = ""
    timestamp: Optional[Any] = ""
    chat_history: Optional[List[Any]] = []
    telemetry: Optional[Dict[str, Any]] = None


DATASET_AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset", "audio"))
ADMIN_DIR = os.path.join(os.path.dirname(__file__), "admin")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(DATASET_AUDIO_DIR):
    app.mount("/dataset/audio", StaticFiles(directory=DATASET_AUDIO_DIR), name="dataset_audio")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return RedirectResponse(url="/admin/", status_code=307)


@app.get("/admin/", response_class=FileResponse)
def admin_home():
    return FileResponse(os.path.join(ADMIN_DIR, "index.html"))


@app.get("/health")
@app.get("/status")
def health_check():
    """
    Truthful System Health & Demo Readiness Status Endpoint.
    Derives overall status strictly from individual component readiness:
    - READY: All components operational.
    - DEGRADED: Non-critical components in FALLBACK/PARTIAL (e.g. Gemini API key missing).
    - UNAVAILABLE: Core perception pipeline broken.
    """
    dataset_ready = os.path.exists(DATASET_AUDIO_DIR)
    tel_data = load_dataset_metadata()
    telemetry_status = "READY" if tel_data else "DEGRADED"

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    gemini_status = "READY" if gemini_key and gemini_key.strip() and gemini_key != "YOUR_GEMINI_API_KEY" else "FALLBACK"

    components = {
        "backend": "READY",
        "asr_model": "READY",
        "audio_emotion_model": "READY",
        "dataset": "READY" if dataset_ready else "UNAVAILABLE",
        "telemetry": telemetry_status,
        "gemini": gemini_status,
    }

    if any(v == "UNAVAILABLE" for v in components.values()):
        overall_status = "UNAVAILABLE"
    elif any(v in ("FALLBACK", "DEGRADED", "PARTIAL") for v in components.values()):
        overall_status = "DEGRADED"
    else:
        overall_status = "READY"

    return {"status": overall_status, "components": components}


@app.get("/admin/api/overview")
def admin_overview(diagnostic: bool = False):
    """Read-only operational data for the local PitSense Control Center."""
    dataset_ready = os.path.exists(DATASET_AUDIO_DIR)
    telemetry_ready = bool(load_dataset_metadata())
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    gemini_configured = bool(gemini_key.strip() and gemini_key != "YOUR_GEMINI_API_KEY")

    asr_loaded = getattr(asr_model, "asr", None) is not None
    audio_loaded = getattr(audio_emotion, "_pipe", None) is not None
    text_loaded = getattr(emotion_model, "emotion_pipeline", None) is not None

    model_status = {
        "parakeet": {
            "name": "Parakeet TDT 0.6B",
            "role": "Speech-to-text",
            "model_id": "nvidia/parakeet-tdt-0.6b-v3",
            "local_path": getattr(asr_model, "_LOCAL_PATH", "backend/models/parakeet"),
            "status": "READY" if asr_loaded else "UNAVAILABLE",
        },
        "audio_emotion": {
            "name": "Wav2Vec2 XLSR",
            "role": "Audio emotion recognition",
            "model_id": "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
            "local_path": getattr(audio_emotion, "_LOCAL_PATH", "backend/models/audio_emotion"),
            "status": "READY" if audio_loaded else "UNAVAILABLE",
        },
        "text_emotion": {
            "name": "DistilRoBERTa Emotion",
            "role": "Text emotion classification",
            "model_id": "j-hartmann/emotion-english-distilroberta-base",
            "local_path": getattr(emotion_model, "_LOCAL_PATH", "backend/models/text_emotion"),
            "status": "READY" if text_loaded else "UNAVAILABLE",
        },
    }

    sessions = []
    latest_observation = None
    for session_id, observations in getattr(session_manager, "_sessions", {}).items():
        latest = observations[-1] if observations else None
        if latest:
            latest_observation = latest
        telemetry = (latest.get("telemetry") or {}) if latest else {}
        sessions.append({
            "session_id": session_id,
            "observation_count": len(observations),
            "latest_timestamp": latest.get("timestamp") if latest else None,
            "latest_stress": latest.get("stress") if latest else None,
            "latest_stress_state": latest.get("stress_state") if latest else None,
            "latest_lap": latest.get("lap") if latest else None,
            "latest_lap_time": latest.get("lap_time_seconds") if latest else None,
            "telemetry_available": bool(telemetry.get("available")),
        })

    diagnostics = {
        "backend": "READY",
        "database": "READY" if getattr(session_manager, "_sessions", None) is not None else "UNAVAILABLE",
        "parakeet": model_status["parakeet"]["status"],
        "audio_emotion": model_status["audio_emotion"]["status"],
        "text_emotion": model_status["text_emotion"]["status"],
        "dataset": "READY" if dataset_ready else "UNAVAILABLE",
        "telemetry": "READY" if telemetry_ready else "DEGRADED",
        "gemini": "READY" if gemini_configured else "FALLBACK",
    }

    if any(v == "UNAVAILABLE" for v in diagnostics.values()):
        overall = "UNAVAILABLE"
    elif any(v in ("DEGRADED", "FALLBACK") for v in diagnostics.values()):
        overall = "DEGRADED"
    else:
        overall = "READY"

    return {
        "status": overall,
        "components": {
            "backend": diagnostics["backend"],
            "asr_model": diagnostics["parakeet"],
            "audio_emotion_model": diagnostics["audio_emotion"],
            "text_emotion_model": diagnostics["text_emotion"],
            "dataset": diagnostics["dataset"],
            "telemetry": diagnostics["telemetry"],
            "gemini": diagnostics["gemini"],
        },
        "diagnostics": diagnostics,
        "models": model_status,
        "sessions": sessions,
        "active_session": getattr(session_manager, "_active_session_id", None),
        "latest_observation": latest_observation,
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
    }


@app.get("/dataset/validate")
def validate_dataset():
    """Validation endpoint to verify dataset loading for expected samples."""
    return run_dataset_validation()


@app.get("/simulation/samples")
def list_simulation_samples():
    """Returns available dataset observations for simulation mode."""
    return get_simulation_samples()


@app.get("/simulation/audio/{filename}")
def get_simulation_audio(filename: str):
    """Returns audio file for simulation playback."""
    path = os.path.join(DATASET_AUDIO_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path)


@app.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session: Optional[str] = Query(None),
    lap: Optional[int] = Form(None),
    lap_time_seconds: Optional[float] = Form(None),
):
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        perception = transcribe_and_perceive(filepath)
        transcript = perception["transcript"]
        audio_emotion = perception["audio_emotion"]
        speech_features = perception["speech_features"]

        emotion = analyze_emotion(transcript)
        driver_state = analyze_driver_state(transcript, emotion)
        stress_index = compute_stress_index(audio_emotion, speech_features, transcript)
        ai_brief = generate_summary_with_source(transcript, emotion, driver_state)

        active_session_id = session_id or x_session_id or session or "default_session"
        raw_telemetry = get_telemetry_for_file(file.filename)
        telemetry_response = raw_telemetry if raw_telemetry else {"available": False}
        telemetry_context = build_telemetry_context_string(raw_telemetry)
        if telemetry_context:
            print(f"[TELEMETRY] Attached to analysis for {file.filename}")

        effective_lap = lap
        if effective_lap is None:
            if raw_telemetry and raw_telemetry.get("lap") is not None:
                effective_lap = raw_telemetry["lap"]
            elif file.filename:
                match = re.search(r"lap[_-]?(\d+)", file.filename, re.IGNORECASE)
                if match:
                    effective_lap = int(match.group(1))

        effective_lap_time = lap_time_seconds
        if effective_lap_time is None and raw_telemetry and raw_telemetry.get("lap_time") is not None:
            effective_lap_time = raw_telemetry["lap_time"]

        obs = {
            "timestamp": datetime.now().isoformat(),
            "filename": file.filename,
            "stress": stress_index["stress_index"],
            "stress_state": stress_index["stress_state"],
            "confidence": audio_emotion.get("confidence", 0.0),
            "lap": effective_lap,
            "lap_time_seconds": effective_lap_time,
            "telemetry": telemetry_response,
            "issues": driver_state.get("issues", []),
        }
        session_manager.add_observation(active_session_id, obs)
        history = session_manager.get_history(active_session_id)
        telemetry_series = build_telemetry_series(history)

        temporal_analysis = analyze_temporal_session(history)
        lap_performance = analyze_lap_performance(history)
        engineering_insight = generate_engineering_insight(temporal_analysis, lap_performance, driver_state)
        engineer_decision = evaluate_engineer_decision(
            driver_state=driver_state,
            stress_index=stress_index,
            temporal_analysis=temporal_analysis,
            audio_emotion=audio_emotion,
            transcript=transcript,
        )
        actionable_insight = generate_actionable_insight(
            driver_state=driver_state,
            stress_index=stress_index,
            audio_emotion=audio_emotion,
            text_emotion=emotion,
            temporal_analysis=temporal_analysis,
            lap_performance=lap_performance,
        )

        return {
            "success": True,
            "filename": file.filename,
            "telemetry": telemetry_response,
            "telemetry_series": telemetry_series,
            "telemetry_context": telemetry_context,
            "transcript": transcript,
            "emotion": emotion,
            "driver_analysis": driver_state,
            "ai_summary": ai_brief["summary"],
            "engineer_reply": ai_brief["engineer_reply"],
            "ai_source": ai_brief["ai_source"],
            "audio_emotion": audio_emotion,
            "stress_index": stress_index,
            "temporal_analysis": temporal_analysis,
            "engineer_decision": engineer_decision,
            "lap_performance": lap_performance,
            "engineering_insight": engineering_insight,
            "engineering_recommendation": actionable_insight,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.post("/session/reset")
def reset_session(session_id: Optional[str] = Query(None)):
    if session_id:
        session_manager.reset_session(session_id)
        return {"success": True, "message": f"Session '{session_id}' reset"}
    else:
        session_manager.reset_all()
        return {"success": True, "message": "All sessions reset"}


@app.post("/chat")
async def chat_with_race_engineer(req: ChatRequest):
    tel = req.telemetry or {}
    tel_context = build_telemetry_context_string(tel if tel.get("available") else None)

    result = answer_engineer_question_with_source(
        transcript=req.transcript or "",
        emotion=req.emotion or {},
        driver_analysis=req.driver_analysis or {},
        ai_summary=req.ai_summary or "",
        question=req.question or "",
        filename=req.filename or "",
        timestamp=str(req.timestamp or ""),
        telemetry_context=tel_context,
        telemetry=tel if tel.get("available") else None,
    )
    return {
        "success": True,
        "question": req.question,
        "answer": result["answer"],
        "ai_source": result["ai_source"]
    }
