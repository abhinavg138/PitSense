from ai.config.racing_keywords import KEYWORDS

POSITIVE_PHRASES = [
    "feels good",
    "everything feels good",
    "all good",
    "car feels good",
    "balance is good",
    "balance is pretty",
    "balance is stable",
    "holding up well",
    "holding well",
    "grip is good",
    "good grip",
    "looks stable",
    "stable",
    "good pace",
    "keep pushing",
    "can stay out",
    "front grip is holding",
    "rear grip is holding",
    "tyres look good",
    "tyre temperatures look stable",
]

NEGATIVE_BOOST = [
    "help",
    "problem",
    "emergency",
    "losing",
    "gone",
    "sliding",
    "spinning",
    "crash",
    "damage",
    "overheating",
    "temperature",
    "power loss",
    "engine",
]


def analyze_driver_state(transcript: str, emotion: dict):

    text = transcript.lower()

    stress = emotion["stress"]
    urgency = emotion["urgency"]

    issues = []
    recommendations = []

    positive = any(
        phrase in text
        for phrase in POSITIVE_PHRASES
    )

    if positive:

        stress = max(stress - 25, 0)
        urgency = max(urgency - 20, 0)

    else:

        for category in KEYWORDS.values():

            if any(
                word in text
                for word in category["words"]
            ):

                if category["issue"] not in issues:

                    issues.append(category["issue"])
                    recommendations.append(
                        category["recommendation"]
                    )

                stress += category["stress"]
                urgency += category["urgency"]

    for word in NEGATIVE_BOOST:

        if word in text:

            stress += 5
            urgency += 5

    stress = max(0, min(stress, 100))
    urgency = max(0, min(urgency, 100))

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
        "recommendations": recommendations,
    }