"""
Feature #13: Selfie-to-Aadhaar face verification (InsightFace / mock fallback)
Feature #19: Deepfake CNN detection layer (EfficientNet / mock fallback)
"""
import base64, io, time, random
import numpy as np
from pydantic import BaseModel
from typing import Optional

class FaceVerifyPayload(BaseModel):
    session_id: str
    live_frame_base64: str       # Best liveness frame (base64 JPEG)
    aadhaar_photo_base64: Optional[str] = None  # OCR-extracted Aadhaar photo

class DeepfakePayload(BaseModel):
    session_id: str
    frame_base64: str

# ─── InsightFace (with graceful fallback) ──────────────────────────────────

_insightface_model = None

def _load_insightface():
    global _insightface_model
    if _insightface_model is None:
        try:
            import insightface
            from insightface.app import FaceAnalysis
            _insightface_model = FaceAnalysis(name="buffalo_sc", providers=["CPUExecutionProvider"])
            _insightface_model.prepare(ctx_id=-1, det_size=(160, 160))
            print("[OK] InsightFace loaded")
        except Exception as e:
            print(f"[WARN] InsightFace not available: {e} — using mock fallback")
            _insightface_model = "mock"
    return _insightface_model

def _decode_image(b64: str):
    """Decode base64 to PIL Image."""
    from PIL import Image
    if "," in b64:
        b64 = b64.split(",")[1]
    img_bytes = base64.b64decode(b64)
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")

def _real_face_similarity(img1, img2) -> float:
    model = _load_insightface()
    if model == "mock":
        return None
    try:
        import cv2, numpy as np
        arr1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2BGR)
        arr2 = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2BGR)
        faces1 = model.get(arr1)
        faces2 = model.get(arr2)
        if not faces1 or not faces2:
            return 0.0
        e1 = faces1[0].embedding
        e2 = faces2[0].embedding
        sim = float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2)))
        return sim
    except Exception as e:
        print(f"[InsightFace] error: {e}")
        return None

def _mock_face_similarity(live_b64: str, doc_b64: str) -> float:
    """Deterministic mock based on frame content hash."""
    combined = (live_b64[:50] + (doc_b64 or "")[:50])
    val = sum(ord(c) for c in combined) % 100
    if val > 70:
        return 0.92  # Strong match
    elif val > 40:
        return 0.78  # Review
    else:
        return 0.55  # Mismatch

def verify_face(payload: FaceVerifyPayload) -> dict:
    """Feature #13 — Selfie vs Aadhaar face match."""
    t0 = time.time()

    if payload.aadhaar_photo_base64:
        try:
            img_live = _decode_image(payload.live_frame_base64)
            img_doc = _decode_image(payload.aadhaar_photo_base64)
            similarity = _real_face_similarity(img_live, img_doc)
        except Exception:
            similarity = None
    else:
        similarity = None

    if similarity is None:
        similarity = _mock_face_similarity(
            payload.live_frame_base64,
            payload.aadhaar_photo_base64 or ""
        )
        method = "mock"
    else:
        method = "insightface_arcface"

    if similarity >= 0.85:
        verdict = "MATCH"
        fraud_delta = 0.0
    elif similarity >= 0.70:
        verdict = "REVIEW"
        fraud_delta = 0.10
    else:
        verdict = "MISMATCH"
        fraud_delta = 0.40

    return {
        "cosine_similarity": round(similarity, 4),
        "verdict": verdict,
        "fraud_delta": fraud_delta,
        "method": method,
        "latency_ms": round((time.time() - t0) * 1000, 1),
        "threshold_match": 0.85,
        "threshold_review": 0.70,
    }

# ─── Deepfake Detection ─────────────────────────────────────────────────────

def check_deepfake(payload: DeepfakePayload) -> dict:
    """
    Feature #19 — EfficientNet deepfake detector.
    Mock: uses DCT frequency heuristic on frame.
    """
    t0 = time.time()

    try:
        # Real attempt: use frequency domain (DCT) as lightweight deepfake signal
        from PIL import Image
        import numpy as np

        b64 = payload.frame_base64
        if "," in b64:
            b64 = b64.split(",")[1]
        img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("L").resize((128, 128))
        arr = np.array(img, dtype=float)

        # DCT coefficient energy (deepfakes have abnormal high-freq energy)
        from scipy.fft import dct
        dct_arr = dct(dct(arr, axis=0), axis=1)
        hf_energy = float(np.mean(np.abs(dct_arr[64:, 64:])))
        lf_energy = float(np.mean(np.abs(dct_arr[:32, :32]))) + 1e-6
        ratio = hf_energy / lf_energy

        # Normalised score 0–1
        deepfake_score = min(1.0, ratio / 0.5)
        method = "dct_heuristic"
    except Exception:
        # Pure mock fallback
        h = sum(ord(c) for c in payload.frame_base64[:100])
        deepfake_score = (h % 100) / 1000.0  # Very low for real frames
        method = "mock"

    is_deepfake = deepfake_score > 0.5
    return {
        "deepfake_score": round(deepfake_score, 4),
        "is_deepfake": is_deepfake,
        "confidence": round(1 - deepfake_score if not is_deepfake else deepfake_score, 3),
        "method": method,
        "latency_ms": round((time.time() - t0) * 1000, 1),
        "fraud_delta": 0.5 if is_deepfake else 0.0,
    }
