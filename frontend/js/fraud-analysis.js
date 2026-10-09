/**
 * Fraud Analysis & ML Explainability Controller
 */

let featureImportanceChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!AuthStore.isAuthenticated()) {
    window.location.href = '/login';
    return;
  }

  await loadModelEvaluationData();
  setupLiveSimulator();
});

async function loadModelEvaluationData() {
  try {
    const data = await API.getModelMetrics();
    const models = data.models || {};
    const bestModelName = data.selected_model;

    document.getElementById('analysisSelectedModelBadge').textContent = bestModelName;

    // Populate Comparative Model Cards
    const modelsContainer = document.getElementById('modelCardsContainer');
    if (modelsContainer) {
      modelsContainer.innerHTML = Object.entries(models).map(([name, m]) => {
        const isBest = name === bestModelName;
        return `
          <div class="col-md-4 mb-3">
            <div class="card h-100 shadow-sm ${isBest ? 'border-primary border-2' : ''}">
              <div class="card-header d-flex justify-content-between align-items-center bg-white py-3">
                <h6 class="fw-bold mb-0">${name}</h6>
                ${isBest ? '<span class="badge bg-primary">Best Model</span>' : ''}
              </div>
              <div class="card-body">
                <div class="d-flex justify-content-between mb-2">
                  <span class="text-muted">Accuracy:</span>
                  <span class="fw-bold">${(m.accuracy * 100).toFixed(2)}%</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                  <span class="text-muted">Precision:</span>
                  <span class="fw-bold text-success">${(m.precision * 100).toFixed(2)}%</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                  <span class="text-muted">Recall:</span>
                  <span class="fw-bold text-primary">${(m.recall * 100).toFixed(2)}%</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                  <span class="text-muted">F1-Score:</span>
                  <span class="fw-bold text-info">${(m.f1_score * 100).toFixed(2)}%</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                  <span class="text-muted">ROC-AUC:</span>
                  <span class="fw-bold text-purple">${m.roc_auc.toFixed(4)}</span>
                </div>
                <div class="pt-2 border-top small text-muted">
                  <strong>Confusion Matrix:</strong><br>
                  TN: ${m.confusion_matrix[0]} | FP: ${m.confusion_matrix[1]}<br>
                  FN: ${m.confusion_matrix[2]} | TP: ${m.confusion_matrix[3]}
                </div>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Render Feature Importance Chart
    const bestModel = models[bestModelName];
    if (bestModel && bestModel.feature_importances) {
      renderFeatureImportanceChart(bestModel.feature_importances);
    }
  } catch (err) {
    console.error('Failed to load ML analysis data:', err);
  }
}

function renderFeatureImportanceChart(importances) {
  const ctx = document.getElementById('featureImportanceCanvas');
  if (!ctx || !window.Chart) return;

  const sorted = Object.entries(importances).sort((a, b) => b[1] - a[1]);
  const labels = sorted.map(s => s[0].replace(/_/g, ' ').toUpperCase());
  const values = sorted.map(s => (s[1] * 100).toFixed(2));

  if (featureImportanceChart) featureImportanceChart.destroy();
  featureImportanceChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Feature Importance (%)',
        data: values,
        backgroundColor: 'rgba(37, 99, 235, 0.8)',
        borderColor: '#2563eb',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          beginAtZero: true,
          title: { display: true, text: 'Contribution Weight (%)' }
        }
      }
    }
  });
}

// Live Interactive Parameter Simulator
function setupLiveSimulator() {
  const simAmount = document.getElementById('simAmount');
  const simAvgAmount = document.getElementById('simAvgAmount');
  const simDeviceNew = document.getElementById('simDeviceNew');
  const simLocationChange = document.getElementById('simLocationChange');
  const simTimeOfDay = document.getElementById('simTimeOfDay');
  const simVelocity = document.getElementById('simVelocity');
  const simFailedPins = document.getElementById('simFailedPins');
  const simRunBtn = document.getElementById('simRunBtn');

  async function executeSimulation() {
    const payload = {
      receiver_id: 'test.simulator@upi',
      receiver_name: 'Simulator Sandbox Test',
      amount: parseFloat(simAmount?.value) || 2500,
      average_amount: parseFloat(simAvgAmount?.value) || 1200,
      device_new: simDeviceNew?.checked ? 1 : 0,
      location_change: simLocationChange?.checked ? 1 : 0,
      time_of_day: parseInt(simTimeOfDay?.value) || 12,
      transaction_velocity: parseFloat(simVelocity?.value) || 1.0,
      failed_transactions: parseInt(simFailedPins?.value) || 0,
      time_since_last_transaction: 45,
      transaction_type: 'P2P'
    };

    try {
      if (simRunBtn) {
        simRunBtn.disabled = true;
        simRunBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Simulating...';
      }

      const res = await API.predictRisk(payload);
      updateSimulationUI(res);
    } catch (e) {
      console.error('Simulation error:', e);
    } finally {
      if (simRunBtn) {
        simRunBtn.disabled = false;
        simRunBtn.innerHTML = '<i class="fas fa-play me-2"></i>Run Interactive Simulation';
      }
    }
  }

  if (simRunBtn) simRunBtn.addEventListener('click', executeSimulation);
  // Auto-run once on load
  setTimeout(executeSimulation, 400);
}

function updateSimulationUI(result) {
  const score = result.risk_score;
  const level = result.risk_level;

  document.getElementById('simScoreValue').textContent = `${score}%`;
  document.getElementById('simProbValue').textContent = `${(result.fraud_probability * 100).toFixed(2)}%`;
  document.getElementById('simBadgeValue').innerHTML = UI.renderRiskBadge(level, score);

  const meter = document.getElementById('simMeterBar');
  if (meter) {
    meter.style.width = `${score}%`;
    meter.className = `risk-meter-bar ${score <= 30 ? 'low' : (score <= 70 ? 'medium' : 'high')}`;
  }

  const recBox = document.getElementById('simRecommendationBox');
  if (recBox) recBox.textContent = result.recommendation;

  const reasonsList = document.getElementById('simReasonsList');
  if (reasonsList) {
    reasonsList.innerHTML = result.reasons.map(r => `<li><i class="fas fa-caret-right text-primary me-2"></i>${r}</li>`).join('');
  }
}
