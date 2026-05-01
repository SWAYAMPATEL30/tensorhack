"""
Feature #21: Education loan ROI predictor
Feature #22: Graduation-linked flexible EMI scheduler
Feature #46: Applicant financial health score dashboard
Feature #53: Predictive offer acceptance optimizer
Feature #62: Interactive EMI comparison widget data
Feature #66: Hyperlocal pin code risk calibration
Feature #16: Alternative credit scoring for thin-file applicants
"""
import math, random, time
from typing import List, Optional
from pydantic import BaseModel

# ─── Feature #21: Education Loan ROI ─────────────────────────────────────────

INSTITUTION_TIERS = {
    "tier1": ["iit", "iim", "bits", "nit", "aiims", "iiser"],
    "tier2": ["vit", "manipal", "srm", "symbiosis", "christ", "amity"],
    "tier3": [],  # default
}

COURSE_SALARY_MAP = {
    "cs": {"tier1": 1800000, "tier2": 900000, "tier3": 450000},
    "mba": {"tier1": 2200000, "tier2": 1000000, "tier3": 500000},
    "medicine": {"tier1": 1200000, "tier2": 900000, "tier3": 600000},
    "law": {"tier1": 1000000, "tier2": 600000, "tier3": 300000},
    "engineering": {"tier1": 1500000, "tier2": 800000, "tier3": 400000},
    "arts": {"tier1": 600000, "tier2": 350000, "tier3": 200000},
}

def predict_education_roi(institution: str, course: str, graduation_year: int) -> dict:
    """Feature #21 — Predict starting salary from institution + course."""
    inst_lower = institution.lower()
    tier = "tier3"
    for t, keywords in INSTITUTION_TIERS.items():
        if any(k in inst_lower for k in keywords):
            tier = t
            break
    
    course_lower = course.lower()
    course_key = "engineering"
    for k in COURSE_SALARY_MAP:
        if k in course_lower:
            course_key = k
            break
    
    expected_annual = COURSE_SALARY_MAP[course_key][tier]
    expected_monthly = expected_annual // 12
    years_left = max(0, graduation_year - 2026)
    
    return {
        "institution_tier": tier,
        "course": course,
        "expected_starting_salary_annual": expected_annual,
        "expected_starting_salary_monthly": expected_monthly,
        "years_until_graduation": years_left,
        "max_emi_at_graduation": int(expected_monthly * 0.35),
        "confidence": 0.78,
        "note": f"Based on {tier.upper()} institution placement data (NASSCOM/NIRF 2024)",
    }

# ─── Feature #22: Graduated EMI Schedule ──────────────────────────────────────

def graduated_emi_schedule(principal: float, annual_rate: float, graduation_date: str) -> dict:
    """Feature #22 — 3-phase graduated EMI schedule."""
    monthly_rate = annual_rate / 100 / 12
    n = 36  # Full tenure months
    
    full_emi = principal * monthly_rate * (1 + monthly_rate)**n / ((1 + monthly_rate)**n - 1)
    interest_only = principal * monthly_rate
    
    schedule = []
    balance = principal
    
    for month in range(1, n + 1):
        if month <= 12:
            emi = interest_only
            phase = "Study (Interest Only)"
        elif month <= 24:
            emi = full_emi * 0.5
            phase = "Year 1 Post-Grad (50%)"
        else:
            emi = full_emi
            phase = "Year 2+ (100%)"
        
        interest = balance * monthly_rate
        principal_paid = max(0, emi - interest)
        balance = max(0, balance - principal_paid)
        
        schedule.append({
            "month": month, "phase": phase,
            "emi": round(emi), "interest": round(interest),
            "principal": round(principal_paid), "balance": round(balance),
        })
    
    return {
        "full_emi": round(full_emi),
        "study_emi": round(interest_only),
        "year1_emi": round(full_emi * 0.5),
        "schedule": schedule,
        "total_payable": round(sum(m["emi"] for m in schedule)),
        "total_interest": round(sum(m["interest"] for m in schedule)),
    }

# ─── Feature #46: Financial Health Score ─────────────────────────────────────

