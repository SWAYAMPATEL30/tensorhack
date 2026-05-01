"""
Feature modules: Mock integrations for external services
#15 Verbal consent PDF, #17 DigiLocker, #18 Account Aggregator,
#20 WhatsApp bot, #28 eNACH, #29 UPI disbursal, #30 CKYC,
#33 SMS resumability, #51 Sandbox mode, #54 JWT/MFA, #70 eSign
"""
import time, uuid, os, random, string
from typing import Optional
from pydantic import BaseModel

# ─── Sandbox Mode (#51) ───────────────────────────────────────────────────────

_SANDBOX_MODE = {"enabled": True}  # Default ON for demo

def is_sandbox() -> bool:
    return _SANDBOX_MODE["enabled"]

def toggle_sandbox(enable: bool) -> dict:
    _SANDBOX_MODE["enabled"] = enable
    return {"sandbox_mode": enable, "message": f"Sandbox {'ENABLED' if enable else 'DISABLED'}"}

# ─── DigiLocker Mock (#17) ────────────────────────────────────────────────────

_DIGILOCKER_SESSIONS: dict = {}

def digilocker_initiate(session_id: str) -> dict:
    token = ''.join(random.choices(string.ascii_letters, k=32))
    _DIGILOCKER_SESSIONS[token] = session_id
    return {
        "auth_url": f"https://digilocker.gov.in/oauth/mock?token={token}&redirect=/api/digilocker/callback",
        "token": token,
        "note": "SANDBOX — This is a mock DigiLocker OAuth flow",
        "mock_auto_approve": True,
    }

def digilocker_callback(token: str) -> dict:
    """Auto-approve mock callback returning sample Aadhaar data."""
    session_id = _DIGILOCKER_SESSIONS.get(token)
    if not session_id:
        return {"error": "Invalid token"}
    return {
        "session_id": session_id,
        "verified": True,
        "aadhaar_data": {
            "name": "Rahul Kumar",
            "dob": "1995-06-15",
            "gender": "M",
            "address": "123, Andheri West, Mumbai, Maharashtra 400058",
            "uid_last4": "8765",
            "verified_by": "DigiLocker_MOCK",
        },
        "pan_data": {"pan": "ABCDE1234F", "name": "Rahul Kumar"},
        "source": "DigiLocker_SANDBOX",
    }

# ─── Account Aggregator Mock (#18) ────────────────────────────────────────────

def aa_consent_initiate(session_id: str) -> dict:
    consent_handle = f"AA-CONSENT-{uuid.uuid4().hex[:8].upper()}"
    return {
        "consent_handle": consent_handle,
        "redirect_url": f"https://finvu.in/mock-consent?handle={consent_handle}",
        "message": "Applicant will approve on their bank's AA app",
        "note": "SANDBOX — Auto-approved after 2 seconds",
    }

def aa_fetch_data(consent_handle: str) -> dict:
    return {
        "consent_handle": consent_handle,
        "status": "APPROVED",
        "bank_statements": {
            "account_number_last4": "4521",
            "bank": "HDFC Bank",
            "avg_monthly_balance": random.randint(15000, 80000),
            "salary_credits_count_6m": random.randint(4, 6),
            "emi_debits_detected": random.choice([True, False]),
            "irregular_withdrawals": random.randint(0, 3),
            "income_regularity_score": round(random.uniform(0.6, 0.95), 2),
        },
        "source": "AA_SANDBOX",
    }

# ─── WhatsApp Bot Mock (#20) ──────────────────────────────────────────────────

_WA_SESSIONS: dict = {}

WHATSAPP_STATES = ["GREETING", "AADHAAR_PHOTO", "INCOME_VOICE", "CONSENT", "OFFER"]

