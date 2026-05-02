import os
import sys
import time
import asyncio
import cv2
import numpy as np
import json
import torch
import urllib.request
import aiohttp
import mediapipe as mp
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, stt
from livekit.plugins import deepgram
from ultralytics import YOLO
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from datetime import datetime

load_dotenv()

MODEL_PATH = 'face_landmarker.task'
if not os.path.exists(MODEL_PATH):
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task", MODEL_PATH)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
yolo_model = YOLO('yolo11s.pt').to(device)

base_options = python.BaseOptions(model_asset_path=MODEL_PATH, delegate=python.BaseOptions.Delegate.CPU)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=True,
    num_faces=1,
    min_face_detection_confidence=0.3, 
    min_face_presence_confidence=0.3,
    min_tracking_confidence=0.3
)
detector = vision.FaceLandmarker.create_from_options(options)

pan_success = asyncio.Event()

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    print("--- [SYS] Agent Active ---", flush=True)

    @ctx.room.on("data_received")
    def on_data_received(dp: rtc.DataPacket):
        if dp.topic == "kyc-control":
            try:
                if dp.data.decode('utf-8') == "pan_upload_success":
                    pan_success.set()
            except: pass

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, pub: rtc.RemoteTrackPublication, p: rtc.RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            asyncio.create_task(process_video(track, ctx.room))
        elif track.kind == rtc.TrackKind.KIND_AUDIO:
            asyncio.create_task(process_audio(track, ctx.room))

async def process_video(track: rtc.VideoTrack, room: rtc.Room):
    stream = rtc.VideoStream(track)
    
    # Thresholds
    M_AWAY = 2.0  # M seconds
    N_FOCUS = 1.0 # N seconds
    CAL_DUR = 5.0
    
    # State
    last_t = None
    unf_s = 0.0
    foc_s = 0.0
    tick = 0
    
    base_l = base_r = base_ly = base_ry = None
    base_lr = base_rr = base_p = -1.0
    
    S_PAN = "pan"
    S_CAL = "cal"   
    S_DET = "det"
    state = S_PAN
    
    cal_data = []
    cal_start = 0.0
    alert = False
    last_alert = None
    prompt_t = 0.0

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

        if state == S_PAN:
            if (now - prompt_t) >= 3.0:
                prompt_t = now
                await room.local_participant.publish_data(b"focus-alert:upload-required", topic="focus-alert")
            if pan_success.is_set():
                state = S_CAL
                cal_start = now
                await room.local_participant.publish_data(b"focus-alert:upload-done", topic="focus-alert")
            continue

        res = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        has_f = res.face_landmarks and len(res.face_landmarks) > 0

        if has_f:
            lm = res.face_landmarks[0]
            ns, lc, rc = lm[1], lm[234], lm[454]
            fw = max(1e-6, rc.x - lc.x)
            lr, rr = (ns.x - lc.x)/fw, (rc.x - ns.x)/fw
            
            # Iris
            l_is = [lm[i] for i in (473, 474, 475, 476, 477)]
            r_is = [lm[i] for i in (468, 469, 470, 471, 472)]
            lx, ly = sum(p.x for p in l_is)/5, sum(p.y for p in l_is)/5
            rx, ry = sum(p.x for p in r_is)/5, sum(p.y for p in r_is)/5

            # Eye Bounds
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
                
                # SEND THE UI MESSAGE SIGNAL
                msg = f"focus-alert:calibrating-{max(0, int(rem))}".encode()
                await room.local_participant.publish_data(msg, topic="focus-alert")

                if (now - cal_start) >= CAL_DUR:
                    base_l, base_r = sum(d[0] for d in cal_data)/len(cal_data), sum(d[1] for d in cal_data)/len(cal_data)
                    base_ly, base_ry = sum(d[2] for d in cal_data)/len(cal_data), sum(d[3] for d in cal_data)/len(cal_data)
                    base_p = sum(d[4] for d in cal_data)/len(cal_data)
                    base_lr, base_rr = sum(d[5] for d in cal_data)/len(cal_data), sum(d[6] for d in cal_data)/len(cal_data)
                    state = S_DET
                    unf_s = foc_s = 0.0
                    await room.local_participant.publish_data(b"focus-alert:cal-done", topic="focus-alert")
                continue

            elif state == S_DET:
                dx, dy = (abs(lpx - base_l) + abs(rpx - base_r))/2, (abs(lpy - base_ly) + abs(rpy - base_ry))/2
                h_off = abs(lr - base_lr) > 0.10 or abs(rr - base_rr) > 0.10
                p_off = (pr - base_p) > 0.08
                
                unf_now = (dx > 0.025 or dy > 0.035 or h_off or p_off)

                if unf_now:
                    unf_s += dt
                    foc_s = 0.0
                    if unf_s > 5.0 and not alert:
                        print(f"[⚠️ WARNING] User unfocused for {unf_s:.1f}s")
                        alert = True
                        
                        # --- FIRE ALERT TO FASTAPI SERVER ---
                        try:
                            alert_payload = {
                                "type": "ATTENTION_LOSS",
                                "severity": "HIGH",
                                "message": f"Applicant looking away for {unf_s:.1f} seconds.",
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                            async with aiohttp.ClientSession() as session:
                                await session.post('http://localhost:8000/api/admin/trigger-alert', json=alert_payload)
                        except Exception as e:
                            print(f"[SYS] Could not send alert to server: {e}")
                        # ------------------------------------
                else:
                    if alert:
                        foc_s += dt
                        if foc_s >= N_FOCUS:
                            alert = False
                            unf_s = 0.0
                    else: unf_s = 0.0

                if alert != last_alert:
                    await room.local_participant.publish_data(b"focus-alert:unfocused" if alert else b"focus-alert:focused", topic="focus-alert")
                    last_alert = alert

                if tick % 8 == 0: print(f"[DEBUG] alert={alert} unf={unf_s:.1f}")
                tick += 1
        else:
            if state == S_DET:
                unf_s += dt
                if unf_s > 5.0 and not alert:
                    alert = True
                    await room.local_participant.publish_data(b"focus-alert:unfocused", topic="focus-alert")

async def process_audio(track: rtc.AudioTrack, room: rtc.Room):
    audio_stream = rtc.AudioStream(track)
    stt_plugin = deepgram.STT(model="nova-2", language="hi")
    stt_stream = stt_plugin.stream()
    
    async def push():
        async for ev in audio_stream: 
            stt_stream.push_frame(ev.frame)
            
    asyncio.create_task(push())
    print("--- [SYS] Audio Active: Listening for Verbal Consent ---", flush=True)
    
    consent_given = False

    async for ev in stt_stream:
        if ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
            alt = ev.alternatives[0]
            text = alt.text.strip().lower()
            confidence = alt.confidence
            
            if not text or confidence < 0.70:
                continue
            
            print(f"[🗣️ USER]: {text} (Conf: {confidence:.2f})")
            
            if not consent_given:
                consent_keywords = ["agree", "yes", "consent", "मंजूर", "सहमत", "हां", "ha", "haan"]
                if len(text.split()) >= 3 and any(word in text for word in consent_keywords):
                    consent_given = True
                    consent_timestamp = datetime.utcnow().isoformat() + "Z"
                    
                    print(f"\n✅ [LEGAL] Verbal Consent Captured at: {consent_timestamp}")
                    print(f"📝 [EVIDENCE] Utterance: '{text}'\n")
                    
                    msg = f"focus-alert:consent-{consent_timestamp}".encode()
                    await room.local_participant.publish_data(msg, topic="focus-alert")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))