def compute_health_score(session_data: dict) -> dict:
    """Feature #46 — 5-component financial health score (0-100)."""
    credit_score = session_data.get("credit_score", 680)
    income = session_data.get("monthly_income", 50000)
    emi_ratio = session_data.get("emi_ratio", 0.3)
    existing_loans = session_data.get("existing_loans", 0)
    fraud_score = session_data.get("fraud_score", 0.1)
    
    # Sub-scores (0-100)
    credit_util = min(100, max(0, (credit_score - 300) / 5.5))
    income_stability = min(100, (income / 100000) * 100)
    repayment_history = max(0, 100 - (existing_loans * 10))
    dti_score = max(0, 100 - (emi_ratio * 200))
    fraud_penalty = max(0, 100 - (fraud_score * 100))
    
    weighted = (
        credit_util * 0.35 +
        income_stability * 0.25 +
        repayment_history * 0.20 +
        dti_score * 0.15 +
        fraud_penalty * 0.05
    )
    
    health_score = round(min(100, weighted))
    band = "Excellent" if health_score >= 80 else ("Good" if health_score >= 60 else ("Fair" if health_score >= 40 else "Poor"))
    
    tips = []
    if credit_score < 750:
        tips.append("Maintain credit score > 750 by paying EMIs on time — could improve your score by 15 points in 3 months.")
    if emi_ratio > 0.35:
        tips.append("Reduce existing EMI obligations to under 35% of income — opens up Rs.15,000–20,000 more in borrowing capacity.")
    if existing_loans > 2:
        tips.append("Close 1 existing loan before reapplying — reduces your credit burden and improves eligibility.")
    if not tips:
        tips.append("Your financial health is excellent! You qualify for our Prime offer tier.")
    
    return {
        "health_score": health_score,
        "band": band,
        "components": {
            "credit_utilization": round(credit_util),
            "income_stability": round(income_stability),
            "repayment_history": round(repayment_history),
            "dti_score": round(dti_score),
            "fraud_clearance": round(fraud_penalty),
        },
        "tips": tips[:3],
        "color": "#10B981" if health_score >= 80 else ("#3B82F6" if health_score >= 60 else ("#F59E0B" if health_score >= 40 else "#EF4444")),
    }

# ─── Feature #53: Offer Acceptance Optimizer ──────────────────────────────────

def optimize_offer(base_offer: dict, risk_score: float, persona: str) -> dict:
    """Feature #53 — Predict acceptance probability and optimize if < 40%."""
    amount = base_offer.get("amount", 300000)
    rate = base_offer.get("rate", 12.5)
    tenure = base_offer.get("tenure_months", 36)
    
    # Simplified acceptance probability model
    acceptance_prob = max(0.1, 0.9 - risk_score * 0.8 - (rate - 10) * 0.03)
    
    optimized = dict(base_offer)
    optimization_applied = False
    
    if acceptance_prob < 0.40:
        # Try lower rate or longer tenure
        new_rate = max(10.5, rate - 1.5)
        new_tenure = min(60, tenure + 12)
        mr = new_rate / 100 / 12
        new_emi = round(amount * mr / (1 - (1 + mr)**-new_tenure))
        
        new_acceptance = min(0.85, acceptance_prob + 0.30)
        optimized.update({"rate": new_rate, "tenure_months": new_tenure, "emi": new_emi})
        optimization_applied = True
    else:
        new_acceptance = acceptance_prob
    
    return {
        "original_offer": base_offer,
        "optimized_offer": optimized,
        "original_acceptance_probability": round(acceptance_prob, 3),
        "optimized_acceptance_probability": round(new_acceptance, 3),
        "optimization_applied": optimization_applied,
        "optimization_reason": "Reduced rate by 1.5% and extended tenure by 12 months to maximize conversion" if optimization_applied else "Original offer already optimal",
    }

# ─── Feature #66: Pincode Risk Calibration ────────────────────────────────────

PINCODE_RISK_DB = {
    # Maharashtra
    "400001": {"city": "Mumbai South", "default_rate": 0.035, "adjustment": 0.92},
    "400070": {"city": "Andheri", "default_rate": 0.042, "adjustment": 0.95},
    "411001": {"city": "Pune Central", "default_rate": 0.038, "adjustment": 0.93},
    # Delhi
    "110001": {"city": "Connaught Place", "default_rate": 0.030, "adjustment": 0.90},
    "110044": {"city": "Okhla", "default_rate": 0.065, "adjustment": 1.05},
    # Karnataka
    "560001": {"city": "Bengaluru Central", "default_rate": 0.032, "adjustment": 0.91},
    # Tamil Nadu
    "600001": {"city": "Chennai Central", "default_rate": 0.040, "adjustment": 0.94},
    # Flood zones
    "713101": {"city": "Asansol (Flood Zone)", "default_rate": 0.120, "adjustment": 1.25},
    "585101": {"city": "Gulbarga (Drought Zone)", "default_rate": 0.095, "adjustment": 1.15},
    # Default
    "000000": {"city": "Unknown", "default_rate": 0.060, "adjustment": 1.0},
}

def get_pincode_risk(pincode: str) -> dict:
    """Feature #66 — Get risk adjustment for a pin code."""
    data = PINCODE_RISK_DB.get(pincode, PINCODE_RISK_DB["000000"])
    risk_level = "HIGH" if data["adjustment"] > 1.10 else ("MEDIUM" if data["adjustment"] > 0.98 else "LOW")
    
    return {
        "pincode": pincode,
        "city": data["city"],
        "historical_default_rate": data["default_rate"],
        "risk_adjustment_factor": data["adjustment"],
        "risk_level": risk_level,
        "max_loan_cap": 100000 if risk_level == "HIGH" else None,
        "note": "Flood/drought zone — capped at Rs.1L" if risk_level == "HIGH" else "Standard lending applies",
    }

