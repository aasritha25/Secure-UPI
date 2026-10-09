const state = {
  token: localStorage.getItem('secure_upi_token') || '',
  user: JSON.parse(localStorage.getItem('secure_upi_user') || 'null'),
  locale: localStorage.getItem('secure_upi_lang') || 'en',
  wallet: null,
  riskResult: null,
  authMode: 'login',
  lastScan: null,
};

const translations = {};
const navButtons = document.querySelectorAll('.nav-link');
const screens = document.querySelectorAll('.screen');
const authTabs = document.querySelectorAll('.tab-btn');

function getApiHeaders(extra = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...extra,
  };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  return headers;
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: getApiHeaders(options.headers || {}),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

async function loadTranslations(lang) {
  const response = await fetch(`/locales/${lang}.json`);
  const data = await response.json();
  translations[lang] = data;
  return data;
}

function t(key) {
  const dict = translations[state.locale] || {};
  return dict[key] || key;
}

function updateLanguageSelector() {
  document.getElementById('languageSelector').value = state.locale;
  document.getElementById('settingsLanguage').value = state.locale;
}

function setScreen(screenId) {
  screens.forEach((screen) => {
    screen.classList.toggle('active-screen', screen.id === screenId);
  });

  navButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.target === screenId);
  });
}

function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.dataset.i18n;
    el.textContent = t(key);
  });

  const map = {
    login: t('login'),
    register: t('register'),
    home: t('home'),
    dashboard: t('dashboard'),
    pay: t('pay'),
    transactions: t('transactions'),
    alerts: t('alerts'),
    profile: t('profile'),
    settings: t('settings'),
    voiceGuide: t('voiceGuide'),
  };

  Object.entries(map).forEach(([key, value]) => {
    const textNode = document.querySelector(`[data-i18n="${key}"]`);
    if (textNode) textNode.textContent = value;
  });

  document.title = 'SECURE UPI';
}

function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.remove('hidden');
  clearTimeout(showToast.timeoutId);
  showToast.timeoutId = setTimeout(() => toast.classList.add('hidden'), 2600);
}

