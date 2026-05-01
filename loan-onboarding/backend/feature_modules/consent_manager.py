"""
Feature #15: Verbal consent timestamped recording
Feature #10: Multilingual STT — Hindi + regional languages
Feature #34: Dynamic question adapter
"""
import time, re
from typing import Optional, Dict
from langdetect import detect as lang_detect  # type: ignore

# ─── Consent Phrases ─────────────────────────────────────────────────────────

CONSENT_PHRASES_EN = ["i agree", "i consent", "i accept", "yes i agree", "i confirm"]
CONSENT_PHRASES_HI = ["haan main manta hoon", "mujhe manzoor hai", "haan", "theek hai", "main razi hoon", "main manta hoon"]
CONSENT_PHRASES_TA = ["sari", "aamam"]  # Tamil
CONSENT_PHRASES_TE = ["aye", "avunnu"]  # Telugu
ALL_CONSENT = CONSENT_PHRASES_EN + CONSENT_PHRASES_HI + CONSENT_PHRASES_TA + CONSENT_PHRASES_TE

# ─── Vernacular amount parser ────────────────────────────────────────────────

HINDI_NUMERALS = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
    "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "bees": 20, "tees": 30, "chaalis": 40, "pachas": 50,
}

def parse_vernacular_amount(text: str) -> int:
    """Parse Indian-language amount expressions to integer (rupees)."""
    tl = text.lower()
    val = 0
    
    # Lakh variants
    m = re.search(r'([\d.]+)\s*(lakh|lac|लाख)', tl)
    if m:
        return int(float(m.group(1)) * 100000)
    
    # Crore
    m = re.search(r'([\d.]+)\s*(crore|करोड़)', tl)
    if m:
        return int(float(m.group(1)) * 10000000)
    
    # Hazaar / thousand
    m = re.search(r'([\d.]+)\s*(hazaar|hazar|thousand|हज़ार)', tl)
    if m:
        return int(float(m.group(1)) * 1000)
    
    # Hindi number + lakh (e.g. "paanch lakh")
    for word, num in HINDI_NUMERALS.items():
        if word in tl and "lakh" in tl:
            return num * 100000
    
    return 0

def detect_language(text: str) -> str:
    """Detect transcript language."""
    try:
        return lang_detect(text) if len(text) > 20 else "en"
    except Exception:
        return "en"

LANG_LABELS = {
    "en": "English", "hi": "Hindi", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "gu": "Gujarati", "bn": "Bengali",
    "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi",
}

def detect_consent(transcript: str, timestamp_ms: Optional[float] = None) -> dict:
    """Feature #15 — Detect verbal consent in transcript."""
    tl = transcript.lower()
    detected = False
    phrase_found = None
    for phrase in ALL_CONSENT:
        if phrase in tl:
            detected = True
            phrase_found = phrase
            break
    
    return {
        "consent_detected": detected,
        "phrase": phrase_found,
        "timestamp_ms": timestamp_ms or (time.time() * 1000),
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "certificate_id": f"CONS-{int(time.time())}" if detected else None,
    }

# ─── Dynamic Question Adapter ─────────────────────────────────────────────────

QUESTIONS = {
    "income": {
        "en": "Please tell me your approximate monthly income.",
        "hi": "Kripya apni maasik aamdani batayein.",
        "ta": "Ungal masadhiya varumanam sollungal.",
        "te": "Meeru nela aadayamu cheppandi.",
    },
    "employer": {
        "en": "Where do you currently work or run your business?",
        "hi": "Aap filhaal kahan kaam karte hain ya apna business chalate hain?",
        "ta": "Neengal ippodhu engey velaigey seigireerkal?",
    },
    "loan_purpose": {
        "en": "What would you like to use this loan for?",
        "hi": "Is loan ko aap kis kaam ke liye use karna chahte hain?",
    },
    "consent": {
        "en": "Do you consent to this loan application and authorize us to check your credit history?",
        "hi": "Kya aap is loan application ke liye sahmat hain aur hume apni credit history check karne ki anumati dete hain?",
    },
}

def get_next_question(field_coverage: Dict[str, bool], lang: str = "en") -> Optional[dict]:
    """Feature #34 — Return next uncovered question in detected language."""
    order = ["income", "employer", "loan_purpose", "consent"]
    for field in order:
        if not field_coverage.get(field, False):
            q = QUESTIONS.get(field, {})
            text = q.get(lang) or q.get("en", f"Please tell us your {field}.")
            return {
                "field": field,
                "question": text,
                "language": lang,
                "language_label": LANG_LABELS.get(lang, lang),
            }
    return None  # All covered

def update_field_coverage(transcript: str, current_coverage: Dict[str, bool]) -> Dict[str, bool]:
    """Update coverage dict based on what was extracted from latest transcript chunk."""
    from .llm_engine import RISK_KEYWORDS
    import re as _re
    
    tl = transcript.lower()
    cov = dict(current_coverage)
    
    # Income
    if not cov.get("income"):
        if re.search(r'\b(\d{4,}|lakh|hazaar|salary|income|earn)\b', tl):
            cov["income"] = True
    
    # Employer
    if not cov.get("employer"):
        if re.search(r'\b(work|job|company|business|infosys|wipro|tcs|hospital|school|government)\b', tl):
            cov["employer"] = True
    
    # Loan purpose
    if not cov.get("loan_purpose"):
        if re.search(r'\b(home|house|car|bike|education|medical|business|travel|wedding|loan for)\b', tl):
            cov["loan_purpose"] = True
    
    # Consent
    if not cov.get("consent"):
        cov["consent"] = detect_consent(transcript)["consent_detected"]
    
    return cov
