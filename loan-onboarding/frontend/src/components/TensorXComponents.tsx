"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useDataChannel } from '@livekit/components-react';
import fpPromise from '@fingerprintjs/fingerprintjs';

// --- FRAUD ENGINE: Captures Features 8 & 9 ---
export const captureSecurityMetadata = async () => {
  try {
    const fp = await fpPromise.load();
    const result = await fp.get();
    const visitorId = result.visitorId;

    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const geoPayload = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: position.coords.accuracy,
            visitorId: visitorId,
            timestamp: new Date().toISOString()
          };
          console.log("✅ Security Metadata Captured:", geoPayload);
          // Optional: Send to backend telemetry
          try {
            await fetch("http://localhost:8000/api/geo/capture", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(geoPayload)
            });
          } catch (e) {}
        },
        (error) => console.error("❌ Geo-location denied/failed:", error.message)
      );
    }
  } catch (error) {
    console.error("❌ Fingerprint failed:", error);
  }
};

// --- 5-SECOND CALIBRATION OVERLAY ---
export function CalibrationOverlay() {
  const [calibrationMsg, setCalibrationMsg] = useState<string | null>(null);

  useDataChannel('focus-alert', (messageOrPayload: any) => {
    const data = messageOrPayload.payload || messageOrPayload;
    const msg = typeof data === 'string' ? data : new TextDecoder().decode(data);

    if (msg.startsWith('focus-alert:calibrating-')) {
      setCalibrationMsg(msg.split('-')[2]);
    } else if (msg === 'focus-alert:cal-done') {
      setCalibrationMsg(null);
    }
  });

  if (!calibrationMsg) return null;

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none bg-black/40 backdrop-blur-[2px]">
      <div className="bg-gray-900/90 border border-indigo-500/50 shadow-[0_0_30px_rgba(99,102,241,0.3)] rounded-2xl p-8 max-w-sm w-full mx-4 flex flex-col items-center animate-fade-in-up">
        <div className="w-16 h-16 relative mb-6">
          <div className="absolute inset-0 border-4 border-indigo-500/30 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <h3 className="text-xl font-black text-white tracking-tight mb-2">NEURAL CALIBRATION</h3>
        <p className="text-sm text-indigo-200 text-center mb-6 leading-relaxed">
          Please look directly into the camera to establish baseline biometric focus.
        </p>
        <div className="w-full bg-gray-800 rounded-full h-2 mb-3 overflow-hidden">
          <div 
            className="bg-indigo-500 h-2 rounded-full transition-all duration-1000 ease-linear"
            style={{ width: `${(5 - parseInt(calibrationMsg)) * 20}%` }}
          ></div>
        </div>
        <div className="text-xs font-bold text-gray-400 tracking-widest">
          {calibrationMsg} SECONDS REMAINING
        </div>
      </div>
    </div>
  );
}

// --- VERBAL CONSENT BADGE (Feature 15) ---
export function ConsentBadge() {
  const [consentTime, setConsentTime] = useState<string | null>(null);

  useDataChannel('focus-alert', (messageOrPayload: any) => {
    const data = messageOrPayload.payload || messageOrPayload;
    const msg = typeof data === 'string' ? data : new TextDecoder().decode(data);

    if (msg.startsWith('focus-alert:consent-')) {
      const rawTimestamp = msg.split('consent-')[1];
      const formattedTime = new Date(rawTimestamp).toLocaleTimeString();
      setConsentTime(formattedTime);
    }
  });

  if (!consentTime) return null;

  return (
    <div style={{
      position: 'fixed', bottom: '30px', right: '30px',
      background: 'rgba(16, 185, 129, 0.95)', color: '#fff',
      padding: '12px 24px', borderRadius: '12px',
      boxShadow: '0 10px 25px rgba(16, 185, 129, 0.4)',
      border: '1px solid rgba(255, 255, 255, 0.3)',
      zIndex: 999999,
      fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '10px',
      animation: 'slideIn 0.5s ease-out'
    }}>
      <span style={{ fontSize: '20px' }}>🎙️✅</span>
      <div>
        <div style={{ fontSize: '14px' }}>Verbal Consent Verified</div>
        <div style={{ fontSize: '11px', opacity: 0.9, marginTop: '2px' }}>{consentTime}</div>
      </div>
      <style>{`@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }`}</style>
    </div>
  );
}

