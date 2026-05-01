from pydantic import BaseModel
from typing import Optional

class SessionInitResponse(BaseModel):
    session_id: str
    secure_token: str

class TelemetryPayload(BaseModel):
    session_id: str
    ip_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ProcessVideoPayload(BaseModel):
    session_id: str
    frame_base64: str

class ProcessVideoResponse(BaseModel):
    cv_age_estimate: float
    confidence: float

class ProcessAudioPayload(BaseModel):
    session_id: str
    audio_base64: str

class ProcessAudioResponse(BaseModel):
    transcript_text: str
    extracted_income: Optional[int]
    extracted_profession: Optional[str]

class EvaluateRiskPayload(BaseModel):
    session_id: str

class EvaluateRiskResponse(BaseModel):
    risk_band: str
    persona_classification: str
    truthfulness_confidence: float

class CalculateOfferPayload(BaseModel):
    session_id: str

class LoanOfferResponse(BaseModel):
    status: str
    maximum_amount: Optional[float] = None
    tenure_months: Optional[int] = None
    interest_rate: Optional[float] = None
    calculated_emi: Optional[float] = None
    reason: Optional[str] = None
