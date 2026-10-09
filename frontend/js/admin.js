/**
 * Enterprise Admin Dashboard Controller
 */

let adminTimelineChart = null;
let adminRiskPieChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!AuthStore.isAuthenticated()) {
    window.location.href = '/login';
    return;
  }

  const user = AuthStore.getUser();
  if (!user || user.role !== 'admin') {
    UI.showToast('Access denied. Administrator privileges required.', 'danger');
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 800);
    return;
  }

  await loadAdminStats();
  await loadAdminTransactions();
  await loadAdminUsers();
  await loadModelMetrics();
  setupFilterHandlers();
});

async function loadAdminStats() {
  try {
    const data = await API.getAdminStats();
    const kpis = data.kpis;

    document.getElementById('adminTotalUsers').textContent = kpis.total_users;
    document.getElementById('adminTotalTxns').textContent = kpis.total_transactions;
    document.getElementById('adminLegitTxns').textContent = kpis.legitimate_transactions;
    document.getElementById('adminSuspiciousTxns').textContent = kpis.suspicious_transactions;
    document.getElementById('adminFraudTxns').textContent = kpis.fraudulent_transactions;
    document.getElementById('adminFraudPct').textContent = `${kpis.fraud_percentage}%`;
    document.getElementById('adminTotalVolume').textContent = UI.formatCurrency(kpis.total_volume_inr);
    document.getElementById('adminFraudIntercepted').textContent = UI.formatCurrency(kpis.fraud_volume_intercepted_inr);
    document.getElementById('adminTotalAlerts').textContent = kpis.total_alerts;

    // Render Admin Charts
    renderAdminCharts(data.charts);
  } catch (err) {
    console.error('Failed to load admin statistics:', err);
    UI.showToast('Failed to load admin metrics: ' + err.message, 'danger');
  }
}

