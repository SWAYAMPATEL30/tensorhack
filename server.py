from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2
import numpy as np
import easyocr
import re
import torch
import asyncio
import json
import uuid
import aiohttp
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MOCK REDIS STORE (For Hackathon Demo) ---
session_store = {}

APP_PUBLIC_BASE_URL = os.getenv("APP_PUBLIC_BASE_URL", "http://49.36.106.153")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
SMS_DEFAULT_COUNTRY_CODE = os.getenv("SMS_DEFAULT_COUNTRY_CODE", "+91")

# ==========================================
# FEATURE 33: SMS RESUME LINK
# ==========================================
@app.post("/api/kyc/simulate-drop")
async def simulate_drop(request: Request):
    data = await request.json()
    phone = data.get("phone", "9930350234")
    
    # Generate unique resume token
    resume_id = str(uuid.uuid4())[:8]
    session_store[resume_id] = {"status": "calibrated", "phone": phone}
    
    recovery_link = f"{APP_PUBLIC_BASE_URL}/?resume_id={resume_id}"
    
    sms_message = f"TensorX KYC Drop Detected. Resume here: {recovery_link}"
    
    print(f"\n📡 [REDIS] State saved for session: {resume_id}")
    print(f"📱 [Twilio] Sending SMS to {phone}: {sms_message}\n")
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_FROM_NUMBER:
        return {
            "status": "error",
            "message": "Twilio credentials are missing. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER in .env and restart the server.",
        }

    normalized_phone = phone.replace(" ", "")
    if normalized_phone.startswith("+"):
        to_number = normalized_phone
    elif normalized_phone.isdigit() and len(normalized_phone) == 10:
        to_number = f"{SMS_DEFAULT_COUNTRY_CODE}{normalized_phone}"
    else:
        return {"status": "error", "message": "Invalid phone number format. Use 10 digits or E.164 (+countrycode)."}

    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                auth=aiohttp.BasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                data={
                    "From": TWILIO_FROM_NUMBER,
                    "To": to_number,
                    "Body": sms_message,
                },
            )
            resp_json = await resp.json(content_type=None)
            if resp.status >= 400:
                return {
                    "status": "error",
                    "message": "Twilio request failed.",
                    "details": resp_json,
                }
    except Exception as exc:
        return {"status": "error", "message": f"Twilio error: {exc}"}

    return {"status": "success", "resume_id": resume_id, "link": recovery_link}


# ==========================================
# FEATURE 39: SSE REAL-TIME ALERT SYSTEM
# ==========================================
alert_queue = asyncio.Queue()

@app.post("/api/admin/trigger-alert")
async def trigger_alert(request: Request):
    data = await request.json()
    await alert_queue.put(json.dumps(data)) 
    print(f"🚨 [SYSTEM] Received Fraud Alert: {data}")
    return {"status": "Alert queued"}

async def event_generator() -> AsyncGenerator[str, None]:
    while True:
        alert_json_str = await alert_queue.get()
        yield f"data: {alert_json_str}\n\n"

@app.get("/api/admin/alerts/stream")
async def sse_alerts_stream():
    return StreamingResponse(event_generator(), media_type="text/event-stream")
# ==========================================


# ==========================================
# FEATURE 11: OCR PIPELINE
# ==========================================
print("Loading EasyOCR...")
reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

@app.post("/api/kyc/upload-pan")
async def upload_pan(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    results = reader.readtext(img, detail=0)
    raw_text = " ".join(results).upper()

    clean_text = re.sub(r'[^A-Z0-9]', '', raw_text)

    found_pan = None
    for i in range(len(clean_text) - 9):
        candidate = list(clean_text[i:i+10])
        
        for j in range(5):
            if candidate[j] == '0': candidate[j] = 'O'
            elif candidate[j] == '1': candidate[j] = 'I'
            elif candidate[j] == '5': candidate[j] = 'S'
            elif candidate[j] == '8': candidate[j] = 'B'
            
        for j in range(5, 9):
            if candidate[j] == 'O': candidate[j] = '0'
            elif candidate[j] == 'I': candidate[j] = '1'
            elif candidate[j] == 'S': candidate[j] = '5'
            elif candidate[j] == 'B': candidate[j] = '8'
            elif candidate[j] == 'Z': candidate[j] = '2'
            
        if candidate[9] == '0': candidate[9] = 'O'
        elif candidate[9] == '1': candidate[9] = 'I'
        elif candidate[9] == '5': candidate[9] = 'S'
        elif candidate[9] == '8': candidate[9] = 'B'
        
        final_str = "".join(candidate)
        
        if re.fullmatch(r'[A-Z]{5}[0-9]{4}[A-Z]', final_str):
            found_pan = final_str
            break

    if found_pan:
        return {"status": "success", "pan": found_pan}
    else:
        return {
            "status": "error", 
            "message": f"Could not extract PAN. Raw OCR saw: {raw_text[:100]}..."
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)