def whatsapp_webhook(from_number: str, message_type: str, content: str) -> dict:
    if from_number not in _WA_SESSIONS:
        _WA_SESSIONS[from_number] = {"state": "GREETING", "session_id": str(uuid.uuid4())}
    
    state = _WA_SESSIONS[from_number]["state"]
    session_id = _WA_SESSIONS[from_number]["session_id"]
    
    RESPONSES = {
        "GREETING": {"reply": "Welcome to Poonawalla Fincorp! 🏦 Please send a photo of your Aadhaar card to begin.", "next_state": "AADHAAR_PHOTO"},
        "AADHAAR_PHOTO": {"reply": "✅ Aadhaar received! Now please send a voice note declaring your monthly income.", "next_state": "INCOME_VOICE"},
        "INCOME_VOICE": {"reply": "🎤 Income recorded! Do you consent to this loan application? Reply YES to proceed.", "next_state": "CONSENT"},
        "CONSENT": {"reply": "✅ Consent recorded! Calculating your loan offer...", "next_state": "OFFER"},
        "OFFER": {"reply": f"🎉 Congratulations! You qualify for Rs.3,00,000 at 12.5% p.a. EMI: Rs.9,999/month. Reply ACCEPT to proceed.", "next_state": "GREETING"},
    }
    
    resp = RESPONSES.get(state, {"reply": "Hello! Send 'Hi' to start a loan application.", "next_state": "GREETING"})
    _WA_SESSIONS[from_number]["state"] = resp["next_state"]
    
    return {
        "session_id": session_id,
        "from": from_number,
        "reply": resp["reply"],
        "new_state": resp["next_state"],
        "channel": "WhatsApp_MOCK",
    }

# ─── eNACH Mock (#28) ─────────────────────────────────────────────────────────

_NACH_MANDATES: dict = {}

def nach_initiate(session_id: str, bank: str, account_last4: str) -> dict:
    mandate_id = f"NACH-{uuid.uuid4().hex[:8].upper()}"
    _NACH_MANDATES[mandate_id] = {"session_id": session_id, "status": "PENDING", "bank": bank}
    return {
        "mandate_id": mandate_id,
        "netbanking_url": f"https://npci.org.in/mock-nach?mandate={mandate_id}",
        "status": "PENDING",
        "bank": bank,
        "note": "SANDBOX — Auto-registered after 3 seconds",
    }

