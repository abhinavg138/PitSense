import os
from transformers import pipeline

_MODEL_ID = "j-hartmann/emotion-english-distilroberta-base"
_LOCAL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "text_emotion"))
_MODEL_PATH = _LOCAL_PATH if os.path.isdir(_LOCAL_PATH) and os.listdir(_LOCAL_PATH) else _MODEL_ID

# Load model once at startup
emotion_pipeline = pipeline(
    "text-classification",
    model=_MODEL_PATH,
    top_k=None
)


def analyze_emotion(text: str):
    # Whisper sometimes returns empty or whitespace-only strings.
    # The model doesn't handle that well, so fall back to neutral.
    if not text or not text.strip():
        return {
            "emotion": "neutral",
            "confidence": 100,
            "stress": 20,
            "urgency": 10,
            "driver_state": "Calm"
        }

    predictions = emotion_pipeline(text)[0]

    predictions = sorted(
        predictions,
        key=lambda x: x["score"],
        reverse=True
    )

    top = predictions[0]

    emotion = top["label"]
    confidence = round(top["score"] * 100)

    stress_map = {
        "fear": 95,
        "anger": 85,
        "surprise": 75,
        "sadness": 60,
        "neutral": 20,
        "joy": 5,
        "disgust": 70
    }

    urgency_map = {
        "fear": 95,
        "anger": 80,
        "surprise": 70,
        "sadness": 45,
        "neutral": 10,
        "joy": 5,
        "disgust": 75
    }

    driver_state = {
        "fear": "Emergency",
        "anger": "Frustrated",
        "surprise": "Alert",
        "sadness": "Fatigued",
        "neutral": "Calm",
        "joy": "Confident",
        "disgust": "Concerned"
    }

    return {
        "emotion": emotion,
        "confidence": confidence,
        "stress": stress_map[emotion],
        "urgency": urgency_map[emotion],
        "driver_state": driver_state[emotion]
    }