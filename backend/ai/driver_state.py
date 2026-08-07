from ai.config.racing_keywords import KEYWORDS


def analyze_driver_state(transcript: str, emotion: dict):

    text = transcript.lower()

    stress = emotion["stress"]
    urgency = emotion["urgency"]

    issues = []
    recommendations = []

    for category in KEYWORDS.values():

        if any(word in text for word in category["words"]):

            issues.append(category["issue"])

            recommendations.append(
                category["recommendation"]
            )

            stress += category["stress"]
            urgency += category["urgency"]

    # Keep values between 0 and 100
    stress = min(stress, 100)
    urgency = min(urgency, 100)

    # Determine driver state
    if urgency >= 90:
        state = "Emergency"

    elif stress >= 70:
        state = "High Stress"

    elif stress >= 40:
        state = "Concerned"

    else:
        state = "Calm"

    return {
        "driver_state": state,
        "stress": stress,
        "urgency": urgency,
        "issues": issues,
        "recommendations": recommendations
    }