# ─── Feature #16: Alternative Credit Scoring ──────────────────────────────────

def alt_credit_score(upi_regularity: float = 0.7, utility_payments: float = 0.8,
                     avg_balance: int = 15000, income_regularity: float = 0.75) -> dict:
    """Feature #16 — Score thin-file applicants using alternative data."""
    # Weighted composite
    alt_score = int(
        upi_regularity * 30 +
        utility_payments * 25 +
        min(1.0, avg_balance / 50000) * 25 +
        income_regularity * 20
    )
    
    band = "GOOD" if alt_score >= 70 else ("FAIR" if alt_score >= 50 else "POOR")
    risk_adj = -0.05 if alt_score >= 70 else (0.05 if alt_score >= 50 else 0.15)
    max_amount = 100000  # Always cap thin-file at Rs.1L first loan
    
    return {
        "alt_credit_score": alt_score,
        "band": band,
        "risk_adjustment": risk_adj,
        "components": {
            "upi_regularity": round(upi_regularity * 30),
            "utility_payments": round(utility_payments * 25),
            "avg_balance_score": round(min(1.0, avg_balance / 50000) * 25),
            "income_regularity": round(income_regularity * 20),
        },
        "max_loan_amount": max_amount,
        "tier": "Conservative (Thin-File)",
        "note": "First loan capped at Rs.1L. Post repayment, eligible for Standard tier.",
    }

# ─── Feature #62: EMI Comparison Widget ──────────────────────────────────────

def get_emi_variants(amount: int, risk_band: str) -> List[dict]:
    """Feature #62 — 3 offer variants for EMI comparison widget."""
    base_rate = {"LOW": 10.5, "MEDIUM": 14.5, "HIGH": 18.5}.get(risk_band, 12.5)
    
    def emi(a, r, n):
        mr = r / 100 / 12
        return round(a * mr / (1 - (1 + mr)**-n))
    
    return [
        {
            "label": "Short & Fast",
            "badge": None,
            "amount": amount,
            "rate": base_rate + 0.5,
            "tenure_months": 18,
            "emi": emi(amount, base_rate + 0.5, 18),
            "total_payable": emi(amount, base_rate + 0.5, 18) * 18,
            "color": "#EF4444",
        },
        {
            "label": "Balanced",
            "badge": "Best Value",
            "amount": amount,
            "rate": base_rate,
            "tenure_months": 36,
            "emi": emi(amount, base_rate, 36),
            "total_payable": emi(amount, base_rate, 36) * 36,
            "color": "#2563EB",
        },
        {
            "label": "Easy Monthly",
            "badge": None,
            "amount": amount,
            "rate": base_rate + 1.0,
            "tenure_months": 60,
            "emi": emi(amount, base_rate + 1.0, 60),
            "total_payable": emi(amount, base_rate + 1.0, 60) * 60,
            "color": "#10B981",
        },
    ]

# Feature #36: Psychometric Assessment

PSYCHOMETRIC_QUESTIONS = [
    {"id": 1, "text": "Rs.10,000 today or Rs.12,000 in 1 month?", "options": ["Rs.10,000 today", "Rs.12,000 in 1 month"], "points": [0, 10]},
    {"id": 2, "text": "Unexpected Rs.50,000 — what do you do?", "options": ["Spend on wants", "Save/invest", "Pay off debt"], "points": [0, 10, 8]},
    {"id": 3, "text": "How often do you check your bank balance?", "options": ["Rarely", "Monthly", "Weekly", "Daily"], "points": [0, 5, 8, 10]},
    {"id": 4, "text": "Ever missed a loan/CC payment?", "options": ["Yes, often", "Once or twice", "Never"], "points": [0, 5, 10]},
    {"id": 5, "text": "Max vacation spend?", "options": [">2 months salary", "1-2 months salary", "<1 month salary"], "points": [0, 5, 10]},
]

def score_psychometric(answers: dict) -> dict:
    total = 0
    for q in PSYCHOMETRIC_QUESTIONS:
        idx = answers.get(str(q["id"]), -1)
        if isinstance(idx, int) and 0 <= idx < len(q["points"]):
            total += q["points"][idx]
    fri = round(total / 50 * 100)
    return {
        "financial_responsibility_index": fri,
        "band": "High" if fri >= 70 else ("Medium" if fri >= 50 else "Low"),
        "risk_adjustment": -0.05 if fri >= 70 else (0.0 if fri >= 50 else 0.05),
        "score": total, "max_score": 50,
    }
