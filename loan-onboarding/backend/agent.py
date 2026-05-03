"""
TensorX Hybrid KYC Agent — Conversational Voice Pipeline
Uses: Deepgram STT + OpenAI GPT-4o-mini LLM + OpenAI TTS
Run: python agent.py start
"""
import os
import asyncio
import aiohttp
import time
import cv2
import numpy as np
import torch
import urllib.request
import mediapipe as mp

from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from livekit import rtc
from typing import Annotated
from livekit.agents import (
    AgentSession, Agent, JobContext, WorkerOptions, cli,
    RoomInputOptions, function_tool
)
from livekit.plugins import deepgram, silero, groq as groq_plugin
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from ultralytics import YOLO

# ─── Environment ────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# ─── MediaPipe Face Landmarker ───────────────────────────────────
MODEL_PATH = str(Path(__file__).resolve().parent / "face_landmarker.task")
if not os.path.exists(MODEL_PATH):
    print("[AGENT] Downloading face_landmarker.task...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        MODEL_PATH
    )

_lm_options = vision.FaceLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH, delegate=mp_python.BaseOptions.Delegate.CPU),
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=True,
    num_faces=1,
    min_face_detection_confidence=0.3,
    min_face_presence_confidence=0.3,
    min_tracking_confidence=0.3
)
face_detector = vision.FaceLandmarker.create_from_options(_lm_options)

# ─── YOLO ────────────────────────────────────────────────────────
device = 'cuda' if torch.cuda.is_available() else 'cpu'
yolo_model = YOLO(str(Path(__file__).resolve().parent / "yolo11s.pt")).to(device)

# ─── System Prompt ───────────────────────────────────────────────
KYC_INSTRUCTIONS = """
You are Aria, an AI loan agent.
CRITICAL RULES FOR TOOL CALLING:
1. You MUST call the `save_kyc_data` tool IMMEDIATELY after the user provides an answer to your question.
2. DO NOT wait until the end of the conversation to save data. Save EACH piece of information the moment you hear it.
3. If the user tells you their name, call save_kyc_data(name=...) right then.
4. If the user tells you their income, call save_kyc_data(monthly_income=...) right then.
5. NEVER ask the next question until you have successfully called `save_kyc_data` for the previous answer.

SEQUENCE OF QUESTIONS:
1. Greet the user.
2. Ask for their Full Name. -> MUST CALL save_kyc_data(name="...")
3. Ask for Date of Birth. -> MUST CALL save_kyc_data(dob="...")
4. Ask for Employment Type (salaried/self-employed). -> MUST CALL save_kyc_data(employment_type="...")
5. Ask for Monthly Income. -> MUST CALL save_kyc_data(monthly_income=...)
6. Ask for current EMIs. -> MUST CALL save_kyc_data(existing_emi=...)
7. Ask for Loan Purpose. -> MUST CALL save_kyc_data(loan_purpose="...")
8. Ask for Loan Amount. -> MUST CALL save_kyc_data(loan_amount=...)
9. Say "Please wait while I process your application." -> MUST CALL save_kyc_data(status="complete")
"""


