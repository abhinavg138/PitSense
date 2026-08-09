# PitSense

> AI-powered race intelligence that turns driver communication into actionable engineering insight.

PitSense analyzes race radio audio, transcribes the driver's message using Nvidia Parakeet TDT ASR, detects emotional tone, extracts acoustic speech features, estimates stress and urgency, identifies vehicle and driving concerns, correlates stress with lap performance, and generates structured AI Race Engineer reports and deterministic decisions.

---

## Overview

Motorsport race engineers must interpret compressed, emotional driver radio under extreme time pressure. PitSense turns unstructured driver communications into structured operational intelligence:

- **Audio Perception**: Processes uploaded audio files (.mp3, .m4a, .wav, etc.) or live microphone streams.
- **Parakeet ASR**: High-speed, high-accuracy speech recognition using `nvidia/parakeet-tdt-0.6b-v3`.
- **Dual-Domain Emotion & Acoustic Features**: Combines Transformers text emotion classification (`j-hartmann/emotion-english-distilroberta-base`) and HF audio emotion detection (`ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition`) with speech acoustic metrics (pitch/energy/tempo).
- **Explainable Stress Engine**: Multi-signal scoring engine outputting driver state (`CALM`, `ELEVATED`, `STRESSED`, `CRITICAL`), stress index, and confidence.
- **Temporal & Lap Performance Engine**: Tracks multi-lap stress trends, baseline lap times, performance deltas (+s vs baseline = SLOWER), and non-causal observed associations between driver stress and lap times.
- **Deterministic Engineer Decision Engine**: Rule-based decision support system generating authoritative severity (`CRITICAL`, `STRESSED`, `ELEVATED`, `CALM`), decisions (`PIT_AND_INSPECT`, `RADIO_INTERVENTION`, `MONITOR`, etc.), and explainable reasons.
- **Gemini Race Engineer Response**: Natural-language communication layer using Gemini 3.6 Flash while respecting deterministic backend decisions.
- **OpenF1 Telemetry Integration**: Merges official F1 telemetry (sector times, trap speeds, lap times, pit status) from `metadata.csv` and `openf1_extended.json`.
- **Race Simulation & Session Replay Mode**: Automated playback mode discovering dataset samples to demonstrate evolving multi-lap race scenarios.

---

## System Architecture

```text
Audio (Upload / Simulation)
            │
            ▼
Nvidia Parakeet TDT ASR (nvidia/parakeet-tdt-0.6b-v3)
            │
            ▼
HF Audio Emotion + Text Emotion + Acoustic Speech Features
            │
            ▼
Explainable Stress Engine (Stress Index & Urgency)
            │
            ▼
Temporal Analysis & OpenF1 Lap Correlation
            │
            ▼
Deterministic Engineer Decision Support Engine
            │
            ▼
Gemini Natural-Language Race Engineer Response Layer
            │
            ▼
PitSense Race Engineering Dashboard & Session Replay UI
```

---

## Key Features

| Feature | Description |
| --- | --- |
| **Live Radio & File Upload** | Upload driver radio audio (.mp3, .wav, .m4a) or stream live audio. |
| **Parakeet TDT ASR** | Transcribes high-speed race communications with high accuracy. |
| **Dual-Domain Emotion Perception** | Combines text emotion, audio emotion, and speech acoustics. |
| **Explainable Stress Index** | Transparent driver state scoring (`CALM`, `ELEVATED`, `STRESSED`, `CRITICAL`). |
| **Temporal Stress & Pace Correlation** | Multi-lap trend analysis, performance direction, and non-causal correlation statement. |
| **Engineer Decision Engine** | Authoritative severity, decision, and explicit explainable reasons (`WHY?`). |
| **Gemini Engineer Layer** | Formulates natural-language pit-wall replies based on deterministic context. |
| **Race Simulation Mode** | Auto-discovers dataset samples from `dataset/metadata.csv` and replays race sessions with controls (`START`, `PAUSE`, `NEXT`, `RESET`). |

---

## Tech Stack

### Frontend
- React 19, Vite
- Tailwind CSS v4 + Vanilla CSS Design System
- Lucide React Icons & Chart.js
- Browser MediaRecorder & LocalStorage

### Backend
- FastAPI & Uvicorn
- PyTorch & HuggingFace Transformers
- `nvidia/parakeet-tdt-0.6b-v3` (ASR)
- `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` (Audio Emotion)
- `j-hartmann/emotion-english-distilroberta-base` (Text Emotion)
- Optional Gemini 3.6 Flash (`google-genai` / REST API)

---

## Project Structure

```text
PitSense/
├── backend/
│   ├── ai/
│   │   ├── asr_model.py          # Nvidia Parakeet TDT ASR
│   │   ├── audio_emotion.py      # Audio domain speech emotion model
│   │   ├── decision_engine.py    # Deterministic Race Engineer Decision Engine
│   │   ├── driver_state.py      # Driver state classification
│   │   ├── emotion_model.py     # Text domain emotion model
│   │   ├── llm_summary.py       # Gemini Race Engineer synthesis
│   │   ├── race_engineer.py     # Session-grounded Q&A engine
│   │   ├── recommendation_engine.py # Strategic insights
│   │   ├── speech_features.py   # Acoustic signal processing
│   │   ├── stress_engine.py     # Explainable multi-signal stress engine
│   │   └── temporal_analysis.py # Consolidated Temporal & Correlation engine
│   ├── dataset_loader.py        # OpenF1 & dataset metadata loader
│   ├── app.py                   # FastAPI backend server & endpoints
│   └── requirements.txt
├── dataset/
│   ├── audio/                   # F1 Radio audio files (.mp3)
│   ├── metadata.csv             # Lap timing & OpenF1 metadata
│   ├── openf1_extended.json     # Extended sector & trap speed telemetry
│   └── build_dataset.py         # OpenF1 dataset builder script
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/       # DecisionCard, TelemetryCard, SimulationControls, etc.
│   │   │   └── upload/          # UploadCard
│   │   ├── pages/
│   │   │   └── Dashboard.jsx    # Main Race Intelligence Dashboard
│   │   ├── services/
│   │   └── utils/
│   └── package.json
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg installed locally and accessible in system PATH.

### 1. Set Up Backend

```bash
cd backend
python -m venv .venv
# On Windows:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Optional Gemini Key Configuration

Create `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```
*Note: If no API key is provided, PitSense automatically falls back to deterministic local race engineer replies.*

Start FastAPI backend:
```bash
python -m uvicorn app:app --reload --port 8000
```

### 2. Set Up Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Race Simulation Mode

Click **▶ START RACE SIMULATION** on the dashboard. The application will:
1. Automatically discover available observations from `dataset/metadata.csv` and `dataset/audio/`.
2. Process each sample sequentially through the full AI & telemetry pipeline.
3. Dynamically update the stress trend, lap performance, deterministic decision, and Gemini response.
4. Support controls: `START`, `PAUSE`, `NEXT`, `RESET`.

---

## License & Author

Developed for PitSense AI Race Engineering.
Author: Abhinav Gupta
