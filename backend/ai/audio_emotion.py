"""
PitSense audio-domain emotion recognition.

The Hugging Face checkpoint used here has two historical layouts. Older local
copies contain the trained head as classifier.dense -> classifier.output,
with a 1024-dimensional projection. Newer revisions use the modern
Wav2Vec2ForSequenceClassification layout. This loader supports the older
checkpoint without changing the user's installed Transformers/PyTorch
versions.
"""

import os
from typing import Dict, Any

import torch
import torch.nn.functional as F
from safetensors.torch import load_file
from transformers import AutoConfig, AutoFeatureExtractor, AutoModelForAudioClassification

_MODEL_ID = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
_LOCAL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models", "audio_emotion")
)
_LOCAL_MODEL_AVAILABLE = all(
    os.path.isfile(os.path.join(_LOCAL_PATH, filename))
    for filename in ("config.json", "model.safetensors", "preprocessor_config.json")
)
_MODEL_PATH = _LOCAL_PATH if _LOCAL_MODEL_AVAILABLE else _MODEL_ID

_DEFAULT_LABELS = [
    "angry", "calm", "disgust", "fearful",
    "happy", "neutral", "sad", "surprised",
]

_UNAVAILABLE = {"label": "unavailable", "confidence": 0.0, "probabilities": {}}

_model = None
_feature_extractor = None
_load_error = None


def _resolve_weight_file() -> str:
    local_weights = os.path.join(_LOCAL_PATH, "model.safetensors")
    if os.path.isfile(local_weights):
        return local_weights

    from huggingface_hub import hf_hub_download
    return hf_hub_download(repo_id=_MODEL_ID, filename="model.safetensors")


def _load_model() -> tuple[Any, Any]:
    config = AutoConfig.from_pretrained(_MODEL_PATH)

    # The local checkpoint that produced the original UNEXPECTED/MISSING
    # warning has a 1024 -> 1024 trained projection, while its config may
    # advertise the newer 1024 -> 256 projection. Force the architecture to
    # match the actual trained tensors before constructing the model.
    config.classifier_proj_size = 1024

    model = AutoModelForAudioClassification.from_config(config)

    weights_path = _resolve_weight_file()
    state_dict = load_file(weights_path, device="cpu")

    mapped_state = {}
    for key, value in state_dict.items():
        if key == "classifier.dense.weight":
            mapped_state["projector.weight"] = value
        elif key == "classifier.dense.bias":
            mapped_state["projector.bias"] = value
        elif key == "classifier.output.weight":
            mapped_state["classifier.weight"] = value
        elif key == "classifier.output.bias":
            mapped_state["classifier.bias"] = value
        else:
            mapped_state[key] = value

    missing, unexpected = model.load_state_dict(mapped_state, strict=False)
    if missing or unexpected:
        raise RuntimeError(
            "Audio emotion checkpoint could not be loaded exactly. "
            f"Missing keys: {missing}; Unexpected keys: {unexpected}"
        )

    model.eval()
    feature_extractor = AutoFeatureExtractor.from_pretrained(_MODEL_PATH)

    head_norm = float(model.classifier.weight.detach().norm().item())
    if head_norm < 0.5:
        raise RuntimeError(
            f"Audio emotion classifier head norm is unexpectedly small ({head_norm:.4f})."
        )

    return model, feature_extractor


try:
    _model, _feature_extractor = _load_model()
    print(
        "[audio_emotion] Loaded trained Wav2Vec2 emotion checkpoint "
        f"({'local' if _LOCAL_MODEL_AVAILABLE else 'Hugging Face fallback'})."
    )
except Exception as _exc:
    _load_error = _exc
    _model = None
    _feature_extractor = None
    print(f"[audio_emotion] WARNING: model load failed — {_exc}")


# Compatibility with existing admin/control-center code.
_pipe = _model


def _labels() -> Dict[int, str]:
    try:
        config = AutoConfig.from_pretrained(_MODEL_PATH)
        id2label = getattr(config, "id2label", {}) or {}
        return {
            index: str(id2label.get(index, id2label.get(str(index), fallback))).lower()
            for index, fallback in enumerate(_DEFAULT_LABELS)
        }
    except Exception:
        return {index: label for index, label in enumerate(_DEFAULT_LABELS)}


_ID2LABEL = _labels()


def analyze_audio_emotion(wav_path: str) -> dict:
    """Run the trained HF audio emotion classifier on a 16 kHz mono WAV file."""
    if _model is None or _feature_extractor is None:
        return _UNAVAILABLE

    try:
        import numpy as np
        import librosa

        waveform, _ = librosa.load(wav_path, sr=16000, mono=True)
        if waveform is None or len(waveform) == 0:
            return _UNAVAILABLE

        inputs = _feature_extractor(
            waveform,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        )

        with torch.no_grad():
            logits = _model(
                input_values=inputs.input_values,
                attention_mask=getattr(inputs, "attention_mask", None),
            )
            probabilities = F.softmax(logits.logits, dim=-1).squeeze(0).cpu().numpy()

        if not isinstance(probabilities, np.ndarray) or probabilities.size == 0:
            return _UNAVAILABLE

        probability_map = {
            _ID2LABEL.get(index, f"class_{index}"): round(float(score), 4)
            for index, score in enumerate(probabilities)
        }
        top_index = int(probabilities.argmax())
        top_label = _ID2LABEL.get(top_index, f"class_{top_index}")

        return {
            "label": top_label,
            "confidence": round(float(probabilities[top_index]), 4),
            "probabilities": probability_map,
        }

    except Exception as exc:
        print(f"[audio_emotion] WARNING: inference failed — {exc}")
        return _UNAVAILABLE
