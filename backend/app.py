from fastapi import FastAPI, UploadFile, File, Form, Header, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import os
import shutil
import re
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
from dataset_loader import (
    get_telemetry_for_file,
    run_dataset_validation,
    build_telemetry_context_string,
    get_simulation_samples,
)
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
    return {
        "message": "PitSense Backend Running 🚀"
    }


@app.get("/dataset/validate")
def validate_dataset():
    """
    Validation endpoint to verify dataset loading for expected samples.
    """
    return run_dataset_validation()


@app.get("/simulation/samples")
def list_simulation_samples():
    """
    Returns available dataset observations for simulation mode, dynamically discovered.
    """
    return get_simulation_samples()


@app.get("/simulation/audio/{filename}")
def get_simulation_audio(filename: str):
    """
    Returns audio file for simulation playback.
    """
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
        perception      = transcribe_and_perceive(filepath)
        transcript      = perception["transcript"]
        audio_emotion   = perception["audio_emotion"]
        speech_features = perception["speech_features"]

        emotion      = analyze_emotion(transcript)
        driver_state = analyze_driver_state(transcript, emotion)
        stress_index = compute_stress_index(audio_emotion, speech_features, transcript)
        ai_brief     = generate_summary_with_source(transcript, emotion, driver_state)

        # Session tracking
        active_session_id = session_id or x_session_id or session or "default_session"

        # Lookup telemetry metadata from dataset (returns None if not matched)
        raw_telemetry = get_telemetry_for_file(file.filename)

        # Normalise: always return a telemetry object — available=False when unmatched
        telemetry_response = raw_telemetry if raw_telemetry else {"available": False}

        # Build a human-readable context string for the Race Engineer
        telemetry_context = build_telemetry_context_string(raw_telemetry)
        if telemetry_context:
            print(f"[TELEMETRY] Attached to analysis for {file.filename}")

        # Attempt to extract lap and lap_time from telemetry or filename if not explicitly provided
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

        # Record observation in session history
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

        # Phase 7 — Temporal Stress & Lap-Time Correlation Analysis
        temporal_analysis   = analyze_temporal_session(history)
        lap_performance     = analyze_lap_performance(history)
        engineering_insight = generate_engineering_insight(temporal_analysis, lap_performance, driver_state)

        # Phase 8 — Engineer Decision Support Engine
        engineer_decision   = evaluate_engineer_decision(
            driver_state=driver_state,
            stress_index=stress_index,
            temporal_analysis=temporal_analysis,
            audio_emotion=audio_emotion,
            transcript=transcript,
        )

        # Phase 5 — Actionable Recommendation Engine
        actionable_insight  = generate_actionable_insight(
            driver_state=driver_state,
            stress_index=stress_index,
            audio_emotion=audio_emotion,
            text_emotion=emotion,
            temporal_analysis=temporal_analysis,
            lap_performance=lap_performance,
        )

        return {
            "success":                    True,
            "filename":                   file.filename,
            # Telemetry — always present, available=True/False
            "telemetry":                  telemetry_response,
            "telemetry_context":          telemetry_context,
            "transcript":                 transcript,
            "emotion":                    emotion,
            "driver_analysis":            driver_state,
            "ai_summary":                 ai_brief["summary"],
            "engineer_reply":             ai_brief["engineer_reply"],
            "ai_source":                  ai_brief["ai_source"],
            # Phase 1 — HF audio perception
            "audio_emotion":              audio_emotion,
            # Phase 2 — Explainable Stress Index
            "stress_index":               stress_index,
            # Phase 7 — Temporal Stress & Lap-Time Correlation
            "temporal_analysis":          temporal_analysis,
            # Phase 8 — Engineer Decision Support Engine
            "engineer_decision":          engineer_decision,
            # Phase 4 — Lap Performance Correlation
            "lap_performance":            lap_performance,
            # Decision Support Insights
            "engineering_insight":        engineering_insight,
            "engineering_recommendation": actionable_insight,
        }

    except Exception as e:
        # Surface a useful message to the frontend instead of a raw 500.
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Always clean up the uploaded file — we don't need it after processing.
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
    # Build telemetry context string from session telemetry if present
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