// --- INTERACTIVE EMI WIDGET (Feature 62) ---
export function EMIWidget({ amount: initialAmount = 100000 }) {
  const [amount, setAmount] = useState(initialAmount);
  const [tenure, setTenure] = useState(12);
  const baseRate = 12.0;

  useEffect(() => {
    setAmount(initialAmount);
  }, [initialAmount]);

  const calculateEMI = (principal: number, rateYearly: number, months: number) => {
    const r = (rateYearly / 12) / 100;
    const emi = (principal * r * Math.pow(1 + r, months)) / (Math.pow(1 + r, months) - 1);
    return Math.round(emi);
  };

  const offers = [
    { name: "Special Promo", rate: baseRate - 1.5, color: "#10b981", tag: "Best Value" },
    { name: "Standard Rate", rate: baseRate, color: "#3b82f6", tag: "Standard" },
    { name: "No Collateral", rate: baseRate + 3.0, color: "#f59e0b", tag: "Fast Approval" }
  ];

  return (
    <div style={{
      width: '100%',
      background: 'rgba(17, 24, 39, 0.95)', border: '1px solid #374151',
      borderRadius: '16px', padding: '20px', color: '#fff',
      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)', marginTop: '20px'
    }}>
      <h3 style={{ margin: '0 0 15px 0', fontSize: '18px' }}>📊 Interactive EMI Offers</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', marginBottom: '5px' }}>
          <span>Loan Amount</span><strong>₹{amount.toLocaleString('en-IN')}</strong>
        </div>
        <input type="range" min="10000" max="500000" step="10000" value={amount} 
          onChange={(e) => setAmount(Number(e.target.value))} style={{ width: '100%' }} />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', marginBottom: '5px' }}>
          <span>Tenure (Months)</span><strong>{tenure} mo</strong>
        </div>
        <input type="range" min="6" max="60" step="6" value={tenure} 
          onChange={(e) => setTenure(Number(e.target.value))} style={{ width: '100%' }} />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {offers.map((offer, idx) => (
          <div key={idx} style={{
            background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px',
            borderLeft: `4px solid ${offer.color}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <div>
              <div style={{ fontSize: '13px', color: '#9ca3af' }}>{offer.name} ({offer.rate}%)</div>
              <div style={{ fontSize: '11px', color: offer.color, fontWeight: 'bold', marginTop: '2px' }}>{offer.tag}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>₹{calculateEMI(amount, offer.rate, tenure).toLocaleString('en-IN')}</div>
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>/ month</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- PAN UPLOAD MODAL (Feature 69: WebP Compression Added) ---
export function PanUploadModal({ isResumingSession, onComplete, roomName }: { isResumingSession: boolean, onComplete: () => void, roomName: string }) {
  const [uploadRequired, setUploadRequired] = useState(!isResumingSession);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { send } = useDataChannel('kyc-control');

  useEffect(() => {
    if (uploadRequired) captureSecurityMetadata();
  }, [uploadRequired]);

  useEffect(() => {
    if (isResumingSession) {
      console.log("🔄 Resuming Session detected. Bypassing PAN upload...");
      setTimeout(() => {
        try { send(new TextEncoder().encode('pan_upload_success'), { reliable: true }); } catch (e) {}
        onComplete();
      }, 1500);
    }
  }, [send, isResumingSession, onComplete]);

  useDataChannel('focus-alert', (messageOrPayload: any) => {
    if (isResumingSession) return; 

    try {
      const data = messageOrPayload.payload || messageOrPayload;
      const payloadString = typeof data === 'string' ? data : new TextDecoder().decode(data);
      
      if (payloadString.includes('focus-alert:upload-required')) setUploadRequired(true);
      else if (payloadString.includes('focus-alert:upload-done') || payloadString.includes('calibrating')) {
        setUploadRequired(false);
        onComplete();
      }
    } catch (e) { console.error(e); }
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true); 
    setUploadError(null);

    const img = new Image();
    img.src = URL.createObjectURL(file);
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const MAX_WIDTH = 1200;
      let width = img.width;
      let height = img.height;
      if (width > MAX_WIDTH) {
        height = Math.round((height * MAX_WIDTH) / width);
        width = MAX_WIDTH;
      }
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      ctx?.drawImage(img, 0, 0, width, height);

      canvas.toBlob(async (blob) => {
        if (!blob) {
          setUploadError('Compression failed.');
          setIsUploading(false);
          return;
        }

        const originalKb = (file.size / 1024).toFixed(1);
        const compressedKb = (blob.size / 1024).toFixed(1);
        const savingsPercent = (((file.size - blob.size) / file.size) * 100).toFixed(1);

        console.log(`📉 FEATURE 69 ENABLED: Compressed ${originalKb}KB PNG/JPG to ${compressedKb}KB WebP.`);

        const formData = new FormData();
        formData.append('file', blob, 'document.webp');

        try {
          const response = await fetch('http://localhost:8000/api/kyc/upload-pan', { method: 'POST', body: formData });
          const result = await response.json();

          if (response.ok && result.status === 'success') {
            try { send(new TextEncoder().encode('pan_upload_success'), { reliable: true }); } catch (e) {}
            
            if (roomName) {
              fetch('http://localhost:8000/api/kyc/conversation-update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room_name: roomName, field: 'pan_number', value: result.pan })
              }).catch(() => {});
            }

            setUploadRequired(false); 
            alert(`✅ PAN Verified: ${result.pan}\n\n[Feature 69: WebP Active]\nPayload compressed by ${savingsPercent}%\nOriginal: ${originalKb}KB -> Sent: ${compressedKb}KB`);
            onComplete();
          } else {
            setUploadError(result.message || 'Failed to read PAN.');
          }
        } catch (error) { 
          setUploadError('Server connection failed.'); 
        } finally { 
          setIsUploading(false); 
        }
      }, 'image/webp', 0.7); 
    };
  };
  
  if (!uploadRequired || isResumingSession) return null;

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0,0,0,0.85)', zIndex: 99999, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#1e293b', padding: '40px', borderRadius: '16px', border: '1px solid #334155', textAlign: 'center', maxWidth: '400px' }}>
        <h2 style={{ color: '#fff', marginTop: 0, marginBottom: '10px' }}>PAN Verification</h2>
        <input type="file" accept="image/*" ref={fileInputRef} style={{ display: 'none' }} onChange={handleFileUpload} />
        <button onClick={() => fileInputRef.current?.click()} disabled={isUploading}
          style={{ background: isUploading ? '#475569' : '#3b82f6', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: '8px', fontSize: '16px', fontWeight: 'bold', cursor: isUploading ? 'not-allowed' : 'pointer' }}>
          {isUploading ? 'Compressing & Analyzing...' : 'Upload PAN Card'}
        </button>
        {uploadError && <p style={{ color: '#ef4444', fontSize: '13px', marginTop: '16px' }}>{uploadError}</p>}
      </div>
    </div>
  );
}

// --- FOCUS ALERT BANNER ---
export function FocusAlertBanner() {
  const [isFocused, setIsFocused] = useState(true);

  useDataChannel('focus-alert', (messageOrPayload: any) => {
    try {
      const data = messageOrPayload.payload || messageOrPayload;
      const payloadString = typeof data === 'string' ? data : new TextDecoder().decode(data);
      if (payloadString.includes('focus-alert:focused')) setIsFocused(true);
      else if (payloadString.includes('focus-alert:unfocused')) setIsFocused(false);
    } catch (e) { console.error(e); }
  });

  if (isFocused) return null;

  return (
    <div style={{ position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 9999, padding: '14px 20px', borderRadius: 14, background: 'rgba(163, 27, 27, 0.96)', color: '#fff', fontWeight: 700, textAlign: 'center' }}>
      <div style={{ fontSize: 16 }}>Not focused</div>
      <div style={{ fontSize: 13, opacity: 0.92, marginTop: 4 }}>Please look at the screen to continue.</div>
    </div>
  );
}

// --- ADMIN LIVE ALERTS (Feature 39) ---
export function AdminAlertFeed() {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8000/api/admin/alerts/stream_v2");

    eventSource.onmessage = (event) => {
      const newAlert = JSON.parse(event.data);
      setAlerts((prev) => [newAlert, ...prev].slice(0, 3)); 
    };

    eventSource.onerror = () => {
      console.log("SSE Stream disconnected. Reconnecting...");
    };

    return () => eventSource.close();
  }, []);

  if (alerts.length === 0) return null;

  return (
    <div style={{
      position: 'fixed', top: '20px', right: '20px', width: '320px',
      zIndex: 999999, display: 'flex', flexDirection: 'column', gap: '10px'
    }}>
      <div style={{ background: '#111827', color: '#fff', padding: '8px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold', borderBottom: '2px solid #ef4444' }}>
        🛡️ ADMIN FRAUD FEED (LIVE)
      </div>
      {alerts.map((alert, idx) => (
        <div key={idx} style={{
          background: 'rgba(239, 68, 68, 0.95)', color: '#fff',
          padding: '12px', borderRadius: '8px',
          boxShadow: '0 4px 15px rgba(239, 68, 68, 0.3)',
          animation: 'slideInRight 0.3s ease-out'
        }}>
          <div style={{ fontSize: '11px', opacity: 0.9, marginBottom: '4px', display: 'flex', justifyContent: 'space-between' }}>
            <span>🚨 {alert.type}</span>
            <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
          </div>
          <div style={{ fontSize: '14px', fontWeight: 'bold' }}>{alert.message}</div>
        </div>
      ))}
      <style>{`@keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }`}</style>
    </div>
  );
}

// --- FEATURE 33: DEMO DROP BUTTON ---
export function DropConnectionDemo({ isResumingSession }: { isResumingSession: boolean }) {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneError, setPhoneError] = useState<string | null>(null);

  const handleDrop = async () => {
    try {
      const trimmed = phoneNumber.replace(/\s+/g, '');
      if (!/^\d{10}$/.test(trimmed) && !/^\+\d{10,15}$/.test(trimmed)) {
        setPhoneError('Enter a valid 10-digit phone number or +countrycode format.');
        return;
      }
      setPhoneError(null);

      const res = await fetch('http://localhost:8000/api/kyc/simulate-drop', {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ phone: trimmed }) 
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert(`📡 SMS SENT!\n\nCheck your phone for the resume link.\nLink: ${data.link}`);
      } else {
        alert(`❌ SMS FAILED\n\n${data.message || 'Unknown error.'}`);
      }
    } catch (e) { console.error(e); }
  };

  if (isResumingSession) {
    return (
      <div style={{ marginBottom: '20px', background: '#10b981', color: 'white', padding: '8px 16px', borderRadius: '8px', fontWeight: 'bold', display: 'inline-block' }}>
        🔄 Recovered Session Active
      </div>
    );
  }

  return (
    <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', alignItems: 'center', background: '#1e293b', padding: '12px', borderRadius: '12px', border: '1px solid #334155' }}>
      <span style={{color: 'white', fontWeight: 'bold', fontSize: '14px'}}>Test Recovery:</span>
      <input
        type="tel"
        inputMode="numeric"
        placeholder="Enter 10-digit phone"
        value={phoneNumber}
        onChange={(e) => setPhoneNumber(e.target.value)}
        style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #475569', width: '200px', color: '#f1f5f9', background: '#0f172a', outline: 'none', fontSize: '14px' }}
      />
      <button onClick={handleDrop} style={{ background: '#ef4444', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', transition: 'all 0.2s' }}>
        ⚡ Simulate Network Drop (Send SMS)
      </button>
      {phoneError && <div style={{ color: '#ef4444', fontSize: '12px', fontWeight: 'bold' }}>{phoneError}</div>}
    </div>
  );
}

// --- REAL-TIME CONVERSATION DATA TABLE (Feature: Live KYC Field Extraction) ---
const FIELD_META: Record<string, { label: string; icon: string }> = {
  name:            { label: 'Full Name',        icon: '👤' },
  dob:             { label: 'Date of Birth',    icon: '🎂' },
  employment_type: { label: 'Employment Type',  icon: '💼' },
  monthly_income:  { label: 'Monthly Income',   icon: '💰' },
  existing_emi:    { label: 'Existing EMI',     icon: '📋' },
  loan_purpose:    { label: 'Loan Purpose',     icon: '🎯' },
  loan_amount:     { label: 'Loan Amount',      icon: '🏦' },
  pan_number:      { label: 'PAN Number',       icon: '🪪' },
};

export function ConversationTable({ roomName, onComplete, onFieldUpdate }: { roomName: string, onComplete?: () => void, onFieldUpdate?: (field: string, value: string) => void }) {
  const [fields, setFields] = React.useState<Record<string, string>>({});
  const [status, setStatus] = React.useState<'waiting' | 'in_progress' | 'complete'>('waiting');
  const [lastUpdated, setLastUpdated] = React.useState<string | null>(null);

  useEffect(() => {
    if (!roomName) return;
    const es = new EventSource(`http://localhost:8000/api/kyc/conversation-stream/${roomName}`);
    es.onmessage = (event) => {
      try {
        const { field, value } = JSON.parse(event.data);
        if (field === 'status') {
          setStatus(value as 'complete' | 'in_progress');
        } else {
          setFields(prev => ({ ...prev, [field]: value }));
          setLastUpdated(new Date().toLocaleTimeString());
          // Propagate each field to parent for AI Appraisal live updates
          if (onFieldUpdate) onFieldUpdate(field, value);
        }
      } catch {}
    };
    es.onerror = () => { /* silent reconnect */ };
    return () => es.close();
  }, [roomName, onFieldUpdate]);

  // Use a ref to ensure onComplete is always the latest without adding it to dependency array
  const onCompleteRef = React.useRef(onComplete);
  React.useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  React.useEffect(() => {
    if (status === 'complete' && onCompleteRef.current) {
      onCompleteRef.current();
    }
  }, [status]);

  const filledCount = Object.keys(fields).filter(k => k !== 'status' && fields[k]).length;
  const totalFields = Object.keys(FIELD_META).length;
  const progress = Math.round((filledCount / totalFields) * 100);

  return (
    <div style={{
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      border: '1px solid #334155', borderRadius: '16px', padding: '20px',
      color: '#fff', width: '100%', boxShadow: '0 20px 40px rgba(0,0,0,0.4)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, letterSpacing: '0.05em' }}>
            🤖 AI EXTRACTION — LIVE
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: '11px', color: '#94a3b8' }}>
            Fields auto-populate as Aria speaks with applicant
          </p>
        </div>
        <div style={{
          background: status === 'complete' ? '#10b981' : status === 'in_progress' ? '#6366f1' : '#475569',
          padding: '4px 12px', borderRadius: '100px', fontSize: '11px', fontWeight: 700
        }}>
          {status === 'complete' ? '✅ COMPLETE' : status === 'in_progress' ? '🔴 LIVE' : '⏳ WAITING'}
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ background: '#1e293b', borderRadius: '100px', height: '6px', marginBottom: '16px', overflow: 'hidden' }}>
        <div style={{
          width: `${progress}%`, height: '100%',
          background: 'linear-gradient(90deg, #6366f1, #818cf8)',
          borderRadius: '100px', transition: 'width 0.5s ease'
        }} />
      </div>
      <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '16px', textAlign: 'right' }}>
        {filledCount}/{totalFields} fields captured • {progress}%
      </div>

      {/* Fields Table */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {Object.entries(FIELD_META).map(([key, meta]) => {
          const value = fields[key];
          const filled = !!value;
          return (
            <div key={key} style={{
              display: 'flex', alignItems: 'center', gap: '12px',
              background: filled ? 'rgba(99,102,241,0.1)' : 'rgba(255,255,255,0.02)',
              border: `1px solid ${filled ? 'rgba(99,102,241,0.3)' : '#1e293b'}`,
              borderRadius: '10px', padding: '10px 14px',
              transition: 'all 0.3s ease'
            }}>
              <span style={{ fontSize: '18px', width: '24px', textAlign: 'center' }}>{meta.icon}</span>
              <span style={{ fontSize: '12px', color: '#94a3b8', width: '130px', flexShrink: 0, fontWeight: 600 }}>
                {meta.label}
              </span>
              <div style={{ flex: 1, borderLeft: '1px solid #334155', paddingLeft: '12px' }}>
                {filled ? (
                  <span style={{
                    fontSize: '14px', fontWeight: 700, color: '#e2e8f0',
                    animation: 'fadeIn 0.4s ease'
                  }}>
                    {value}
                  </span>
                ) : (
                  <span style={{ fontSize: '12px', color: '#475569', fontStyle: 'italic' }}>
                    Awaiting response...
                  </span>
                )}
              </div>
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0,
                background: filled ? '#10b981' : '#334155',
                boxShadow: filled ? '0 0 8px rgba(16,185,129,0.6)' : 'none',
                transition: 'all 0.3s ease'
              }} />
            </div>
          );
        })}
      </div>

      {lastUpdated && (
        <p style={{ margin: '12px 0 0', fontSize: '10px', color: '#475569', textAlign: 'right' }}>
          Last updated: {lastUpdated}
        </p>
      )}

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateX(-4px); } to { opacity: 1; transform: translateX(0); } }
      `}</style>
    </div>
  );
}
