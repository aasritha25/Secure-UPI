/**
 * Transaction Simulator & Real-Time ML Fraud Detection Controller
 * Supports: Pay Through Mobile, Self Bank Transfer, SecureUPI Wallet, and UPI ID/QR.
 */

let currentPaymentMode = 'mobile';

document.addEventListener('DOMContentLoaded', async () => {
  if (!AuthStore.isAuthenticated()) {
    window.location.href = '/login';
    return;
  }

  const user = AuthStore.getUser();
  if (user) {
    const senderIdInput = document.getElementById('senderUserId');
    if (senderIdInput) senderIdInput.value = `${user.name} (${user.email})`;
  }

  // Check URL query param for default mode
  const urlParams = new URLSearchParams(window.location.search);
  const modeParam = urlParams.get('mode') || 'mobile';
  switchPaymentMode(modeParam);

  // Load latest balance
  await refreshBalance();

  setupScenarioButtons();
  setupFormHandlers();
});

async function refreshBalance() {
  try {
    const profile = await API.getProfile();
    if (profile.account) {
      document.querySelectorAll('.user-balance-value').forEach(el => {
        el.textContent = UI.formatCurrency(profile.account.balance);
      });
    }
  } catch (e) {
    console.error('Failed to load profile balance:', e);
  }
}

