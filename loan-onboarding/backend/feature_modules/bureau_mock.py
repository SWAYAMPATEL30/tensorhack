"""
Feature #12: CIBIL score API (mock with realistic sandbox)
Feature #35: Multi-bureau aggregation (CIBIL + Experian + CRIF)
"""
import asyncio, random, time
from pydantic import BaseModel
from typing import Optional

class BureauPayload(BaseModel):
    session_id: str
    pan_number: Optional[str] = "ABCDE1234F"
    dob: Optional[str] = "1990-01-01"
    name: Optional[str] = "Applicant"

_bureau_cache: dict = {}  # {pan: {score, timestamp}}

def _mock_cibil(pan: str) -> dict:
    """Deterministic mock score based on PAN suffix."""
    pan = (pan or "").upper().strip()
    if pan.endswith("TEST"):
        score = 775
    elif pan.endswith("POOR"):
        score = 520
    elif pan.endswith("MED"):
        score = 660
    else:
        # Deterministic but varied
        seed = sum(ord(c) for c in pan[-4:]) if len(pan) >= 4 else 700
        score = 600 + (seed % 200)

    dpd = 0 if score > 700 else (1 if score > 600 else 3)
    accounts = random.randint(2, 8)
    return {
        "bureau": "CIBIL",
        "score": score,
        "accounts": accounts,
        "dpd_30": dpd,
        "credit_inquiries_6m": random.randint(0, 4),
        "oldest_account_years": random.randint(1, 10),
        "status": "SUCCESS",
        "pull_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

def _mock_experian(pan: str) -> dict:
    base = _mock_cibil(pan)
    # Experian may differ slightly
    base["bureau"] = "Experian"
    base["score"] = min(850, base["score"] + random.randint(-30, 30))
    return base

def _mock_crif(pan: str) -> dict:
    base = _mock_cibil(pan)
    base["bureau"] = "CRIF"
    base["score"] = min(850, base["score"] + random.randint(-20, 20))
    return base

def pull_single_bureau(payload: BureauPayload) -> dict:
    """Feature #12 — Single CIBIL pull with 24h cache."""
    cache_key = f"{payload.pan_number}_{payload.dob}"
    if cache_key in _bureau_cache:
        cached = _bureau_cache[cache_key]
        if time.time() - cached["ts"] < 86400:
            result = dict(cached["data"])
            result["from_cache"] = True
            return result

    # Simulate 0.8s API latency
    time.sleep(0.3)
    result = _mock_cibil(payload.pan_number or "")

    # Risk adjustment
    score = result["score"]
    if score >= 750:
        risk_adj = -0.10
        band = "EXCELLENT"
    elif score >= 700:
        risk_adj = -0.05
        band = "GOOD"
    elif score >= 650:
        risk_adj = 0.0
        band = "FAIR"
    elif score >= 600:
        risk_adj = 0.10
        band = "POOR"
    else:
        risk_adj = 0.20
        band = "BAD"

    result["risk_adjustment"] = risk_adj
    result["bureau_band"] = band
    result["from_cache"] = False

    _bureau_cache[cache_key] = {"data": result, "ts": time.time()}
    return result

def pull_multi_bureau(payload: BureauPayload) -> dict:
    """Feature #35 — Pull 3 bureaus, aggregate, flag discrepancies."""
    pan = payload.pan_number or ""
    cibil = _mock_cibil(pan)
    experian = _mock_experian(pan)
    crif = _mock_crif(pan)

    # Weighted aggregate
    agg_score = int(cibil["score"] * 0.5 + experian["score"] * 0.3 + crif["score"] * 0.2)
    discrepancy = abs(cibil["score"] - experian["score"]) > 100
    dpd_worst = max(cibil["dpd_30"], experian["dpd_30"], crif["dpd_30"])

    return {
        "cibil": cibil,
        "experian": experian,
        "crif": crif,
        "aggregated_score": agg_score,
        "data_mismatch_flag": discrepancy,
        "dpd_worst": dpd_worst,
        "recommendation": "PROCEED" if agg_score >= 650 and not discrepancy else "MANUAL_REVIEW",
    }
