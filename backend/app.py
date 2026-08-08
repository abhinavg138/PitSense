import tarfile
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import os
import shutil

from ai.whisper_model import transcribe_audio
from ai.emotion_model import analyze_emotion
from ai.driver_state import analyze_driver_state
from ai.race_engineer import generate_summary, answer_engineer_question
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

    transcript = transcribe_audio(filepath)

    emotion = analyze_emotion(transcript)

    driver_state = analyze_driver_state(transcript, emotion)

    ai_summary = generate_summary(
        transcript,
        emotion,
        driver_state
    )
    return {
        "success": True,
        "filename": file.filename,
        "transcript": transcript,
        "emotion": emotion,
        "driver_analysis": driver_state,
        "ai_summary": ai_summary
    }


@app.post("/chat")
async def chat_with_race_engineer(req: ChatRequest):
    answer = answer_engineer_question(
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
        "answer": answer
    }