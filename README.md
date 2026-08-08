# PitSense

> AI-powered race intelligence that turns driver communication into actionable engineering insight.

---

## Overview

**PitSense** is an advanced AI-powered race engineering decision-support platform designed for motorsport teams. During high-stakes sessions, race engineers must process fast, stressful, and unstructured driver radio communications while making split-second tactical calls.

PitSense automates communication analysis by ingesting live driver voice audio or uploaded radio recordings, generating real-time operational insights, driver workload metrics, and strategic recommendations.

### Core Capabilities

- **Processes Driver Radio/Audio**: Ingests audio files (`.mp3`, `.wav`, `.m4a`) and live voice recordings.
- **Whisper Transcription**: Transcribes race radio transmissions into precise text.
- **Driver Emotion Detection**: Analyzes acoustic tone and verbal markers to classify emotional state (e.g., Calm, Anxious, Frustrated, Urgent).
- **Stress & Urgency Scoring**: Computes quantitative stress (0–100%) and urgency (0–100%) indices.
- **Driver State Classification**: Categorizes overall driver state (`Calm`, `Concerned`, `High Stress`, `Emergency`).
- **Vehicle Issue Detection**: Identifies reported handling, mechanical, or thermal anomalies (e.g., tyre degradation, balance loss, overheating).
- **Strategy Recommendations**: Recommends actionable pit wall responses and stint adjustments.
- **AI Race Engineer Report**: Compiles executive summaries, vehicle health checks, telemetry flags, and confidence scores.
- **Ask the Race Engineer**: Interactive AI chat interface for querying session details in natural language.
- **Browser Microphone Support**: Built-in HD voice recording directly from the web dashboard.
- **Local Session Persistence**: Automatically stores session history and conversation logs locally.

---

## Key Features

