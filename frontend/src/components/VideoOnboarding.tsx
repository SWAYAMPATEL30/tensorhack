"use client";

import React, { useEffect, useRef, useState } from "react";

// Use NEXT_PUBLIC_API_BASE env var; fall back to localhost:8000 for local dev
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

// ─── Inner component (needs no Suspense) ───────────────────────────────────────
export default function VideoOnboarding() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamActive, setStreamActive] = useState(false);
  const [transcript, setTranscript] = useState<string>("");
  const [extractedData, setExtractedData] = useState<{
    income?: number;
    profession?: string;
  }>({});
  const [offer, setOffer] = useState<any>(null);
  const [error, setError] = useState<string>("");
  const [backendOffline, setBackendOffline] = useState(false);

  // ── Initialize session ──────────────────────────────────────────────────────
  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/session/initialize`, {
          method: "POST",
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        setSessionId(data.session_id);
        setBackendOffline(false);
      } catch (err) {
        console.error("Backend not reachable:", err);
        setBackendOffline(true);
        // Generate a local fallback session so the UI stays usable
        setSessionId(`local-${crypto.randomUUID()}`);
      }
    };
    initSession();
  }, []);

  // ── Start webcam ────────────────────────────────────────────────────────────
  const startVideoKyc = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: true,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setStreamActive(true);
      }
    } catch (err) {
      setError("Please allow camera and microphone permissions to proceed.");
      console.error(err);
    }
  };

  // ── Telemetry + frame capture loops ────────────────────────────────────────
  useEffect(() => {
    if (!sessionId || !streamActive || backendOffline) return;

    const geoInterval = setInterval(() => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
          try {
            await fetch(`${API_BASE}/api/v1/telemetry/ingest`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: sessionId,
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
              }),
            });
          } catch (_) {}
        });
      }
    }, 10000);

    const frameInterval = setInterval(async () => {
      if (videoRef.current && canvasRef.current) {
        const context = canvasRef.current.getContext("2d");
        if (context) {
          canvasRef.current.width = videoRef.current.videoWidth;
          canvasRef.current.height = videoRef.current.videoHeight;
          context.drawImage(
            videoRef.current,
            0,
            0,
            canvasRef.current.width,
            canvasRef.current.height
          );
          const base64 = canvasRef.current.toDataURL("image/webp");
          try {
            await fetch(`${API_BASE}/api/v1/ai/process-video-frame`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ session_id: sessionId, frame_base64: base64 }),
            });
          } catch (_) {}
        }
      }
    }, 5000);

    return () => {
      clearInterval(geoInterval);
      clearInterval(frameInterval);
    };
  }, [sessionId, streamActive, backendOffline]);

  // ── Simulate audio processing ───────────────────────────────────────────────
  const simulateAudioProcessing = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/ai/process-audio-chunk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, audio_base64: "fake_audio_blob" }),
      });
      const data = await res.json();
      setTranscript(data.transcript_text);
      setExtractedData({
        income: data.extracted_income,
        profession: data.extracted_profession,
      });
    } catch (e) {
      console.error(e);
    }
  };

  // ── Evaluate risk & calculate offer ────────────────────────────────────────
  const requestOffer = async () => {
    if (!sessionId) return;
    try {
      await fetch(`${API_BASE}/api/v1/ai/evaluate-risk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });

      const res = await fetch(`${API_BASE}/api/v1/offer/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
      const offerData = await res.json();
      setOffer(offerData);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 w-full max-w-6xl mx-auto p-4 items-start">
      {/* ── Backend offline warning ─────────────────────────────────────────── */}
      {backendOffline && (
        <div
          className="w-full bg-amber-50 border border-amber-300 text-amber-800 px-4 py-3 rounded-lg text-sm flex items-center gap-2"
          style={{ gridColumn: "1 / -1" }}
        >
          <span>⚠️</span>
          <span>
            Backend at <code className="font-mono">{API_BASE}</code> is not reachable. Running in
            demo mode — API calls will be skipped.
          </span>
        </div>
      )}

      {/* ── LEFT: Webcam panel ─────────────────────────────────────────────── */}
      {/*
          Key fixes:
          - Fixed width (flex-none w-[380px]) so it never grows beyond its share
          - aspect-video (16:9) on the video container so height is always proportional
          - max-h is derived from aspect ratio automatically
          - object-cover keeps the face centered
      */}
      <div className="flex-none w-full md:w-[420px] flex flex-col gap-3">
        <div
          className="relative w-full bg-gray-900 rounded-xl overflow-hidden shadow-2xl"
          style={{ aspectRatio: "4/3" }} /* 4:3 is natural for a webcam portrait */
        >
          {/* Camera-permission error */}
          {error && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/80 px-6 text-center">
              <p className="text-red-400 text-sm font-medium">{error}</p>
            </div>
          )}

          {/* "Start KYC" CTA */}
          {!streamActive && !error && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-gray-900/90">
              <div className="w-16 h-16 rounded-full bg-indigo-600/20 flex items-center justify-center">
                {/* Camera icon */}
                <svg
                  className="w-8 h-8 text-indigo-400"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6.827 6.175A2.31 2.31 0 0 1 5.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 0 0-1.134-.175 2.31 2.31 0 0 1-1.64-1.055l-.822-1.316a2.192 2.192 0 0 0-1.736-1.039 48.774 48.774 0 0 0-5.232 0 2.192 2.192 0 0 0-1.736 1.039l-.821 1.316Z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M16.5 12.75a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0ZM18.75 10.5h.008v.008h-.008V10.5Z"
                  />
                </svg>
              </div>
              <button
                onClick={startVideoKyc}
                className="bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white font-semibold py-2.5 px-7 rounded-lg transition-all text-sm shadow-lg"
              >
                Start Video KYC
              </button>
              <p className="text-gray-500 text-xs">Camera &amp; microphone required</p>
            </div>
          )}

          {/* Webcam feed */}
          <video
            ref={videoRef}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${
              streamActive ? "opacity-100" : "opacity-0"
            }`}
            muted
            playsInline
          />

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} className="hidden" />

          {/* Live transcript overlay */}
          {streamActive && (
            <div className="absolute bottom-3 left-3 right-3 bg-black/60 text-white px-3 py-2 rounded-lg backdrop-blur-sm text-xs leading-relaxed">
              <span className="font-semibold text-indigo-300">Live: </span>
              {transcript || "Listening…"}
            </div>
          )}

          {/* Recording indicator */}
          {streamActive && (
            <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-black/50 px-2 py-1 rounded-full backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-white text-[10px] font-medium uppercase tracking-wider">
                Live
              </span>
            </div>
          )}
        </div>

        {/* Session ID badge */}
        {sessionId && (
          <div className="text-[10px] text-gray-400 font-mono truncate text-center">
            Session: {sessionId}
          </div>
        )}
      </div>

      {/* ── RIGHT: Application details + offer ────────────────────────────── */}
      <div className="flex-1 min-w-0 space-y-5">
        {/* Application details card */}
        <div className="bg-white rounded-xl shadow-md border border-gray-100 p-5">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Application Details</h2>

          <div className="space-y-3 text-gray-600">
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Extracted Profession
              </label>
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
                {extractedData.profession ?? (
                  <span className="italic text-gray-400">Awaiting audio extraction…</span>
                )}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Extracted Annual Income (INR)
              </label>
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
                {extractedData.income != null ? (
                  `₹${extractedData.income.toLocaleString("en-IN")}`
                ) : (
                  <span className="italic text-gray-400">Awaiting audio extraction…</span>
                )}
              </div>
            </div>
          </div>

          {streamActive && !offer && (
            <div className="mt-5 flex gap-3">
              <button
                onClick={simulateAudioProcessing}
                className="flex-1 bg-gray-100 hover:bg-gray-200 active:scale-95 text-gray-700 font-medium py-2 rounded-lg transition-all text-sm"
              >
                [Dev] Extract Data
              </button>
              <button
                onClick={requestOffer}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-semibold py-2 rounded-lg transition-all text-sm shadow"
              >
                Generate Offer
              </button>
            </div>
          )}
        </div>

        {/* Loan offer card */}
        {offer && (
          <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-xl shadow-2xl p-5 text-white">
            <h2 className="text-xl font-bold mb-1">Personalized Loan Offer</h2>
            <p className="text-indigo-200 text-xs mb-4">Based on your voice interview &amp; risk assessment</p>

            {offer.status === "APPROVED" ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center border-b border-indigo-400/30 pb-2">
                  <span className="text-indigo-100 text-sm">Approved Limit</span>
                  <span className="text-2xl font-bold">
                    ₹{offer.maximum_amount?.toLocaleString("en-IN")}
                  </span>
                </div>
                <div className="flex justify-between items-center border-b border-indigo-400/30 pb-2">
                  <span className="text-indigo-100 text-sm">Tenure</span>
                  <span className="font-semibold">{offer.tenure_months} Months</span>
                </div>
                <div className="flex justify-between items-center border-b border-indigo-400/30 pb-2">
                  <span className="text-indigo-100 text-sm">Interest Rate (APR)</span>
                  <span className="font-semibold">{offer.interest_rate}% p.a.</span>
                </div>
                <div className="flex justify-between items-center pt-1">
                  <span className="text-indigo-100 font-semibold">Monthly EMI</span>
                  <span className="text-xl font-bold text-emerald-300">
                    ₹{Math.round(offer.calculated_emi).toLocaleString("en-IN")}
                  </span>
                </div>
                <button className="w-full mt-3 bg-white text-indigo-700 hover:bg-gray-50 active:scale-[0.99] font-bold py-3 rounded-xl transition-all shadow">
                  Accept Offer
                </button>
              </div>
            ) : (
              <div className="mt-3 bg-red-500/20 text-red-100 p-4 rounded-lg border border-red-500/30">
                <p className="font-semibold">Application Rejected</p>
                <p className="text-sm mt-1">{offer.reason}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