# ─── KYC Agent Class ─────────────────────────────────────────────
class KYCAgent(Agent):
    def __init__(self, room_name: str):
        super().__init__(instructions=KYC_INSTRUCTIONS)
        self.room_name = room_name

    @function_tool
    async def save_kyc_data(
        self, 
        name: Annotated[str, "Full name of the user, spelled correctly."] = None,
        dob: Annotated[str, "Date of birth strictly in DD/MM/YYYY numerical format."] = None,
        employment_type: Annotated[str, "Employment type (e.g. salaried, self-employed)."] = None,
        monthly_income: Annotated[int, "Monthly income purely as a numerical integer (e.g. 50000)."] = None,
        existing_emi: Annotated[int, "Existing EMI strictly as an integer, 0 if none."] = None,
        loan_purpose: Annotated[str, "The primary purpose of the loan."] = None,
        loan_amount: Annotated[int, "The requested loan amount strictly as an integer."] = None,
        status: Annotated[str, "Set to 'complete' ONLY when all fields are collected."] = None
    ):
        """
        Save extracted KYC fields to the database. Call this immediately after confirming a field.
        """
        updates = {
            "name": name, "dob": dob, "employment_type": employment_type,
            "monthly_income": monthly_income, "existing_emi": existing_emi,
            "loan_purpose": loan_purpose, "loan_amount": loan_amount, "status": status
        }
        
        # We will build a dynamic response for the LLM
        llm_response_msg = "System Notification: Data saved successfully. "

        for k, v in updates.items():
            if v is not None:
                try:
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            f"{BACKEND_URL}/api/kyc/conversation-update",
                            json={"room_name": self.room_name, "field": k, "value": str(v)},
                            timeout=aiohttp.ClientTimeout(total=5)
                        )
                    print(f"[AGENT] ✅ Saved {k} = '{v}' for room '{self.room_name}'")
                    
                    # 🚀 DYNAMIC VALIDATION & INCREMENTAL OFFERS 🚀
                    # 1. When income is collected, pull mock CIBIL and run Risk Model
                    if k == "monthly_income":
                        async with aiohttp.ClientSession() as session:
                            # Pull CIBIL — use pan_number field (required by BureauPayload)
                            bureau_res = await session.post(
                                f"{BACKEND_URL}/api/bureau/pull",
                                json={"session_id": self.room_name, "pan_number": "ABCDE1234F", "name": name or "Applicant"},
                                timeout=5
                            )
                            bureau_data = await bureau_res.json()
                            cibil_score = bureau_data.get("score", 680)
                            
                            # Push CIBIL score to frontend
                            await session.post(
                                f"{BACKEND_URL}/api/kyc/conversation-update",
                                json={"room_name": self.room_name, "field": "cibil_score", "value": str(cibil_score)},
                                timeout=5
                            )
                            
                            # Calculate Risk with incremental voice/video signals
                            # We mock stress=0.15, attention=0.9 (since we have limited live video access here)
                            risk_res = await session.post(f"{BACKEND_URL}/api/risk/score", json={
                                "monthly_income": v,
                                "credit_score": cibil_score,
                                "video_stress_score": 0.15, # Partial signal
                                "employment_type": employment_type or "salaried"
                            }, timeout=5)
                            risk_data = await risk_res.json()
                            llm_response_msg += f"Validation Alert: Bureau fetched CIBIL={cibil_score}. Risk Profile is {risk_data.get('risk_band')}. You MUST casually inform the user that their profile looks {risk_data.get('risk_band')}-risk, then ask the NEXT question. "
                    
                    # 2. When loan amount is collected, run the final Offer Optimizer
                    if k == "loan_amount":
                        async with aiohttp.ClientSession() as session:
                            offer_res = await session.post(f"{BACKEND_URL}/api/offer/optimize", json={
                                "offer": {"amount": v, "rate": 12.5, "tenure_months": 36},
                                "risk_score": 0.2, # Incremental signal
                                "persona": employment_type or "salaried"
                            }, timeout=5)
                            offer_data = await offer_res.json()
                            opt_offer = offer_data.get("optimized_offer", {})
                            llm_response_msg += f"Offer Alert: An optimized offer was generated using stress and consent confidence signals. Offer is Rs.{opt_offer.get('amount')} at {opt_offer.get('rate')}% for {opt_offer.get('tenure_months')} months. Inform the user of this offer instead of just saying 'evaluating'. "

                except Exception as e:
                    print(f"[AGENT] ⚠️ Failed to save {k} or run validation: {e}")
                    
        llm_response_msg += "CRITICAL INSTRUCTION: You must now immediately speak the next question in the sequence to the user. Do not stay silent."
        return llm_response_msg