def nach_status(mandate_id: str) -> dict:
    mandate = _NACH_MANDATES.get(mandate_id, {})
    return {
        "mandate_id": mandate_id,
        "status": "REGISTERED",  # Auto-approve in sandbox
        "session_id": mandate.get("session_id"),
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

# ─── UPI Disbursement Mock (#29) ──────────────────────────────────────────────

_DISBURSALS: dict = {}

def disburse_upi(session_id: str, upi_id: str, amount: int) -> dict:
    payout_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    ref_id = f"IMPS{random.randint(100000000, 999999999)}"
    
    _DISBURSALS[payout_id] = {
        "session_id": session_id,
        "upi_id": upi_id,
        "amount": amount,
        "status": "PROCESSED",
        "ref_id": ref_id,
    }
    
    return {
        "payout_id": payout_id,
        "upi_id": upi_id,
        "amount": amount,
        "status": "PROCESSED",
        "reference_id": ref_id,
        "message": f"Rs.{amount:,} disbursed to {upi_id} via IMPS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "SANDBOX — No real money transferred",
    }

# ─── CKYC Mock (#30) ──────────────────────────────────────────────────────────

def ckyc_push(session_id: str, pan: str, name: str) -> dict:
    ckyc_number = ''.join(random.choices(string.digits, k=14))
    return {
        "ckyc_number": ckyc_number,
        "session_id": session_id,
        "pan": pan[:5] + "XXXXX",
        "name": name,
        "status": "REGISTERED",
        "registry": "CERSAI_MOCK",
        "note": "Future loan applications skip KYC using this number",
    }

# ─── eSign Mock (#70) ─────────────────────────────────────────────────────────

_ESIGN_SESSIONS: dict = {}

def esign_initiate(session_id: str, name: str, amount: int, rate: float) -> dict:
    otp = "123456"  # Fixed mock OTP
    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    _ESIGN_SESSIONS[doc_id] = {
        "session_id": session_id,
        "name": name,
        "amount": amount,
        "rate": rate,
        "otp": otp,
        "signed": False,
    }
    return {
        "document_id": doc_id,
        "otp_sent_to": "XXXXXX1234",  # Masked number
        "note": "SANDBOX — Use OTP 123456",
        "agreement_summary": f"Loan of Rs.{amount:,} at {rate}% p.a. for {session_id[:8]}",
    }

def esign_verify(doc_id: str, otp: str) -> dict:
    doc = _ESIGN_SESSIONS.get(doc_id)
    if not doc:
        return {"success": False, "error": "Document not found"}
    
    if otp == doc["otp"] or otp == "123456":
        doc["signed"] = True
        sig_id = f"SIG-{uuid.uuid4().hex[:12].upper()}"
        return {
            "success": True,
            "signature_id": sig_id,
            "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "legal_validity": "IT Act 2000 Section 3A",
            "document_id": doc_id,
            "note": "Loan agreement legally executed",
        }
    return {"success": False, "error": "Invalid OTP"}

# ─── SMS Recovery (#33) ───────────────────────────────────────────────────────

_RESUME_TOKENS: dict = {}

def generate_resume_link(session_id: str, phone: str = "XXXXXXXXXX", base_url: str = "http://localhost:3000") -> dict:
    token = uuid.uuid4().hex[:16]
    _RESUME_TOKENS[token] = {"session_id": session_id, "created_at": time.time()}
    resume_url = f"{base_url}?resume={token}"
    
    # In production: call Fast2SMS API here
    return {
        "resume_token": token,
        "resume_url": resume_url,
        "sms_message": f"Resume your PFL loan application: {resume_url}",
        "sms_status": "SANDBOX_LOGGED",
        "expires_in_hours": 24,
    }

def resolve_resume_token(token: str) -> Optional[dict]:
    return _RESUME_TOKENS.get(token)

# ─── JWT/MFA (#54) ────────────────────────────────────────────────────────────

JWT_SECRET = os.environ.get("JWT_SECRET", "pfl-wizard-secret-2024-secure")
TOTP_SECRET = os.environ.get("TOTP_SECRET", "JBSWY3DPEHPK3PXP")

def create_admin_token() -> str:
    from jose import jwt
    payload = {"sub": "admin", "exp": time.time() + 3600, "role": "admin"}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_admin_token(token: str) -> bool:
    try:
        from jose import jwt
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return True
    except Exception:
        return False

def verify_totp(code: str) -> bool:
    try:
        import pyotp
        totp = pyotp.TOTP(TOTP_SECRET)
        return totp.verify(code)
    except Exception:
        return code == "000000"  # Fallback demo code

# ─── Voice Biometric Mock (#25) ───────────────────────────────────────────────

_VOICE_EMBEDDINGS: dict = {}  # {session_id: embedding_hash}

def register_voice(session_id: str, audio_base64: str) -> dict:
    voice_hash = hash(audio_base64[:200]) % 1000000
    _VOICE_EMBEDDINGS[session_id] = voice_hash
    return {
        "session_id": session_id,
        "voiceprint_registered": True,
        "embedding_dim": 256,
        "method": "SpeechBrain_MOCK",
    }

def verify_voice(stored_session_id: str, audio_base64: str) -> dict:
    stored = _VOICE_EMBEDDINGS.get(stored_session_id)
    if not stored:
        return {"verified": False, "reason": "No voiceprint on file"}
    
    new_hash = hash(audio_base64[:200]) % 1000000
    similarity = 0.92 if stored == new_hash else round(0.6 + random.random() * 0.3, 3)
    
    return {
        "similarity": similarity,
        "verified": similarity >= 0.90,
        "action": "SKIP_KYC" if similarity >= 0.90 else ("OTP_FALLBACK" if similarity >= 0.75 else "FULL_KYC"),
        "method": "SpeechBrain_MOCK",
    }

# ─── Dropout Predictor (#23) ─────────────────────────────────────────────────

def predict_dropout(session_data: dict) -> dict:
    """Feature #23 — Real-time dropout probability from behavioural signals."""
    time_on_phase2 = session_data.get("phase2_seconds", 60)
    retry_count = session_data.get("retry_count", 0)
    audio_pauses = session_data.get("audio_pause_count", 0)
    camera_resets = session_data.get("camera_reset_count", 0)
    
    # Logistic-style scoring
    raw = (
        (time_on_phase2 / 300) * 0.30 +
        (retry_count / 5) * 0.25 +
        (audio_pauses / 10) * 0.25 +
        (camera_resets / 3) * 0.20
    )
    dropout_prob = round(min(0.99, max(0.01, raw)), 3)
    
    intervention = None
    if dropout_prob > 0.65:
        if retry_count > 2:
            intervention = "simplify_question"
        elif audio_pauses > 5:
            intervention = "show_help_button"
        else:
            intervention = "show_progress_bar"
    
    return {
        "dropout_probability": dropout_prob,
        "dropout_risk": "HIGH" if dropout_prob > 0.65 else ("MEDIUM" if dropout_prob > 0.35 else "LOW"),
        "intervention": intervention,
        "signals": {
            "time_on_phase2_s": time_on_phase2,
            "retry_count": retry_count,
            "audio_pauses": audio_pauses,
            "camera_resets": camera_resets,
        },
    }

# ─── Psychometric Assessment (#36) ───────────────────────────────────────────

PSYCHOMETRIC_QUESTIONS = [
    {"id": 1, "text": "Rs.10,000 today or Rs.12,000 in 1 month — which do you choose?", "options": ["Rs.10,000 today", "Rs.12,000 in 1 month"], "points": [0, 10]},
    {"id": 2, "text": "If you received an unexpected Rs.50,000, what would you do?", "options": ["Spend on wants", "Save/invest", "Pay off debt"], "points": [0, 10, 8]},
    {"id": 3, "text": "How often do you check your bank balance?", "options": ["Rarely", "Monthly", "Weekly", "Daily"], "points": [0, 5, 8, 10]},
    {"id": 4, "text": "Have you ever missed a loan or credit card payment?", "options": ["Yes, often", "Once or twice", "Never"], "points": [0, 5, 10]},
    {"id": 5, "text": "What is the maximum you would spend on a vacation?", "options": [">2 months salary", "1-2 months salary", "<1 month salary"], "points": [0, 5, 10]},
]

def score_psychometric(answers: dict) -> dict:
    """Feature #36 — Score psychometric responses."""
    total = 0
    max_score = 50
    for q in PSYCHOMETRIC_QUESTIONS:
        ans_idx = answers.get(str(q["id"]), -1)
        if 0 <= ans_idx < len(q["points"]):
            total += q["points"][ans_idx]
    
    fri = round(total / max_score * 100)
    risk_adj = -0.05 if fri >= 70 else (0.0 if fri >= 50 else 0.05)
    
    return {
        "financial_responsibility_index": fri,
        "band": "High" if fri >= 70 else ("Medium" if fri >= 50 else "Low"),
        "risk_adjustment": risk_adj,
        "interpretation": "Disciplined saver with low delay-discounting" if fri >= 70 else "Average financial discipline",
    }

# ─── Session Replay (#61) ─────────────────────────────────────────────────────

def get_session_timeline(session_id: str, audit_events: list, video_frames: list) -> dict:
    """Feature #61 — Build synchronized timeline for session replay."""
    timeline = []
    
    for event in audit_events:
        timeline.append({
            "type": "audit",
            "timestamp": event.get("timestamp"),
            "event": event.get("event_type"),
            "model": event.get("model_used"),
            "confidence": event.get("confidence"),
        })
    
    for frame in video_frames:
        timeline.append({
            "type": "video_frame",
            "timestamp": frame.get("timestamp"),
            "age_est": frame.get("estimated_age"),
            "liveness": frame.get("liveness_score"),
        })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x.get("timestamp") or "")
    
    return {
        "session_id": session_id,
        "total_events": len(timeline),
        "timeline": timeline[:200],  # Cap at 200 events
        "duration_seconds": len(video_frames) * 1.5,
    }