function renderAdminCharts(chartData) {
  // 1. Multi-line Timeline Chart
  const timelineCtx = document.getElementById('adminTimelineChart');
  if (timelineCtx && window.Chart) {
    if (adminTimelineChart) adminTimelineChart.destroy();
    adminTimelineChart = new Chart(timelineCtx, {
      type: 'line',
      data: {
        labels: chartData.timeline.labels,
        datasets: [
          {
            label: 'Legitimate',
            data: chartData.timeline.legitimate,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.3
          },
          {
            label: 'Suspicious',
            data: chartData.timeline.suspicious,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            tension: 0.3
          },
          {
            label: 'Fraudulent (Blocked)',
            data: chartData.timeline.fraudulent,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    });
  }

  // 2. Risk Level Pie Chart
  const pieCtx = document.getElementById('adminRiskPieChart');
  if (pieCtx && window.Chart) {
    if (adminRiskPieChart) adminRiskPieChart.destroy();
    adminRiskPieChart = new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: chartData.risk_pie.labels,
        datasets: [{
          data: chartData.risk_pie.data,
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        cutout: '65%'
      }
    });
  }
}

async function loadAdminTransactions() {
  const tbody = document.getElementById('adminTransactionsTable');
  if (!tbody) return;

  const filters = {
    status: document.getElementById('filterStatus')?.value || 'ALL',
    risk_level: document.getElementById('filterRiskLevel')?.value || 'ALL',
    user: document.getElementById('filterUser')?.value.trim() || '',
    location: document.getElementById('filterLocation')?.value.trim() || '',
    min_amount: document.getElementById('filterMinAmount')?.value || '',
    max_amount: document.getElementById('filterMaxAmount')?.value || ''
  };

  try {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading transactions...</td></tr>`;
    const res = await API.getAdminTransactions(filters);
    const txns = res.transactions || [];

    if (txns.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-muted">No transactions matching selected filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = txns.map(t => `
      <tr>
        <td><span class="font-monospace text-primary fw-semibold">${t.transaction_id}</span></td>
        <td>
          <div class="fw-semibold">${t.user_name || `User #${t.user_id}`}</div>
          <div class="small text-muted">${t.user_email || ''}</div>
        </td>
        <td>
          <div class="fw-medium">${t.receiver_name}</div>
          <div class="small text-muted font-monospace">${t.receiver_id}</div>
        </td>
        <td class="fw-bold">${UI.formatCurrency(t.amount)}</td>
        <td>${t.location || 'Unknown'}</td>
        <td><span class="badge bg-light text-dark border font-monospace">${t.device_id || 'N/A'}</span></td>
        <td><span class="fw-bold">${t.risk_score}%</span></td>
        <td>${UI.renderRiskBadge(t.risk_level)}</td>
        <td>${UI.renderStatusBadge(t.status)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="inspectTransaction('${t.transaction_id}')">
            <i class="fas fa-search-plus"></i> Inspect
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-danger text-center py-3">Error: ${err.message}</td></tr>`;
  }
}

async function loadAdminUsers() {
  const tbody = document.getElementById('adminUsersTable');
  if (!tbody) return;

  try {
    const res = await API.getAdminUsers();
    const users = res.users || [];

    tbody.innerHTML = users.map(u => `
      <tr>
        <td>#${u.id}</td>
        <td class="fw-semibold">${u.name}</td>
        <td>${u.email}</td>
        <td>${u.phone}</td>
        <td><span class="badge ${u.role === 'admin' ? 'bg-dark' : 'bg-primary'}">${u.role.toUpperCase()}</span></td>
        <td class="fw-bold text-success">${UI.formatCurrency(u.account_balance)}</td>
        <td class="small text-muted">${UI.formatDate(u.created_at)}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load users:', err);
  }
}

async function loadModelMetrics() {
  try {
    const data = await API.getModelMetrics();
    const models = data.models || {};

    const tbody = document.getElementById('modelComparisonTable');
    if (tbody) {
      tbody.innerHTML = Object.entries(models).map(([name, m]) => {
        const isBest = name === data.selected_model;
        return `
          <tr class="${isBest ? 'table-primary fw-semibold' : ''}">
            <td>
              ${name} ${isBest ? '<span class="badge bg-success ms-2"><i class="fas fa-crown me-1"></i>Selected Best</span>' : ''}
            </td>
            <td>${(m.accuracy * 100).toFixed(2)}%</td>
            <td>${(m.precision * 100).toFixed(2)}%</td>
            <td>${(m.recall * 100).toFixed(2)}%</td>
            <td>${(m.f1_score * 100).toFixed(2)}%</td>
            <td>${m.roc_auc.toFixed(4)}</td>
            <td><span class="font-monospace small">[TN:${m.confusion_matrix[0]}, FP:${m.confusion_matrix[1]}, FN:${m.confusion_matrix[2]}, TP:${m.confusion_matrix[3]}]</span></td>
          </tr>
        `;
      }).join('');
    }

    // Render Feature Importances
    const bestModel = models[data.selected_model];
    if (bestModel && bestModel.feature_importances) {
      const topFeaturesContainer = document.getElementById('topFeaturesBarContainer');
      if (topFeaturesContainer) {
        const sorted = Object.entries(bestModel.feature_importances)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 8);

        topFeaturesContainer.innerHTML = sorted.map(([fname, val]) => `
          <div class="mb-2">
            <div class="d-flex justify-content-between small fw-semibold mb-1">
              <span>${fname.replace(/_/g, ' ').toUpperCase()}</span>
              <span>${(val * 100).toFixed(1)}%</span>
            </div>
            <div class="progress" style="height: 7px;">
              <div class="progress-bar bg-primary" style="width: ${Math.min(100, val * 250)}%"></div>
            </div>
          </div>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Failed to load model metrics:', err);
  }
}

function setupFilterHandlers() {
  const applyBtn = document.getElementById('applyFiltersBtn');
  const resetBtn = document.getElementById('resetFiltersBtn');

  if (applyBtn) {
    applyBtn.addEventListener('click', () => loadAdminTransactions());
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      document.getElementById('filterStatus').value = 'ALL';
      document.getElementById('filterRiskLevel').value = 'ALL';
      document.getElementById('filterUser').value = '';
      document.getElementById('filterLocation').value = '';
      document.getElementById('filterMinAmount').value = '';
      document.getElementById('filterMaxAmount').value = '';
      loadAdminTransactions();
    });
  }
}

async function inspectTransaction(txnId) {
  try {
    const res = await API.getTransactionDetail(txnId);
    const txn = res.transaction;
    const analysis = res.analysis;

    document.getElementById('inspectTxnId').textContent = txn.transaction_id;
    document.getElementById('inspectUser').textContent = `${txn.user_name} (${txn.user_email})`;
    document.getElementById('inspectReceiver').textContent = `${txn.receiver_name} (${txn.receiver_id})`;
    document.getElementById('inspectAmount').textContent = UI.formatCurrency(txn.amount);
    document.getElementById('inspectStatus').innerHTML = UI.renderStatusBadge(txn.status);
    document.getElementById('inspectRisk').innerHTML = UI.renderRiskBadge(txn.risk_level, txn.risk_score);
    document.getElementById('inspectLocation').textContent = txn.location;
    document.getElementById('inspectDevice').textContent = txn.device_id;
    document.getElementById('inspectTimestamp').textContent = UI.formatDate(txn.timestamp);

    const reasonsContainer = document.getElementById('inspectReasonsList');
    if (analysis && analysis.reasons && analysis.reasons.length > 0) {
      reasonsContainer.innerHTML = analysis.reasons.map(r => `<li>${r}</li>`).join('');
    } else {
      reasonsContainer.innerHTML = '<li>Standard baseline operational checks passed.</li>';
    }

    const modal = new bootstrap.Modal(document.getElementById('inspectTxnModal'));
    modal.show();
  } catch (err) {
    UI.showToast('Failed to inspect transaction: ' + err.message, 'danger');
  }
}