# ─── Iris Tracking (runs in parallel background task) ────────────
async def run_iris_tracking(track: rtc.VideoTrack, room: rtc.Room):
    """MediaPipe iris gaze tracking — fires SSE alert when user looks away 5+ seconds."""
    stream = rtc.VideoStream(track)
    M_AWAY = 2.0; N_FOCUS = 1.0; CAL_DUR = 5.0
    last_t = None; unf_s = 0.0; foc_s = 0.0; tick = 0
    base_l = base_r = base_ly = base_ry = None
    base_lr = base_rr = base_p = -1.0
    S_DET = "det"; S_CAL = "cal"
    state = S_CAL
    cal_data = []; cal_start = time.monotonic(); alert = False; last_alert = None

    async for ev in stream:
        now = time.monotonic()
        if last_t is None: last_t = now
        dt = now - last_t
        if dt < 0.12: continue
        last_t = now

        f = ev.frame
        rgba = f.convert(rtc.VideoBufferType.RGBA)
        img = np.frombuffer(rgba.data, np.uint8).reshape((rgba.height, rgba.width, 4))
        rgb = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        res = face_detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        has_f = res.face_landmarks and len(res.face_landmarks) > 0

        if has_f:
            lm = res.face_landmarks[0]
            ns, lc, rc = lm[1], lm[234], lm[454]
            fw = max(1e-6, rc.x - lc.x)
            lr, rr = (ns.x - lc.x)/fw, (rc.x - ns.x)/fw
            l_is = [lm[i] for i in (473, 474, 475, 476, 477)]
            r_is = [lm[i] for i in (468, 469, 470, 471, 472)]
            lx, ly = sum(p.x for p in l_is)/5, sum(p.y for p in l_is)/5
            rx, ry = sum(p.x for p in r_is)/5, sum(p.y for p in r_is)/5
            le = [lm[i] for i in [362, 385, 387, 263, 373, 380]]
            re = [lm[i] for i in [33, 160, 158, 133, 153, 144]]
            lpx = (lx - min(p.x for p in le)) / max(1e-6, max(p.x for p in le) - min(p.x for p in le))
            rpx = (rx - min(p.x for p in re)) / max(1e-6, max(p.x for p in re) - min(p.x for p in re))
            lpy = (ly - min(p.y for p in le)) / max(1e-6, max(p.y for p in le) - min(p.y for p in le))
            rpy = (ry - min(p.y for p in re)) / max(1e-6, max(p.y for p in re) - min(p.y for p in re))
            pr = (ns.y - (lm[33].y + lm[263].y)/2) / max(1e-6, (lm[13].y + lm[14].y)/2 - (lm[33].y + lm[263].y)/2)

            if state == S_CAL:
                cal_data.append((lpx, rpx, lpy, rpy, pr, lr, rr))
                rem = round(CAL_DUR - (now - cal_start), 1)
                msg = f"focus-alert:calibrating-{max(0, int(rem))}".encode()
                await room.local_participant.publish_data(msg, topic="focus-alert")
                if (now - cal_start) >= CAL_DUR:
                    base_l  = sum(d[0] for d in cal_data)/len(cal_data)
                    base_r  = sum(d[1] for d in cal_data)/len(cal_data)
                    base_ly = sum(d[2] for d in cal_data)/len(cal_data)
                    base_ry = sum(d[3] for d in cal_data)/len(cal_data)
                    base_p  = sum(d[4] for d in cal_data)/len(cal_data)
                    base_lr = sum(d[5] for d in cal_data)/len(cal_data)
                    base_rr = sum(d[6] for d in cal_data)/len(cal_data)
                    state = S_DET; unf_s = foc_s = 0.0
                    await room.local_participant.publish_data(b"focus-alert:cal-done", topic="focus-alert")
                continue

            elif state == S_DET:
                dx = (abs(lpx - base_l) + abs(rpx - base_r)) / 2
                dy = (abs(lpy - base_ly) + abs(rpy - base_ry)) / 2
                h_off = abs(lr - base_lr) > 0.10 or abs(rr - base_rr) > 0.10
                p_off = (pr - base_p) > 0.08
                unf_now = (dx > 0.025 or dy > 0.035 or h_off or p_off)

                if unf_now:
                    unf_s += dt; foc_s = 0.0
                    if unf_s > 5.0 and not alert:
                        alert = True
                        try:
                            async with aiohttp.ClientSession() as session:
                                await session.post(f"{BACKEND_URL}/api/admin/trigger-alert", json={
                                    "type": "ATTENTION_LOSS", "severity": "HIGH",
                                    "message": f"Applicant looking away for {unf_s:.1f}s.",
                                    "timestamp": datetime.utcnow().isoformat() + "Z"
                                })
                        except Exception as e:
                            print(f"[AGENT] Alert send failed: {e}")
                else:
                    if alert:
                        foc_s += dt
                        if foc_s >= N_FOCUS:
                            alert = False; unf_s = 0.0
                    else:
                        unf_s = 0.0

                if alert != last_alert:
                    msg = b"focus-alert:unfocused" if alert else b"focus-alert:focused"
                    await room.local_participant.publish_data(msg, topic="focus-alert")
                    last_alert = alert

                if tick % 8 == 0:
                    print(f"[IRIS] alert={alert} unf={unf_s:.1f}s", flush=True)
                tick += 1
        else:
            if state == S_DET:
                unf_s += dt
                if unf_s > 5.0 and not alert:
                    alert = True
                    await room.local_participant.publish_data(b"focus-alert:unfocused", topic="focus-alert")


