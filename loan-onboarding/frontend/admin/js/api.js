// ═══════════════════════════════════════════════════════════
// POONAWALLA LOAN WIZARD — SHARED API CLIENT
// ═══════════════════════════════════════════════════════════
const API_BASE = '';

const API = {
  async get(path) {
    try {
      const res = await fetch(`${API_BASE}${path}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) { toast(`API Error: ${e.message}`, 'error'); throw e; }
  },

  async post(path, body) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) { toast(`API Error: ${e.message}`, 'error'); throw e; }
  },

  async patch(path, body) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      return await res.json();
    } catch (e) { toast(`API Error: ${e.message}`, 'error'); throw e; }
  }
};

// Toast notifications
const toastEl = document.createElement('div');
toastEl.className = 'toast-container';
document.body.appendChild(toastEl);

function toast(msg, type = 'info', duration = 3500) {
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  t.innerHTML = `<span>${icons[type] || '📢'}</span> ${msg}`;
  toastEl.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(100%)'; t.style.transition = '0.3s'; setTimeout(() => t.remove(), 300); }, duration);
}

// Format helpers
function formatINR(n) {
  if (!n) return '₹0';
  return '₹' + Number(n).toLocaleString('en-IN');
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-IN', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' });
}

function getBadgeClass(decision) {
  const map = { 'APPROVED': 'green', 'REJECTED': 'red', 'REVIEW': 'orange', 'FRAUD': 'red', 'CLEAR': 'green', 'LOW': 'green', 'MEDIUM': 'orange', 'HIGH': 'red', 'active': 'blue', 'completed': 'green' };
  return `badge badge-${map[decision] || 'gray'}`;
}

function withLoading(el, fn) {
  const loader = document.createElement('div');
  loader.className = 'loading-overlay';
  loader.innerHTML = '<div class="spinner"></div>';
  el.style.position = 'relative';
  el.appendChild(loader);
  return fn().finally(() => loader.remove());
}
