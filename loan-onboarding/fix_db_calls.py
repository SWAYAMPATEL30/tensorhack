"""Fix ORM-style DB calls in features_api section to raw sqlite3."""
import re

with open("backend/main.py", encoding="utf-8", errors="replace") as f:
    code = f.read()

# Replace patterns: next(get_db()) + ORM query → raw sqlite3
FIXES = [
    # fraud_ring
    (r"db = next\(get_db\(\)\)\r?\n    try:\r?\n        sessions = \[.*?\.query\(CustomerSession\)\.limit\(50\)\.all\(\)\]\r?\n    except: sessions = \[\]",
     """try:
        db = get_db()
        rows = db.execute("SELECT session_id, applicant_name, decision, fraud_score FROM sessions LIMIT 50").fetchall()
        sessions = [{"session_id": r[0], "applicant_name": r[1], "decision": r[2], "fraud_score": r[3] or 0, "city": "Mumbai"} for r in rows]
        db.close()
    except: sessions = []"""),
    # uw_queue
    (r"db = next\(get_db\(\)\)\r?\n    try:\r?\n        review = db\.query\(CustomerSession\)\.filter\(CustomerSession\.decision == \"REVIEW\"\).*?\.all\(\)\r?\n        return.*?for s in review\].*?\}\r?\n    except: return \{\"queue\": \[\], \"count\": 0\}",
     """try:
        db = get_db()
        rows = db.execute("SELECT session_id, applicant_name, fraud_score, created_at FROM sessions WHERE decision='REVIEW' ORDER BY created_at DESC LIMIT 10").fetchall()
        db.close()
        return {"queue": [{"session_id": r[0], "applicant_name": r[1], "fraud_score": r[2], "created_at": str(r[3])} for r in rows], "count": len(rows)}
    except: return {"queue": [], "count": 0}"""),
    # rbi_report
    (r"db = next\(get_db\(\)\)\r?\n    try:\r?\n        sessions = \[.*?\"fraud_verdict\".*?\.all\(\)\]\r?\n    except: sessions = \[\]\r?\n    return generate_rbi_report_data",
     """try:
        db = get_db()
        rows = db.execute("SELECT decision, monthly_income, fraud_verdict FROM sessions").fetchall()
        sessions = [{"decision": r[0], "monthly_income": r[1], "fraud_verdict": r[2]} for r in rows]
        db.close()
    except: sessions = []
    return generate_rbi_report_data"""),
    # health_score
    (r"db = next\(get_db\(\)\)\r?\n    try:\r?\n        s = db\.query\(CustomerSession\)\.filter_by\(session_id=session_id\)\.first\(\)\r?\n        data = \{\"credit_score\".*?\} if s else \{\}\r?\n    except: data = \{\}\r?\n    return compute_health_score",
     """try:
        db = get_db()
        row = db.execute("SELECT monthly_income, fraud_score FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        db.close()
        data = {"credit_score": 680, "monthly_income": (row[0] or 50000) if row else 50000, "fraud_score": (row[1] or 0.1) if row else 0.1}
    except: data = {}
    return compute_health_score"""),
    # session_summary
    (r"db = next\(get_db\(\)\)\r?\n    try:\r?\n        s = db\.query\(CustomerSession\)\.filter_by\(session_id=session_id\)\.first\(\)\r?\n        sdata = \{.*?\"liveness_score\": 0\.95.*?\} if s else \{\}\r?\n    except: sdata = \{\"session_id\": session_id\}\r?\n    return generate_session_summary",
     """try:
        db = get_db()
        row = db.execute("SELECT applicant_name, monthly_income, risk_band, fraud_verdict, decision, employment_type, fraud_score FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        db.close()
        sdata = {"session_id": session_id, "applicant_name": row[0], "monthly_income": row[1], "risk_band": row[2], "fraud_verdict": row[3], "decision": row[4], "employment_type": row[5], "emotion": "neutral", "liveness_score": 0.95, "fraud_score": row[6]} if row else {"session_id": session_id}
    except: sdata = {"session_id": session_id}
    return generate_session_summary"""),
    # benchmark count
    (r"db = next\(get_db\(\)\)\r?\n    try:\r?\n        total = db\.query\(CustomerSession\)\.count\(\)",
     """try:
        db = get_db()
        total = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        db.close()"""),
    # fairness
    (r"db = next\(get_db\(\)\)\r?\n    try:\r?\n        sessions = \[.*?\"monthly_income\".*?\.all\(\)\]\r?\n    except: sessions = \[\]\r?\n    return generate_fairness_report",
     """try:
        db = get_db()
        rows = db.execute("SELECT decision, monthly_income FROM sessions").fetchall()
        sessions = [{"decision": r[0], "monthly_income": r[1]} for r in rows]
        db.close()
    except: sessions = []
    return generate_fairness_report"""),
    # fraud_report
    (r"db = next\(get_db\(\)\)\r?\n    try:\r?\n        s = db\.query\(CustomerSession\)\.filter_by\(session_id=session_id\)\.first\(\)\r?\n        data = \{\"session_id\": session_id.*?\"decision\".*?\} if s else \{\"session_id\": session_id\}\r?\n    except: data = \{\"session_id\": session_id\}\r?\n    return generate_fraud_report",
     """try:
        db = get_db()
        row = db.execute("SELECT applicant_name, fraud_score, fraud_verdict, decision FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        db.close()
        data = {"session_id": session_id, "applicant_name": row[0], "fraud_score": row[1], "fraud_verdict": row[2], "decision": row[3]} if row else {"session_id": session_id}
    except: data = {"session_id": session_id}
    return generate_fraud_report"""),
    # SSE alert stream
    (r"db = next\(get_db\(\)\)\r?\n            try:\r?\n                high_risk = db\.query.*?\.all\(\)\r?\n                alerts = \[.*?for s in high_risk\]\r?\n            except: alerts = \[\]",
     """try:
                db = get_db()
                rows = db.execute("SELECT session_id, applicant_name, fraud_score, decision, created_at FROM sessions WHERE CAST(fraud_score AS REAL) > 0.4 ORDER BY created_at DESC LIMIT 5").fetchall()
                alerts = [{"session_id": (r[0] or '')[:8], "name": r[1], "fraud_score": r[2], "decision": r[3], "ts": str(r[4])} for r in rows]
                db.close()
            except: alerts = []"""),
]

for pattern, replacement in FIXES:
    code, count = re.subn(pattern, replacement, code, flags=re.DOTALL)
    if count:
        print(f"  Fixed: {pattern[:60]}... ({count} replacements)")
    else:
        print(f"  MISS:  {pattern[:60]}...")

with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Done. Total lines:", code.count("\n"))
