/**
 * Customer Dashboard Controller & Chart.js Visualizations
 */

let spendingChartInstance = null;
let statusPieChartInstance = null;
let riskDistChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!AuthStore.isAuthenticated()) {
    window.location.href = '/login';
    return;
  }

  const user = AuthStore.getUser();
  if (user) {
    const greetingEl = document.getElementById('userGreeting');
    if (greetingEl) greetingEl.textContent = user.name;
  }

  await loadDashboardData();
  await loadDashboardCharts();
});

async function loadDashboardData() {
  try {
    const data = await API.getDashboardStats();
    const metrics = data.metrics;
    const user = data.user;
    const account = data.account;

    // Update Top Balance & KPIs
    const balanceEls = document.querySelectorAll('.user-balance-value');
    balanceEls.forEach(el => el.textContent = UI.formatCurrency(metrics.available_balance));

    const totalTxnEl = document.getElementById('metricTotalTxn');
    if (totalTxnEl) totalTxnEl.textContent = metrics.total_transactions;

    const legitTxnEl = document.getElementById('metricLegitTxn');
    if (legitTxnEl) legitTxnEl.textContent = metrics.successful_payments || metrics.successful_transactions;

    const suspiciousTxnEl = document.getElementById('metricSuspiciousTxn');
    if (suspiciousTxnEl) suspiciousTxnEl.textContent = metrics.suspicious_transactions;

    const fraudTxnEl = document.getElementById('metricFraudTxn');
    if (fraudTxnEl) fraudTxnEl.textContent = metrics.fraudulent_transactions;

    const avgRiskEl = document.getElementById('metricAvgRisk');
    if (avgRiskEl) avgRiskEl.textContent = `${metrics.average_risk_score}%`;

    // Security Status Indicator
    const secStatusEl = document.getElementById('securityStatusBadge');
    if (secStatusEl) {
      if (metrics.current_risk_status === 'SECURE') {
        secStatusEl.className = 'badge bg-success py-2 px-3';
        secStatusEl.innerHTML = '<i class="fas fa-shield-check me-1"></i> Account Safe & Monitored';
      } else if (metrics.current_risk_status === 'MODERATE_MONITORED') {
        secStatusEl.className = 'badge bg-warning text-dark py-2 px-3';
        secStatusEl.innerHTML = '<i class="fas fa-exclamation-circle me-1"></i> Suspicious Activity Detected';
      } else {
        secStatusEl.className = 'badge bg-danger py-2 px-3';
        secStatusEl.innerHTML = '<i class="fas fa-shield-virus me-1"></i> High Fraud Risk Intercepted';
      }
    }

    // Render Recent Transactions
    renderRecentTransactions(data.recent_transactions);

    // Render Recent Alerts
    renderRecentAlerts(data.recent_alerts);
  } catch (err) {
    console.error('Failed to load dashboard statistics:', err);
    UI.showToast('Unable to load dashboard data. ' + err.message, 'danger');
  }
}

function renderRecentTransactions(txns) {
  const tbody = document.getElementById('recentTransactionsTable');
  if (!tbody) return;

  if (!txns || txns.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No transactions found. Make your first simulated payment!</td></tr>`;
    return;
  }

  tbody.innerHTML = txns.map(t => `
    <tr>
      <td><span class="font-monospace fw-semibold text-primary">${t.transaction_id}</span></td>
      <td>
        <div class="fw-semibold">${t.receiver_name}</div>
        <div class="small text-muted font-monospace">${t.receiver_id}</div>
      </td>
      <td class="fw-bold">${UI.formatCurrency(t.amount)}</td>
      <td><span class="badge bg-light text-dark border">${t.transaction_type || 'P2P'}</span></td>
      <td>${UI.renderRiskBadge(t.risk_level, t.risk_score)}</td>
      <td>${UI.renderStatusBadge(t.status)}</td>
      <td class="small text-muted">${UI.formatDate(t.timestamp)}</td>
    </tr>
  `).join('');
}

function renderRecentAlerts(alerts) {
  const container = document.getElementById('recentAlertsContainer');
  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = `
      <div class="p-3 bg-light rounded text-center text-muted">
        <i class="fas fa-shield-alt text-success me-2"></i>No active security alerts for your account.
      </div>`;
    return;
  }

  container.innerHTML = alerts.map(a => `
    <div class="alert ${a.severity === 'HIGH' ? 'alert-danger' : 'alert-warning'} d-flex align-items-start gap-3 mb-2 shadow-sm">
      <i class="fas ${a.severity === 'HIGH' ? 'fa-ban' : 'fa-exclamation-triangle'} fs-4 mt-1"></i>
      <div class="flex-grow-1">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <strong class="fw-bold">${a.title}</strong>
          <span class="badge ${a.alert_status === 'ACTIVE' ? 'bg-danger' : 'bg-secondary'}">${a.alert_status}</span>
        </div>
        <p class="mb-1 small">${a.message}</p>
        ${a.reason ? `<div class="small text-muted fst-italic">Reason: ${a.reason}</div>` : ''}
        <div class="small text-muted mt-1">${UI.formatDate(a.created_at)}</div>
      </div>
    </div>
  `).join('');
}

async function loadDashboardCharts() {
  try {
    const data = await API.getDashboardCharts();

    // 1. Spending Trends Over Time
    const timelineCtx = document.getElementById('spendingTimelineChart');
    if (timelineCtx && window.Chart) {
      if (spendingChartInstance) spendingChartInstance.destroy();
      spendingChartInstance = new Chart(timelineCtx, {
        type: 'line',
        data: {
          labels: data.timeline.labels,
          datasets: [{
            label: 'Transaction Amount (₹)',
            data: data.timeline.spending,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.12)',
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: '#2563eb'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { callback: v => '₹' + v.toLocaleString('en-IN') }
            }
          }
        }
      });
    }

    // 2. Legitimate vs Suspicious vs Fraudulent Breakdown
    const statusPieCtx = document.getElementById('statusBreakdownChart');
    if (statusPieCtx && window.Chart) {
      if (statusPieChartInstance) statusPieChartInstance.destroy();
      statusPieChartInstance = new Chart(statusPieCtx, {
        type: 'doughnut',
        data: {
          labels: data.status_breakdown.labels,
          datasets: [{
            data: data.status_breakdown.data,
            backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom' }
          },
          cutout: '68%'
        }
      });
    }

    // 3. Risk Level Distribution
    const riskDistCtx = document.getElementById('riskDistributionChart');
    if (riskDistCtx && window.Chart) {
      if (riskDistChartInstance) riskDistChartInstance.destroy();
      const riskVals = Object.values(data.risk_distribution);
      riskDistChartInstance = new Chart(riskDistCtx, {
        type: 'bar',
        data: {
          labels: ['Low Risk (0-30)', 'Medium Risk (31-70)', 'High Risk (71-100)'],
          datasets: [{
            label: 'Transactions',
            data: riskVals,
            backgroundColor: ['rgba(16, 185, 129, 0.85)', 'rgba(245, 158, 11, 0.85)', 'rgba(239, 68, 68, 0.85)'],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
        }
      });
    }

  } catch (err) {
    console.error('Failed to load dashboard chart data:', err);
  }
}
