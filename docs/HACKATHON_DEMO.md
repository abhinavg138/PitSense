# PitSense — 2-Minute Judge Pitch & Demonstration Script

This document details the optimal 2-minute demonstration flow for hackathon judging, highlighting end-to-end driver communication perception, vocal emotion, temporal stress evolution, race telemetry alignment, and explainable race engineering decision support.

---

## ⏱️ Timeline & Script (2-Minute Demo)

### 0:00 – 0:20 | Introduction & Problem Statement
- **Action**: Open PitSense Dashboard in browser (`http://localhost:5173`). Point out clean Apple-inspired dark aesthetic.
- **Pitch**:
  > *"PitSense is an explainable AI race engineering platform built for Formula 1 and endurance racing. In high-speed motorsport, driver radio is noisy and emotional, while telemetry is massive. PitSense bridges vocal driver state with race telemetry to give pit walls deterministic, explainable decision support."*

---

### 0:20 – 1:00 | Live Race Simulation Playback
- **Action**: Toggle **"▶ Race Simulation Mode"**. Click **START**.
- **Pitch**:
  > *"We are streaming real Formula 1 driver radio communications lap-by-lap. Notice how HuggingFace Parakeet ASR transcribes the audio, while our dual-domain perception engine analyzes vocal pitch, tempo, and emotion in real time."*
- **Visual Callouts**:
  - Show live transcript popping up.
  - Point to **Driver Stress Index** (`31 → 38 → 51 → 64`).

---

### 1:00 – 1:30 | Explainable Decision Support & Evidence Block
- **Action**: Pause on Lap 50 (or after 4+ observations). Point to **Engineer Decision Support Engine**.
- **Pitch**:
  > *"Look at the decision engine. PitSense doesn't just return a black-box recommendation. It deterministically computes a severity level (`CRITICAL`), recommended action (`PIT AND INSPECT`), and an explicit `WHY?` rationale. Furthermore, our **Evidence Block** displays the exact stress trajectory, lap pace delta (+0.96s vs baseline), and non-causal observational association statement."*
- **Visual Callouts**:
  - Point to **WHY?** reasons.
  - Point to **Data Quality Badges** (`Transcript: AVAILABLE`, `Emotion: AVAILABLE`, `Telemetry: AVAILABLE`, `Correlation: AVAILABLE`).

---

### 1:30 – 1:50 | Gemini Natural-Language Synthesis
- **Action**: Scroll down to the **Race Engineer Summary** & **Interactive AI Radio Assistant**.
- **Pitch**:
  > *"Behind the scenes, Gemini acts as a natural-language synthesis layer. It translates our deterministic backend engineering analysis into concise, realistic race-engineer radio replies."*

---

### 1:50 – 2:00 | Architecture & Session Persistence Wrap-Up
- **Action**: Point to status bar or architecture summary.
- **Pitch**:
  > *"PitSense is powered by HuggingFace Parakeet TDT ASR, HF Emotion models, OpenF1 telemetry, and a durable SQLite temporal store. All temporal intelligence is stored in SQLite so race state is preserved cleanly across backend updates. Thank you!"*

---

## 💡 Optional Judge Q&A Demonstrations

### Q1: "What happens if a service or API fails?"
- **Demo**: PitSense operates with strict fallback guarantees:
  - If Gemini API is unconfigured/rate-limited, PitSense falls back to local deterministic responses.
  - If OpenF1 telemetry is missing, PitSense clearly marks Telemetry as `UNAVAILABLE` or `PARTIAL` without fabricating data.

### Q2: "Does race state survive backend server restarts?"
- **Demo**: Stop the backend process (`Ctrl+C`), restart `uvicorn app:app --reload`, and refresh the frontend.
  - Show how past stress trends, lap baselines, and correlation history survive backend restart.
