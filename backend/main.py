import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
import models
import schemas
import math

app = FastAPI(title="Loan Wizard API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/session/initialize", response_model=schemas.SessionInitResponse)
async def initialize_session(db: Session = Depends(get_db)):
    secure_token = str(uuid.uuid4())
    session = models.CustomerSession(secure_token=secure_token)
    db.add(session)
    db.commit()
    db.refresh(session)
    return schemas.SessionInitResponse(session_id=str(session.id), secure_token=secure_token)

@app.post("/api/v1/telemetry/ingest")
async def ingest_telemetry(payload: schemas.TelemetryPayload, db: Session = Depends(get_db)):
    log = models.TelemetryLog(
        session_id=payload.session_id,
        ip_address=payload.ip_address,
        latitude=payload.latitude,
        longitude=payload.longitude
    )
    db.add(log)
    db.commit()
    return {"status": "success"}

@app.post("/api/v1/ai/process-video-frame", response_model=schemas.ProcessVideoResponse)
async def process_video_frame(payload: schemas.ProcessVideoPayload, db: Session = Depends(get_db)):
    # Mock CV processing
    mock_age = 32.5
    confidence = 0.95
    return schemas.ProcessVideoResponse(cv_age_estimate=mock_age, confidence=confidence)

@app.post("/api/v1/ai/process-audio-chunk", response_model=schemas.ProcessAudioResponse)
async def process_audio_chunk(payload: schemas.ProcessAudioPayload, db: Session = Depends(get_db)):
    # Mock STT inference
    transcript = "My income is 5 Lakhs per year and I am a Doctor."
    income = 500000
    profession = "Doctor"
    
    record = models.TranscriptRecord(
        session_id=payload.session_id,
        raw_dialogue=transcript,
        extracted_income=income,
        extracted_profession=profession
    )
    db.add(record)
    db.commit()
    
    return schemas.ProcessAudioResponse(
        transcript_text=transcript,
        extracted_income=income,
        extracted_profession=profession
    )

@app.post("/api/v1/ai/evaluate-risk", response_model=schemas.EvaluateRiskResponse)
async def evaluate_risk(payload: schemas.EvaluateRiskPayload, db: Session = Depends(get_db)):
    # Mock LLM evaluation
    risk_band = "LOW"
    persona = "Stable Professional"
    truthfulness = 0.98

    eval_record = models.RiskEvaluation(
        session_id=payload.session_id,
        llm_behavioral_persona=persona,
        llm_risk_band=risk_band,
        final_approval_decision=None
    )
    db.add(eval_record)
    db.commit()

    return schemas.EvaluateRiskResponse(
        risk_band=risk_band,
        persona_classification=persona,
        truthfulness_confidence=truthfulness
    )

@app.post("/api/v1/offer/calculate", response_model=schemas.LoanOfferResponse)
async def calculate_offer(payload: schemas.CalculateOfferPayload, db: Session = Depends(get_db)):
    # Fetch risk evaluation and transcipt
    evaluation = db.query(models.RiskEvaluation).filter(models.RiskEvaluation.session_id == payload.session_id).order_by(models.RiskEvaluation.id.desc()).first()
    transcript = db.query(models.TranscriptRecord).filter(models.TranscriptRecord.session_id == payload.session_id).order_by(models.TranscriptRecord.id.desc()).first()
    
    if evaluation and evaluation.llm_risk_band == "HIGH":
        return schemas.LoanOfferResponse(status="REJECTED", reason="High Risk Band")
        
    # We will assume a valid age if we don't store it in db from mock
    # Let's say age is 32.5
    age = 32.5
    if age < 24 or age > 65:
        return schemas.LoanOfferResponse(status="REJECTED", reason="Age out of bounds")
        
    income = transcript.extracted_income if transcript and transcript.extracted_income else 500000
    
    # Calculate simple loan offer
    max_amount = income * 0.8  # e.g., 80% of annual income
    tenure = 36 # 36 months
    rate = 10.5 # 10.5% yearly
    
    # EMI calculation: P * R * (1+R)^N / ((1+R)^N - 1)
    monthly_rate = rate / (12 * 100)
    emi = max_amount * monthly_rate * math.pow(1 + monthly_rate, tenure) / (math.pow(1 + monthly_rate, tenure) - 1)
    
    offer = models.LoanOffer(
        session_id=payload.session_id,
        maximum_amount=max_amount,
        tenure_months=tenure,
        interest_rate=rate,
        calculated_emi=emi
    )
    db.add(offer)
    if evaluation:
        evaluation.final_approval_decision = True
    db.commit()
    
    return schemas.LoanOfferResponse(
        status="APPROVED",
        maximum_amount=max_amount,
        tenure_months=tenure,
        interest_rate=rate,
        calculated_emi=emi
    )
