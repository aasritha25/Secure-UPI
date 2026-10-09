/**
 * Global Configuration and Utility Helpers for Secure UPI Platform
 */

const CONFIG = {
  API_BASE: window.location.origin + '/api',
  TOKEN_KEY: 'secure_upi_jwt_token',
  USER_KEY: 'secure_upi_user_data',
  DEFAULT_LANGUAGE: 'en'
};

const AuthStore = {
  getToken() {
    return localStorage.getItem(CONFIG.TOKEN_KEY);
  },
  setToken(token) {
    localStorage.setItem(CONFIG.TOKEN_KEY, token);
  },
  getUser() {
    try {
      const data = localStorage.getItem(CONFIG.USER_KEY);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      return null;
    }
  },
  setUser(user) {
    localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(CONFIG.TOKEN_KEY);
    localStorage.removeItem(CONFIG.USER_KEY);
  },
  isAuthenticated() {
    return !!this.getToken();
  },
  isAdmin() {
    const user = this.getUser();
    return user && user.role === 'admin';
  }
};

const UI = {
  formatCurrency(amount) {
    const num = Number(amount) || 0;
    return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  formatDate(isoString) {
    if (!isoString) return 'N/A';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return isoString;
    }
  },
  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.position = 'fixed';
      container.style.top = '20px';
      container.style.right = '20px';
      container.style.zIndex = '9999';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgClass = type === 'success' ? 'bg-success' : (type === 'danger' || type === 'error' ? 'bg-danger' : (type === 'warning' ? 'bg-warning text-dark' : 'bg-primary'));
    toast.className = `toast align-items-center text-white ${bgClass} border-0 show mb-2 shadow`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body fw-medium">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 4500);
  },
  renderRiskBadge(riskLevel, riskScore) {
    const level = (riskLevel || 'LOW_RISK').toUpperCase();
    const score = riskScore !== undefined ? `${riskScore}%` : '';
    if (level === 'LOW_RISK' || level === 'LOW') {
      return `<span class="risk-badge low"><i class="fas fa-shield-alt"></i> Low Risk ${score}</span>`;
    } else if (level === 'MEDIUM_RISK' || level === 'MEDIUM') {
      return `<span class="risk-badge medium"><i class="fas fa-exclamation-triangle"></i> Medium Risk ${score}</span>`;
    } else {
      return `<span class="risk-badge high"><i class="fas fa-ban"></i> High Risk ${score}</span>`;
    }
  },
  renderStatusBadge(status) {
    const s = (status || 'SUCCESS').toUpperCase();
    if (s === 'SUCCESS' || s === 'APPROVED') {
      return `<span class="status-badge success"><i class="fas fa-check-circle"></i> Approved</span>`;
    } else if (s === 'FLAGGED_FOR_VERIFICATION' || s === 'FLAGGED') {
      return `<span class="status-badge flagged"><i class="fas fa-flag"></i> Flagged</span>`;
    } else if (s === 'BLOCKED') {
      return `<span class="status-badge blocked"><i class="fas fa-shield-virus"></i> Blocked</span>`;
    } else {
      return `<span class="status-badge failed">${s}</span>`;
    }
  }
};