- 🎙️ **Live Driver Radio** — Real-time browser audio recording with waveform visuals and simulated demo comms.
- 🧠 **Emotion Detection** — Multi-modal sentiment and confidence scoring from driver radio transmissions.
- 🏎️ **Driver Intelligence** — Real-time assessment of driver workload, stress levels, and operational state.
- ⚠️ **Risk Assessment** — Automatic classification of session risk (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
- 🏁 **Race Strategy Recommendations** — Context-aware pit window and stint strategy advice.
- 🤖 **AI Race Engineer** — Automated structured reports summarizing executive data, metrics, and radio replies.
- 💬 **Ask the Race Engineer** — Conversational AI chat with clickable suggested questions, quick actions, and strict factual grounding.
- 📚 **Persistent Session History** — Sidebar session switching, session search, renaming, and local storage retention.

---

## How It Works

```
Driver Radio
    │
    ▼
Whisper Transcription
    │
    ▼
Emotion Analysis
    │
    ▼
Driver State Analysis
    │
    ▼
Issue Detection
    │
    ▼
Strategy Recommendations
    │
    ▼
AI Race Engineer
```

---

## Tech Stack

### Frontend
- **Framework**: [React 19](https://react.dev/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Charts**: [Chart.js](https://www.chartjs.org/) & [React-ChartJS-2](https://react-chartjs-2.js.org/)
- **HTTP Client**: [Axios](https://axios-http.com/)
- **Routing**: [React Router DOM](https://reactrouter.com/)

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Validation**: [Pydantic](https://docs.pydantic.dev/)
- **Multipart Processing**: `python-multipart`

### AI / ML & Heuristics
- **Transcription**: Whisper Speech Recognition engine
- **Emotion & Driver State Models**: Rule-based lexical & acoustic keyword intelligence
- **Race Engineer AI**: Context-grounded operational reasoning engine with telemetry guardrails

### Styling & Design
- Apple-inspired dark glassmorphism UI system
- Vanilla CSS tokens + [TailwindCSS v4](https://tailwindcss.com/)

### Storage
- Browser `localStorage` for session persistence & chat logs

### Development Tools
- Python `venv`
- Node.js & npm

---

## Project Structure

```
PitSense/
├── backend/
│   ├── ai/
│   │   ├── config/
│   │   │   └── racing_keywords.py    # Racing terminology dictionary
│   │   ├── correlation.py             # Feature correlation utilities
│   │   ├── driver_state.py            # Driver stress/urgency heuristic model
│   │   ├── emotion_model.py           # Speech emotion classification
│   │   ├── llm_summary.py             # Summary helper logic
│   │   ├── race_engineer.py           # Report generator & /chat query engine
│   │   └── whisper_model.py           # Audio transcription handler
│   ├── database/                      # Database models & handlers
│   ├── outputs/                       # Generated analysis outputs
│   ├── routes/                        # FastAPI route modules
│   ├── uploads/                       # Temp audio upload storage
│   ├── app.py                         # FastAPI application entry point
│   └── requirements.txt               # Backend Python dependencies
├── docs/
│   └── screenshots/                   # Application screenshots
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   └── Sidebar.jsx        # Navigation & session history sidebar
│   │   │   ├── dashboard/
│   │   │   │   ├── AISummary.jsx      # AI Race Engineer report card
│   │   │   │   ├── DriverGauge.jsx    # Gauge visualizations
│   │   │   │   ├── EmotionCard.jsx    # Emotion breakdown card
│   │   │   │   ├── PerformanceGraph.jsx
│   │   │   │   └── TranscriptCard.jsx # Speech transcript display
│   │   │   ├── engineer/
│   │   │   │   ├── ChatMessage.jsx    # Engineer/User chat bubbles
│   │   │   │   ├── EngineerChat.jsx   # Interactive AI chat container
│   │   │   │   ├── EngineerInput.jsx  # Input bar & key handlers
│   │   │   │   └── SuggestedQuestions.jsx # Preset question pills & actions
│   │   │   ├── upload/
│   │   │   │   └── UploadCard.jsx     # Live recording & upload dropzone
│   │   │   ├── AudioPlayer.jsx
│   │   │   └── Loader.jsx
│   │   ├── hooks/
│   │   │   └── useAudioRecorder.js    # MediaRecorder browser hook
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx          # Main application dashboard
│   │   │   └── History.jsx            # Session history page
│   │   ├── services/
│   │   │   └── api.js                 # Axios API service configuration
│   │   ├── utils/
│   │   │   ├── engineerAI.js          # Client-side AI fallback engine
│   │   │   └── sessions.js            # LocalStorage session utilities
│   │   ├── App.jsx
│   │   ├── index.css                  # Core CSS tokens & animations
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites
- **Python**: 3.9+ installed
- **Node.js**: v18+ and `npm` installed

### Setup Instructions

#### 1. Clone Repository
```bash
git clone https://github.com/abhinavg138/PitSense.git
cd PitSense
```

#### 2. Backend Setup
Navigate into the `backend` directory, create a Python virtual environment, and install dependencies:

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup
In a new terminal window, navigate to the `frontend` directory and install Node dependencies:

```bash
cd frontend
npm install
```

#### 4. Run Application

**Start Backend Server:**
```bash
# Inside backend/ directory with active venv:
uvicorn app:app --reload
```
The FastAPI backend will start running on `http://127.0.0.1:8000`.

**Start Frontend Development Server:**
```bash
# Inside frontend/ directory:
npm run dev
```
Open your browser and navigate to `http://localhost:5173`.

---

## Usage

1. **Start PitSense**: Launch both backend and frontend servers following the setup guide above.
2. **Select Input Method**: Click **Upload Audio** to upload a file (`.mp3`, `.wav`, `.m4a`) or click **Record Audio** to record live via browser microphone.
3. **Record Driver Comms**: Speak into the microphone or use the **Simulate Demo Recording** button.
4. **Pipeline Processing**: Watch the step-by-step progress indicator (Upload → Whisper → Emotion → Intelligence → Complete).
5. **Review Speech Transcript**: Read the transcribed audio in the transcript card.
6. **Analyze Driver State & Emotion**: Review stress percentages, urgency metrics, and primary driver emotion classification.
7. **Inspect AI Race Engineer Report**: Examine detected vehicle issues, strategy recommendations, and suggested pit wall radio replies.
8. **Ask the Race Engineer**: Scroll down to **"Ask the Race Engineer"**, click a suggested question or type a custom question (e.g. *"Why did you recommend a pit stop?"*).
9. **Switch Between Sessions**: Use the left sidebar to switch between saved sessions or click **+ New Analysis** to start fresh.

---

## AI Safety / Data Integrity

PitSense enforces strict factual guardrails to prevent hallucinating unverified vehicle telemetry:

- **Strict Session Scope**: Answers generated by the AI Race Engineer rely exclusively on the data captured during the current session (transcript, emotion, driver state, stress/urgency scores, and identified issues).
- **Telemetry Guardrail**: If a user asks for telemetry metrics not present in the session (such as exact fuel levels, lap times, tyre temperatures, brake temperatures, sector times, or tyre compounds), the system explicitly states:
  > *"That information is not available in the current session."*

---

## Hackathon Focus

### The Problem
During motorsport events, pit wall engineers must process immense volumes of high-speed driver radio communication while managing race strategy under extreme time pressure and high stress. Important verbal cues indicating handling instability or driver fatigue can easily be overlooked.

### Why PitSense Matters
PitSense converts unstructured driver audio into structured operational intelligence. By pairing speech emotion detection with real-time driver state modeling, PitSense equips race engineers with rapid, data-backed decision support when seconds count.

---

## Roadmap

- ⚡ **Real-time Streaming Transcription**: Live audio stream chunking for sub-second radio processing.
- 📡 **Live Telemetry Integration**: Integration with CAN bus / telemetry data streams (tyre temps, speed, fuel load).
- 📊 **Historical Driver Analytics**: Long-term driver stress baseline tracking across multiple stints and races.
- 🏎️ **Strategy Simulation Engine**: Monte Carlo pit window and undercut/overcut simulation.
- 👥 **Multi-User Team Dashboards**: Role-based views for Race Engineer, Performance Engineer, and Strategist.
- ☁️ **Cloud Deployment**: Containerized deployment pipelines for AWS / GCP edge environments.

---

## Screenshots

> *Placeholder: Add application screenshots to `docs/screenshots/`.*

- **Dashboard Overview**: `docs/screenshots/dashboard.png`
- **AI Race Engineer Report**: `docs/screenshots/race-engineer.png`
- **Live Microphone Recording**: `docs/screenshots/microphone.png`
- **Ask the Race Engineer Chat**: `docs/screenshots/engineer-chat.png`

---

## License

This project currently has no license.

---

## Author

**Abhinav Gupta**
