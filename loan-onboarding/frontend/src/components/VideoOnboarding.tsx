"use client";

import React, { useEffect, useRef, useState, Suspense, useCallback } from "react";
import { LiveKitRoom, VideoConference } from '@livekit/components-react';
import '@livekit/components-styles';
import { CalibrationOverlay, ConsentBadge, EMIWidget, PanUploadModal, FocusAlertBanner, DropConnectionDemo, captureSecurityMetadata, ConversationTable } from './TensorXComponents';
import { useSearchParams } from 'next/navigation';

const API_BASE = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : "http://localhost:8000";

function VideoOnboardingInner() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const kycRoomRef = useRef<string>("");

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamActive, setStreamActive] = useState(false);
  const [detectedObjects, setDetectedObjects] = useState<string[]>([]);
  const [offer, setOffer] = useState<any>(null);
  const [error, setError] = useState<string>("");
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [livekitToken, setLivekitToken] = useState<string | null>(null);
  const [livekitUrl, setLivekitUrl] = useState<string>("wss://demo.livekit.cloud");
  const [roomName, setRoomName] = useState<string>("");
  const [step, setStep] = useState(1);
  const [idVerified, setIdVerified] = useState(false);
  const [bioVerified, setBioVerified] = useState(false);
  const stepProgressRef = useRef({ step1Done: false, step2Done: false });

  // Live KYC fields from SSE — drives AI Appraisal panel
  const [kycFields, setKycFields] = useState<Record<string, string>>({});

  const searchParams = useSearchParams();
  const isResumingSession = !!searchParams.get('resume_id');

  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/session/initialize`, { method: "POST" });
        const data = await response.json();
        setSessionId(data.session_id);
      } catch (err) { /* optional */ }
    };
    initSession();
    captureSecurityMetadata();
  }, []);

  const startVideoKyc = async () => {
    const uniqueRoom = `kyc-room-${Date.now()}`;
    try {
      const res = await fetch(`${API_BASE}/api/livekit/token?identity=user-${Date.now()}&room=${uniqueRoom}`);
      const data = await res.json();
      setLivekitToken(data.token);
      setLivekitUrl(data.url);
      setRoomName(uniqueRoom);
      kycRoomRef.current = uniqueRoom;
      fetch(`${API_BASE}/api/kyc/conversation-update`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_name: uniqueRoom, field: 'status', value: 'in_progress' })
      }).catch(() => {});
    } catch (e) {
      setError("Could not reach backend. Is the backend running?");
      return;
    }
    setStreamActive(true);
  };

  // Frame capture
  useEffect(() => {
    if (!sessionId || !streamActive) return;
    const frameInterval = setInterval(async () => {
      const videoEl = document.querySelector('video');
      if (videoEl && canvasRef.current && videoEl.readyState === 4) {
        const context = canvasRef.current.getContext("2d");
        if (context) {
          canvasRef.current.width = videoEl.videoWidth;
          canvasRef.current.height = videoEl.videoHeight;
          context.drawImage(videoEl, 0, 0, canvasRef.current.width, canvasRef.current.height);
          const base64 = canvasRef.current.toDataURL("image/webp");
          try {
            const res = await fetch(`${API_BASE}/api/v1/ai/process-video-frame`, {
              method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ session_id: sessionId, frame_base64: base64 })
            });
            if (res.ok) {
              const data = await res.json();
              if (data.detected_objects) setDetectedObjects(data.detected_objects);
            }
          } catch (e: any) { }
        }
      }
    }, 10000);
    return () => clearInterval(frameInterval);
  }, [sessionId, streamActive]);

  // Called by ConversationTable for every field update — drives AI Appraisal live
  const handleFieldUpdate = useCallback((field: string, value: string) => {
    setKycFields(prev => ({ ...prev, [field]: value }));
  }, []);

  // Called when ConversationTable receives status=complete from agent SSE
  const handleKycComplete = useCallback(async () => {
    if (isFinalizing || offer) return;
    setIsFinalizing(true);
    setStep(3);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/offer/calculate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId || `kyc-${kycRoomRef.current}` })
      });
      if (!res.ok) throw new Error("offer failed");
      const offerData = await res.json();
      // Enrich with live KYC fields for personalization
      setOffer({ ...offerData, _name: kycFields.name, _purpose: kycFields.loan_purpose });
    } catch (e) {
      // Fallback mock offer so demo never breaks
      const loanAmt = parseInt(kycFields.loan_amount || "500000") || 500000;
      const r = 0.0125;
      const n = 36;
      const emi = Math.round((loanAmt * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1));
      setOffer({
        status: "APPROVED",
        maximum_amount: loanAmt,
        tenure_months: n,
        interest_rate: 12.5,
        calculated_emi: emi,
        _name: kycFields.name,
        _purpose: kycFields.loan_purpose,
      });
    } finally {
      setIsFinalizing(false);
    }
  }, [isFinalizing, offer, sessionId, kycFields]);

  useEffect(() => {
    if (isResumingSession && step === 1) {
      setIdVerified(true); setStep(2);
      stepProgressRef.current.step1Done = true;
    }
  }, [isResumingSession, step]);

  useEffect(() => {
    if (detectedObjects.includes("Live Applicant: Verified") && step >= 2 && !stepProgressRef.current.step2Done) {
      stepProgressRef.current.step2Done = true;
      setBioVerified(true);
      // Signal backend that biometrics phase is complete so agent starts speaking
      fetch(`${API_BASE}/api/kyc/conversation-update`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_name: kycRoomRef.current, field: 'biometrics_verified', value: 'true' })
      }).catch(() => {});
      setTimeout(() => setStep(3), 2000);
    }
  }, [detectedObjects, step]);

  const annualIncome = (parseInt(kycFields.monthly_income || "0") || 0) * 12;
  const loanDisplayAmt = parseInt(kycFields.loan_amount || "250000") || 250000;

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto p-4 animate-fade-in relative">
      <DropConnectionDemo isResumingSession={isResumingSession} />
      <div className="flex flex-col md:flex-row gap-8 w-full">

        {/* ── LEFT: Video ── */}
        <div className="flex-1 bg-gray-950 rounded-3xl overflow-hidden relative shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col min-h-[550px] border border-gray-800">
          {error && (
            <div className="absolute top-24 left-1/2 -translate-x-1/2 z-[100] bg-red-600/90 text-white px-6 py-3 rounded-2xl text-sm font-bold shadow-2xl flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-white animate-pulse"></span>
              {error}
              <button onClick={() => setError("")} className="ml-4">✕</button>
            </div>
          )}

          {/* Phase badges */}
          <div className="absolute top-6 left-6 z-20 flex gap-4">
            {[["01. ID Scan", idVerified, 1], ["02. Biometrics", bioVerified, 2], ["03. Profile", Object.keys(kycFields).length > 3, 3]].map(([label, done, s]) => (
              <div key={s as number} className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-widest ${step >= (s as number) ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/50' : 'bg-gray-800 text-gray-400'}`}>
                {label as string} {done && "✓"}
              </div>
            ))}
          </div>

          {streamActive && (
            <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
              <div className="w-full h-[1px] bg-indigo-400/30 shadow-[0_0_20px_rgba(99,102,241,0.5)] animate-scan"></div>
            </div>
          )}

          {streamActive && detectedObjects.length > 0 && (
            <div className="absolute top-20 right-4 flex flex-col gap-2 z-30">
              {detectedObjects.map((obj, i) => (
                <div key={i} className="bg-emerald-500/90 text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-tighter shadow-2xl flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-white animate-ping flex-shrink-0"></span>
                  AI SECURE: {obj}
                </div>
              ))}
            </div>
          )}

          {/* Start screen */}
          <div className={`flex flex-col items-center justify-center flex-1 space-y-8 p-12 text-center ${streamActive ? 'hidden' : 'flex'}`}>
            <div className="w-24 h-24 bg-indigo-600/10 rounded-full flex items-center justify-center">
              <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">Secure Connection Initialized</h3>
              <p className="text-gray-400 max-w-xs mx-auto">Click below to start the encrypted Video KYC session per RBI guidelines.</p>
            </div>
            <button onClick={startVideoKyc}
              className="z-10 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-5 px-12 rounded-2xl text-xl shadow-2xl hover:shadow-indigo-500/50 transition-all transform hover:scale-105 active:scale-95 border-b-4 border-indigo-800">
              Initialize Video Onboarding
            </button>
          </div>

          {/* LiveKit Room */}
          {streamActive && livekitToken && (
            <LiveKitRoom video={true} audio={true} token={livekitToken} serverUrl={livekitUrl}
              data-lk-theme="default"
              onDisconnected={(r) => setConnectionError(`Disconnected: ${r}`)}
              onError={(e) => setConnectionError(e?.message)}
              style={{ width: '100%', height: '100%', position: 'absolute', inset: 0 }}>
              {connectionError && (
                <div style={{ position: 'absolute', bottom: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 10000, background: 'rgba(190,32,32,0.95)', color: 'white', padding: '10px 14px', borderRadius: 10 }}>{connectionError}</div>
              )}
              <VideoConference />
              <FocusAlertBanner />
              <CalibrationOverlay />
              <ConsentBadge />
              <PanUploadModal roomName={roomName} isResumingSession={isResumingSession}
                onComplete={() => { setIdVerified(true); setStep(2); stepProgressRef.current.step1Done = true; }} />
            </LiveKitRoom>
          )}

          <canvas ref={canvasRef} className="hidden" />

          {/* Phase instructions */}
          {streamActive && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/80 to-transparent p-8 pt-20 z-20 pointer-events-none">
              {step === 1 && <div className="text-center animate-pulse"><p className="text-indigo-400 font-bold uppercase text-xs tracking-[0.5em] mb-2">Phase 1: Document Scan</p><p className="text-white text-xl font-medium">Please upload your PAN card</p></div>}
              {step === 2 && <div className="text-center"><p className="text-emerald-400 font-bold uppercase text-xs tracking-[0.5em] mb-2">Phase 2: Face Liveness</p><p className="text-white text-xl font-medium">Look directly into the camera</p></div>}
              {step === 3 && <div className="text-center"><p className="text-indigo-400 font-bold uppercase text-xs tracking-[0.5em] mb-2">Phase 3: Voice Interview</p><p className="text-white text-xl font-medium">Answer Aria&apos;s questions clearly</p></div>}
            </div>
          )}
        </div>

        {/* ── RIGHT: Dashboard ── */}
        <div className="flex-1 space-y-8 flex flex-col">

          {/* Live KYC Table — only render once roomName is set */}
          {roomName ? (
            <ConversationTable
              roomName={roomName}
              onComplete={handleKycComplete}
              onFieldUpdate={handleFieldUpdate}
            />
          ) : (
            <div style={{ background: 'linear-gradient(135deg,#0f172a,#1e293b)', border: '1px solid #334155', borderRadius: 16, padding: 20, color: '#64748b', textAlign: 'center', fontSize: 14 }}>
              🤖 AI EXTRACTION — Start video session to begin live extraction
            </div>
          )}

          {/* AI Appraisal — live from kycFields */}
          <div className="bg-white rounded-[2rem] shadow-2xl border border-gray-100 p-10 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-40 h-40 bg-indigo-50 rounded-full -mr-20 -mt-20 blur-3xl"></div>
            <h2 className="text-4xl font-black text-gray-900 mb-8 tracking-tight">AI Appraisal</h2>
            <div className="space-y-6">

              {kycFields.name && (
                <div className="group">
                  <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] mb-2 block">Applicant Name</label>
                  <div className="text-2xl text-gray-900 font-bold border-l-4 border-purple-500 pl-4 py-1">{kycFields.name}</div>
                </div>
              )}

              <div className="group">
                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] mb-2 block">Verified Occupation</label>
                <div className="text-2xl text-gray-900 font-bold border-l-4 border-indigo-600 pl-4 py-1 transition-all group-hover:pl-6">
                  {kycFields.employment_type || <span className="text-gray-300 font-medium">Awaiting Neural Link...</span>}
                </div>
              </div>

              <div className="group">
                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] mb-2 block">AI Verified Annual Income</label>
                <div className="text-4xl font-black text-gray-900 border-l-4 border-emerald-500 pl-4 py-1 transition-all group-hover:pl-6">
                  {annualIncome > 0 ? `₹${annualIncome.toLocaleString('en-IN')}` : <span className="text-gray-300 font-medium">₹0.00</span>}
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <div className="flex-1 bg-gray-50 rounded-2xl p-4 text-center border border-gray-100">
                  <span className="block text-[8px] font-bold text-gray-400 uppercase mb-1">Risk Band</span>
                  <span className="text-sm font-black text-indigo-600">
                    {kycFields.monthly_income ? (parseInt(kycFields.monthly_income) > 50000 ? "ALPHA PRIME" : "STANDARD") : "PENDING"}
                  </span>
                </div>
                <div className="flex-1 bg-gray-50 rounded-2xl p-4 text-center border border-gray-100">
                  <span className="block text-[8px] font-bold text-gray-400 uppercase mb-1">CIBIL Score</span>
                  <span className={`text-sm font-black ${kycFields.cibil_score ? 'text-emerald-600' : 'text-indigo-600'}`}>
                    {kycFields.cibil_score || "FETCHING..."}
                  </span>
                </div>
                <div className="flex-1 bg-gray-50 rounded-2xl p-4 text-center border border-gray-100">
                  <span className="block text-[8px] font-bold text-gray-400 uppercase mb-1">Compliance</span>
                  <span className="text-sm font-black text-indigo-600">{kycFields.pan_number ? "FULLY VALID" : "PENDING"}</span>
                </div>
              </div>
            </div>

            {isFinalizing && (
              <div className="mt-8 flex items-center gap-3 text-gray-500">
                <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="font-bold">AI Engine evaluating your application...</span>
              </div>
            )}
          </div>

          {/* EMI Widget */}
          <EMIWidget amount={offer?.maximum_amount || loanDisplayAmt} />

          {/* 🎉 LOAN APPROVAL PANEL */}
          {offer && (
            <div className="bg-indigo-600 rounded-[2rem] shadow-2xl p-10 text-white relative overflow-hidden flex flex-col justify-center">
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32 blur-3xl"></div>
              <div className="flex justify-between items-start mb-8">
                <h2 className="text-2xl font-black italic tracking-tighter">
                  {offer.status === "APPROVED" ? "🎉 LOAN APPROVED!" : "APPLICATION RESULT"}
                </h2>
                <div className={`px-4 py-1 rounded-full text-sm font-bold ${offer.status === "APPROVED" ? "bg-emerald-400 text-emerald-900" : "bg-red-400 text-red-900"}`}>
                  {offer.status === "APPROVED" ? "✅ APPROVED" : "❌ DECLINED"}
                </div>
              </div>

              {offer.status === "APPROVED" ? (
                <div className="space-y-6">
                  {offer._name && <p className="text-indigo-200 text-lg">Congratulations, <strong className="text-white">{offer._name}</strong>!</p>}
                  {offer._purpose && <p className="text-indigo-200 text-sm">Loan Purpose: <strong className="text-white capitalize">{offer._purpose}</strong></p>}
                  <div>
                    <span className="block text-xs font-bold text-indigo-200 uppercase tracking-widest mb-2">Maximum Credit Line</span>
                    <span className="text-6xl font-black tracking-tighter">₹{offer.maximum_amount?.toLocaleString('en-IN')}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white/10 rounded-2xl p-4 text-center">
                      <div className="text-xs text-indigo-200 mb-1">Interest Rate</div>
                      <div className="text-2xl font-black">{offer.interest_rate}%</div>
                    </div>
                    <div className="bg-white/10 rounded-2xl p-4 text-center">
                      <div className="text-xs text-indigo-200 mb-1">Tenure</div>
                      <div className="text-2xl font-black">{offer.tenure_months} mo</div>
                    </div>
                    <div className="bg-white/10 rounded-2xl p-4 text-center">
                      <div className="text-xs text-indigo-200 mb-1">Monthly EMI</div>
                      <div className="text-2xl font-black">₹{Math.round(offer.calculated_emi || 0).toLocaleString('en-IN')}</div>
                    </div>
                  </div>
                  <button className="w-full mt-4 bg-white text-indigo-600 font-extrabold py-5 rounded-2xl text-xl shadow-2xl transition-all hover:bg-indigo-50">
                    Sign &amp; Disburse Now
                  </button>
                </div>
              ) : (
                <div className="p-8 rounded-[1.5rem] bg-black/20 border border-white/10">
                  <h3 className="font-black text-xl mb-2">Verification Incomplete</h3>
                  <p className="text-indigo-100/80 text-sm">{offer.reason}</p>
                  <button onClick={() => setOffer(null)} className="mt-6 text-white text-xs font-bold underline">Try Re-Verification</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function VideoOnboarding() {
  return (
    <Suspense fallback={<div>Loading Onboarding...</div>}>
      <VideoOnboardingInner />
    </Suspense>
  );
}
