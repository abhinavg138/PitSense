from transformers import pipeline as hf_pipeline

# Model: ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition
# A wav2vec2-based audio classifier fine-tuned on RAVDESS/TESS for
# speech emotion recognition. Runs locally on CPU, no API key needed.
# Labels: angry, calm, disgust, fearful, happy, neutral, sad, surprised
_MODEL_ID = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

# Sentinel returned when the model is unavailable or inference fails.
# Using "unavailable" (not a real emotion label) makes it unambiguous that
# this is missing data, not a model prediction.
_UNAVAILABLE = {"label": "unavailable", "confidence": 0.0, "probabilities": {}}

try:
    _pipe = hf_pipeline(
        "audio-classification",
        model=_MODEL_ID,
        top_k=None,   # return probabilities for all classes
    )
except Exception as _load_err:
    # Model failed to load (network issue, corrupted cache, etc.).
    # Store None so analyze_audio_emotion() can return _UNAVAILABLE cleanly.
    _pipe = None
    print(f"[audio_emotion] WARNING: model load failed — {_load_err}")


def analyze_audio_emotion(wav_path: str) -> dict:
    """Run the HF audio emotion classifier on a 16 kHz mono WAV file.

    Returns a dict with the top emotion label, its confidence, and full
    per-class probabilities.  If the model is not available or inference
    fails, returns the _UNAVAILABLE sentinel — never a fabricated score.
    """
    if _pipe is None:
        return _UNAVAILABLE

    try:
        results = _pipe(wav_path)
        # results: [{"label": str, "score": float}, ...]
        top = max(results, key=lambda x: x["score"])
        return {
            "label": top["label"],
            "confidence": round(top["score"], 4),
            "probabilities": {r["label"]: round(r["score"], 4) for r in results},
        }
    except Exception as e:
        print(f"[audio_emotion] WARNING: inference failed — {e}")
        return _UNAVAILABLE
