from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import os
import shutil

from ai.asr_model import transcribe_audio
from ai.emotion_model import analyze_emotion
from ai.driver_state import analyze_driver_state
from ai.race_engineer import generate_summary_with_source, answer_engineer_question_with_source
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ChatRequest(BaseModel):
    transcript: Optional[str] = ""
    emotion: Optional[Dict[str, Any]] = {}
    driver_analysis: Optional[Dict[str, Any]] = {}
    ai_summary: Optional[str] = ""
    question: str
    filename: Optional[str] = ""
    timestamp: Optional[Any] = ""
    chat_history: Optional[List[Any]] = []


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "PitSense Backend Running 🚀"
    }


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        transcript = transcribe_audio(filepath)
        emotion = analyze_emotion(transcript)
        driver_state = analyze_driver_state(transcript, emotion)
        ai_brief = generate_summary_with_source(transcript, emotion, driver_state)

        return {
            "success": True,
            "filename": file.filename,
            "transcript": transcript,
            "emotion": emotion,
            "driver_analysis": driver_state,
            "ai_summary": ai_brief["summary"],
            "engineer_reply": ai_brief["engineer_reply"],
            "ai_source": ai_brief["ai_source"]
        }

    except Exception as e:
        # Surface a useful message to the frontend instead of a raw 500.
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Always clean up the uploaded file — we don't need it after processing.
        if os.path.exists(filepath):
            os.remove(filepath)


@app.post("/chat")
async def chat_with_race_engineer(req: ChatRequest):
    result = answer_engineer_question_with_source(
        transcript=req.transcript or "",
        emotion=req.emotion or {},
        driver_analysis=req.driver_analysis or {},
        ai_summary=req.ai_summary or "",
        question=req.question or "",
        filename=req.filename or "",
        timestamp=str(req.timestamp or "")
    )
    return {
        "success": True,
        "question": req.question,
        "answer": result["answer"],
        "ai_source": result["ai_source"]
    }
