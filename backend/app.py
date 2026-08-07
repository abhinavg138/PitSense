import tarfile
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import os
import shutil

from ai.whisper_model import transcribe_audio
from ai.emotion_model import analyze_emotion
from ai.driver_state import analyze_driver_state


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
    return {
        "success": True,
        "filename": file.filename,
        "transcript": transcript,
        "emotion": emotion,
        "driver_analysis": driver_state
    }