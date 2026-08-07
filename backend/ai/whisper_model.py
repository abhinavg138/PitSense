import os

# Tell Whisper exactly where ffmpeg is
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg-9.0-essentials_build\bin"

import whisper

model = whisper.load_model("base")


def transcribe_audio(filepath: str):
    result = model.transcribe(filepath)
    return result["text"]