// Switch between UPI Payment Modes
function switchPaymentMode(mode) {
  currentPaymentMode = mode;
  document.querySelectorAll('#paymentModeTabs .mode-select-box, #paymentModeTabs button').forEach(btn => btn.classList.remove('active'));
  const activeTab = document.getElementById(`tab-${mode}`);
  if (activeTab) activeTab.classList.add('active');

  const headerTitle = document.getElementById('modeHeaderTitle');
  const headerDesc = document.getElementById('modeHeaderDesc');
  const container = document.getElementById('dynamicModeContainer');
  const receiverIdInput = document.getElementById('receiverId');
  const receiverNameInput = document.getElementById('receiverName');
  const txnTypeSelect = document.getElementById('txnType');

  if (mode === 'mobile') {
    headerTitle.innerHTML = '<i class="fas fa-mobile-screen text-primary me-2"></i>Pay Through Mobile Number';
    headerDesc.textContent = 'Enter beneficiary 10-digit mobile number or select a recent contact.';
    txnTypeSelect.value = 'P2P';
    container.innerHTML = `
      <div class="row g-3 align-items-center">
        <div class="col-md-6">
          <label class="form-label small fw-bold">Enter Mobile Number</label>
          <div class="input-group">
            <span class="input-group-text bg-white"><i class="fas fa-phone text-primary"></i> +91</span>
            <input type="tel" id="mobileNumberInput" class="form-control font-monospace" placeholder="9812345678" maxlength="10">
          </div>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-bold">Recent Contacts (One-Click Select):</label>
          <div class="d-flex flex-wrap gap-2">
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="selectContact('9812345678', 'Priya Patel')">
              <i class="fas fa-user me-1"></i> Priya Patel
            </button>
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="selectContact('9898765432', 'Rahul Verma')">
              <i class="fas fa-user me-1"></i> Rahul Verma
            </button>
          </div>
        </div>
      </div>
    `;

    const mobInput = document.getElementById('mobileNumberInput');
    if (mobInput) {
      mobInput.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        receiverIdInput.value = val ? `${val}@secureupi` : '';
        if (!receiverNameInput.value) receiverNameInput.value = `Mobile User (${val})`;
      });
    }

  } else if (mode === 'scan') {
    headerTitle.innerHTML = '<i class="fas fa-camera text-primary me-2"></i>Scan &amp; Pay (UPI QR Scanner)';
    headerDesc.textContent = 'Point camera at any UPI QR code or select a verified merchant QR to scan instantly.';
    txnTypeSelect.value = 'P2M';

    container.innerHTML = `
      <div class="row g-4 align-items-center">
        <!-- Live Scanner Viewfinder Column -->
        <div class="col-md-6 text-center">
          <div class="scanner-container mb-2">
            <div class="scanner-viewfinder position-relative">
              <video id="cameraScannerVideo" playsinline autoplay muted style="width: 100%; height: 100%; object-fit: cover; display: none;"></video>
              <div id="scannerFallbackVisual" class="text-center p-3 text-white">
                <i class="fas fa-qrcode fs-1 text-success mb-2"></i>
                <div class="small fw-semibold">Align UPI QR inside viewfinder</div>
                <div class="text-muted" style="font-size: 0.75rem;">Supports BharatQR, UPI QR, Paytm, PhonePe, GPay</div>
              </div>
              <div class="scanner-laser"></div>
              <div class="scanner-frame-corner scanner-frame-tl"></div>
              <div class="scanner-frame-corner scanner-frame-tr"></div>
              <div class="scanner-frame-corner scanner-frame-bl"></div>
              <div class="scanner-frame-corner scanner-frame-br"></div>
            </div>
          </div>

          <div class="d-flex justify-content-center gap-2">
            <button type="button" id="toggleCameraBtn" class="btn btn-sm btn-outline-dark" onclick="toggleCameraScanner()">
              <i class="fas fa-video me-1"></i> Start Device Camera
            </button>
            <label class="btn btn-sm btn-outline-secondary mb-0">
              <i class="fas fa-upload me-1"></i> Upload QR Image
              <input type="file" accept="image/*" style="display: none;" onchange="handleQRImageUpload(event)">
            </label>
          </div>
        </div>

        <!-- Instant Merchant QR Preset Gallery -->
        <div class="col-md-6">
          <div class="small fw-bold text-muted text-uppercase mb-2">
            <i class="fas fa-store text-primary me-1"></i> Instant QR Gallery (Click to Scan):
          </div>

          <div class="d-flex flex-column gap-2">
            <div class="qr-merchant-card d-flex align-items-center justify-content-between" onclick="scanMerchantQR('cafe')">
              <div class="d-flex align-items-center gap-2">
                <div class="brand-logo-icon bg-light text-primary border" style="width: 36px; height: 36px; font-size: 1rem;">
                  <i class="fas fa-coffee"></i>
                </div>
                <div>
                  <div class="fw-bold small text-dark">Blue Tokai Specialty Coffee</div>
                  <div class="text-muted font-monospace" style="font-size: 0.75rem;">cafecoffee@upi | ₹450.00</div>
                </div>
              </div>
              <span class="badge bg-success-subtle text-success border"><i class="fas fa-qrcode me-1"></i>Scan</span>
            </div>

            <div class="qr-merchant-card d-flex align-items-center justify-content-between" onclick="scanMerchantQR('groceries')">
              <div class="d-flex align-items-center gap-2">
                <div class="brand-logo-icon bg-light text-success border" style="width: 36px; height: 36px; font-size: 1rem;">
                  <i class="fas fa-basket-shopping"></i>
                </div>
                <div>
                  <div class="fw-bold small text-dark">Nature Basket Supermarket</div>
                  <div class="text-muted font-monospace" style="font-size: 0.75rem;">naturebasket@upi | ₹2,450.00</div>
                </div>
              </div>
              <span class="badge bg-success-subtle text-success border"><i class="fas fa-qrcode me-1"></i>Scan</span>
            </div>

            <div class="qr-merchant-card d-flex align-items-center justify-content-between" onclick="scanMerchantQR('electricity')">
              <div class="d-flex align-items-center gap-2">
                <div class="brand-logo-icon bg-light text-warning border" style="width: 36px; height: 36px; font-size: 1rem;">
                  <i class="fas fa-bolt"></i>
                </div>
                <div>
                  <div class="fw-bold small text-dark">TSSPDCL Electricity Utility Bill</div>
                  <div class="text-muted font-monospace" style="font-size: 0.75rem;">tsspdcl.bill@upi | ₹1,850.00</div>
                </div>
              </div>
              <span class="badge bg-success-subtle text-success border"><i class="fas fa-qrcode me-1"></i>Scan</span>
            </div>

            <div class="qr-merchant-card d-flex align-items-center justify-content-between border-danger" onclick="scanMerchantQR('suspicious_crypto')">
              <div class="d-flex align-items-center gap-2">
                <div class="brand-logo-icon bg-danger text-white" style="width: 36px; height: 36px; font-size: 1rem;">
                  <i class="fas fa-triangle-exclamation"></i>
                </div>
                <div>
                  <div class="fw-bold small text-danger">Unverified Night Crypto QR (Test ML)</div>
                  <div class="text-danger font-monospace" style="font-size: 0.75rem;">unverified.drain88@ybl | ₹85,000.00</div>
                </div>
              </div>
              <span class="badge bg-danger text-white"><i class="fas fa-shield-virus me-1"></i>Test Fraud</span>
            </div>
          </div>

        </div>
      </div>
    `;

  } else if (mode === 'self') {
    headerTitle.innerHTML = '<i class="fas fa-building-columns text-success me-2"></i>Self Bank Account Transfer';
    headerDesc.textContent = 'Transfer funds between your own linked bank accounts with zero transaction fees.';
    txnTypeSelect.value = 'P2P';
    receiverIdInput.value = 'self.icici@secureupi';
    receiverNameInput.value = 'My ICICI Salary Account (Self)';
    container.innerHTML = `
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label small fw-bold">Transfer From (Debit):</label>
          <div class="p-2 border rounded bg-white">
            <div class="fw-bold small text-dark"><i class="fas fa-building-columns text-primary me-2"></i>State Bank of India (**** 4829)</div>
            <div class="small text-muted">Primary Linked Savings Account</div>
          </div>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-bold">Transfer To (Credit):</label>
          <select id="selfToAccount" class="form-select form-select-sm" onchange="updateSelfTransferAccount(this.value)">
            <option value="icici">ICICI Bank Ltd (**** 8892) - Salary Account</option>
            <option value="hdfc">HDFC Bank Ltd (**** 1145) - Savings Account</option>
          </select>
        </div>
      </div>
    `;

  } else if (mode === 'wallet') {
    headerTitle.innerHTML = '<i class="fas fa-wallet text-info me-2"></i>SecureUPI Digital Wallet';
    headerDesc.textContent = 'Pay instantly using your digital wallet balance without UPI PIN for fast checkouts.';
    txnTypeSelect.value = 'P2M';
    receiverIdInput.value = 'wallet.merchant@secureupi';
    receiverNameInput.value = 'Fast Checkout Merchant';
    container.innerHTML = `
      <div class="p-3 bg-info-subtle rounded border border-info-subtle d-flex justify-content-between align-items-center">
        <div>
          <div class="fw-bold text-dark"><i class="fas fa-wallet text-info me-2"></i>SecureUPI Digital Wallet Balance</div>
          <div class="small text-muted">Instant 1-Click Payment Mode (No PIN Required for &lt; ₹2,000)</div>
        </div>
        <div class="text-end">
          <span class="user-balance-value fs-5 fw-bold text-dark">₹0.00</span>
        </div>
      </div>
    `;

  } else { // vpa / qr
    headerTitle.innerHTML = '<i class="fas fa-qrcode text-warning me-2"></i>Pay to UPI ID / VPA &amp; QR Code';
    headerDesc.textContent = 'Enter any standard UPI Virtual Payment Address (e.g. merchant@okhdfcbank or user@ybl).';
    container.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <span class="small text-muted">Enter any valid UPI VPA handle or merchant identifier below.</span>
        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="simulateQRScan()">
          <i class="fas fa-camera me-1"></i> Scan QR Code (Simulated)
        </button>
      </div>
    `;
  }
}

function selectContact(phone, name) {
  const mobInput = document.getElementById('mobileNumberInput');
  if (mobInput) mobInput.value = phone;
  document.getElementById('receiverId').value = `${phone}@secureupi`;
  document.getElementById('receiverName').value = name;
  UI.showToast(`Contact selected: ${name} (${phone})`, 'info');
}

function updateSelfTransferAccount(val) {
  if (val === 'hdfc') {
    document.getElementById('receiverId').value = 'self.hdfc@secureupi';
    document.getElementById('receiverName').value = 'My HDFC Bank Savings Account (Self)';
  } else {
    document.getElementById('receiverId').value = 'self.icici@secureupi';
    document.getElementById('receiverName').value = 'My ICICI Salary Account (Self)';
  }
}

let scannerStream = null;

async function toggleCameraScanner() {
  const video = document.getElementById('cameraScannerVideo');
  const fallback = document.getElementById('scannerFallbackVisual');
  const btn = document.getElementById('toggleCameraBtn');
  
  if (scannerStream) {
    // Stop camera stream
    scannerStream.getTracks().forEach(track => track.stop());
    scannerStream = null;
    if (video) video.style.display = 'none';
    if (fallback) fallback.style.display = 'block';
    if (btn) {
      btn.innerHTML = '<i class="fas fa-video me-1"></i> Start Device Camera';
      btn.className = 'btn btn-sm btn-outline-dark';
    }
    UI.showToast('Camera scanner turned off.', 'info');
    return;
  }

  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Camera device access is not supported by your current browser.');
    }
    
    scannerStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }
    });
    
    if (video) {
      video.srcObject = scannerStream;
      video.style.display = 'block';
      await video.play();
    }
    if (fallback) fallback.style.display = 'none';
    if (btn) {
      btn.innerHTML = '<i class="fas fa-video-slash me-1"></i> Stop Camera Scanner';
      btn.className = 'btn btn-sm btn-danger';
    }
    UI.showToast('Camera active! Point camera at any UPI QR code.', 'success');
  } catch (err) {
    console.warn('Camera stream warning:', err);
    UI.showToast('Camera could not be activated: ' + (err.message || 'Permission denied'), 'warning');
    if (fallback) fallback.style.display = 'block';
    if (video) video.style.display = 'none';
  }
}

function scanMerchantQR(type) {
  const presets = {
    cafe: {
      receiver_id: 'cafecoffee@upi',
      receiver_name: 'Blue Tokai Specialty Coffee',
      amount: 450,
      transaction_type: 'P2M',
      location: 'Hyderabad',
      device_id: 'DEV_ANDROID_14_HYD',
      time_of_day: 10,
      average_amount: 1200,
      transaction_frequency: 15,
      time_since_last_transaction: 180,
      failed_transactions: 0,
      transaction_velocity: 1.2,
      note: 'Morning espresso & pastry'
    },
    groceries: {
      receiver_id: 'naturebasket@upi',
      receiver_name: 'Nature Basket Supermarket',
      amount: 2450,
      transaction_type: 'P2M',
      location: 'Hyderabad',
      device_id: 'DEV_ANDROID_14_HYD',
      time_of_day: 18,
      average_amount: 1200,
      transaction_frequency: 15,
      time_since_last_transaction: 60,
      failed_transactions: 0,
      transaction_velocity: 1.5,
      note: 'Supermarket checkout'
    },
    electricity: {
      receiver_id: 'tsspdcl.bill@upi',
      receiver_name: 'TSSPDCL Electricity Utility Bill',
      amount: 1850,
      transaction_type: 'BILL_PAYMENT',
      location: 'Hyderabad',
      device_id: 'DEV_ANDROID_14_HYD',
      time_of_day: 14,
      average_amount: 1200,
      transaction_frequency: 15,
      time_since_last_transaction: 300,
      failed_transactions: 0,
      transaction_velocity: 1.0,
      note: 'Monthly Electricity Bill'
    },
    suspicious_crypto: {
      receiver_id: 'unverified.drain88@ybl',
      receiver_name: 'Unverified Night Crypto Gateway (Test ML)',
      amount: 85000,
      transaction_type: 'INVESTMENT',
      location: 'Kolkata',
      device_id: 'DEV_UNKNOWN_EMULATOR',
      time_of_day: 3,
      average_amount: 1200,
      transaction_frequency: 38,
      time_since_last_transaction: 4,
      failed_transactions: 3,
      transaction_velocity: 7.2,
      note: 'High-risk unverified QR code drain'
    }
  };

  const data = presets[type];
  if (!data) return;

  document.getElementById('receiverId').value = data.receiver_id;
  document.getElementById('receiverName').value = data.receiver_name;
  document.getElementById('txnAmount').value = data.amount;
  document.getElementById('txnType').value = data.transaction_type;
  document.getElementById('txnLocation').value = data.location;
  document.getElementById('deviceId').value = data.device_id;
  document.getElementById('timeOfDay').value = data.time_of_day;
  document.getElementById('avgAmount').value = data.average_amount;
  document.getElementById('txnFrequency').value = data.transaction_frequency;
  document.getElementById('timeSinceLast').value = data.time_since_last_transaction;
  document.getElementById('failedTxnCount').value = data.failed_transactions;
  document.getElementById('txnVelocity').value = data.transaction_velocity;
  document.getElementById('txnNote').value = data.note;

  UI.showToast(`QR Code Scanned: ${data.receiver_name} (₹${data.amount})`, type === 'suspicious_crypto' ? 'warning' : 'success');
}

function handleQRImageUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  UI.showToast(`Analyzing uploaded QR image: ${file.name}...`, 'info');

  setTimeout(() => {
    scanMerchantQR('groceries');
    UI.showToast(`Decoded QR Image successfully: Nature Basket Supermarket QR`, 'success');
  }, 600);
}

function simulateQRScan() {
  scanMerchantQR('groceries');
}

function openMyQrModal() {
  const user = AuthStore.getUser();
  if (!user) return;
  
  const vpa = `${user.phone || '9876543210'}@secureupi`;
  const name = user.name || 'Secure UPI User';
  const qrData = `upi://pay?pa=${encodeURIComponent(vpa)}&pn=${encodeURIComponent(name)}&cu=INR`;
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(qrData)}`;

  const modalName = document.getElementById('myQrUserName');
  const modalVpa = document.getElementById('myQrVpa');
  const modalImg = document.getElementById('myQrCodeImg');
  const downloadLink = document.getElementById('myQrDownloadBtn');

  if (modalName) modalName.textContent = name;
  if (modalVpa) modalVpa.textContent = vpa;
  if (modalImg) modalImg.src = qrUrl;
  if (downloadLink) {
    downloadLink.href = qrUrl;
    downloadLink.download = `${name.replace(/\s+/g, '_')}_UPI_QR.png`;
  }

  const modal = new bootstrap.Modal(document.getElementById('myQrCodeModal'));
  modal.show();
}

function copyMyUpiId() {
  const user = AuthStore.getUser();
  const vpa = user ? `${user.phone || '9876543210'}@secureupi` : 'demo@secureupi';
  navigator.clipboard.writeText(vpa).then(() => {
    UI.showToast(`Copied UPI ID: ${vpa} to clipboard!`, 'success');
  }).catch(() => {
    UI.showToast(`UPI ID: ${vpa}`, 'info');
  });
}

// Demo Scenario Quick-Fill Buttons
function setupScenarioButtons() {
  const scenarios = {
    legit: {
      receiver_id: 'cafe.bluetokai@upi',
      receiver_name: 'Blue Tokai Specialty Coffee',
      amount: 450,
      transaction_type: 'P2M',
      location: 'Hyderabad',
      device_id: 'DEV_ANDROID_14_HYD',
      time_of_day: 10,
      average_amount: 1200,
      transaction_frequency: 15,
      time_since_last_transaction: 180,
      failed_transactions: 0,
      transaction_velocity: 1.2,
      note: 'Morning coffee & breakfast'
    },
    suspicious: {
      receiver_id: 'croma.retail@upi',
      receiver_name: 'Croma Electronics Megastore',
      amount: 19500,
      transaction_type: 'ONLINE_SHOPPING',
      location: 'Bengaluru',
      device_id: 'DEV_ANDROID_14_HYD',
      time_of_day: 16,
      average_amount: 1500,
      transaction_frequency: 12,
      time_since_last_transaction: 45,
      failed_transactions: 1,
      transaction_velocity: 2.8,
      note: 'Noise cancelling headphones purchase'
    },
    midnight_drain: {
      receiver_id: 'unverified.merchant88@ybl',
      receiver_name: 'Unknown Crypto Transfer Node',
      amount: 85000,
      transaction_type: 'INVESTMENT',
      location: 'Kolkata',
      device_id: 'DEV_UNKNOWN_EMULATOR',
      time_of_day: 3,
      average_amount: 1200,
      transaction_frequency: 35,
      time_since_last_transaction: 5,
      failed_transactions: 3,
      transaction_velocity: 6.5,
      note: 'Attempted midnight high-value wallet drain'
    },
    velocity_burst: {
      receiver_id: 'quick.p2p.node99@axl',
      receiver_name: 'Unverified Rapid Beneficiary',
      amount: 42000,
      transaction_type: 'P2P',
      location: 'Mumbai',
      device_id: 'DEV_UNKNOWN',
      time_of_day: 22,
      average_amount: 1500,
      transaction_frequency: 48,
      time_since_last_transaction: 1,
      failed_transactions: 4,
      transaction_velocity: 9.8,
      note: 'Rapid consecutive high-velocity transfers'
    }
  };

  document.querySelectorAll('[data-scenario]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const sKey = btn.getAttribute('data-scenario');
      const data = scenarios[sKey];
      if (!data) return;

      document.getElementById('receiverId').value = data.receiver_id;
      document.getElementById('receiverName').value = data.receiver_name;
      document.getElementById('txnAmount').value = data.amount;
      document.getElementById('txnType').value = data.transaction_type;
      document.getElementById('txnLocation').value = data.location;
      document.getElementById('deviceId').value = data.device_id;
      document.getElementById('timeOfDay').value = data.time_of_day;
      document.getElementById('avgAmount').value = data.average_amount;
      document.getElementById('txnFrequency').value = data.transaction_frequency;
      document.getElementById('timeSinceLast').value = data.time_since_last_transaction;
      document.getElementById('failedTxnCount').value = data.failed_transactions;
      document.getElementById('txnVelocity').value = data.transaction_velocity;
      document.getElementById('txnNote').value = data.note;

      UI.showToast(`Scenario loaded: ${btn.textContent.trim()}`, 'info');
    });
  });
}

function getFormData() {
  return {
    receiver_id: document.getElementById('receiverId').value.trim(),
    receiver_name: document.getElementById('receiverName').value.trim() || document.getElementById('receiverId').value.trim(),
    amount: parseFloat(document.getElementById('txnAmount').value) || 0,
    transaction_type: document.getElementById('txnType').value,
    location: document.getElementById('txnLocation').value.trim(),
    device_id: document.getElementById('deviceId').value.trim(),
    time_of_day: parseInt(document.getElementById('timeOfDay').value) || 12,
    average_amount: parseFloat(document.getElementById('avgAmount').value) || 1000,
    transaction_frequency: parseFloat(document.getElementById('txnFrequency').value) || 5,
    time_since_last_transaction: parseFloat(document.getElementById('timeSinceLast').value) || 60,
    failed_transactions: parseInt(document.getElementById('failedTxnCount').value) || 0,
    transaction_velocity: parseFloat(document.getElementById('txnVelocity').value) || 1.0,
    note: document.getElementById('txnNote').value.trim()
  };
}

function setupFormHandlers() {
  const transactionForm = document.getElementById('transactionForm');
  const checkRiskBtn = document.getElementById('checkRiskBtn');

  // 1. Live Pre-Payment ML Risk Analysis Button
  if (checkRiskBtn) {
    checkRiskBtn.addEventListener('click', async () => {
      const payload = getFormData();
      if (!payload.receiver_id || payload.amount <= 0) {
        UI.showToast('Please enter a valid receiver UPI ID and amount.', 'warning');
        return;
      }

      try {
        checkRiskBtn.disabled = true;
        checkRiskBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing with ML...';

        const result = await API.predictRisk(payload);
        displayRiskAnalysisModal(result, payload);
      } catch (err) {
        UI.showToast('ML Risk Analysis failed: ' + err.message, 'danger');
      } finally {
        checkRiskBtn.disabled = false;
        checkRiskBtn.innerHTML = '<i class="fas fa-brain me-2"></i>Run Real-Time ML Fraud Scan';
      }
    });
  }

  // 2. Direct Transaction Execution Form Submission
  if (transactionForm) {
    transactionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = getFormData();

      if (!payload.receiver_id || payload.amount <= 0) {
        UI.showToast('Please enter a valid receiver and amount.', 'warning');
        return;
      }

      const submitBtn = transactionForm.querySelector('button[type="submit"]');
      try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing UPI Payment...';

        const response = await API.createTransaction(payload);
        displayTransactionResultModal(response);
        await refreshBalance();
      } catch (err) {
        UI.showToast(err.message || 'Payment execution failed.', 'danger');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Submit Simulated UPI Transaction';
      }
    });
  }
}

// Display Pre-Payment ML Risk Modal
function displayRiskAnalysisModal(analysis, payload) {
  const modalEl = document.getElementById('riskAnalysisModal');
  if (!modalEl) return;

  const score = analysis.risk_score;
  const prob = (analysis.fraud_probability * 100).toFixed(2);
  const level = analysis.risk_level;

  document.getElementById('modalRiskScore').textContent = `${score}%`;
  document.getElementById('modalFraudProb').textContent = `${prob}%`;
  document.getElementById('modalModelUsed').textContent = analysis.model_used;

  const badgeContainer = document.getElementById('modalRiskBadge');
  badgeContainer.innerHTML = UI.renderRiskBadge(level, score);

  const meterBar = document.getElementById('modalRiskMeterBar');
  meterBar.style.width = `${score}%`;
  meterBar.className = `risk-meter-bar ${score <= 30 ? 'low' : (score <= 70 ? 'medium' : 'high')}`;

  const recEl = document.getElementById('modalRecommendation');
  recEl.textContent = analysis.recommendation;

  const reasonsList = document.getElementById('modalReasonsList');
  reasonsList.innerHTML = analysis.reasons.map(r => `<li class="mb-1"><i class="fas fa-info-circle text-primary me-2"></i>${r}</li>`).join('');

  // Feature Contributions Bar Chart
  const contribContainer = document.getElementById('modalFeatureContributions');
  if (analysis.feature_contributions && analysis.feature_contributions.length > 0) {
    contribContainer.innerHTML = analysis.feature_contributions.map(c => {
      const pct = Math.min(100, Math.round(c.impact * 100));
      const colorClass = c.contribution_level === 'High' ? 'high' : (c.contribution_level === 'Medium' ? 'medium' : 'low');
      return `
        <div class="contrib-row">
          <span style="min-width: 140px;" class="fw-semibold">${c.name}</span>
          <div class="contrib-bar-bg">
            <div class="contrib-bar-fill ${colorClass}" style="width: ${pct}%;"></div>
          </div>
          <span class="badge ${c.contribution_level === 'High' ? 'bg-danger' : (c.contribution_level === 'Medium' ? 'bg-warning text-dark' : 'bg-success')}">${c.contribution_level}</span>
        </div>
      `;
    }).join('');
  } else {
    contribContainer.innerHTML = '<div class="text-muted small">Standard baseline model weights applied.</div>';
  }

  // Setup proceed button in modal
  const proceedBtn = document.getElementById('modalProceedPaymentBtn');
  if (proceedBtn) {
    proceedBtn.onclick = async () => {
      const modalInstance = bootstrap.Modal.getInstance(modalEl);
      if (modalInstance) modalInstance.hide();
      
      try {
        const res = await API.createTransaction(payload);
        displayTransactionResultModal(res);
        await refreshBalance();
      } catch (e) {
        UI.showToast(e.message, 'danger');
      }
    };
  }

  const modal = new bootstrap.Modal(modalEl);
  modal.show();
}

// Display Final Transaction Result Modal
function displayTransactionResultModal(response) {
  const modalEl = document.getElementById('txnResultModal');
  if (!modalEl) return;

  const txn = response.transaction;
  document.getElementById('resTxnId').textContent = txn.transaction_id;
  document.getElementById('resAmount').textContent = UI.formatCurrency(txn.amount);
  document.getElementById('resReceiver').textContent = `${txn.receiver_name} (${txn.receiver_id})`;
  document.getElementById('resRiskScore').textContent = `${txn.risk_score}%`;
  document.getElementById('resStatusBadge').innerHTML = UI.renderStatusBadge(txn.status);
  document.getElementById('resRiskBadge').innerHTML = UI.renderRiskBadge(txn.risk_level, txn.risk_score);
  document.getElementById('resMessage').textContent = response.message;

  if (response.remaining_balance !== undefined) {
    document.getElementById('resRemainingBalance').textContent = UI.formatCurrency(response.remaining_balance);
  }

  const modal = new bootstrap.Modal(modalEl);
  modal.show();
}

// Check Balance Functions
function openCheckBalanceModal() {
  const pinStep = document.getElementById('pinEntryStep');
  const resStep = document.getElementById('balanceResultStep');
  const pinInput = document.getElementById('upiPinInput');
  if (pinStep) pinStep.style.display = 'block';
  if (resStep) resStep.style.display = 'none';
  if (pinInput) pinInput.value = '';
  const modal = new bootstrap.Modal(document.getElementById('checkBalanceModal'));
  modal.show();
}

async function verifyAndShowBalance() {
  const pin = document.getElementById('upiPinInput').value.trim();
  if (!pin || pin.length < 4) {
    UI.showToast('Please enter your 4 or 6 digit UPI PIN.', 'warning');
    return;
  }
  try {
    const res = await API.request('/auth/check-balance', { method: 'POST', body: { upi_pin: pin } });
    document.getElementById('modalRevealedBalance').textContent = UI.formatCurrency(res.available_balance);
    document.getElementById('modalBankDetails').textContent = `${res.bank_name} (${res.account_number_masked})`;
    document.getElementById('modalTimestamp').textContent = `Verified at ${UI.formatDate(res.checked_at)}`;
    document.getElementById('pinEntryStep').style.display = 'none';
    document.getElementById('balanceResultStep').style.display = 'block';
    UI.showToast('UPI PIN verified. Available balance displayed.', 'success');
  } catch (err) {
    UI.showToast(err.message || 'Invalid UPI PIN.', 'danger');
  }
}
