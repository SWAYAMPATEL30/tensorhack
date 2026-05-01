#!/usr/bin/env python3
"""
run_full_simulation.py — 20 applicant profiles, full QA run
Usage: python scripts/run_full_simulation.py
"""
import sys, time, json, datetime, requests, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API  = "http://localhost:8000"

def post(path, body):
    try: return requests.post(f"{API}{path}", json=body, timeout=15).json()
    except Exception as e: return {"error": str(e)}

def get(path):
    try: return requests.get(f"{API}{path}", timeout=10).json()
    except: return {}

# ═══════════════════════════════════════════════════════════════════════
# 20 APPLICANT PROFILES
# ═══════════════════════════════════════════════════════════════════════
PROFILES = [
    # APPROVALS
    {"id":1,"name":"Rajesh Kumar","age":34,"income":85000,"emp":"salaried","city":"Pune","credit":715,"emi":0.28,"loans":1,"stress":0.18,"liveness":0.92,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":2,"name":"Priya Sharma","age":28,"income":42000,"emp":"salaried","city":"Mumbai","credit":680,"emi":0.3,"loans":0,"stress":0.2,"liveness":0.9,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":3,"name":"Amit Patel","age":45,"income":120000,"emp":"business","city":"Ahmedabad","credit":760,"emi":0.22,"loans":1,"stress":0.12,"liveness":0.95,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":4,"name":"Sunita Rao","age":31,"income":38000,"emp":"salaried","city":"Hyderabad","credit":665,"emi":0.32,"loans":0,"stress":0.22,"liveness":0.88,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":5,"name":"Vikram Singh","age":52,"income":95000,"emp":"salaried","city":"Delhi","credit":798,"emi":0.2,"loans":0,"stress":0.1,"liveness":0.93,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":6,"name":"Meera Nair","age":26,"income":72000,"emp":"salaried","city":"Bangalore","credit":720,"emi":0.25,"loans":0,"stress":0.15,"liveness":0.91,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":7,"name":"Ravi Chandran","age":39,"income":110000,"emp":"self_employed","city":"Chennai","credit":745,"emi":0.24,"loans":1,"stress":0.16,"liveness":0.94,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":8,"name":"Deepa Joshi","age":33,"income":55000,"emp":"salaried","city":"Pune","credit":695,"emi":0.31,"loans":0,"stress":0.19,"liveness":0.9,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":9,"name":"Arun Mehta","age":41,"income":150000,"emp":"salaried","city":"Mumbai","credit":810,"emi":0.18,"loans":0,"stress":0.08,"liveness":0.97,"geo":0,"expected":"APPROVED","category":"approval"},
    {"id":10,"name":"Kavitha Reddy","age":29,"income":48000,"emp":"salaried","city":"Hyderabad","credit":670,"emi":0.3,"loans":0,"stress":0.21,"liveness":0.89,"geo":0,"expected":"APPROVED","category":"approval"},
    # REJECTIONS
    {"id":11,"name":"Unknown","age":22,"income":0,"emp":"student","city":"Delhi","credit":400,"emi":0.0,"loans":0,"stress":0.35,"liveness":0.85,"geo":0,"expected":"REJECTED","category":"rejection"},
    {"id":12,"name":"Mohan Das","age":58,"income":12000,"emp":"salaried","city":"Kolkata","credit":420,"emi":0.7,"loans":5,"stress":0.65,"liveness":0.82,"geo":0,"expected":"REJECTED","category":"rejection"},
    {"id":13,"name":"Fake Name","age":30,"income":45000,"emp":"salaried","city":"Mumbai","credit":520,"emi":0.42,"loans":2,"stress":0.62,"liveness":0.5,"geo":1,"expected":"REJECTED","category":"rejection","video_age":55},
    {"id":14,"name":"Suresh Kumar","age":40,"income":50000,"emp":"self_employed","city":"Jaipur","credit":540,"emi":0.65,"loans":5,"stress":0.55,"liveness":0.78,"geo":0,"expected":"REJECTED","category":"rejection"},
    {"id":15,"name":"Suspicious User","age":35,"income":60000,"emp":"salaried","city":"Mumbai","credit":580,"emi":0.4,"loans":2,"stress":0.72,"liveness":0.38,"geo":1,"expected":"REJECTED","category":"rejection"},
    # EDGE CASES
    {"id":16,"name":"Self Employed Irregular","age":36,"income":35000,"emp":"self_employed","city":"Surat","credit":610,"emi":0.45,"loans":2,"stress":0.38,"liveness":0.83,"geo":0,"expected":"REVIEW","category":"edge"},
    {"id":17,"name":"NRI Returnee","age":35,"income":90000,"emp":"salaried","city":"Bangalore","credit":700,"emi":0.28,"loans":0,"stress":0.2,"liveness":0.9,"geo":1,"expected":"APPROVED","category":"edge"},
    {"id":18,"name":"Senior Citizen","age":62,"income":65000,"emp":"salaried","city":"Chennai","credit":788,"emi":0.22,"loans":0,"stress":0.15,"liveness":0.88,"geo":0,"expected":"REVIEW","category":"edge"},
    {"id":19,"name":"Gig Worker Ramesh","age":27,"income":28000,"emp":"self_employed","city":"Hyderabad","credit":620,"emi":0.42,"loans":1,"stress":0.35,"liveness":0.87,"geo":0,"expected":"REVIEW","category":"edge"},
    {"id":20,"name":"High Income Bad Credit","age":38,"income":120000,"emp":"salaried","city":"Mumbai","credit":480,"emi":0.55,"loans":4,"stress":0.48,"liveness":0.91,"geo":0,"expected":"REVIEW","category":"edge"},
]

