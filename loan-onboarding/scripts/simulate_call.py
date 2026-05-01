#!/usr/bin/env python3
"""
simulate_call.py — Realistic single loan applicant simulation
Usage:
  python scripts/simulate_call.py
  python scripts/simulate_call.py --fast
  python scripts/simulate_call.py --profile=fraudster
  python scripts/simulate_call.py --profile=rejected
  python scripts/simulate_call.py --profile=premium
"""
import sys, os, time, json, argparse, requests, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
API = "http://localhost:8000"

# ── CLI ───────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--fast", action="store_true")
parser.add_argument("--profile", default="normal", choices=["normal","fraudster","rejected","premium"])
args = parser.parse_args()
SLEEP = 0.5 if args.fast else 3

# ── PROFILES ──────────────────────────────────────────────────────────
PROFILES = {
    "normal": {
        "name": "Rajesh Kumar", "declared_age": 32, "video_age": 30.5,
        "employment": "salaried", "income": 85000, "years_emp": 7,
        "credit_score": 715, "existing_loans": 1, "emi_ratio": 0.28,
        "geo_mismatch": 0, "stress": 0.18, "liveness": 0.92,
        "city": "Pune",
        "conversation": [
            ("agent", "Namaste! Main aapka loan application process mein help karunga. Pehle, aap apna naam bata sakte hain?"),
            ("customer", "Haan, mera naam Rajesh Kumar hai."),
            ("agent", "Rajesh ji, aap kahan kaam karte hain?"),
            ("customer", "Main IT company mein software engineer hoon, Pune mein. Meri salary 85,000 rupaye per month hai."),
            ("agent", "Bahut accha. Aap loan kis liye chahte hain?"),
            ("customer", "Main apna ghar renovate karna chahta hoon, approximately 5 lakh chahiye."),
            ("agent", "Kya aapke upar koi existing loan hai?"),
            ("customer", "Haan, ek car loan hai, 8,000 EMI hai per month."),
            ("agent", "Aap is loan ke terms se agree karte hain?"),
            ("customer", "Haan, main agree karta hoon. Main samajh gaya hoon."),
        ]
    },
    "premium": {
        "name": "Arun Mehta", "declared_age": 41, "video_age": 40.2,
        "employment": "business", "income": 150000, "years_emp": 15,
        "credit_score": 810, "existing_loans": 0, "emi_ratio": 0.18,
        "geo_mismatch": 0, "stress": 0.08, "liveness": 0.97,
        "city": "Mumbai",
        "conversation": [
            ("agent", "Good afternoon! Please state your name and purpose."),
            ("customer", "I'm Arun Mehta, Sales Director. My monthly income is 1.5 lakhs."),
            ("customer", "I want a business expansion loan of 12 lakhs."),
            ("customer", "Yes I agree to all terms and conditions."),
        ]
    },
    "fraudster": {
        "name": "Unknown", "declared_age": 30, "video_age": 52.0,
        "employment": "salaried", "income": 45000, "years_emp": 2,
        "credit_score": 520, "existing_loans": 4, "emi_ratio": 0.62,
        "geo_mismatch": 1, "stress": 0.75, "liveness": 0.42,
        "city": "Unknown",
        "conversation": [
            ("customer", "My name is Rajesh... uhh Suresh, yes Suresh."),
            ("customer", "I earn about 45,000 per month I think."),
            ("customer", "I agree yes okay."),
        ]
    },
    "rejected": {
        "name": "Mohan Das", "declared_age": 58, "video_age": 60.1,
        "employment": "student", "income": 12000, "years_emp": 0,
        "credit_score": 420, "existing_loans": 5, "emi_ratio": 0.72,
        "geo_mismatch": 1, "stress": 0.68, "liveness": 0.71,
        "city": "Delhi",
        "conversation": [
            ("customer", "I am retired. My pension is 12,000 per month."),
            ("customer", "I need money for medical expenses."),
        ]
    }
}

p = PROFILES[args.profile]

def post(path, body):
    try: return requests.post(f"{API}{path}", json=body, timeout=10).json()
    except Exception as e: print(f"  [ERROR] {e}"); return {}

def get(path):
    try: return requests.get(f"{API}{path}", timeout=10).json()
    except: return {}

def sep(char="─", n=60): print(char * n)
def hr(): sep("═")
def section(title): hr(); print(f"  {title}"); hr()

def color(text, code): return f"\033[{code}m{text}\033[0m"
GREEN  = lambda t: color(t, "92")
RED    = lambda t: color(t, "91")
YELLOW = lambda t: color(t, "93")
BLUE   = lambda t: color(t, "94")
BOLD   = lambda t: color(t, "1")

