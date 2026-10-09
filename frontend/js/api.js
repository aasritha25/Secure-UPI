/**
 * REST API Client for Secure UPI
 */

const API = {
  async request(endpoint, options = {}) {
    const url = CONFIG.API_BASE + endpoint;
    const headers = options.headers || {};
    
    headers['Content-Type'] = 'application/json';
    const token = AuthStore.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const fetchOptions = {
      ...options,
      headers
    };

    if (options.body && typeof options.body === 'object') {
      fetchOptions.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, fetchOptions);
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401 && !endpoint.includes('/auth/login')) {
          AuthStore.clear();
          window.location.href = '/login';
        }
        throw new Error(data.error || data.message || `HTTP Error ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error(`API Error on ${endpoint}:`, error);
      throw error;
    }
  },

  // Auth APIs
  register(payload) {
    return this.request('/auth/register', { method: 'POST', body: payload });
  },
  login(payload) {
    return this.request('/auth/login', { method: 'POST', body: payload });
  },
  getProfile() {
    return this.request('/auth/profile', { method: 'GET' });
  },
  updateProfile(payload) {
    return this.request('/auth/profile', { method: 'PUT', body: payload });
  },

  // Transaction APIs
  createTransaction(payload) {
    return this.request('/transactions', { method: 'POST', body: payload });
  },
  getTransactions(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request('/transactions' + (query ? `?${query}` : ''), { method: 'GET' });
  },
  getTransactionDetail(id) {
    return this.request(`/transactions/${id}`, { method: 'GET' });
  },

  // ML Prediction APIs
  predictRisk(payload) {
    return this.request('/predict', { method: 'POST', body: payload });
  },
  getModelMetrics() {
    return this.request('/model/metrics', { method: 'GET' });
  },

  // Alerts APIs
  getAlerts() {
    return this.request('/alerts', { method: 'GET' });
  },
  resolveAlert(alertId, status = 'RESOLVED') {
    return this.request(`/alerts/${alertId}/resolve`, { method: 'PUT', body: { status } });
  },

  // Dashboard APIs
  getDashboardStats() {
    return this.request('/dashboard/stats', { method: 'GET' });
  },
  getDashboardCharts() {
    return this.request('/dashboard/charts', { method: 'GET' });
  },

  // Admin APIs
  getAdminStats() {
    return this.request('/admin/stats', { method: 'GET' });
  },
  getAdminUsers() {
    return this.request('/admin/users', { method: 'GET' });
  },
  getAdminTransactions(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request('/admin/transactions' + (query ? `?${query}` : ''), { method: 'GET' });
  },
  getAdminAlerts() {
    return this.request('/admin/alerts', { method: 'GET' });
  }
};
