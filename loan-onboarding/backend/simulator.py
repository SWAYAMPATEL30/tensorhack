import sqlite3, uuid, time, random, datetime
import os
db_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'loan_wizard.db')
db_path = os.path.abspath(db_path)

print(f'Starting real-time load simulator on {db_path}...')
while True:
    try:
        db = sqlite3.connect(db_path)
        c = db.cursor()
        sid = str(uuid.uuid4())
        name = random.choice(['Vikram P', 'Sunita R', 'Rajesh K', 'Priya M', 'Amit S', 'Deepa L'])
        # slightly more APPROVED to make metrics look good
        decision = random.choice(['APPROVED', 'APPROVED', 'REVIEW', 'REJECTED'])
        f_score = random.random() * 0.4 if decision != 'REJECTED' else 0.5 + random.random() * 0.4
        f_verdict = 'FRAUD' if f_score > 0.5 else 'CLEAR'
        income = random.randint(25000, 200000)
        now = datetime.datetime.now().isoformat()
        amount = random.randint(50000, 1000000)
        risk = random.random() * 0.2
        city = random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Pune', 'Chennai'])
        
        c.execute('''INSERT INTO sessions 
                     (session_id, created_at, ended_at, status, applicant_name, decision, fraud_score, monthly_income, offer_amount, default_probability, fraud_verdict, city, employment_type) 
                     VALUES (?, ?, ?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?, 'Salaried')''',
                  (sid, now, now, name, decision, f_score, income, amount, risk, f_verdict, city))
        db.commit()
        db.close()
        time.sleep(3) # insert every 3 seconds
    except Exception as e:
        print(e)
        time.sleep(5)