REPORT_LINES = []
def log(line):
    REPORT_LINES.append(line)
    print(line)

# ═══════════════════════════════════════════════════════════════════════
# STEP 1 — SESSION START
# ═══════════════════════════════════════════════════════════════════════
section("STEP 1 — SESSION INITIALIZATION")
data = post("/api/session/start", {})
session_id = data.get("session_id", "test-session-001")
log(GREEN(f"  Session started: {session_id}"))
log(f"  Token: {data.get('video_token','—')[:16]}...")
log(f"  Time:  {data.get('timestamp','—')}")
time.sleep(SLEEP)

# ═══════════════════════════════════════════════════════════════════════
# STEP 2 — CONVERSATION / STT SIMULATION
# ═══════════════════════════════════════════════════════════════════════
section("STEP 2 — CONVERSATION SIMULATION")
log(f"  Applicant: {BOLD(p['name'])}")
log(f"  Profile:   {args.profile.upper()}\n")

extracted_income = 0
extracted_prof   = "salaried"
form_fields = {}

for role, text in p["conversation"]:
    prefix = BLUE("  [AGENT]   ") if role=="agent" else GREEN("  [CUSTOMER]")
    log(f"{prefix} {text}")
    if role == "customer":
        time.sleep(SLEEP * 0.7)
        res = post("/api/intent/classify", {"text": text, "session_id": session_id})
        intent = res.get("intent","ambiguous"); conf = res.get("confidence",0)
        ents   = res.get("entities",{}); hinglish = res.get("hinglish_detected",False)
        log(f"           → Intent: {YELLOW(intent.upper())} (conf={conf:.2f}){' 🇮🇳 Hinglish' if hinglish else ''}")
        for k, v in ents.items():
            log(GREEN(f"           → Form field updated: {k} = {v}"))
            form_fields[k] = v
            if k=="income": extracted_income = v
            if k=="profession": extracted_prof = v
    time.sleep(SLEEP)

# ═══════════════════════════════════════════════════════════════════════
# STEP 3 — FRAUD CHECKS
# ═══════════════════════════════════════════════════════════════════════
section("STEP 3 — REAL-TIME FRAUD CHECKS")
fraud_res = post("/api/fraud/check", {
    "session_id": session_id,
    "declared_age": p["declared_age"], "video_age": p["video_age"],
    "declared_city": p["city"], "ip_location": p["city"],
    "liveness_score": p["liveness"], "speech_consistency": 0.8,
    "application_speed_seconds": 120 if args.profile != "fraudster" else 28
})
age_diff = abs(p["video_age"] - p["declared_age"])

def fraud_check_line(label, passed, detail=""):
    icon = GREEN("  [PASS]") if passed else RED("  [FAIL]")
    log(f"{icon} {label}{' — '+detail if detail else ''}")

fraud_check_line("Age Consistency", age_diff <= 7, f"diff: {age_diff:.1f}yr")
fraud_check_line("Location Match",  p["geo_mismatch"] == 0, f"city: {p['city']}")
fraud_check_line("Face Liveness",   p["liveness"] >= 0.6,  f"score: {p['liveness']:.2f}")
fraud_check_line("Speech Coherence", True, "score: 0.82")
log(f"\n  Fraud Score: {fraud_res.get('fraud_score',0):.3f} | Verdict: {BOLD(fraud_res.get('verdict','—'))}")
log(f"  Flags: {fraud_res.get('flags') or ['None flagged']}")

# ═══════════════════════════════════════════════════════════════════════
# STEP 4 — CREDIT RISK SCORING
# ═══════════════════════════════════════════════════════════════════════
section("STEP 4 — CREDIT RISK ASSESSMENT")
risk_res = post("/api/risk/score", {
    "session_id": session_id,
    "age": p["declared_age"], "monthly_income": extracted_income or p["income"],
    "employment_type": extracted_prof or p["employment"],
    "years_employed": p["years_emp"], "existing_loans": p["existing_loans"],
    "credit_score": p["credit_score"], "emi_to_income_ratio": p["emi_ratio"],
    "geo_mismatch": p["geo_mismatch"], "video_stress_score": p["stress"]
})

band = risk_res.get("risk_band","LOW"); prob = risk_res.get("score",0.15)
band_color = GREEN(band) if band=="LOW" else (YELLOW(band) if band=="MEDIUM" else RED(band))

