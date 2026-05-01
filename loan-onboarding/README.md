# Poonawalla Fincorp Loan Wizard

An enterprise-grade, real-time AI onboarding system built with FastAPI and an interactive Admin Dashboard. It evaluates credit risk, validates identity (liveness, age discrepancy), performs speech-to-text with STT (Whisper), and generates customized loan offers on the fly using a multi-model ML ensemble.

---

## 🏗 Architecture Overview

1. **FastAPI Backend (`main.py`)**: Core server running on port `8000`. Exposes REST APIs for session management, risk evaluation, and fraud checks, along with WebSockets for real-time video/audio streaming.
2. **ML Ensemble**:
   - **XGBoost Risk Classifier**: Probabilistic default prediction.
   - **Fraud Detector**: Ensemble flagging mismatch anomalies.
   - **Age Validator**: Video-to-declared age regression.
   - **Offer Engine**: SHAP-explained tiering.
   - **Speech Intent**: Audio transcript NLP extraction.
   - **Emotion Classifier**: Stress signal detection via audio.
3. **Frontend Admin Dashboard (`frontend/admin/`)**: Fully static, responsive monitoring dashboard that connects directly to the FastAPI backend without external Node.js dependencies. Served via FastAPI `StaticFiles`.
4. **SQLite Persistence**: Local lightweight database tracks audit trails, model performance, and applicant sessions.

## 🚀 Getting Started

### 1. Requirements

Ensure you have Python 3.9+ and `ffmpeg` installed (for audio processing).

### 2. Setup

```bash
# Create and activate virtual environment
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
pip install rich  # Optional, for enhanced terminal UI
```

### 3. Running the Server

Start the full system (Backend + Admin Dashboard serving):

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **API Docs:** `http://localhost:8000/docs`
- **Admin Dashboard:** `http://localhost:8000/admin/index.html`
- **Live Monitor:** `http://localhost:8000/admin/monitor.html`

## 🧪 Simulation Testing Platform

A complete QA testing pipeline is included to simulate real applicant flows without requiring actual webcam/audio input.

### Run an Automated 20-Profile Test

Tests the full spectrum of applicant conditions (Approvals, Rejections, Fraud, Manual Reviews). Generates an HTML report in the `reports/` folder.

```bash
python scripts/run_full_simulation.py
```

### Run a Single Profile

Run specific edge cases in detail (e.g., normal, premium, fraudster, rejected). Output is visible in the terminal.

```bash
python scripts/simulate_call.py --profile fraudster
```

## 🛡 Live Production Monitoring

You can launch a split-screen live monitor (terminal summary + browser dashboard). Ensure the FastAPI server is already running before executing this.

```bash
python scripts/start_monitor.py
```

## 🔐 Compliance & Security

- All applicant data is stored encrypted at rest via internal SQLite mechanisms.
- Video and Audio streams are transiently processed in memory and immediately discarded.
- Audit trails log every single AI decision (Fraud Score, Risk Band, Confidence levels) for complete DPDPA 2023 regulatory compliance.