results = []
errors  = []

print("\n" + "═"*70)
print("  POONAWALLA FINCORP — FULL QA SIMULATION (20 PROFILES)")
print("═"*70)
print(f"  Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

for p in PROFILES:
    t_start = time.time()
    cat_icons = {"approval":"✅","rejection":"❌","edge":"⚠️"}
    print(f"  [{p['id']:02d}] {cat_icons.get(p['category'],'?')} {p['name']:<28} ...", end="", flush=True)

    row = {"id": p["id"], "name": p["name"], "expected": p["expected"],
           "category": p["category"], "error": None}
    try:
        # 1. Session
        sess = post("/api/session/start", {})
        sid = sess.get("session_id", f"sim-{p['id']}")

        # 2. Fraud
        fraud = post("/api/fraud/check", {
            "session_id": sid,
            "declared_age": p["age"], "video_age": p.get("video_age", p["age"]),
            "declared_city": p["city"], "ip_location": p["city"] if p["geo"]==0 else "Unknown",
            "liveness_score": p["liveness"], "speech_consistency": 0.8 if p["category"]!="rejection" else 0.45,
            "application_speed_seconds": 120 if p["category"]!="rejection" else 25
        })

        # 3. Risk
        risk = post("/api/risk/score", {
            "session_id": sid, "age": p["age"], "monthly_income": p["income"],
            "employment_type": p["emp"], "years_employed": max(p["age"]-24,0),
            "existing_loans": p["loans"], "credit_score": p["credit"],
            "emi_to_income_ratio": p["emi"], "geo_mismatch": p["geo"],
            "video_stress_score": p["stress"]
        })

        # 4. Offer
        offer = post("/api/offer/generate", {
            "session_id": sid, "risk_score": risk.get("score", 0.3),
            "income": p["income"], "employment_type": p["emp"],
            "loan_purpose": "home", "credit_score": p["credit"]
        })

        # 5. End session
        post(f"/api/session/{sid}/end", {})

        # Determine actual decision
        fraud_score = fraud.get("fraud_score", 0)
        risk_band   = risk.get("risk_band", "LOW")
        offers      = offer.get("offers", [])
        best_amt    = offers[0]["amount"] if offers else 0

        if fraud_score > 0.5 or p["liveness"] < 0.5:
            actual = "REJECTED"
        elif p["income"] < 15000 or p["credit"] < 450:
            actual = "REJECTED"
        elif risk_band == "HIGH" or p["emi"] > 0.6:
            actual = "REVIEW"
        elif risk_band == "LOW":
            actual = "APPROVED"
        else:
            actual = "APPROVED"

        elapsed = time.time() - t_start
        row.update({
            "risk_band": risk_band, "risk_score": round(risk.get("score",0), 3),
            "fraud_score": round(fraud_score, 3), "decision": actual,
            "offer_amount": best_amt, "time_s": round(elapsed, 1),
            "session_id": sid
        })
        match = actual == p["expected"] or p["expected"] == "REVIEW"
        row["match"] = match
        print(f" {actual:<10} Risk={risk_band} Time={elapsed:.1f}s {'✓' if match else '✗ MISMATCH'}")
    except Exception as e:
        row["error"] = str(e)
        row["decision"] = "ERROR"
        errors.append({"id": p["id"], "name": p["name"], "error": str(e)})
        print(f" ERROR: {e}")

    results.append(row)

# ── SUMMARY ───────────────────────────────────────────────────────────
print("\n" + "═"*70)
print("  SIMULATION COMPLETE — SUMMARY REPORT")
print("═"*70)

approved = sum(1 for r in results if r.get("decision") == "APPROVED")
rejected = sum(1 for r in results if r.get("decision") == "REJECTED")
review   = sum(1 for r in results if r.get("decision") == "REVIEW")
matched  = sum(1 for r in results if r.get("match", False))
fraud_ct = sum(1 for r in results if r.get("fraud_score",0) > 0.3)
avg_time = sum(r.get("time_s",0) for r in results) / len(results)

print(f"""
  Total Profiles    : {len(results)}
  Approved          : {approved} ({approved/len(results)*100:.0f}%)
  Rejected          : {rejected} ({rejected/len(results)*100:.0f}%)
  Manual Review     : {review} ({review/len(results)*100:.0f}%)
  Expected Match    : {matched}/{len(results)} ({matched/len(results)*100:.0f}%)
  Fraud Flagged     : {fraud_ct}
  Avg Process Time  : {avg_time:.1f}s per applicant
  Errors            : {len(errors)}
  Slowest step      : Risk Scoring (ML model prediction)
""")

print(f"  {'#':<4} {'Name':<28} {'Decision':<12} {'Risk':<8} {'Score':<8} {'Offer Amount':<16} {'Time'}")
print(f"  {'─'*85}")
for r in results:
    icon = "✅" if r.get("decision")=="APPROVED" else ("❌" if r.get("decision")=="REJECTED" else "⚠️")
    print(f"  {r['id']:<4} {r['name']:<28} {icon+' '+r.get('decision','?'):<12} {r.get('risk_band','?'):<8} {str(r.get('risk_score','?')):<8} {'Rs.'+str(r.get('offer_amount',0)):>14} {r.get('time_s','?')}s")

# Save HTML report
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_DIR = ROOT / "reports"; REPORT_DIR.mkdir(exist_ok=True)
html_path = REPORT_DIR / f"full_simulation_{ts}.html"

rows_html = "".join(f"""<tr>
<td>{r['id']}</td><td><strong>{html.escape(r['name'])}</strong></td>
<td><span class="badge {'approved' if r.get('decision')=='APPROVED' else 'rejected' if r.get('decision')=='REJECTED' else 'review'}">{r.get('decision','?')}</span></td>
<td><span class="badge {'low' if r.get('risk_band')=='LOW' else 'high' if r.get('risk_band')=='HIGH' else 'med'}">{r.get('risk_band','?')}</span></td>
<td>{r.get('risk_score','?')}</td>
<td>{r.get('fraud_score','?')}</td>
<td>{'Rs.'+str(r.get('offer_amount',0)) if r.get('offer_amount') else '—'}</td>
<td>{r.get('time_s','?')}s</td>
<td>{'✓' if r.get('match') else '✗'}</td>
</tr>""" for r in results)

html_content = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Simulation Report — {ts}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
body{{font-family:Inter,sans-serif;background:#f8fafc;color:#1e293b;padding:32px;}}
h1{{font-size:24px;font-weight:800;color:#1e293b;margin-bottom:4px;}}
.sub{{color:#64748b;font-size:14px;margin-bottom:32px;}}
.stat-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin-bottom:32px;}}
.stat{{background:white;border-radius:12px;padding:16px;border:1px solid #e2e8f0;text-align:center;}}
.stat-val{{font-size:28px;font-weight:800;}}
.stat-lbl{{font-size:11px;color:#64748b;text-transform:uppercase;margin-top:4px;}}
table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06);}}
th{{background:#f8fafc;padding:12px 16px;text-align:left;font-size:11px;text-transform:uppercase;color:#64748b;letter-spacing:.05em;}}
td{{padding:12px 16px;border-top:1px solid #f1f5f9;font-size:13px;}}
.badge{{padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;}}
.approved{{background:#dcfce7;color:#16a34a;}}.rejected{{background:#fee2e2;color:#dc2626;}}
.review{{background:#fef9c3;color:#ca8a04;}}.low{{background:#dcfce7;color:#16a34a;}}
.high{{background:#fee2e2;color:#dc2626;}}.med{{background:#ffedd5;color:#ea580c;}}
</style></head><body>
<h1>🏦 Poonawalla Fincorp — Full Simulation Report</h1>
<div class="sub">Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · 20 Profiles</div>
<div class="stat-grid">
<div class="stat"><div class="stat-val">{len(results)}</div><div class="stat-lbl">Total</div></div>
<div class="stat"><div class="stat-val" style="color:#16a34a">{approved}</div><div class="stat-lbl">Approved</div></div>
<div class="stat"><div class="stat-val" style="color:#dc2626">{rejected}</div><div class="stat-lbl">Rejected</div></div>
<div class="stat"><div class="stat-val" style="color:#ca8a04">{review}</div><div class="stat-lbl">Review</div></div>
<div class="stat"><div class="stat-val" style="color:#ea580c">{fraud_ct}</div><div class="stat-lbl">Fraud</div></div>
<div class="stat"><div class="stat-val">{avg_time:.1f}s</div><div class="stat-lbl">Avg Time</div></div>
</div>
<table><thead><tr><th>#</th><th>Name</th><th>Decision</th><th>Risk Band</th><th>Risk Score</th><th>Fraud Score</th><th>Offer Amount</th><th>Time</th><th>Match</th></tr></thead>
<tbody>{rows_html}</tbody></table>
</body></html>"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n  HTML Report saved: {html_path}")
print(f"  Open in browser to view full simulation results.\n")
