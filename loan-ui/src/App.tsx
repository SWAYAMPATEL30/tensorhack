import {
  LiveKitRoom,
  VideoConference,
  RoomAudioRenderer,
  useDataChannel,
} from '@livekit/components-react';
import '@livekit/components-styles';

import { useState, useRef, useEffect } from 'react';
import fpPromise from '@fingerprintjs/fingerprintjs';

const BACKEND = 'http://localhost:8000';

// Decode room name from LiveKit JWT without any library
function getRoomFromToken(jwt: string): string {
  try {
    const payload = JSON.parse(atob(jwt.split('.')[1]));
    return payload?.video?.room || 'kyc-room';
  } catch {
    return 'kyc-room';
  }
}

// --- FRAUD ENGINE: Captures Features 8 & 9 ---
const captureSecurityMetadata = async () => {
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
        },
        (error) => console.error("❌ Geo-location denied/failed:", error.message)
      );
    }
  } catch (error) {
    console.error("❌ Fingerprint failed:", error);
  }
};

const serverUrl = process.env.REACT_APP_LIVEKIT_URL;
const token = process.env.REACT_APP_LIVEKIT_TOKEN;

// --- FEATURE 33: CHECK IF WE ARE RESUMING FROM SMS ---
const urlParams = new URLSearchParams(window.location.search);
const isResumingSession = !!urlParams.get('resume_id');

// --- 5-SECOND CALIBRATION OVERLAY ---
function CalibrationOverlay() {
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
    <div style={{
      position: 'absolute', top: '20%', left: '25%', transform: 'translateX(-50%)',
      zIndex: 10000, textAlign: 'center', pointerEvents: 'none'
    }}>
      <div style={{
        background: 'rgba(0, 0, 0, 0.85)', color: '#00ff00',
        padding: '12px 24px', borderRadius: '100px', border: '2px solid #00ff00', fontSize: '18px', fontWeight: 'bold',
      }}>
        🎯 CALIBRATING: {calibrationMsg}s
      </div>
    </div>
  );
}

