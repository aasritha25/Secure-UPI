/**
 * Fraud & Security Alerts Management Controller
 */

let allAlertsData = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!AuthStore.isAuthenticated()) {
    window.location.href = '/login';
    return;
  }

  await loadAlerts();
  setupFilterListeners();
});

async function loadAlerts() {
  const container = document.getElementById('alertsListContainer');
  try {
    const data = await API.getAlerts();
    allAlertsData = data.alerts || [];

    // Update Counts
    const totalEl = document.getElementById('totalAlertsCount');
    const activeEl = document.getElementById('activeAlertsCount');
    const resolvedEl = document.getElementById('resolvedAlertsCount');

    if (totalEl) totalEl.textContent = data.total_alerts || allAlertsData.length;
    if (activeEl) activeEl.textContent = data.active_alerts || allAlertsData.filter(a => a.alert_status === 'ACTIVE').length;
    if (resolvedEl) resolvedEl.textContent = allAlertsData.filter(a => a.alert_status === 'RESOLVED').length;

    renderAlerts(allAlertsData);
  } catch (err) {
    console.error('Failed to load alerts:', err);
    if (container) {
      container.innerHTML = `<div class="alert alert-danger">Failed to load alerts: ${err.message}</div>`;
    }
  }
}

function renderAlerts(alerts) {
  const container = document.getElementById('alertsListContainer');
  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = `
      <div class="card p-5 text-center text-muted border-0 shadow-sm">
        <i class="fas fa-check-circle fs-1 text-success mb-3"></i>
        <h5>No Fraud Alerts Found</h5>
        <p class="mb-0">There are no security alerts matching your active criteria.</p>
      </div>`;
    return;
  }

  container.innerHTML = alerts.map(a => {
    const isHigh = a.severity === 'HIGH';
    const isMedium = a.severity === 'MEDIUM';
    const borderClass = isHigh ? 'border-danger' : (isMedium ? 'border-warning' : 'border-info');
    const badgeClass = a.alert_status === 'ACTIVE' ? 'bg-danger' : (a.alert_status === 'ACKNOWLEDGED' ? 'bg-warning text-dark' : 'bg-success');

    return `
      <div class="card mb-3 shadow-sm border-start border-4 ${borderClass}">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
              <span class="badge ${badgeClass} mb-2">${a.alert_status}</span>
              ${UI.renderRiskBadge(a.risk_level)}
              <h5 class="fw-bold mt-1 text-dark">${a.title}</h5>
            </div>
            <div class="text-end text-muted small">
              <div><i class="far fa-clock me-1"></i>${UI.formatDate(a.created_at)}</div>
              ${a.transaction_id ? `<div class="font-monospace text-primary fw-semibold mt-1">${a.transaction_id}</div>` : ''}
            </div>
          </div>
          <p class="card-text text-secondary mb-2">${a.message}</p>
          ${a.reason ? `
            <div class="p-2 bg-light rounded text-muted small mb-3">
              <strong><i class="fas fa-microchip text-primary me-1"></i>ML Detection Reason:</strong> ${a.reason}
            </div>` : ''}
          <div class="d-flex justify-content-between align-items-center pt-2 border-top">
            <span class="small text-muted">User: <strong class="text-dark">${a.user_name || 'Account Owner'}</strong></span>
            <div>
              ${a.alert_status === 'ACTIVE' ? `
                <button class="btn btn-sm btn-outline-warning me-2" onclick="handleResolveAlert(${a.id}, 'ACKNOWLEDGED')">
                  <i class="fas fa-eye me-1"></i>Acknowledge
                </button>
                <button class="btn btn-sm btn-success" onclick="handleResolveAlert(${a.id}, 'RESOLVED')">
                  <i class="fas fa-check me-1"></i>Resolve Alert
                </button>
              ` : `
                <span class="text-success small fw-semibold"><i class="fas fa-check-double me-1"></i>Resolved</span>
              `}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function setupFilterListeners() {
  const statusFilter = document.getElementById('alertStatusFilter');
  const severityFilter = document.getElementById('alertSeverityFilter');

  function applyFilters() {
    let filtered = [...allAlertsData];
    if (statusFilter && statusFilter.value !== 'ALL') {
      filtered = filtered.filter(a => a.alert_status === statusFilter.value);
    }
    if (severityFilter && severityFilter.value !== 'ALL') {
      filtered = filtered.filter(a => a.severity === severityFilter.value);
    }
    renderAlerts(filtered);
  }

  if (statusFilter) statusFilter.addEventListener('change', applyFilters);
  if (severityFilter) severityFilter.addEventListener('change', applyFilters);
}

async function handleResolveAlert(alertId, newStatus) {
  try {
    await API.resolveAlert(alertId, newStatus);
    UI.showToast(`Alert marked as ${newStatus}.`, 'success');
    await loadAlerts();
  } catch (err) {
    UI.showToast('Failed to update alert: ' + err.message, 'danger');
  }
}
