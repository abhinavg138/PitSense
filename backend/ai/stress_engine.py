# ─────────────────────────────────────────────────────────────────────────────
# PitSense Stress Engine
#
# Combines three observable signals into a single Stress Index (0–100).
#
# Signal weights are defined in STRESS_WEIGHTS and must sum to 1.0.
# When a signal is unavailable (the audio model failed, or acoustic feature
# extraction returned None), that signal is excluded and the remaining weights
# are re-normalised so the output stays on a 0–100 scale.
# Missing data is never substituted with an arbitrary mid-range value.
# ─────────────────────────────────────────────────────────────────────────────

# --- Configuration -----------------------------------------------------------

# How much each signal contributes to the final Stress Index.
# Tune these values; they must sum to 1.0.
STRESS_WEIGHTS = {
    "vocal":      0.50,   # HF audio emotion probabilities
    "speech":     0.20,   # acoustic features (RMS, ZCR, non-silence ratio)
    "transcript": 0.30,   # Parakeet transcript keyword cues
}

# Arousal/stress contribution per audio emotion label (0–100 scale).
# Rationale:
#   - High-arousal, negative valence (angry, fearful) → high stress contribution.
#   - Low-arousal, positive (calm, happy) → very low contribution.
#   - Neutral / ambiguous (surprised, sad) sit in the middle.
# These are *contribution weights per class*, not a direct "emotion = stress"
# substitution.  The final vocal score is a probability-weighted average.
VOCAL_AROUSAL_MAP = {
    "angry":     85,
    "fearful":   80,
    "disgust":   60,
    "surprised": 50,
    "sad":       35,
    "neutral":   20,
    "calm":      10,
    "happy":     10,
}
# Fallback arousal for any label not in the map (model may add new classes).
_UNKNOWN_LABEL_AROUSAL = 30

# Transcript cue tiers — intentionally small and readable.
# CRITICAL cues indicate immediate danger or inability to continue.
# ELEVATED cues indicate difficulty or a developing problem.
_CRITICAL_CUES = [
    "can't keep",
    "cannot keep",
    "lost it",
    "lost control",
    "sliding",
    "damage",
    "help",
    "emergency",
    "gone",
    "spin",
    "crash",
    "box this lap",
]
_ELEVATED_CUES = [
    "struggling",
    "problem",
    "something doesn't feel",
    "something feels off",
    "too much",
    "pit",
    "overheating",
    "vibration",
    "losing",
    "pace",
    "can't",
]

# Stress state bands (inclusive upper bounds applied in order).
_STRESS_BANDS = [
    (30,  "CALM"),
    (60,  "ELEVATED"),
    (80,  "STRESSED"),
    (100, "CRITICAL"),
]

# --- Internal signal computers -----------------------------------------------

def _vocal_score(audio_emotion: dict) -> int | None:
    """Probability-weighted arousal score from HF audio emotion output.

    Returns None when audio_emotion is the unavailable sentinel (empty
    probabilities) so the engine knows to exclude this signal entirely.
    """
    probs = audio_emotion.get("probabilities", {})
    if not probs:
        # "unavailable" sentinel — not a real prediction.
        return None

    score = sum(
        prob * VOCAL_AROUSAL_MAP.get(label, _UNKNOWN_LABEL_AROUSAL)
        for label, prob in probs.items()
    )
    return int(min(100, max(0, round(score))))


def _speech_score(speech_features: dict | None) -> int | None:
    """0–100 acoustic stress score from raw speech features.

    Returns None when features are unavailable — never a synthetic value.
    Ceiling values for normalisation are calibrated against typical 16 kHz
    mono voice recordings produced by FFmpeg at reasonable speaking levels.
    """
    if not speech_features:
        return None

    try:
        rms = speech_features["rms"]
        zcr = speech_features["zcr"]
        nsr = speech_features["non_silence_ratio"]

        # Clamp each feature to [0, 1] against an empirical ceiling.
        # Anything above the ceiling is genuinely loud/tense speech.
        rms_norm = min(rms / 0.15, 1.0)   # 0.15 ≈ loud speech RMS at 16 kHz
        zcr_norm = min(zcr / 0.25, 1.0)   # 0.25 ≈ high-ZCR tense speech
        nsr_norm = min(nsr / 0.90, 1.0)   # 0.90 ≈ nearly continuous speech

        combined = (rms_norm + zcr_norm + nsr_norm) / 3.0
        return int(round(combined * 100))

    except (KeyError, TypeError, ZeroDivisionError) as e:
        print(f"[stress_engine] WARNING: speech score calculation failed — {e}")
        return None


def _transcript_score(transcript: str) -> int:
    """Keyword-based urgency score from the Parakeet transcript (0–100).

    Always returns a real value: 0 means no stress cues were found,
    which is itself meaningful information.
    """
    text = transcript.lower()
    score = 0

    for cue in _CRITICAL_CUES:
        if cue in text:
            score += 20

    for cue in _ELEVATED_CUES:
        if cue in text:
            score += 10

    return min(100, score)


def _stress_state(score: int) -> str:
    for ceiling, label in _STRESS_BANDS:
        if score <= ceiling:
            return label
    return "CRITICAL"


# --- Public API --------------------------------------------------------------

def compute_stress_index(
    audio_emotion: dict,
    speech_features: dict | None,
    transcript: str,
) -> dict:
    """Combine three signals into the PitSense Stress Index.

    Signals that are genuinely unavailable are excluded.  The remaining
    configured weights are re-normalised so the final score remains on the
    0–100 scale.  No signal is ever fabricated.

    Returns:
        {
            "stress_index":  int,         # 0–100
            "stress_state":  str,         # CALM / ELEVATED / STRESSED / CRITICAL
            "stress_signals": {           # only contains signals that ran
                "vocal":      int | None,
                "speech":     int | None,
                "transcript": int,
            }
        }
    """
    # Compute each signal (None means unavailable).
    raw = {
        "vocal":      _vocal_score(audio_emotion),
        "speech":     _speech_score(speech_features),
        "transcript": _transcript_score(transcript),   # always an int
    }

    # Separate available signals for weight normalisation.
    available = {k: v for k, v in raw.items() if v is not None}

    total_weight = sum(STRESS_WEIGHTS[k] for k in available)

    if total_weight == 0:
        # Degenerate — should never happen since transcript is always present.
        stress = 0
    else:
        weighted_sum = sum(available[k] * STRESS_WEIGHTS[k] for k in available)
        stress = int(round(weighted_sum / total_weight))
        stress = max(0, min(100, stress))

    return {
        "stress_index":  stress,
        "stress_state":  _stress_state(stress),
        # Include all signals in the output so callers can see what ran.
        # None values are kept to make unavailability explicit.
        "stress_signals": raw,
    }
