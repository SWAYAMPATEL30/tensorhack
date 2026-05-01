import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Enum, ForeignKey
from database import Base

class SessionStatus(str, enum.Enum):
    INITIALIZED = "INITIALIZED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"

class CustomerSession(Base):
    __tablename__ = "customer_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    secure_token = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.INITIALIZED)
    created_at = Column(DateTime, default=datetime.utcnow)

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("customer_sessions.id"), nullable=False)
    ip_address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TranscriptRecord(Base):
    __tablename__ = "transcript_records"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("customer_sessions.id"), nullable=False)
    raw_dialogue = Column(String, nullable=True)
    extracted_income = Column(Integer, nullable=True)
    extracted_profession = Column(String, nullable=True)

class RiskEvaluation(Base):
    __tablename__ = "risk_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("customer_sessions.id"), nullable=False)
    cv_age_estimate = Column(Float, nullable=True)
    llm_behavioral_persona = Column(String, nullable=True)
    llm_risk_band = Column(String, nullable=True)
    final_approval_decision = Column(Boolean, nullable=True)

class LoanOffer(Base):
    __tablename__ = "loan_offers"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("customer_sessions.id"), nullable=False)
    maximum_amount = Column(Float, nullable=True)
    tenure_months = Column(Integer, nullable=True)
    interest_rate = Column(Float, nullable=True)
    calculated_emi = Column(Float, nullable=True)
