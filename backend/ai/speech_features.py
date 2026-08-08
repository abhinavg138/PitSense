import numpy as np
import soundfile as sf


def extract_speech_features(wav_path: str) -> dict | None:
    """Extract lightweight acoustic features from a 16 kHz mono WAV file.

    Returns a dict of raw feature values, or None if the file cannot be
    read or the audio is too short to produce meaningful features.
    Never returns fabricated values — None signals that this signal is
    genuinely unavailable and must be excluded from any downstream calculation.

    Features extracted:
      rms              — Root-mean-square energy; higher in loud/stressed speech.
      zcr              — Zero-crossing rate; correlates with fricative/tense
                         vocal quality and high-frequency content.
      non_silence_ratio— Proportion of samples above a quiet-room threshold;
                         a proxy for speech density (stressed speech often has
                         fewer pauses).
    """
    try:
        samples, _sr = sf.read(wav_path, dtype="float32")

        # Ensure mono — soundfile may return (N, channels) for stereo files.
        if samples.ndim > 1:
            samples = samples[:, 0]

        # Too short to be meaningful (< 16 samples at 16 kHz = 1 ms).
        if len(samples) < 16:
            return None

        rms = float(np.sqrt(np.mean(samples ** 2)))

        # ZCR: fraction of adjacent sample pairs that cross zero.
        zcr = float(np.mean(np.abs(np.diff(np.sign(samples))) > 0))

        # Non-silence ratio: fraction of samples louder than a quiet-room floor.
        silence_threshold = 0.01  # empirically ~-40 dBFS; below this is silence
        non_silence_ratio = float(np.mean(np.abs(samples) > silence_threshold))

        return {
            "rms": rms,
            "zcr": zcr,
            "non_silence_ratio": non_silence_ratio,
        }

    except Exception as e:
        print(f"[speech_features] WARNING: feature extraction failed — {e}")
        return None