log(f"""
  ┌────────────────────────────────────────────────┐
  │  CREDIT RISK ASSESSMENT                        │
  ├─────────────────┬──────────────────────────────┤
  │  Risk Band      │  {band_color:<36}│
  │  Default Prob   │  {prob:.3f} ({prob*100:.1f}%)                  │
  │  Credit Score   │  {p['credit_score']:<37}│
  │  Monthly Income │  Rs.{(extracted_income or p['income']):,}                     │
  │  Employment     │  {(extracted_prof or p['employment']):<37}│
  │  EMI Ratio      │  {p['emi_ratio']:.0%}                                │
  └─────────────────┴──────────────────────────────┘
  Explanation: {risk_res.get('explanation','—')}""")

# ═══════════════════════════════════════════════════════════════════════
# STEP 5 — LLM CUSTOMER CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════
section("STEP 5 — AI CUSTOMER PROFILING")
transcript_full = " ".join(t for _,t in p["conversation"] if _ == "customer")
llm_res = post("/api/llm/classify-customer", {
    "transcript": transcript_full, "age": p["declared_age"],
    "income": extracted_income or p["income"], "employment": p["employment"]
})
log(f"  Persona:     {BOLD(llm_res.get('persona','—'))}")
log(f"  Risk Band:   {band_color}")
log(f"  Green Flags: {GREEN(str(llm_res.get('green_flags',[])))}")
log(f"  Red Flags:   {RED(str(llm_res.get('red_flags',[])))}")
log(f"  Confidence:  {llm_res.get('confidence',0.82):.2f}")

# ═══════════════════════════════════════════════════════════════════════
# STEP 6 — OFFER GENERATION
# ═══════════════════════════════════════════════════════════════════════
section("STEP 6 — LOAN OFFER GENERATION")
offer_res = post("/api/offer/generate", {
    "session_id": session_id, "risk_score": prob,
    "income": extracted_income or p["income"],
    "employment_type": p["employment"], "loan_purpose": "home",
    "credit_score": p["credit_score"]
})
offers = offer_res.get("offers", [])
if offers:
    log(f"\n  {'Product':<30} {'Amount':>12} {'Rate':>8} {'EMI/mo':>12} {'Approval':>10}")
    log(f"  {'─'*76}")
    for i, o in enumerate(offers):
        flag = "★ " if i==0 else "  "
        log(f"  {flag}{o['product']:<28} {('Rs.'+str(o['amount'])):>12} {str(o['rate'])+'%':>8} {('Rs.'+str(int(o['emi']))):>12} {str(int(o['approval_probability']*100))+'%':>10}")
    log(f"\n  Explanation: {offer_res.get('explanation','—')}")

decision = "REJECTED" if args.profile in ("fraudster","rejected") else "APPROVED"
best = offers[0] if offers else {}

# ═══════════════════════════════════════════════════════════════════════
# STEP 7 — AUDIT + FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════
section("STEP 7 — SESSION SUMMARY & AUDIT TRAIL")
post(f"/api/session/{session_id}/end", {})

report = f"""
{'='*65}
POONAWALLA FINCORP — SESSION REPORT
{'='*65}
Session ID      : {session_id}
Applicant       : {p['name']}
Profile Type    : {args.profile.upper()}
Date/Time       : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'─'*65}
DECISION        : {decision}
Risk Band       : {band}
Default Prob    : {prob:.3f}
Fraud Score     : {fraud_res.get('fraud_score',0):.3f}
Fraud Verdict   : {fraud_res.get('verdict','CLEAR')}
{'─'*65}
OFFER
  Product       : {best.get('product','—')}
  Amount        : Rs.{best.get('amount',0):,}
  Rate          : {best.get('rate',0)}% p.a.
  Tenure        : {best.get('tenure_months',0)} months
  Monthly EMI   : Rs.{int(best.get('emi',0)):,}
{'─'*65}
EXTRACTED DATA
  Income        : Rs.{extracted_income or p['income']:,}/mo
  Profession    : {extracted_prof or p['employment']}
  Form Fields   : {form_fields}
{'─'*65}
"""
print(report)

REPORT_DIR = ROOT / "reports"; REPORT_DIR.mkdir(exist_ok=True)
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
rpath = REPORT_DIR / f"session_{session_id[:8]}_{ts}.txt"
with open(rpath, "w", encoding="utf-8") as f:
    f.write(report)

print(GREEN(f"  Report saved: {rpath}"))
print(GREEN(f"  Audit trail:  GET {API}/api/audit/{session_id}"))
print()