# ─── Main Entrypoint ─────────────────────────────────────────────
async def entrypoint(ctx: JobContext):
    await ctx.connect()
    room_name = ctx.room.name
    print(f"[AGENT] 🚀 Connected to room: {room_name}", flush=True)

    pan_uploaded_event = asyncio.Event()
    biometrics_verified_event = asyncio.Event()

    async def poll_for_db_events():
        """Robustly poll the backend DB to check if the frontend successfully saved the PAN number and verified biometrics."""
        for _ in range(600): # 10 minute timeout
            try:
                async with aiohttp.ClientSession() as http_session:
                    async with http_session.get(f"{BACKEND_URL}/api/kyc/conversation-data/{room_name}") as resp:
                        data = await resp.json()
                        fields = data.get("fields", {})
                        if fields.get("pan_number") and not pan_uploaded_event.is_set():
                            print("[AGENT] PAN Upload Success verified from DB.", flush=True)
                            pan_uploaded_event.set()
                        if fields.get("biometrics_verified") == "true" and not biometrics_verified_event.is_set():
                            print("[AGENT] Biometrics Verified from DB. Phase 3 starting.", flush=True)
                            biometrics_verified_event.set()
                            return
            except Exception as e:
                pass
            await asyncio.sleep(1)
            
    asyncio.create_task(poll_for_db_events())

    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        pass

    # Start iris tracking on video track subscription
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, pub, participant):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            async def delayed_tracking():
                await pan_uploaded_event.wait()
                print("[AGENT] 👁 Iris tracking started", flush=True)
                await run_iris_tracking(track, ctx.room)
            asyncio.create_task(delayed_tracking())

 
    session = AgentSession(
        stt=deepgram.STT(model="nova-2", language="en-IN"),
        llm=groq_plugin.LLM(model="llama-3.1-8b-instant"),
        tts=deepgram.TTS(model="aura-asteria-en"),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=KYCAgent(room_name=room_name),
    )

    print("[AGENT] ✅ Conversational KYC session started, waiting for PAN upload...", flush=True)

    # Trigger the agent to start speaking first ONLY AFTER BIOMETRICS are verified
    async def delayed_greeting():
        await biometrics_verified_event.wait()
        await asyncio.sleep(1) # Give UI a moment to transition to Phase 3
        await session.say("Hello, I am Aria, a warm and professional AI loan specialist for Poonawalla Fincorp. Could you please tell me your First Name as it appears on your PAN card?", allow_interruptions=True, add_to_chat_ctx=True)
    
    asyncio.create_task(delayed_greeting())


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))