function speakVoice(text) {
  if (!('speechSynthesis' in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  const langMap = {
    en: 'en-US',
    te: 'te-IN',
    hi: 'hi-IN',
  };
  utterance.lang = langMap[state.locale] || 'en-US';
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

function formatMoney(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function renderRecentTransactions(transactions) {
  const container = document.getElementById('recentTransactions');
  if (!transactions || !transactions.length) {
    container.innerHTML = '<div class="list-item">No transactions yet.</div>';
    return;
  }

  container.innerHTML = transactions.slice(0, 5).map((txn) => `
    <div class="list-item">
      <strong>${txn.receiver_name}</strong>
      <div>${formatMoney(txn.amount)} · ${txn.status}</div>
      <small>${txn.risk_level || 'LOW_RISK'} / ${txn.risk_percentage || 0}%</small>
    </div>
  `).join('');
}

function renderAlerts(alerts) {
  const container = document.getElementById('alertsList');
  if (!alerts || !alerts.length) {
    container.innerHTML = '<div class="list-item">No active alerts.</div>';
    return;
  }
  container.innerHTML = alerts.map((alert) => `
    <div class="list-item">
      <strong>${alert.title}</strong>
      <div>${alert.message}</div>
      <small>${alert.severity} · ${new Date(alert.created_at).toLocaleString()}</small>
    </div>
  `).join('');
}

function renderTransactionsTable(transactions) {
  const body = document.getElementById('transactionsTableBody');
  if (!transactions || !transactions.length) {
    body.innerHTML = '<tr><td colspan="6">No transactions found.</td></tr>';
    return;
  }

  body.innerHTML = transactions.map((txn) => `
    <tr>
      <td>${txn.transaction_id}</td>
      <td>${txn.receiver_name}</td>
      <td>${formatMoney(txn.amount)}</td>
      <td>${txn.risk_percentage || 0}%</td>
      <td>${txn.risk_level || 'LOW_RISK'}</td>
      <td>${txn.status}</td>
    </tr>
  `).join('');
}

function renderProfile(user, account) {
  document.getElementById('profileName').textContent = user.name;
  document.getElementById('profileEmail').textContent = user.email;
  document.getElementById('profilePhone').textContent = user.phone;
  document.getElementById('profileLanguage').textContent = user.language === 'te' ? 'తెలుగు' : user.language === 'hi' ? 'हिंदी' : 'English';
  document.getElementById('profileBalance').textContent = formatMoney(account?.balance || 0);
  document.getElementById('profileRole').textContent = user.role === 'admin' ? 'Admin' : 'Customer';
}

function renderDashboard(data) {
  const metrics = data.metrics || {};
  const user = data.user || state.user;
  state.user = user;
  state.wallet = data.account || state.wallet;
  localStorage.setItem('secure_upi_user', JSON.stringify(user));

  const balance = metrics.available_balance ?? state.wallet?.balance ?? 0;
  document.getElementById('balanceValue').textContent = formatMoney(balance);
  document.getElementById('settingsBalance').value = balance;
  document.getElementById('totalTxns').textContent = metrics.total_transactions || 0;
  document.getElementById('successTxns').textContent = metrics.successful_payments || 0;
  document.getElementById('blockedTxns').textContent = metrics.blocked_transactions || 0;
  document.getElementById('suspiciousTxns').textContent = metrics.suspicious_transactions || 0;
  document.getElementById('riskAlerts').textContent = metrics.current_risk_alerts || 0;

  renderRecentTransactions(data.recent_transactions || []);
  renderAlerts(data.alerts || []);
  renderProfile(user, state.wallet);
}

async function loadDashboard() {
  try {
    const data = await apiFetch('/dashboard');
    renderDashboard(data);
  } catch (error) {
    showToast(error.message);
  }
}

async function loadTransactions() {
  try {
    const data = await apiFetch('/transactions');
    renderTransactionsTable(data.transactions || []);
  } catch (error) {
    showToast(error.message);
  }
}

async function loadAlerts() {
  try {
    const data = await apiFetch('/alerts');
    renderAlerts(data.alerts || []);
  } catch (error) {
    showToast(error.message);
  }
}

function setLoggedInState(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem('secure_upi_token', token);
  localStorage.setItem('secure_upi_user', JSON.stringify(user));
  document.getElementById('logoutBtn').classList.remove('hidden');
  setScreen('dashboard');
  loadDashboard();
  loadTransactions();
  loadAlerts();
}

function logout() {
  state.token = '';
  state.user = null;
  state.wallet = null;
  localStorage.removeItem('secure_upi_token');
  localStorage.removeItem('secure_upi_user');
  document.getElementById('logoutBtn').classList.add('hidden');
  setScreen('landing');
  showToast('Logged out successfully');
}

async function handleLogin(event) {
  event.preventDefault();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;

  try {
    const data = await apiFetch('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    const user = data.user;
    setLoggedInState(data.access_token, user);
    showToast('Welcome back to SECURE UPI');
  } catch (error) {
    showToast(error.message);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const payload = {
    name: document.getElementById('regName').value.trim(),
    email: document.getElementById('regEmail').value.trim(),
    phone: document.getElementById('regPhone').value.trim(),
    password: document.getElementById('regPassword').value,
    confirm_password: document.getElementById('regConfirmPassword').value,
    initial_balance: Number(document.getElementById('regBalance').value || 100000),
    language: state.locale,
  };

  try {
    const data = await apiFetch('/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setLoggedInState(data.access_token, data.user);
    showToast('Account created successfully');
  } catch (error) {
    showToast(error.message);
  }
}

function updateRiskUI(result) {
  const riskCard = document.getElementById('riskCard');
  const scoreElement = document.getElementById('riskScoreValue');
  const levelElement = document.getElementById('riskLevelValue');
  const reasonText = document.getElementById('riskReasonText');
  const reasonsList = document.getElementById('riskReasonsList');

  riskCard.classList.remove('low-risk', 'medium-risk', 'high-risk');

  if (result.risk_level === 'HIGH_RISK') {
    riskCard.classList.add('high-risk');
  } else if (result.risk_level === 'MEDIUM_RISK') {
    riskCard.classList.add('medium-risk');
  } else {
    riskCard.classList.add('low-risk');
  }

  scoreElement.textContent = `${result.risk_percentage}%`;
  levelElement.textContent = result.risk_level.replace('_', ' ');
  reasonText.textContent = result.risk_level === 'LOW_RISK'
    ? 'Transaction appears safe.'
    : 'Suspicious activity detected. Please verify the receiver and transaction details.';

  reasonsList.innerHTML = (result.reasons || []).map((reason) => `<li>${reason}</li>`).join('');
}

function animateScan() {
  const stages = [...document.querySelectorAll('.scan-stage')];
  stages.forEach((stage, index) => {
    stage.classList.toggle('active', index === 0);
  });
  let step = 0;
  const interval = setInterval(() => {
    stages.forEach((stage, index) => stage.classList.toggle('active', index === step));
    step += 1;
    if (step === stages.length) {
      clearInterval(interval);
    }
  }, 800);
  return interval;
}

async function handlePaymentScan(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    receiver_name: document.getElementById('receiverName').value.trim(),
    receiver_id: document.getElementById('receiverId').value.trim(),
    amount: Number(document.getElementById('amount').value),
    note: document.getElementById('note').value.trim(),
    location: document.getElementById('location').value.trim(),
    device_id: document.getElementById('deviceId').value.trim(),
    transaction_frequency: 8,
    average_amount: 5000,
    time_since_last_transaction: 60,
  };

  if (!payload.receiver_id || !payload.amount) {
    showToast('Receiver and amount are required');
    return;
  }

  const panel = document.getElementById('scanResultPanel');
  panel.classList.remove('hidden');
  animateScan();

  try {
    const result = await apiFetch('/predict', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    state.riskResult = result;
    updateRiskUI(result);
    state.lastScan = { ...payload, analysis_id: result.analysis_id };
    speakVoice(result.risk_level === 'HIGH_RISK'
      ? 'Warning. This transaction has a high risk score. Please verify the receiver before continuing.'
      : result.risk_level === 'MEDIUM_RISK'
      ? 'This transaction is medium risk. Please verify the receiver before continuing.'
      : 'This transaction appears safe.'
    );
    setScreen('pay');
  } catch (error) {
    showToast(error.message);
  }
}

async function handleRiskContinue() {
  if (!state.lastScan || !state.riskResult) {
    showToast('Please scan a transaction first');
    return;
  }

  const body = {
    ...state.lastScan,
    analysis_id: state.riskResult.analysis_id,
    user_confirmed: true,
  };

  try {
    const result = await apiFetch('/payment/confirm', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    showToast('Payment successful. Transaction saved.');
    await loadDashboard();
    await loadTransactions();
    setScreen('dashboard');
    document.getElementById('paymentForm').reset();
    document.getElementById('scanResultPanel').classList.add('hidden');
    state.riskResult = null;
    state.lastScan = null;
    const receipt = result.transaction;
    console.log('Receipt', receipt);
  } catch (error) {
    showToast(error.message);
  }
}

function bindEvents() {
  navButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.target;
      setScreen(target);
    });
  });

  authTabs.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.authTab;
      state.authMode = tab;
      document.querySelectorAll('.tab-btn').forEach((item) => item.classList.toggle('active', item === btn));
      document.getElementById('loginForm').classList.toggle('active-auth-form', tab === 'login');
      document.getElementById('registerForm').classList.toggle('active-auth-form', tab === 'register');
    });
  });

  document.getElementById('showLoginBtn').addEventListener('click', () => {
    setScreen('auth');
    document.querySelector('[data-auth-tab="login"]').click();
  });

  document.getElementById('showRegisterBtn').addEventListener('click', () => {
    setScreen('auth');
    document.querySelector('[data-auth-tab="register"]').click();
  });

  document.getElementById('logoutBtn').addEventListener('click', logout);
  document.getElementById('loginForm').addEventListener('submit', handleLogin);
  document.getElementById('registerForm').addEventListener('submit', handleRegister);
  document.getElementById('paymentForm').addEventListener('submit', handlePaymentScan);
  document.getElementById('riskContinueBtn').addEventListener('click', handleRiskContinue);
  document.getElementById('riskCancelBtn').addEventListener('click', () => {
    document.getElementById('scanResultPanel').classList.add('hidden');
    showToast('Payment cancelled');
  });

  document.getElementById('voiceGuideBtn').addEventListener('click', () => {
    const msg = state.locale === 'te'
      ? 'దయచేసి కూడా రిసీవర్ మరియు మొత్తం పరిశీలించండి.'
      : state.locale === 'hi'
      ? 'कृपया प्राप्तकर्ता और राशि की पुष्टि करें।'
      : 'Please verify the receiver and amount before continuing.';
    speakVoice(msg);
  });

  document.getElementById('languageSelector').addEventListener('change', async (event) => {
    state.locale = event.target.value;
    localStorage.setItem('secure_upi_lang', state.locale);
    await loadTranslations(state.locale);
    updateLanguageSelector();
    applyTranslations();
    if (state.user) {
      try {
        await apiFetch('/settings', {
          method: 'POST',
          body: JSON.stringify({ language: state.locale }),
        });
      } catch (error) {
        console.warn(error);
      }
    }
  });

  document.getElementById('settingsLanguage').addEventListener('change', (event) => {
    state.locale = event.target.value;
    localStorage.setItem('secure_upi_lang', state.locale);
    updateLanguageSelector();
    loadTranslations(state.locale).then(applyTranslations);
  });

  document.getElementById('saveSettingsBtn').addEventListener('click', async () => {
    const payload = {
      language: state.locale,
      balance: Number(document.getElementById('settingsBalance').value || 0),
    };
    try {
      const result = await apiFetch('/settings', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      showToast(result.message || 'Settings updated');
      await loadDashboard();
    } catch (error) {
      showToast(error.message);
    }
  });

  document.getElementById('resetBalanceBtn').addEventListener('click', async () => {
    const nextBalance = Number(document.getElementById('settingsBalance').value || 100000);
    try {
      const result = await apiFetch('/settings', {
        method: 'POST',
        body: JSON.stringify({ language: state.locale, balance: nextBalance }),
      });
      showToast(result.message || 'Demo account balance updated.');
      await loadDashboard();
    } catch (error) {
      showToast(error.message);
    }
  });
}

async function bootstrap() {
  bindEvents();
  document.getElementById('languageSelector').value = state.locale;
  document.getElementById('settingsLanguage').value = state.locale;
  await loadTranslations(state.locale);
  applyTranslations();

  if (state.token && state.user) {
    document.getElementById('logoutBtn').classList.remove('hidden');
    setScreen('dashboard');
    loadDashboard();
    loadTransactions();
    loadAlerts();
  } else {
    setScreen('landing');
  }
}

bootstrap();
