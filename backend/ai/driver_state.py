def analyze_driver_state(transcript: str, emotion: dict):

    text = transcript.lower()

    stress = emotion["stress"]
    urgency = emotion["urgency"]

    issues = []
    recommendations = []

    # ---------------- TYRES ----------------

    tyre_keywords = [
        "grip",
        "tyre",
        "tire",
        "sliding",
        "oversteer",
        "understeer",
        "traction",
        "locking",
        "rear",
        "front"
    ]

    if any(word in text for word in tyre_keywords):
        issues.append("Tyre Degradation")
        recommendations.append("Consider an earlier pit stop for fresh tyres.")
        stress += 25
        urgency += 20

    # ---------------- ENGINE ----------------

    engine_keywords = [
        "engine",
        "temperature",
        "power",
        "overheating",
        "smoke"
    ]

    if any(word in text for word in engine_keywords):
        issues.append("Engine Issue")
        recommendations.append("Monitor telemetry and reduce engine load.")
        stress += 30
        urgency += 35

    # ---------------- BRAKES ----------------

    brake_keywords = [
        "brake",
        "pedal",
        "locking"
    ]

    if any(word in text for word in brake_keywords):
        issues.append("Brake Issue")
        recommendations.append("Brake temperatures should be checked.")
        stress += 25
        urgency += 30

    # ---------------- DAMAGE ----------------

    damage_keywords = [
        "crash",
        "wall",
        "damage",
        "contact",
        "spin"
    ]

    if any(word in text for word in damage_keywords):
        issues.append("Vehicle Damage")
        recommendations.append("Inspect the car for damage and prepare for repairs.")
        stress += 40
        urgency += 40

    stress = min(stress, 100)
    urgency = min(urgency, 100)

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