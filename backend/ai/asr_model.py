import os
import subprocess
import tempfile

from transformers import pipeline

# Load Parakeet once at import time so every request reuses the same model.
# nvidia/parakeet-tdt-0.6b-v3 is a CTC/TDT model; chunk_length_s enables
# long-form transcription without hitting the encoder's context limit.
asr = pipeline(
    "automatic-speech-recognition",
    model="nvidia/parakeet-tdt-0.6b-v3",
    chunk_length_s=30,
)

# Parakeet's internal _forward calls model.generate(**inputs) directly,
# bypassing any generate_kwargs passed to the pipeline constructor or call.
# Patching the model's generation_config is the only path that reaches
# _validate_generated_length and suppresses the default max_length warning.
asr.model.generation_config.max_new_tokens = 448


def _to_wav_16k_mono(src: str) -> str:
    """Convert any audio file to a 16 kHz mono WAV using FFmpeg.

    Parakeet expects 16 kHz mono PCM; this handles whatever the browser or
    user uploads (.m4a, .mp3, .webm, .wav, …) without touching the frontend.
    Returns the path to the temporary WAV file — caller is responsible for
    deleting it.
    """
    # Use a named temp file so FFmpeg can write to it; delete=False because
    # FFmpeg opens the file itself after we close the handle here.
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    subprocess.run(
        [
            "ffmpeg",
            "-y",           # overwrite without prompting
            "-i", src,      # input file (any format FFmpeg understands)
            "-ar", "16000", # resample to 16 kHz
            "-ac", "1",     # downmix to mono
            "-f", "wav",    # force WAV container
            tmp_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return tmp_path


def transcribe_audio(filepath: str) -> str:
    """Transcribe audio at *filepath* and return the transcript string.

    Accepts any format FFmpeg can decode; converts to 16 kHz mono WAV
    internally, runs Parakeet, then cleans up the temporary file.
    """
    wav_path = _to_wav_16k_mono(filepath)
    try:
        result = asr(wav_path)
    finally:
        # Always remove the temp WAV even if inference raises an exception.
        os.remove(wav_path)

    return result["text"]