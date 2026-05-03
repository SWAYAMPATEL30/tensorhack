# TensorX: AI-Driven Loan Onboarding Platform

## Overview
TensorX is a next-generation, AI-driven loan onboarding platform built for modern financial institutions. It replaces traditional, tedious form-filling with an interactive, voice-based, real-time AI agent named **Aria**. The platform leverages computer vision, natural language processing, speech-to-text, and predictive risk modeling to instantly verify identity, extract data, assess credit risk, and generate personalized loan offers.

---

## 🏗 System Architecture

The project is structured into two main applications: a FastAPI backend and a Next.js frontend, heavily utilizing WebRTC (LiveKit) for real-time video and audio streaming.

### 1. Frontend (Next.js 14, React, Tailwind CSS)
The frontend serves as the applicant's portal. It is designed with a premium, dynamic, glassmorphic UI to provide a high-end banking experience.
- **`VideoOnboarding.tsx`**: The core component managing the user flow. It handles the LiveKit room connection, multi-phase onboarding (ID Scan -> Biometrics -> Voice Interview), and renders the final Loan Approval dashboard.
- **`TensorXComponents.tsx`**: Contains essential UI widgets:
  - **`ConversationTable`**: Connects via Server-Sent Events (SSE) to the backend to render extracted KYC data in real-time as the applicant speaks.
  - **`PanUploadModal`**: Allows the user to upload their PAN card, compresses it, and sends it to the backend for OCR processing.
  - **`EMIWidget`**: An interactive calculator for visualizing loan terms.
  - **`FocusAlertBanner` & `CalibrationOverlay`**: Visual feedback for the computer vision algorithms analyzing the user's liveness and attention.

### 2. Backend (FastAPI, Python)
The backend acts as the central hub, managing AI models, database persistence, and API endpoints.
- **`main.py`**: The FastAPI server.
  - Manages SQLite database (`loan_wizard.db`) for tracking conversational state.
  - Exposes REST endpoints for OCR (`/api/kyc/upload-pan`), Data streaming (`/api/kyc/conversation-stream`), and Risk/Offer calculation.
  - Integrates pre-trained Machine Learning models (`joblib`) for Credit Risk, Fraud Detection, Age Validation, and Offer Optimization.
  - Processes base64 video frames from the frontend via YOLO (Object Detection) to ensure liveness (e.g., detecting "Live Applicant").
- **`agent.py`**: The LiveKit AI Agent implementation.
  - Uses `livekit-agents` to connect a voice agent to the WebRTC room.
  - **Speech-to-Text (STT)**: Powered by Deepgram (`nova-2`).
  - **LLM Engine**: Powered by Groq (`llama-3.1-8b-instant`) with a strict system prompt to act as Aria, asking KYC questions sequentially.
  - **Text-to-Speech (TTS)**: Powered by Deepgram (`aura-asteria-en`) for a human-like voice.
  - **Computer Vision**: Integrates MediaPipe for real-time Iris/Gaze tracking, firing alerts if the user looks away for too long.
  - Continuously pushes extracted KYC fields (Name, Income, DOB, etc.) back to the FastAPI server via HTTP, which then broadcasts to the frontend via SSE.

---

## 🔄 The User Journey & Data Flow

1. **Initialization**: The user lands on the application and clicks "Initialize Video Onboarding". The frontend requests a LiveKit token from the backend and establishes a WebRTC connection.
2. **Phase 1: Document Scan**: The user uploads their PAN card. The frontend compresses the image to WebP (saving bandwidth) and sends it to the backend. The backend uses `EasyOCR` to extract the PAN number, validates it, and saves it to the session.
3. **Phase 2: Face Liveness**: The backend's YOLO model analyzes frames sent from the frontend to verify a human is present. Concurrently, MediaPipe tracks the user's gaze.
4. **Phase 3: Voice Interview**: Aria (the AI Agent) begins speaking. 
   - She asks questions one by one (Name, DOB, Income, Loan Purpose, etc.).
   - As the user answers, Deepgram transcribes the speech.
   - The LLM identifies the specific data point, triggers a `save_kyc_data` function call, and posts it to the backend.
   - The backend updates the SQLite database and pushes an SSE event to the frontend.
   - The `ConversationTable` and `AI Appraisal` UI panels populate dynamically right before the user's eyes.
5. **Dynamic Risk Assessment**: Mid-conversation, when income is provided, the backend simulates a bureau pull (CIBIL score) and runs a Risk Model, categorizing the user (e.g., ALPHA PRIME).
6. **Final Approval**: Once all data is collected, the agent marks the status as `complete`. The frontend triggers `/api/v1/offer/calculate`, passing the gathered data. The backend's `offer_engine.pkl` determines the final approved limit, interest rate, and tenure, displaying a celebratory dashboard.

---

## 🛠 Tech Stack

*   **Frontend Framework**: Next.js (App Router), React
*   **Styling**: Tailwind CSS
*   **Backend Framework**: FastAPI, Python, Uvicorn
*   **Database**: SQLite (built-in)
*   **Real-time Communication**: LiveKit (WebRTC), Server-Sent Events (SSE)
*   **AI/ML Models**:
    *   LLM: Groq (Llama-3)
    *   Voice: Deepgram (STT/TTS)
    *   Vision: MediaPipe (Iris/Face), Ultralytics YOLOv11s
    *   OCR: EasyOCR
    *   Predictive: Scikit-Learn (XGBoost for Credit Risk, Random Forest for Fraud)

---

## 🚀 Key Features

*   **Conversational Data Extraction**: Eliminates web forms entirely. Users just talk.
*   **Zero-Latency UI Updates**: Utilizing SSE, the frontend UI reacts instantly as the LLM processes data.
*   **Continuous Biometric Authentication**: Background tracking of gaze and liveness prevents spoofing during the interview.
*   **Bandwidth Optimization**: Client-side WebP image compression before uploading documents.
*   **Fallback Resilience**: The agent handles AI rate limits gracefully, and the frontend falls back to mock offers if the predictive models timeout, ensuring a flawless demo experience.
