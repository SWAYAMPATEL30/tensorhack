# Poonawalla Fincorp Loan Wizard - Comprehensive Project Documentation

## System Overview
The **Poonawalla Fincorp Loan Wizard** is an enterprise-grade, real-time AI onboarding system specifically designed to handle end-to-end loan application processing securely and intelligently. It features automated identity verification, credit risk valuation, fraud detection, and multi-modal interaction (video and audio processing in real-time) to generate structured loan offers securely on the fly.

This project is built using modern tech stacks including FastAPI for asynchronous, high-performance backends and a Next.js (React) architecture for fluid front-end experiences, tightly integrated with a static fully-featured administration dashboard for observability and operations.

---

## Technical Stack

### Backend
- **Framework**: `FastAPI` (Python 3.9+) running on an asynchronous `Uvicorn` server. 
- **Database**: Local persistence configured using `SQLite` via direct querying and `SQLAlchemy` ORM wrapper capabilities (for v1 backward compatibility).
- **Communication Protocol**: Dual-support architecture: REST API for standard stateless operations (CRUD and Analytics) and `WebSockets` for continuous multi-media stream processing (audio/video).
- **Machine Learning Integration**: Implemented via `joblib` loading serialized pre-trained `scikit-learn`/`XGBoost` models for rapid in-memory inference.

### Frontend (Main Applicant UI)
- **Framework**: `Next.js` 16+ & `React` 19+ (TypeScript).
- **Styling**: Modern `Tailwind CSS 4.0` integration with Geist Font families.
- **Role**: Provides the client interface handling responsive capture of video and audio feeds securely, invoking the AI models and processing multi-step onboarding sequences (1. document scan, 2. biometrics, 3. profile data/audio interactions).

### Administrative Interface
- **Framework**: Static HTML/Vanilla JS directly served securely through FastAPI's `StaticFiles`.
- **Role**: Read-only observability platform providing live insight into system performance, current sessions, auditing, aggregated multi-model insights (AUC, F1, latency), fraud metrics, and real-time alerts.

---

## Architecture & Component Drilldown

### 1. The FastAPI Backend (`backend/main.py`)
This represents the crux of system operations. Key domains include:

- **Session Management**: Session generation with persistent audit logging linked against DB entities. Multi-endpoint support (v1 legacy models supported alongside v2 optimized flows).
- **Video Processing (via WebSocket)**: Captures Base64 frames from UI, running bounding box object detection (via YOLO bindings `ml.cv_engine`) and age/stress estimation for live feedback. Stores intermediate logs to the database preventing memory bloat.
- **Audio Processing / STT (via WebSocket)**: Streamed audio segments convert continuous speech to text sequences utilizing local optimized mechanisms (e.g., Whisper in `ml.stt_engine`).
- **REST APIs**: Used synchronously inside the user interface to finalize scores, execute fraud logic matching, calculate custom credit rules (offers algorithm), and finalize/persist outputs to the data layer.

### 2. Applied Machine Learning Ensemble (Models & Engines)
The processing layer makes concurrent inferences against isolated models for decision orchestration:

- **`credit_risk` (XGBoost)**: Probabilistic default prediction utilizing demographic, employment, and current credit data mapped against the applicant session.
- **`fraud`** (Fraud Detector): ML ensemble mapping mismatch anomalies (Video Age vs. Declared Age, Speed anomalies, Live Stress).
- **`age_validator`**: Specialized regression model comparing video-frame averaged ages against declared documentation ages.
- **`offer_engine`**: SHAP-explained tiering engine determining maximum loan allowance, tailored interest rate tiers (Prime, Conservative, Flexible), and repayment structuring limits based on Risk classification (LOW/MEDIUM/HIGH risk bands).
- **`intent` (Intent Classifier)**: NLP model powered natively to interpret transcript semantics against targeted goals (Income assertion, Name capture).
- **`emotion`**: Stress signal estimation based directly on audio characteristics.

### 3. Analytics & Logging System (Data Layer)
*Built atop structured SQLite tables setup in `backend/main.py`.*
- **Table `sessions`**: The core source of truth. Captures applicant identifiers, calculated scores (fraud, age, credit), transcript texts, derived loan offers, and final outcomes.
- **Table `audit_logs`**: Crucial compliance structure capturing explicit event triggers against individual endpoints mapped to their originating model, preserving inputs, outputs, precision/confidence metrics, and compute latency (DPDPA 2023 compliant data-trail).
- **Table `video_frames`**: Forensic validation table linking frame timestamps with liveness validations to preserve KYC integrity natively.

### 4. Interactive Applicant Interface (`frontend/src/components/VideoOnboarding.tsx`)
- Secure camera invocation via `navigator.mediaDevices`.
- Continuous `setInterval` loops push base64 canvas-drawn frames mapped natively to resolution constraints avoiding payload overload.
- Intelligent stage gate progressions (Phase 1: ID, Phase 2: Biometrics, Phase 3: Affirmation/Voice Capture) unlocked procedurally based on back-end confidence flags from WebSockets/REST outputs.
- Asynchronous finalized calls compile state-held transcript segments and video parameters into the final decision API (`/offer/calculate`) presenting stylized user-centric offers natively within the UI on transaction completion.

---

## Directory Structure Overview
```
/Problem_Statements/loan-onboarding/
│
├── backend/
│   ├── main.py                # Server, FastAPI App, API orchestration
│   ├── models.py              # SQLAlchemy DB modeling (legacy bindings)
│   ├── schemas.py             # Pydantic structured typing parameters
│   └── database.py            # SQLite wrapper configs
│
├── frontend/
│   ├── admin/                 # Static admin dashboard
│   │   ├── index.html         
│   │   └── js/api.js          # Shared Fetch wrapper functionality
│   ├── src/                   # Next.js Source directory
│   │   ├── app/layout.tsx     # Base App initialization/Metadata
│   │   └── components/
│   │       └── VideoOnboarding.tsx # Main Applicant capture component
│   └── package.json           # Frontend dependencies 
│
└── README.md                  # Short operations & execution guide
```

---

## API Highlights (Routing Mechanics)

**Core Real-Time Pipelines**:
- `WS /ws/video/{session_id}` - Unidirectional real-time frame evaluation for stress/liveness testing.
- `WS /ws/audio/{session_id}` - Transcript generation mapping speech semantics.

**Decision & Calculation APIs**:
- `POST /api/risk/score` & `POST /api/fraud/check`: ML Evaluation against established bounds.
- `POST /api/offer/generate`: Assembles limits and creates finalized tier packaging options.

**Observability APIs (Admin side)**:
- `GET /api/health/detailed` - Hardware (RAM/Disk), Database Size, Model latency diagnostics. 
- `GET /api/analytics/summary` - Aggregated daily system statistics, fraud detections vs approvals ratios for UI rendering.

---

## Final Review
The platform combines a highly isolated, ML-heavy Python backend with a cleanly executed front-end capturing platform to facilitate fully intelligent, agentic evaluation protocols for new users aiming seamlessly to secure credit digitally. The separation of concerns ensures scalability across complex modeling logic without inhibiting UI performance or compliance reporting mechanisms.
