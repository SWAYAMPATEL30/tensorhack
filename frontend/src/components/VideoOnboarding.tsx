"use client";

import React, { useEffect, useRef, useState } from "react";

export default function VideoOnboarding() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamActive, setStreamActive] = useState(false);
  const [transcript, setTranscript] = useState<string>("");
  const [extractedData, setExtractedData] = useState<{income?: number; profession?: string}>({});
  const [offer, setOffer] = useState<any>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    // Initialize session
    const initSession = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/v1/session/initialize", { method: "POST" });
        const data = await response.json();
        setSessionId(data.session_id);
      } catch (err) {
        console.error(err);
      }
    };
    initSession();
  }, []);

  const startVideoKyc = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
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

  useEffect(() => {
    if (!sessionId || !streamActive) return;

    // Telemetry polling
    const geoInterval = setInterval(async () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
          await fetch("http://localhost:8000/api/v1/telemetry/ingest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sessionId,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude
            })
          });
        });
      }
    }, 10000);

    // Frame Capture for CV
    const frameInterval = setInterval(async () => {
      if (videoRef.current && canvasRef.current) {
        const context = canvasRef.current.getContext("2d");
        if (context) {
          canvasRef.current.width = videoRef.current.videoWidth;
          canvasRef.current.height = videoRef.current.videoHeight;
          context.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);
          const base64 = canvasRef.current.toDataURL("image/webp");
          
          await fetch("http://localhost:8000/api/v1/ai/process-video-frame", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, frame_base64: base64 })
          });
        }
      }
    }, 5000);

    return () => {
      clearInterval(geoInterval);
      clearInterval(frameInterval);
    };
  }, [sessionId, streamActive]);

  // Simulate audio chunk ending and getting extracted AI insights
  const simulateAudioProcessing = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch("http://localhost:8000/api/v1/ai/process-audio-chunk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, audio_base64: "fake_audio_blob" })
      });
      const data = await res.json();
      setTranscript(data.transcript_text);
      setExtractedData({ income: data.extracted_income, profession: data.extracted_profession });
    } catch(e) {
       console.error(e);
    }
  };

  // Evaluate risk & calculate offer
  const requestOffer = async () => {
    if (!sessionId) return;
    try {
      await fetch("http://localhost:8000/api/v1/ai/evaluate-risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });
      
      const res = await fetch("http://localhost:8000/api/v1/offer/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });
      const offerData = await res.json();
      setOffer(offerData);
    } catch(e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-8 w-full max-w-6xl mx-auto p-4">
      {/* Left side: Video */}
      <div className="flex-1 bg-gray-900 rounded-xl overflow-hidden relative shadow-2xl flex items-center justify-center min-h-[400px]">
        {error && <div className="absolute z-10 text-red-500 bg-black/80 px-4 py-2 rounded">{error}</div>}
        {!streamActive && !error && (
          <button 
            onClick={startVideoKyc}
            className="absolute z-10 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg transition-transform transform hover:scale-105"
          >
            Start Video KYC
          </button>
        )}
        <video 
          ref={videoRef} 
          className={`w-full h-full object-cover ${streamActive ? 'opacity-100' : 'opacity-0'}`} 
          muted 
          playsInline
        />
        <canvas ref={canvasRef} className="hidden" />
        
        {/* Mock Transcription Overlay */}
        {streamActive && (
          <div className="absolute bottom-4 left-4 right-4 bg-black/60 text-white p-3 rounded-lg backdrop-blur-sm text-sm">
            <span className="font-semibold text-indigo-300">Live Transcript:</span>{" "}
            {transcript || "Listening..."}
          </div>
        )}
      </div>

      {/* Right side: Application & Offer */}
      <div className="flex-1 space-y-6">
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Application Details</h2>
          <div className="space-y-4 text-gray-600">
            <div>
              <label className="block text-sm font-medium text-gray-500">Extracted Profession</label>
              <div className="mt-1 p-3 bg-gray-50 rounded-lg border border-gray-200">
                {extractedData.profession || <span className="italic text-gray-400">Awaiting audio extraction...</span>}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Extracted Annual Income (INR)</label>
              <div className="mt-1 p-3 bg-gray-50 rounded-lg border border-gray-200">
                {extractedData.income ? `₹${extractedData.income.toLocaleString()}` : <span className="italic text-gray-400">Awaiting audio extraction...</span>}
              </div>
            </div>
          </div>
          
          {streamActive && !offer && (
            <div className="mt-6 flex space-x-4">
              <button onClick={simulateAudioProcessing} className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 rounded-lg transition-colors">
                [Dev] Extract Data
              </button>
              <button onClick={requestOffer} className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 rounded-lg transition-colors">
                Generate Offer
              </button>
            </div>
          )}
        </div>

        {offer && (
          <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-xl shadow-2xl p-6 text-white animate-fade-in-up">
            <h2 className="text-2xl font-bold mb-2">Personalized Loan Offer</h2>
            {offer.status === "APPROVED" ? (
              <div className="space-y-4 mt-6">
                <div className="flex justify-between items-center border-b border-indigo-400/30 pb-2">
                  <span className="text-indigo-100">Approved Limit</span>
                  <span className="text-3xl font-bold">₹{offer.maximum_amount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center border-b border-indigo-400/30 pb-2">
                  <span className="text-indigo-100">Tenure</span>
                  <span className="text-xl">{offer.tenure_months} Months</span>
                </div>
                <div className="flex justify-between items-center border-b border-indigo-400/30 pb-2">
                  <span className="text-indigo-100">Interest Rate (APR)</span>
                  <span className="text-xl">{offer.interest_rate}% p.a.</span>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <span className="text-indigo-100 font-semibold text-lg">Monthly EMI</span>
                  <span className="text-2xl font-bold text-emerald-300">₹{Math.round(offer.calculated_emi).toLocaleString()}</span>
                </div>
                <button className="w-full mt-4 bg-white text-indigo-700 hover:bg-gray-50 font-bold py-3 rounded-xl transition-transform hover:scale-[1.02]">
                  Accept Offer
                </button>
              </div>
            ) : (
              <div className="mt-4 bg-red-500/20 text-red-100 p-4 rounded-lg border border-red-500/30">
                <p className="font-semibold text-lg">Application Rejected</p>
                <p>{offer.reason}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
