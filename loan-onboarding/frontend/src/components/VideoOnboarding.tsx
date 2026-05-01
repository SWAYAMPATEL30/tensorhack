"use client";

import React, { useEffect, useRef, useState } from "react";

const API_BASE = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : "http://localhost:8000";

export default function VideoOnboarding() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamActive, setStreamActive] = useState(false);
  const [transcript, setTranscript] = useState<string>("");
  const [extractedData, setExtractedData] = useState<{income?: number; profession?: string}>({});
  const [detectedObjects, setDetectedObjects] = useState<string[]>([]);
  const [offer, setOffer] = useState<any>(null);
  const [error, setError] = useState<string>("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    // Initialize session
    const initSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/session/initialize`, { method: "POST" });
        const data = await response.json();
        setSessionId(data.session_id);
      } catch (err) {
        console.error(err);
        setError("Banking Server Offline. Please start the backend service.");
      }
    };
    initSession();
  }, []);


  const sessionIdRef = useRef<string | null>(null);
  useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);

  const startVideoKyc = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setStreamActive(true);

        const mimeTypes = ['audio/webm', 'audio/ogg', 'audio/mp4', 'audio/wav'];
        const supportedMimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type));
        
        const recorder = supportedMimeType 
          ? new MediaRecorder(stream, { mimeType: supportedMimeType })
          : new MediaRecorder(stream);
        
        mediaRecorderRef.current = recorder;
        
        recorder.ondataavailable = async (e) => {
          if (e.data.size > 0 && sessionIdRef.current) {
            console.log("Processing audio chunk, size:", e.data.size);
            const reader = new FileReader();
            reader.readAsDataURL(e.data);
            reader.onloadend = async () => {
              const base64Audio = reader.result as string;
              try {
                const res = await fetch(`${API_BASE}/api/v1/ai/process-audio-chunk`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ session_id: sessionIdRef.current, audio_base64: base64Audio })
                });
                
                if (res.ok) {
                  const data = await res.json();
                  if (data.transcript_text) {
                    setTranscript(prev => (prev + " " + data.transcript_text).trim());
                    if (data.extracted_income || data.extracted_profession) {
                      setExtractedData(prev => ({ 
                        income: data.extracted_income || prev.income, 
                        profession: data.extracted_profession || prev.profession 
                      }));
                    }
                  }
                }
              } catch (err) {
                console.error("Transcription chunk failed:", err);
              }
            };
          }
        };
      }
    } catch (err) {
      setError("Please allow camera and MIC permissions.");
      console.error(err);
    }
  };

  useEffect(() => {
    let interval: any;
    if (isRecording && mediaRecorderRef.current) {
      interval = setInterval(() => {
        if (mediaRecorderRef.current?.state === "recording") {
          mediaRecorderRef.current.requestData();
        }
      }, 2000); // 2 seconds for live feedback
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const toggleAudioRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return;

    if (isRecording) {
      if (recorder.state !== "inactive") {
        try { recorder.stop(); } catch (e) {}
      }
      setIsRecording(false);
    } else {
      if (recorder.state === "inactive") {
        try {
          recorder.start(2000); 
          setIsRecording(true);
        } catch (err) {
          console.warn("Timeslice start failed:", err);
          if (recorder.state === "inactive") {
            try { recorder.start(); setIsRecording(true); } catch (e2) {}
          } else {
            setIsRecording(true);
          }
        }
      }
    }
  };

  useEffect(() => {
    if (!sessionId || !streamActive) return;

    // Frame Capture for CV
    const frameInterval = setInterval(async () => {
      if (videoRef.current && canvasRef.current) {
        const context = canvasRef.current.getContext("2d");
        if (context) {
          canvasRef.current.width = videoRef.current.videoWidth;
          canvasRef.current.height = videoRef.current.videoHeight;
          context.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);
          const base64 = canvasRef.current.toDataURL("image/webp");
          
          try {
            const res = await fetch(`${API_BASE}/api/v1/ai/process-video-frame`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ session_id: sessionId, frame_base64: base64 })
            });
            if (res.ok) {
              const data = await res.json();
              if (data.detected_objects) {
                setDetectedObjects(data.detected_objects);
              }
            }
          } catch (e) {
            console.error("Frame processing failed:", e);
          }
        }
      }
    }, 3000);

    return () => {
      clearInterval(frameInterval);
    };
  }, [sessionId, streamActive]);

  const [isFinalizing, setIsFinalizing] = useState(false);

  const requestOffer = async () => {
    if (!sessionId) return;
    setIsFinalizing(true);
    setError("");
    
    try {
      // We now call one combined endpoint for speed and reliability
      const res = await fetch(`${API_BASE}/api/v1/offer/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });
      
      if (!res.ok) throw new Error("Server rejected offer calculation");
      
      const offerData = await res.json();
      setOffer(offerData);
    } catch(e) {
      console.error(e);
      setError("AI Engine busy. Please try generating the offer again.");
    } finally {
      setIsFinalizing(false);
    }
  };

  const [step, setStep] = useState(1); // 1: ID, 2: Bio, 3: Income
  const [idVerified, setIdVerified] = useState(false);
  const [bioVerified, setBioVerified] = useState(false);
  const stepProgressRef = useRef({ step1Done: false, step2Done: false });

  // Auto-advance Step 1 (ID Scan) after 3s once stream starts
  useEffect(() => {
    if (streamActive && !stepProgressRef.current.step1Done) {
      stepProgressRef.current.step1Done = true;
      setTimeout(() => {
        setIdVerified(true);
        setStep(2);
      }, 3000);
    }
  }, [streamActive]);

  // Auto-advance Step 2 (Biometrics) on first face detection
  useEffect(() => {
    if (
      detectedObjects.includes("Live Applicant: Verified") &&
      step >= 2 &&
      !stepProgressRef.current.step2Done
    ) {
      stepProgressRef.current.step2Done = true;
      setBioVerified(true);
      setTimeout(() => setStep(3), 2000);
    }
  }, [detectedObjects, step]);

  return (
    <div className="flex flex-col md:flex-row gap-8 w-full max-w-7xl mx-auto p-4 animate-fade-in">
      {/* Left side: Video & Status */}
      <div className="flex-1 bg-gray-950 rounded-3xl overflow-hidden relative shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col min-h-[550px] border border-gray-800">
        {error && (
          <div className="absolute top-24 left-1/2 -translate-x-1/2 z-[100] bg-red-600/90 backdrop-blur-md text-white px-6 py-3 rounded-2xl text-sm font-bold shadow-2xl animate-fade-in-up flex items-center gap-3 border border-red-400/30">
            <span className="w-2 h-2 rounded-full bg-white animate-pulse"></span>
            {error}
            <button onClick={() => setError("")} className="ml-4 opacity-70 hover:opacity-100">✕</button>
          </div>
        )}

        <div className="absolute top-6 left-6 z-20 flex gap-4">
          <div className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-widest ${step >= 1 ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/50' : 'bg-gray-800 text-gray-400'}`}>
            01. ID Scan {idVerified && "✓"}
          </div>
          <div className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-widest ${step >= 2 ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/50' : 'bg-gray-800 text-gray-400'}`}>
            02. Biometrics {bioVerified && "✓"}
          </div>
          <div className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-widest ${step >= 3 ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/50' : 'bg-gray-800 text-gray-400'}`}>
            03. Profile {transcript.length > 20 && "✓"}
          </div>
        </div>

        {streamActive && (
          <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
            <div className="w-full h-[1px] bg-indigo-400/30 shadow-[0_0_20px_rgba(99,102,241,0.5)] animate-scan"></div>
          </div>
        )}

        {/* AI Detection Overlay - top right */}
        {streamActive && (
          <div className="absolute top-20 right-4 flex flex-col gap-2 z-30">
            {detectedObjects.map((obj, i) => (
              <div key={i} className="bg-emerald-500/90 backdrop-blur-md text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-tighter shadow-2xl animate-fade-in-up flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-white animate-ping flex-shrink-0"></span>
                AI SECURE: {obj}
              </div>
            ))}
          </div>
        )}

        {/* Splash screen - shown before stream starts */}
        <div className={`flex flex-col items-center justify-center flex-1 space-y-8 p-12 text-center transition-opacity duration-500 ${streamActive ? 'hidden' : 'flex'}`}>
          <div className="w-24 h-24 bg-indigo-600/10 rounded-full flex items-center justify-center">
             <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white mb-2">Secure Connection Initialized</h3>
            <p className="text-gray-400 max-w-xs mx-auto">Click below to start the encrypted Video KYC session per RBI guidelines.</p>
          </div>
          <button 
            onClick={startVideoKyc}
            className="z-10 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-5 px-12 rounded-2xl text-xl shadow-2xl hover:shadow-indigo-500/50 transition-all transform hover:scale-105 active:scale-95 border-b-4 border-indigo-800"
          >
            Initialize Video Onboarding
          </button>
        </div>

        {/* Video - always rendered but hidden until stream active */}
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className={`w-full h-full object-cover absolute inset-0 transition-opacity duration-700 ${streamActive ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
          style={{ filter: 'grayscale(15%) contrast(1.05)' }}
        />

        <canvas ref={canvasRef} className="hidden" />

        
        {/* Step-specific instructions */}
        {streamActive && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/80 to-transparent p-8 pt-20 z-20">
            {step === 1 && (
              <div className="text-center animate-pulse">
                <p className="text-indigo-400 font-bold uppercase text-xs tracking-[0.5em] mb-2">Phase 1: Document Scan</p>
                <p className="text-white text-xl font-medium">Please hold your ID card clearly in front of the camera</p>
              </div>
            )}
            {step === 2 && (
              <div className="text-center">
                <p className="text-emerald-400 font-bold uppercase text-xs tracking-[0.5em] mb-2">Phase 2: Face Liveness</p>
                <p className="text-white text-xl font-medium">Look directly into the camera and follow the scanner</p>
              </div>
            )}
            {step === 3 && (
              <div className="space-y-4">
                <p className="text-indigo-400 font-bold uppercase text-xs tracking-[0.5em] text-center">Phase 3: Legal Affirmation</p>
                <div className="bg-gray-900/50 backdrop-blur-sm p-4 rounded-2xl border border-gray-700/50 max-h-24 overflow-y-auto">
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {transcript || "\"I hereby confirm that I am applying for this credit facility and the information provided is true to my knowledge...\""}
                  </p>
                </div>
                <button 
                  onClick={toggleAudioRecording}
                  className={`w-full py-4 rounded-2xl font-black uppercase text-sm tracking-widest transition-all select-none ${isRecording ? 'bg-red-500 text-white ring-4 ring-red-500/20 shadow-[0_0_30px_rgba(239,68,68,0.4)]' : 'bg-white text-black hover:bg-gray-100'}`}
                >
                  {isRecording ? "🔴  Transcribing Live... (Click to Stop)" : "🎙  Click to Record Statement"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right side: Bank Dashboard */}
      <div className="flex-1 space-y-8">
        <div className="bg-white rounded-[2rem] shadow-2xl border border-gray-100 p-10 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-40 h-40 bg-indigo-50 rounded-full -mr-20 -mt-20 blur-3xl"></div>
          
          <h2 className="text-4xl font-black text-gray-900 mb-8 tracking-tight">AI Appraisal</h2>
          
          <div className="space-y-6">
            <div className="group">
              <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] mb-2 block">Verified Occupation</label>
              <div className="text-2xl text-gray-900 font-bold border-l-4 border-indigo-600 pl-4 py-1 transition-all group-hover:pl-6">
                {extractedData.profession || <span className="text-gray-300 font-medium">Awaiting Neural Link...</span>}
              </div>
            </div>

            <div className="group">
              <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] mb-2 block">AI Verified Annual Income</label>
              <div className="text-4xl font-black text-gray-900 border-l-4 border-emerald-500 pl-4 py-1 transition-all group-hover:pl-6">
                {extractedData.income ? `₹${extractedData.income.toLocaleString()}` : <span className="text-gray-300 font-medium">₹0.00</span>}
              </div>
            </div>

            <div className="flex gap-4 pt-4">
              <div className="flex-1 bg-gray-50 rounded-2xl p-4 text-center border border-gray-100">
                <span className="block text-[8px] font-bold text-gray-400 uppercase mb-1">Risk Band</span>
                <span className="text-sm font-black text-indigo-600">ALPHA PRIME</span>
              </div>
              <div className="flex-1 bg-gray-50 rounded-2xl p-4 text-center border border-gray-100">
                <span className="block text-[8px] font-bold text-gray-400 uppercase mb-1">Compliance</span>
                <span className="text-sm font-black text-indigo-600">FULLY VALID</span>
              </div>
            </div>
          </div>
          
          {step === 3 && !offer && (
            <div className="mt-10">
              <button 
                onClick={requestOffer} 
                disabled={isFinalizing}
                className={`w-full font-black py-5 rounded-2xl text-lg shadow-2xl transition-all transform active:translate-y-0 ${isFinalizing ? 'bg-gray-400 cursor-not-allowed' : 'bg-black text-white hover:bg-gray-800 hover:-translate-y-1'}`}
              >
                {isFinalizing ? "Processing Neural Data..." : "Finalize Verification & Generate Offer"}
              </button>
            </div>
          )}
        </div>

        {offer && (
          <div className="bg-indigo-600 rounded-[2rem] shadow-2xl p-10 text-white relative overflow-hidden animate-slide-up">
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32 blur-3xl"></div>
            
            <div className="flex justify-between items-start mb-10">
              <h2 className="text-2xl font-black italic tracking-tighter">PREMIUM OFFER</h2>
              <div className="bg-white/20 px-3 py-1 rounded-full text-[10px] font-bold">LIMITED TIME</div>
            </div>

            {offer.status === "APPROVED" ? (
              <div className="space-y-8">
                <div>
                  <span className="block text-xs font-bold text-indigo-200 uppercase tracking-widest mb-2">Maximum Credit Line</span>
                  <span className="text-6xl font-black tracking-tighter">
                    ₹{offer.maximum_amount?.toLocaleString()}
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-8 py-8 border-y border-white/10">
                  <div>
                    <span className="block text-[10px] font-bold text-indigo-200 uppercase mb-1">APR</span>
                    <span className="text-2xl font-black">{offer.interest_rate}%</span>
                  </div>
                  <div>
                    <span className="block text-[10px] font-bold text-indigo-200 uppercase mb-1">Fixed Tenure</span>
                    <span className="text-2xl font-black">{offer.tenure_months} Mo.</span>
                  </div>
                </div>

                <div className="flex justify-between items-center px-8 py-6 bg-white/10 rounded-2xl backdrop-blur-md">
                   <span className="text-xs font-bold uppercase">Estimated EMI</span>
                   <span className="text-3xl font-black">₹{Math.round(offer.calculated_emi).toLocaleString()}</span>
                </div>

                <button className="w-full bg-white text-indigo-600 font-extrabold py-5 rounded-2xl text-xl shadow-2xl transition-all hover:bg-indigo-50">
                  Sign & Disburse Now
                </button>
              </div>
            ) : (
              <div className="p-8 rounded-[1.5rem] bg-black/20 backdrop-blur-md border border-white/10">
                <h3 className="font-black text-xl mb-2">Verification Incomplete</h3>
                <p className="text-indigo-100/80 text-sm leading-relaxed">{offer.reason}</p>
                <button onClick={() => setOffer(null)} className="mt-6 text-white text-xs font-bold underline decoration-2 underline-offset-4">Try Re-Verification</button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
