from transformers import pipeline

# Load model once
emotion_pipeline = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None
)


def analyze_emotion(text: str):

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