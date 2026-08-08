# PitSense

> AI-powered race intelligence that turns driver communication into actionable engineering insight.

PitSense analyzes race radio audio, transcribes the driver's message, detects emotional tone, estimates stress and urgency, identifies likely vehicle or driving issues, and generates a structured AI Race Engineer report.

## Overview

Motorsport teams make critical decisions from short, fast, high-pressure driver radio messages. PitSense turns those unstructured messages into a clearer engineering workflow:

- Processes uploaded driver radio/audio files and browser microphone recordings
- Transcribes communication using Whisper
- Detects driver emotion with a Transformers text-classification model
- Calculates stress and urgency scores
- Determines overall driver state
- Detects racing and vehicle issue categories
- Generates strategy recommendations
- Produces an AI Race Engineer report
- Provides an interactive "Ask the Race Engineer" interface
- Stores analysis sessions and chat history locally in the browser

## Key Features

| Feature | Description |
| --- | --- |
| Live Driver Radio | Record driver comms directly from the browser microphone or upload audio files. |
| Whisper Transcription | Converts race radio audio into text for downstream analysis. |
| Emotion Detection | Uses `j-hartmann/emotion-english-distilroberta-base` through Hugging Face Transformers. |
| Driver Intelligence | Combines emotion, racing keywords, stress, urgency, and driver-state classification. |
| Risk Assessment | Classifies session risk as `LOW`, `MODERATE`, `HIGH`, or `CRITICAL`. |
| Strategy Recommendations | Suggests pit-wall actions based on detected issues and urgency level. |
| AI Race Engineer | Produces a structured report with driver metrics, vehicle health, risk, strategy, and radio response. |
| Ask the Race Engineer | Lets users ask session-specific questions with guardrails against unsupported telemetry claims. |
| Persistent Session History | Saves analysis sessions, active session state, and chat logs in browser `localStorage`. |

## How It Works

```text
Driver Radio
    |
    v
Whisper Transcription
    |
    v
Emotion Analysis
    |
    v
Driver State Analysis
    |
    v
Issue Detection
    |
    v
Strategy Recommendations
    |
    v
AI Race Engineer
```

## Tech Stack

### Frontend

- React 19
- Vite
- React Router DOM
- Axios
- Chart.js and React Chart.js 2
- Lucide React icons
- Tailwind CSS v4 package plus custom CSS in `frontend/src/index.css`
- Browser MediaRecorder API for microphone recording
- Browser `localStorage` for saved sessions

### Backend

- FastAPI
- Uvicorn
- Pydantic
- Python Multipart
- Whisper for speech transcription
- Hugging Face Transformers for emotion classification

### AI / Analysis

- `openai-whisper` loads the Whisper `base` model
- `transformers.pipeline("text-classification")` loads `j-hartmann/emotion-english-distilroberta-base`
- Keyword-based racing issue detection for tyres, engine, brakes, and damage
- Rule-based stress, urgency, risk, and driver-state scoring
- Session-grounded Race Engineer Q&A logic

## Project Structure

```text
PitSense/
|-- backend/
|   |-- ai/
|   |   |-- config/
|   |   |   `-- racing_keywords.py
|   |   |-- correlation.py
|   |   |-- driver_state.py
|   |   |-- emotion_model.py
|   |   |-- llm_summary.py
|   |   |-- race_engineer.py
|   |   `-- whisper_model.py
|   |-- database/
|   |   |-- db.py
|   |   `-- models.py
|   |-- routes/
|   |   |-- emotion.py
|   |   |-- history.py
|   |   |-- report.py
|   |   |-- transcript.py
|   |   `-- upload.py
|   |-- app.py
|   `-- requirements.txt
|-- docs/
|   |-- architecture.png
|   `-- presentation.pptx
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- components/
|   |   |-- hooks/
|   |   |-- pages/
|   |   |-- services/
|   |   |-- utils/
|   |   |-- App.jsx
|   |   |-- index.css
|   |   `-- main.jsx
|   |-- package.json
|   `-- vite.config.js
|-- .gitignore
`-- README.md
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- FFmpeg installed locally

The current Whisper helper appends this Windows path to `PATH`:

```text
C:\ffmpeg-9.0-essentials_build\bin
```

If FFmpeg is installed somewhere else, update the path in `backend/ai/whisper_model.py`.

### 1. Clone the Repository

```bash
git clone https://github.com/abhinavg138/PitSense.git
cd PitSense
```

### 2. Set Up the Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install -r requirements.txt
pip install openai-whisper transformers torch
```

The additional AI packages are required because the backend imports `whisper` and `transformers`.

Start the backend:

```bash
uvicorn app:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

### 3. Set Up the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

## Usage

1. Start both the backend and frontend servers.
2. Open `http://localhost:5173`.
3. Upload an audio file or record live driver radio through the browser.
4. Wait for the processing pipeline to complete.
5. Review the transcript, emotion result, driver state, stress score, urgency score, and AI Race Engineer report.
6. Use "Ask the Race Engineer" to ask questions about the current session.
7. Switch between saved sessions from the sidebar.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Health check for the FastAPI backend. |
| `POST` | `/upload` | Uploads an audio file, transcribes it, analyzes emotion and driver state, and returns the Race Engineer report. |
| `POST` | `/chat` | Answers a session-grounded Race Engineer question. |

## AI Guardrails

The Race Engineer Q&A is designed to stay within the current session context. If a user asks for telemetry that is not present in the transcript or analysis, such as exact fuel levels, lap times, tyre temperatures, brake temperatures, compounds, or sector gaps, PitSense responds that the information is not available in the current session.

## Hackathon Focus

### Problem

Race engineers need to interpret driver radio quickly while also managing strategy, reliability, tyres, safety, and performance. Important signals can be missed when communication is emotional, compressed, or ambiguous.

### Solution

PitSense creates a communication intelligence layer for the pit wall. It converts driver radio into structured insight: what the driver said, how urgent it sounds, what issue category it suggests, how risky the situation is, and what the engineer should do next.

### Why It Matters

PitSense shows how AI can support faster operational decisions in motorsport without pretending to replace telemetry or expert judgment. It focuses on the driver's radio context and clearly separates detected information from unavailable data.

## Roadmap

- Real-time streaming transcription
- Live telemetry integration
- More robust audio emotion analysis from acoustic features
- Driver baseline tracking across sessions
- Multi-driver and multi-team dashboards
- Strategy simulation for pit windows, undercuts, and overcuts
- Cloud deployment with persistent backend storage

## Screenshots and Demo Assets

- Architecture diagram: `docs/architecture.png`
- Presentation deck: `docs/presentation.pptx`

Add application screenshots under `docs/screenshots/` when preparing a final hackathon submission.

## License

No license has been added yet.

## Author

Abhinav Gupta
