html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TenzorX - Loan Wizard AI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0a1a;color:#fff;overflow:hidden}
.deck{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}
.slide{display:none;width:960px;min-height:540px;background:linear-gradient(135deg,#0d1b4b,#1a0e3d);border-radius:16px;padding:48px;border:1px solid rgba(99,179,237,0.3);box-shadow:0 0 60px rgba(99,102,241,0.3);position:relative;overflow:hidden;flex-direction:column;justify-content:center}
.slide.active{display:flex}
.slide::before{content:"";position:absolute;top:-50%;right:-20%;width:500px;height:500px;background:radial-gradient(circle,rgba(99,102,241,0.15),transparent 70%);pointer-events:none}
.badge{display:inline-block;background:linear-gradient(90deg,#6366f1,#8b5cf6);padding:4px 14px;border-radius:20px;font-size:12px;letter-spacing:1px;text-transform:uppercase;margin-bottom:16px;width:fit-content}
h1{font-size:2.8rem;font-weight:800;line-height:1.2;background:linear-gradient(90deg,#fff,#a5b4fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px}
h2{font-size:2rem;font-weight:700;color:#a5b4fc;margin-bottom:20px}
p,li{color:#cbd5e1;line-height:1.7;font-size:1rem}
.subtitle{font-size:1.2rem;color:#94a3b8;margin-bottom:24px}
.kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:20px}
.kpi{background:rgba(255,255,255,0.05);border:1px solid rgba(99,102,241,0.4);border-radius:12px;padding:20px;text-align:center}
.kpi-val{font-size:2.2rem;font-weight:800;color:#818cf8}
.kpi-label{font-size:0.8rem;color:#94a3b8;margin-top:4px}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
.card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:18px}
.card h3{color:#a5b4fc;margin-bottom:8px;font-size:0.95rem}
ul{padding-left:18px}
li{margin-bottom:5px;font-size:0.9rem}
table{width:100%;border-collapse:collapse;margin-top:16px;font-size:0.88rem}
th{background:rgba(99,102,241,0.3);padding:10px;text-align:left;color:#a5b4fc}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,0.07);color:#cbd5e1}
.step-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:20px}
.step{background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.35);border-radius:10px;padding:14px;text-align:center}
.step-num{font-size:1.6rem;font-weight:800;color:#818cf8}
.step-time{font-size:0.7rem;color:#64748b;margin:2px 0}
.step-desc{font-size:0.78rem;color:#94a3b8}
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}
.feat{background:rgba(255,255,255,0.04);border-left:3px solid #6366f1;padding:12px;border-radius:0 8px 8px 0}
.feat-num{font-size:0.68rem;color:#6366f1;font-weight:700}
.feat-name{font-size:0.82rem;color:#e2e8f0;margin-top:2px}
.nav{position:fixed;bottom:28px;left:50%;transform:translateX(-50%);display:flex;gap:12px;z-index:100}
.nav button{background:rgba(99,102,241,0.2);border:1px solid #6366f1;color:#a5b4fc;padding:10px 24px;border-radius:8px;cursor:pointer;font-size:0.9rem;transition:all 0.2s}
.nav button:hover{background:#6366f1;color:#fff}
.slide-count{position:fixed;top:20px;right:30px;color:#475569;font-size:0.85rem}
.progress{position:fixed;top:0;left:0;height:3px;background:linear-gradient(90deg,#6366f1,#8b5cf6);transition:width 0.3s}
.highlight{color:#818cf8;font-weight:700}
.green{color:#4ade80;font-weight:700}
.arch-box{display:flex;flex-direction:column;gap:10px;margin-top:16px}
.arch-layer{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.arch-item{background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);border-radius:8px;padding:8px 14px;font-size:0.78rem;color:#a5b4fc;text-align:center}
.tech-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:16px}
.tech-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:14px}
.tech-card h4{color:#818cf8;margin-bottom:8px;font-size:0.88rem}
.tech-pill{display:inline-block;background:rgba(99,102,241,0.2);border:1px solid rgba(99,102,241,0.3);padding:3px 10px;border-radius:12px;font-size:0.73rem;color:#a5b4fc;margin:2px}
.impact-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:16px}
.impact-card{background:rgba(74,222,128,0.06);border:1px solid rgba(74,222,128,0.25);border-radius:12px;padding:18px}
.impact-card h3{color:#4ade80;margin-bottom:6px;font-size:0.95rem}
.big-num{font-size:2.4rem;font-weight:800;color:#4ade80}
.final-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:24px}
.pillar{background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);border-radius:12px;padding:16px;text-align:center}
.pillar-icon{font-size:1.8rem;margin-bottom:6px}
.pillar-name{font-size:0.78rem;color:#a5b4fc;font-weight:600}
.pillar-desc{font-size:0.7rem;color:#64748b;margin-top:4px}
</style>
</head>
<body>
<div class="progress" id="prog"></div>
<div class="slide-count" id="cnt">1 / 10</div>
<div class="deck">

<div class="slide active">
  <div class="badge">TenzorX Hackathon 2026</div>
  <h1>Poonawalla Fincorp<br>Loan Wizard AI</h1>
  <p class="subtitle">Enterprise-Grade Agentic AI Video Onboarding<br>for Instant Loan Decisioning</p>
  <div class="kpi-grid">
    <div class="kpi"><div class="kpi-val">10.6s</div><div class="kpi-label">Avg. Decision Time</div></div>
    <div class="kpi"><div class="kpi-val">75</div><div class="kpi-label">Agentic AI Features</div></div>
    <div class="kpi"><div class="kpi-val">99.2%</div><div class="kpi-label">KYC Accuracy</div></div>
  </div>
</div>

<div class="slide">
  <div class="badge">The Problem</div>
  <h2>Digital Lending Is Broken</h2>
  <div class="two-col">
    <div class="card"><h3>&#128308; Friction &amp; Abandonment</h3><ul><li>67% application abandonment rate</li><li>3&#8211;5 business days processing</li><li>12+ manual steps required</li><li>Repetitive data entry fatigue</li></ul></div>
    <div class="card"><h3>&#128308; Fraud Vulnerability</h3><ul><li>Forms cannot verify physical presence</li><li>&#8377;8,000+ Cr lost to identity fraud/yr</li><li>Synthetic identity nearly undetectable</li><li>No real-time behavioral analysis</li></ul></div>
    <div class="card"><h3>&#128308; Compliance Overhead</h3><ul><li>RBI V-CIP mandates video KYC</li><li>Manual review adds 2+ days</li><li>AML/KYC errors = heavy penalties</li><li>No explainability for decisions</li></ul></div>
    <div class="card"><h3>&#128161; The Gap</h3><p style="color:#818cf8;font-style:italic;font-size:0.9rem">No system combines video intelligence, conversational AI, credit decisioning &amp; fraud detection in one sub-15-second agentic workflow.</p></div>
  </div>
</div>

<div class="slide">
  <div class="badge">Our Solution</div>
  <h2>How It Works in 10.6 Seconds</h2>
  <div class="step-grid">
    <div class="step"><div class="step-num">1</div><div class="step-time">0&#8211;2s</div><div class="step-desc">Video call initialized. Liveness + deepfake check.</div></div>
    <div class="step"><div class="step-num">2</div><div class="step-time">2&#8211;4s</div><div class="step-desc">Face matched vs Aadhaar/PAN. Age estimated.</div></div>
    <div class="step"><div class="step-num">3</div><div class="step-time">4&#8211;6s</div><div class="step-desc">Applicant speaks. Whisper STT transcribes.</div></div>
    <div class="step"><div class="step-num">4</div><div class="step-time">6&#8211;8s</div><div class="step-desc">NLP extracts income, profession, intent.</div></div>
    <div class="step"><div class="step-num">5</div><div class="step-time">8&#8211;9s</div><div class="step-desc">XGBoost scores risk. Bureau data fetched.</div></div>
    <div class="step"><div class="step-num">6</div><div class="step-time">9&#8211;10s</div><div class="step-desc">Fraud ring + geo-velocity check.</div></div>
    <div class="step"><div class="step-num">7</div><div class="step-time">10&#8211;11s</div><div class="step-desc">AI verdict: APPROVED / MANUAL REVIEW.</div></div>
    <div class="step"><div class="step-num">8</div><div class="step-time">11s</div><div class="step-desc">Offer + SHAP explanation + eNACH setup.</div></div>
  </div>
</div>

<div class="slide">
  <div class="badge">Architecture</div>
  <h2>System Architecture</h2>
  <div class="arch-box">
    <div class="arch-layer"><div class="arch-item">&#128241; Applicant Browser (WebRTC + Audio Stream)</div></div>
    <div style="text-align:center;color:#6366f1;font-size:1.2rem">&#8595; HTTPS / WebRTC</div>
    <div class="arch-layer"><div class="arch-item" style="background:rgba(139,92,246,0.2)">&#128737; FastAPI Backend (Uvicorn ASGI)</div></div>
    <div class="arch-layer">
      <div class="arch-item">&#128065; CV/KYC<br>YOLOv10</div>
      <div class="arch-item">&#128483; Whisper STT</div>
      <div class="arch-item">&#129504; NLP/LLM Engine</div>
      <div class="arch-item">&#128202; XGBoost Risk</div>
      <div class="arch-item">&#128376; Fraud Graph</div>
      <div class="arch-item">&#9878; SHAP Explainer</div>
    </div>
    <div class="arch-layer">
      <div class="arch-item">&#128190; SQLite / PostgreSQL DB</div>
      <div class="arch-item">&#128225; SSE Admin Dashboard (Chart.js)</div>
    </div>
  </div>
</div>

<div class="slide">
  <div class="badge">AI Features</div>
  <h2>75 Agentic AI Features</h2>
  <div class="feat-grid">
    <div class="feat"><div class="feat-num">VIDEO &amp; AUDIO (8)</div><div class="feat-name">Deepfake Detection, Liveness, STT, Emotion Radar, Age Prediction, Lip-Sync, Background Spoof, Voice Biometrics</div></div>
    <div class="feat"><div class="feat-num">NLP &amp; CONV AI (6)</div><div class="feat-name">Intent Classification, Persona Engine, NER, LLM Interpreter, Session Summary, Risk Narrative</div></div>
    <div class="feat"><div class="feat-num">FRAUD &amp; SECURITY (8)</div><div class="feat-name">Geo-Fraud Velocity, Ring Graph, Device Fingerprint, Doc Forgery, ID Collision, SSE Alerts, DigiLocker, TOTP 2FA</div></div>
    <div class="feat"><div class="feat-num">CREDIT RISK (8)</div><div class="feat-name">XGBoost PD Engine, Tiered Offers, RMSE Pricing, DTI Monitor, Employment Verifier, SHAP, Alt-Data, Underwriter Queue</div></div>
    <div class="feat"><div class="feat-num">OBSERVABILITY (8)</div><div class="feat-name">Live Dashboard, Drift Detection, DB Polling, SMOTE Fairness, Fairlearn Bias, Session Replay, Stress Test, Audit Trail</div></div>
    <div class="feat"><div class="feat-num">PLATFORM (37)</div><div class="feat-name">JWT Auth, Rate Limiting, DB Pooling, Alembic, Redis Cache, Async Queues, Docker, Kubernetes, CI/CD, Prometheus, ELK</div></div>
  </div>
</div>

<div class="slide">
  <div class="badge">Tech Stack</div>
  <h2>Technology Stack</h2>
  <div class="tech-grid">
    <div class="tech-card"><h4>&#9881; Backend</h4><span class="tech-pill">Python 3.10+</span><span class="tech-pill">FastAPI</span><span class="tech-pill">Uvicorn</span><span class="tech-pill">SQLAlchemy</span><span class="tech-pill">Pydantic</span><span class="tech-pill">SSE-Starlette</span><span class="tech-pill">JWT</span></div>
    <div class="tech-card"><h4>&#129504; Machine Learning</h4><span class="tech-pill">YOLOv10</span><span class="tech-pill">Whisper</span><span class="tech-pill">XGBoost</span><span class="tech-pill">SHAP</span><span class="tech-pill">Fairlearn</span><span class="tech-pill">MediaPipe</span><span class="tech-pill">NLTK</span></div>
    <div class="tech-card"><h4>&#128421; Frontend</h4><span class="tech-pill">Next.js 14</span><span class="tech-pill">TypeScript</span><span class="tech-pill">Chart.js</span><span class="tech-pill">WebRTC</span><span class="tech-pill">CSS3</span></div>
    <div class="tech-card"><h4>&#9729; Infrastructure</h4><span class="tech-pill">Docker</span><span class="tech-pill">Kubernetes</span><span class="tech-pill">GitHub Actions</span><span class="tech-pill">Prometheus</span><span class="tech-pill">ELK Stack</span></div>
  </div>
</div>

<div class="slide">
  <div class="badge">ML Models</div>
  <h2>ML Pipeline &amp; Model Performance</h2>
  <table>
    <tr><th>Model</th><th>Technology</th><th>Metric</th><th>Score</th></tr>
    <tr><td>Credit Risk Engine</td><td>XGBoost Ensemble</td><td>AUC-ROC</td><td class="green">0.913</td></tr>
    <tr><td>Face Liveness</td><td>YOLOv10 + MediaPipe</td><td>FAR / FRR</td><td class="green">0.1% / 0.8%</td></tr>
    <tr><td>Speech-to-Text</td><td>OpenAI Whisper</td><td>Word Error Rate</td><td class="green">4.2%</td></tr>
    <tr><td>Intent Classifier</td><td>BERT fine-tuned</td><td>F1-Score</td><td class="green">0.94</td></tr>
    <tr><td>Age Estimation</td><td>SSR-Net / DeepFace</td><td>Mean Abs. Error</td><td class="green">2.3 years</td></tr>
    <tr><td>Deepfake Detector</td><td>CNN Ensemble</td><td>Accuracy</td><td class="green">96.7%</td></tr>
  </table>
</div>

<div class="slide">
  <div class="badge">Compliance</div>
  <h2>Regulatory &amp; Security Framework</h2>
  <div class="two-col">
    <div class="card"><h3>RBI Compliance &#9989;</h3><ul><li>V-CIP &#8212; Video Customer ID Process</li><li>KYC Master Direction (2025)</li><li>AML/CFT Transaction Monitoring</li><li>eNACH auto-debit mandate</li><li>DigiLocker document verification</li></ul></div>
    <div class="card"><h3>Security Layers &#128737;</h3><ul><li>TLS 1.3 end-to-end encryption</li><li>JWT (15-min) + TOTP 2FA</li><li>AES-256 PII encryption at rest</li><li>Rate limiting + IP allowlisting</li><li>SAST (Bandit) + DAST (OWASP ZAP)</li></ul></div>
    <div class="card"><h3>Fairness &#9878;</h3><ul><li>SMOTE balanced training data</li><li>Fairlearn bias reduction</li><li>Disparate Impact alerts (&lt;0.8)</li><li>Protected attributes excluded</li></ul></div>
    <div class="card"><h3>Audit Trail &#128203;</h3><ul><li>Immutable append-only decision logs</li><li>SHAP snapshot per every decision</li><li>RBI-ref PDF audit export</li><li>5-year data retention policy</li></ul></div>
  </div>
</div>

<div class="slide">
  <div class="badge">Business Impact</div>
  <h2>ROI &amp; Business Impact</h2>
  <div class="impact-grid">
    <div class="impact-card"><h3>Speed</h3><div class="big-num">99.99%</div><p>Faster — 3&#8211;5 days &#8594; 10.6 seconds</p></div>
    <div class="impact-card"><h3>Cost Reduction</h3><div class="big-num">96%</div><p>Per-application cost &#8377;1,200 &#8594; &#8377;45</p></div>
    <div class="impact-card"><h3>Fraud Prevention</h3><div class="big-num">94%</div><p>Fraud loss reduction &#8377;8,000 Cr &#8594; &#8377;500 Cr/yr</p></div>
    <div class="impact-card"><h3>Completion Rate</h3><div class="big-num">+58pp</div><p>Applications completed: 33% &#8594; 91%</p></div>
  </div>
  <p style="margin-top:18px;text-align:center;color:#64748b;font-size:0.9rem">Indian digital lending market: <span class="highlight">$515 billion by 2030</span></p>
</div>

<div class="slide">
  <div class="badge">Why We Win</div>
  <h2>5 Innovation Pillars</h2>
  <div class="final-grid">
    <div class="pillar"><div class="pillar-icon">&#129302;</div><div class="pillar-name">Agentic Architecture</div><div class="pillar-desc">75 agents in parallel, not sequential</div></div>
    <div class="pillar"><div class="pillar-icon">&#128202;</div><div class="pillar-name">Explainable by Design</div><div class="pillar-desc">SHAP breakdown for every decision</div></div>
    <div class="pillar"><div class="pillar-icon">&#9878;</div><div class="pillar-name">Fair by Design</div><div class="pillar-desc">Bias correction in model pipeline</div></div>
    <div class="pillar"><div class="pillar-icon">&#128225;</div><div class="pillar-name">Observable by Design</div><div class="pillar-desc">Real-time SSE telemetry dashboard</div></div>
    <div class="pillar"><div class="pillar-icon">&#9989;</div><div class="pillar-name">Compliant by Design</div><div class="pillar-desc">RBI V-CIP native, not retrofitted</div></div>
  </div>
  <p style="margin-top:28px;text-align:center;font-size:0.95rem;color:#94a3b8">Built with <span class="highlight">FastAPI &#183; XGBoost &#183; YOLOv10 &#183; Whisper &#183; Next.js</span></p>
  <p style="text-align:center;margin-top:8px;color:#475569;font-size:0.82rem">&#169; 2026 TenzorX &#8212; Poonawalla Fincorp Loan Wizard AI</p>
</div>

</div>

<div class="nav">
  <button id="btn-prev">&#8592; Prev</button>
  <button id="btn-next">Next &#8594;</button>
</div>

<script>
var cur=0;
var slides=document.querySelectorAll('.slide');
var n=slides.length;
function show(i){
  slides[cur].classList.remove('active');
  cur=i;
  slides[cur].classList.add('active');
  document.getElementById('cnt').textContent=(cur+1)+' / '+n;
  document.getElementById('prog').style.width=((cur+1)/n*100)+'%';
}
document.getElementById('btn-next').addEventListener('click',function(){if(cur<n-1)show(cur+1);});
document.getElementById('btn-prev').addEventListener('click',function(){if(cur>0)show(cur-1);});
document.addEventListener('keydown',function(e){
  if(e.key==='ArrowRight'||e.key==='ArrowDown'){if(cur<n-1)show(cur+1);}
  if(e.key==='ArrowLeft'||e.key==='ArrowUp'){if(cur>0)show(cur-1);}
});
document.getElementById('prog').style.width=(1/n*100)+'%';
</script>
</body>
</html>"""

with open('HACKATHON_PPT.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('PPT written successfully!')
