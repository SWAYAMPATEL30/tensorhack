"""
Feature #8: GPS Geo-location capture + fraud check
Feature #9: Device fingerprint + session metadata
"""
import hashlib, json, time, random
from typing import Optional
from pydantic import BaseModel

# ─── Schemas ────────────────────────────────────────────────────────────────

class GeoPayload(BaseModel):
    session_id: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    declared_city: Optional[str] = "Unknown"
    ip_address: Optional[str] = None

class DevicePayload(BaseModel):
    session_id: str
    visitor_id: str
    user_agent: Optional[str] = ""
    screen_res: Optional[str] = ""
    timezone: Optional[str] = ""
    ip_address: Optional[str] = None

# ─── City lookup by coordinates (simplified India pinpoints) ─────────────────

INDIA_CITIES = [
    {"city": "Mumbai", "lat": 19.07, "lng": 72.87},
    {"city": "Delhi", "lat": 28.61, "lng": 77.20},
    {"city": "Bengaluru", "lat": 12.97, "lng": 77.59},
    {"city": "Hyderabad", "lat": 17.38, "lng": 78.47},
    {"city": "Chennai", "lat": 13.08, "lng": 80.27},
    {"city": "Pune", "lat": 18.52, "lng": 73.85},
    {"city": "Kolkata", "lat": 22.57, "lng": 88.36},
    {"city": "Ahmedabad", "lat": 23.02, "lng": 72.57},
    {"city": "Jaipur", "lat": 26.91, "lng": 75.79},
    {"city": "Surat", "lat": 21.17, "lng": 72.83},
]

def _haversine_km(lat1, lng1, lat2, lng2):
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def reverse_geocode(lat: float, lng: float) -> str:
    """Return nearest city from lat/lng."""
    if lat is None or lng is None:
        return "Unknown"
    best, best_dist = "Unknown", 9999
    for c in INDIA_CITIES:
        d = _haversine_km(lat, lng, c["lat"], c["lng"])
        if d < best_dist:
            best_dist = d
            best = c["city"]
    return best

def get_ip_city(ip: str) -> str:
    """Mock IP geolocation — in prod use ip-api.com."""
    try:
        import requests
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        if r.status_code == 200:
            data = r.json()
            return data.get("city", "Unknown")
    except Exception:
        pass
    # Deterministic mock based on IP
    MOCK_IPS = {"127.0.0.1": "Mumbai", "::1": "Mumbai"}
    return MOCK_IPS.get(ip, "Mumbai")

def check_geo_fraud(payload: GeoPayload) -> dict:
    """
    Feature #8 — Cross-check GPS, IP, and declared city.
    Score penalty: +0.25 if all 3 mismatch.
    """
    geo_city = reverse_geocode(payload.lat, payload.lng) if payload.lat else "Unknown"
    ip_city = get_ip_city(payload.ip_address) if payload.ip_address else "Unknown"
    declared = payload.declared_city or "Unknown"

    mismatch_count = sum([
        geo_city != "Unknown" and geo_city.lower() != declared.lower(),
        ip_city != "Unknown" and ip_city.lower() != declared.lower(),
    ])
    fraud_delta = round(mismatch_count * 0.125, 3)

    return {
        "geo_city": geo_city,
        "ip_city": ip_city,
        "declared_city": declared,
        "mismatch_count": mismatch_count,
        "location_fraud_score": fraud_delta,
        "location_status": "CLEAR" if mismatch_count == 0 else ("SUSPICIOUS" if mismatch_count == 1 else "MISMATCH"),
    }

# ─── Device Fingerprint ──────────────────────────────────────────────────────

_device_registry: dict = {}  # In-memory; use Redis in prod

def check_device_fingerprint(payload: DevicePayload) -> dict:
    """
    Feature #9 — Cross-reference device fingerprint across sessions.
    Flag repeated visitor_id appearing in > 2 sessions.
    """
    vid = payload.visitor_id
    if vid not in _device_registry:
        _device_registry[vid] = []
    _device_registry[vid].append({
        "session_id": payload.session_id,
        "timestamp": time.time(),
    })
    count = len(_device_registry[vid])
    reuse_flag = count > 2
    fraud_delta = 0.15 if reuse_flag else 0.0

    return {
        "visitor_id": vid[:16] + "...",
        "sessions_from_device": count,
        "device_reuse_flag": reuse_flag,
        "device_fraud_score": fraud_delta,
        "device_status": "REPEATED_DEVICE" if reuse_flag else "FIRST_USE",
        "screen_res": payload.screen_res,
        "user_agent": (payload.user_agent or "")[:80],
    }