// --- VERBAL CONSENT BADGE (Feature 15) ---
function ConsentBadge() {
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
function EMIWidget() {
  const [amount, setAmount] = useState(100000);
  const [tenure, setTenure] = useState(12);
  const baseRate = 12.0;

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
      position: 'fixed', bottom: '20px', right: '20px', width: '380px',
      background: 'rgba(17, 24, 39, 0.95)', border: '1px solid #374151',
      borderRadius: '16px', padding: '20px', color: '#fff', zIndex: 9999,
      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
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
function PanUploadModal() {
  const [uploadRequired, setUploadRequired] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { send } = useDataChannel('kyc-control');

  useEffect(() => {
    if (uploadRequired) captureSecurityMetadata();
  }, [uploadRequired]);

  // --- FEATURE 33: RESUME SESSION BYPASS ---
  useEffect(() => {
    if (isResumingSession) {
      console.log("🔄 Resuming Session detected. Bypassing PAN upload...");
      // Wait 1.5 seconds so the UI loads, then tell the agent to skip PAN validation
      setTimeout(() => send(new TextEncoder().encode('pan_upload_success'), { reliable: true }), 1500);
    }
  }, [send]);

  useDataChannel('focus-alert', (messageOrPayload: any) => {
    if (isResumingSession) return; // Ignore agent prompts if we are skipping this step

    try {
      const data = messageOrPayload.payload || messageOrPayload;
      const payloadString = typeof data === 'string' ? data : new TextDecoder().decode(data);
      
      if (payloadString.includes('focus-alert:upload-required')) setUploadRequired(true);
      else if (payloadString.includes('focus-alert:upload-done') || payloadString.includes('calibrating')) setUploadRequired(false);
    } catch (e) { console.error(e); }
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true); 
    setUploadError(null);

    // --- FEATURE 69: CLIENT-SIDE WEBP COMPRESSION ---
    const img = new Image();
    img.src = URL.createObjectURL(file);
    img.onload = () => {
      const canvas = document.createElement('canvas');
      
      // Scale down massive phone photos to a max-width of 1200px for OCR
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

      // Convert to WebP with 0.7 Quality
      canvas.toBlob(async (blob) => {
        if (!blob) {
          setUploadError('Compression failed.');
          setIsUploading(false);
          return;
        }

        // Calculate savings for the Hackathon Pitch
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
            send(new TextEncoder().encode('pan_upload_success'), { reliable: true });
            setUploadRequired(false); 
            
            // Show the exact math to the judges
            alert(`✅ PAN Verified: ${result.pan}\n\n[Feature 69: WebP Active]\nPayload compressed by ${savingsPercent}%\nOriginal: ${originalKb}KB -> Sent: ${compressedKb}KB`);
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
  
  // Hide if not required OR if we are resuming via SMS link
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
function FocusAlertBanner() {
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
function AdminAlertFeed() {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8000/api/admin/alerts/stream");

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
function DropConnectionDemo() {
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
        alert(`📡 SMS SENT!\n\nCheck your phone for the resume link.`);
      } else {
        alert(`❌ SMS FAILED\n\n${data.message || 'Unknown error.'}`);
      }
    } catch (e) { console.error(e); }
  };

  if (isResumingSession) {
    return (
      <div style={{ position: 'absolute', top: '10px', left: '10px', zIndex: 10000, background: '#10b981', color: 'white', padding: '8px 16px', borderRadius: '8px', fontWeight: 'bold' }}>
        🔄 Recovered Session Active
      </div>
    );
  }

  return (
    <div style={{ position: 'absolute', top: '10px', left: '10px', zIndex: 10000, display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <input
        type="tel"
        inputMode="numeric"
        placeholder="Enter 10-digit phone or +country"
        value={phoneNumber}
        onChange={(e) => setPhoneNumber(e.target.value)}
        style={{ padding: '8px 10px', borderRadius: '8px', border: '1px solid #e5e7eb', width: '220px' }}
      />
      <button onClick={handleDrop} style={{ background: '#ef4444', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
        ⚡ Simulate Network Drop (Send SMS)
      </button>
      {phoneError && <div style={{ color: '#ef4444', fontSize: '12px', fontWeight: 'bold' }}>{phoneError}</div>}
    </div>
  );
}

// ─── CONVERSATION TABLE (Real-time KYC + CIBIL + Loan Decision) ────────────
const FIELD_LABELS: Record<string, string> = {
  name:            '👤 Full Name',
  dob:             '🎂 Date of Birth',
  employment_type: '💼 Employment',
  monthly_income:  '💰 Monthly Income',
  existing_emi:    '📋 Existing EMI',
  loan_purpose:    '🏠 Loan Purpose',
  loan_amount:     '💵 Loan Amount',
  pan_number:      '🪪 PAN Number',
  status:          '📌 Status',
  cibil_score:     '📊 CIBIL Score',
};

function ConversationTable({ roomName }: { roomName: string }) {
  const [fields, setFields] = useState<Record<string, string>>({});
  const [loanDecision, setLoanDecision] = useState<any>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!roomName) return;
    let es: EventSource;
    let retryTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      es = new EventSource(`${BACKEND}/api/kyc/conversation-stream/${roomName}`);

      es.onopen = () => setConnected(true);

      es.onmessage = (event) => {
        try {
          const { field, value } = JSON.parse(event.data);
          if (field === 'loan_decision') {
            setLoanDecision(JSON.parse(value));
          } else {
            setFields(prev => ({ ...prev, [field]: value }));
          }
        } catch {}
      };

      es.onerror = () => {
        setConnected(false);
        es.close();
        // Auto-reconnect after 3 s
        retryTimer = setTimeout(connect, 3000);
      };
    };

    connect();
    return () => { es?.close(); clearTimeout(retryTimer); };
  }, [roomName]);

  const displayFields = Object.entries(FIELD_LABELS).filter(
    ([k]) => k !== 'cibil_score' && k !== 'status'
  );

  const cibil = fields['cibil_score'];
  const status = fields['status'];

  const getCibilColor = (score: number) =>
    score >= 750 ? '#10b981' : score >= 700 ? '#3b82f6' : score >= 650 ? '#f59e0b' : '#ef4444';

  return (
    <div style={{
      position: 'fixed', bottom: '20px', right: '20px',
      width: '370px', maxHeight: '92vh', overflowY: 'auto',
      background: 'rgba(15, 23, 42, 0.97)',
      border: '1px solid rgba(99, 102, 241, 0.5)',
      borderRadius: '16px', padding: '16px',
      color: '#fff', zIndex: 9999,
      boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
      fontFamily: 'Inter, system-ui, sans-serif',
      backdropFilter: 'blur(12px)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>🤖</span>
          <span style={{ fontWeight: 700, fontSize: '14px', color: '#818cf8' }}>AI Appraisal Panel</span>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '5px',
          fontSize: '10px', color: connected ? '#10b981' : '#f59e0b',
          fontWeight: 600,
        }}>
          <span style={{
            width: '7px', height: '7px', borderRadius: '50%',
            background: connected ? '#10b981' : '#f59e0b',
            animation: connected ? 'pulse 2s infinite' : 'none',
            display: 'inline-block',
          }} />
          {connected ? 'LIVE' : 'RECONNECTING…'}
        </div>
      </div>

      {/* CIBIL Score Badge */}
      {cibil && (
        <div style={{
          background: 'rgba(255,255,255,0.06)',
          border: `2px solid ${getCibilColor(Number(cibil))}`,
          borderRadius: '12px', padding: '12px 16px',
          marginBottom: '12px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          animation: 'fadeInDown 0.4s ease',
        }}>
          <div>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '2px' }}>📊 CIBIL Score (Mock Bureau)</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: getCibilColor(Number(cibil)) }}>{cibil}</div>
          </div>
          <div style={{
            background: getCibilColor(Number(cibil)), borderRadius: '8px',
            padding: '4px 10px', fontSize: '12px', fontWeight: 700, color: '#fff',
          }}>
            {Number(cibil) >= 750 ? 'EXCELLENT' : Number(cibil) >= 700 ? 'GOOD' : Number(cibil) >= 650 ? 'FAIR' : 'POOR'}
          </div>
        </div>
      )}

      {/* KYC Fields Table */}
      <div style={{ marginBottom: '10px' }}>
        {displayFields.map(([key, label]) => (
          <div key={key} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
            padding: '7px 0',
            borderBottom: '1px solid rgba(255,255,255,0.07)',
          }}>
            <span style={{ fontSize: '11px', color: '#64748b', flex: '0 0 140px' }}>{label}</span>
            <span style={{
              fontSize: '12px', fontWeight: 600,
              color: fields[key] ? '#e2e8f0' : '#334155',
              textAlign: 'right', wordBreak: 'break-word',
              animation: fields[key] ? 'fadeIn 0.3s ease' : 'none',
            }}>
              {fields[key]
                ? (key === 'monthly_income' || key === 'existing_emi' || key === 'loan_amount'
                    ? `₹${Number(fields[key]).toLocaleString('en-IN')}`
                    : fields[key])
                : <span style={{ fontStyle: 'italic', color: '#1e293b' }}>Awaiting…</span>
              }
            </span>
          </div>
        ))}

        {/* Status row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '7px 0' }}>
          <span style={{ fontSize: '11px', color: '#64748b' }}>📌 Status</span>
          <span style={{
            fontSize: '11px', fontWeight: 700, padding: '2px 10px', borderRadius: '100px',
            background: status === 'complete' ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.15)',
            color: status === 'complete' ? '#10b981' : '#f59e0b',
          }}>
            {status === 'complete' ? '✅ COMPLETE' : (status || '⏳ IN PROGRESS')}
          </span>
        </div>
      </div>

      {/* Loan Decision Card */}
      {loanDecision ? (
        <div style={{
          borderRadius: '12px', padding: '14px',
          background: loanDecision.decision === 'APPROVED'
            ? 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.1))'
            : 'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(185,28,28,0.1))',
          border: loanDecision.decision === 'APPROVED' ? '1px solid #10b981' : '1px solid #ef4444',
          animation: 'fadeInUp 0.5s ease',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span style={{ fontSize: '22px' }}>{loanDecision.decision === 'APPROVED' ? '✅' : '❌'}</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '16px', color: loanDecision.decision === 'APPROVED' ? '#10b981' : '#ef4444' }}>
                {loanDecision.decision}
              </div>
              <div style={{ fontSize: '10px', color: '#64748b' }}>Risk: {loanDecision.risk_band} | CIBIL: {loanDecision.cibil_score}</div>
            </div>
          </div>

          {loanDecision.decision === 'APPROVED' && (
            <>
              {[['Loan Amount', `₹${Number(loanDecision.offer_amount).toLocaleString('en-IN')}`],
                ['Rate', `${loanDecision.offer_rate}% p.a.`],
                ['Tenure', `${loanDecision.offer_tenure} months`],
                ['Monthly EMI', `₹${Math.round(loanDecision.offer_emi).toLocaleString('en-IN')}`]
              ].map(([label, val]) => (
                <div key={label} style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: '12px', padding: '4px 0',
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                }}>
                  <span style={{ color: '#94a3b8' }}>{label}</span>
                  <span style={{ fontWeight: 700, color: '#e2e8f0' }}>{val}</span>
                </div>
              ))}
            </>
          )}

          {loanDecision.decision === 'REJECTED' && loanDecision.reason && (
            <div style={{ fontSize: '12px', color: '#fca5a5', marginTop: '4px' }}>
              Reason: {loanDecision.reason}
            </div>
          )}
        </div>
      ) : status !== 'complete' ? (
        <div style={{ textAlign: 'center', padding: '12px 0', color: '#334155', fontSize: '12px' }}>
          ⏳ Waiting for KYC completion…
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '12px 0', color: '#f59e0b', fontSize: '12px' }}>
          ⚙️ Computing loan decision…
        </div>
      )}

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeInDown { from{opacity:0;transform:translateY(-12px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
      `}</style>
    </div>
  );
}

export default function App() {
  const [connectionError, setConnectionError] = useState<string | null>(null);
  // Decode room name from the LiveKit JWT so the SSE stream uses the correct room
  const roomName = token ? getRoomFromToken(token) : 'kyc-room';

  if (!serverUrl || !token) {
    return (
      <div style={{ height: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a', color: '#fff', fontWeight: 700 }}>
        Missing LiveKit config. Set REACT_APP_LIVEKIT_URL and REACT_APP_LIVEKIT_TOKEN in loan-ui/.env.
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
      {/* @ts-ignore */}
      <LiveKitRoom video={true} audio={true} token={token} serverUrl={serverUrl} data-lk-theme="default"
        onDisconnected={(reason) => setConnectionError(`Disconnected: ${reason}`)}
        onError={(error) => setConnectionError(error?.message)}
      >
        {connectionError && (
          <div style={{ position: 'fixed', bottom: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 10000, background: 'rgba(190, 32, 32, 0.95)', color: 'white', padding: '10px 14px', borderRadius: 10 }}>{connectionError}</div>
        )}
        
        {/* MODALS, WIDGETS, AND BUTTONS */}
        <DropConnectionDemo />
        <PanUploadModal />
        <FocusAlertBanner />
        <CalibrationOverlay />
        <ConsentBadge />
        <AdminAlertFeed />

        {/* LIVE KYC DATA + CIBIL + LOAN DECISION — replaces the static EMIWidget */}
        <ConversationTable roomName={roomName} />
        
        <VideoConference />
        <RoomAudioRenderer />
        <div style={{ position: 'absolute', top: '50%', left: '25%', transform: 'translate(-50%, -50%)', width: '35vw', height: '60vh', border: '4px dashed rgba(0, 120, 255, 0.8)', borderRadius: '24px', pointerEvents: 'none', zIndex: 50, boxShadow: '0 0 0 9999px rgba(0,0,0,0.3)' }} />
      </LiveKitRoom>
    </div>
  );
}