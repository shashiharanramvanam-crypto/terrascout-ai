/**
 * Main Application Controller & Expedition Tracker for TerraScout AI
 */

let activeExpedition = null;
let timerInterval = null;
let timerSeconds = 0;

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  await fetchStatus();
  await fetchStats();
  await loadExpeditions();
  setupEventListeners();
}

async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    const modelPill = document.getElementById('engine-model');
    if (modelPill) modelPill.textContent = data.model;
  } catch (err) {
    console.warn('Status fetch error:', err);
  }
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const stats = await res.json();
    document.getElementById('stat-minutes').textContent = `${stats.total_minutes_outside}m`;
    document.getElementById('stat-saved').textContent = `${stats.screen_time_saved_estimate_hours}h`;
    document.getElementById('stat-sightings').textContent = stats.total_sightings;
    document.getElementById('stat-expeditions').textContent = stats.total_expeditions;
  } catch (err) {
    console.warn('Stats fetch error:', err);
  }
}

async function loadExpeditions() {
  try {
    const res = await fetch('/api/expeditions');
    const exps = await res.json();
    if (exps.length > 0) {
      setActiveExpedition(exps[0]);
    }
  } catch (err) {
    console.warn('Expeditions fetch error:', err);
  }
}

function setActiveExpedition(exp) {
  activeExpedition = exp;
  document.getElementById('exp-title').textContent = exp.title;
  document.getElementById('exp-meta').textContent = `${exp.activity.replace('_', ' ').toUpperCase()} &bull; ${exp.biome.replace('_', ' ').toUpperCase()}`;
  renderSightings(exp.sightings || []);
  
  if (exp.journal_entry) {
    const journalBox = document.getElementById('exp-journal-box');
    journalBox.style.display = 'block';
    journalBox.innerHTML = `<strong>Naturalist Reflection:</strong> <em>"${exp.journal_entry}"</em>`;
  }
}

function renderSightings(sightings) {
  const container = document.getElementById('sightings-list');
  if (!container) return;
  container.innerHTML = '';

  if (sightings.length === 0) {
    container.innerHTML = `<div style="color:#8da399;font-size:0.85rem;font-style:italic;">No sightings logged yet for this trail session.</div>`;
    return;
  }

  sightings.forEach(s => {
    const item = document.createElement('div');
    item.className = 'sighting-item';
    item.innerHTML = `
      <div>
        <strong>${s.common_name}</strong> <span style="font-size:0.75rem;color:#8da399;">(${s.category})</span>
        <div style="font-size:0.8rem;color:#cfded9;margin-top:2px;">${s.notes || ''}</div>
      </div>
      <span style="font-size:0.75rem;color:#f4a261;">${s.spotted_at || ''}</span>
    `;
    container.appendChild(item);
  });
}

function setupEventListeners() {
  // Audio toggle
  const audioBtn = document.getElementById('btn-nature-sound');
  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      const playing = window.natureAudio.toggle();
      audioBtn.classList.toggle('active', playing);
      audioBtn.innerHTML = playing ? '🔊 Nature Ambience: ON' : '🔈 Nature Ambience: OFF';
    });
  }

  // Timer controls
  const startBtn = document.getElementById('btn-start-timer');
  const stopBtn = document.getElementById('btn-stop-timer');
  const timerDigits = document.getElementById('timer-digits');

  if (startBtn && stopBtn) {
    startBtn.addEventListener('click', () => {
      if (timerInterval) return;
      if (window.natureAudio) window.natureAudio.playTrailChime();
      startBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex';

      timerInterval = setInterval(() => {
        timerSeconds++;
        const mins = String(Math.floor(timerSeconds / 60)).padStart(2, '0');
        const secs = String(timerSeconds % 60).padStart(2, '0');
        timerDigits.textContent = `${mins}:${secs}`;
      }, 1000);
    });

    stopBtn.addEventListener('click', async () => {
      clearInterval(timerInterval);
      timerInterval = null;
      startBtn.style.display = 'inline-flex';
      stopBtn.style.display = 'none';

      const elapsedMins = Math.max(1, Math.round(timerSeconds / 60));
      if (activeExpedition) {
        await fetch(`/api/expeditions/${activeExpedition.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            elapsed_minutes: (activeExpedition.elapsed_minutes || 0) + elapsedMins,
            steps: (activeExpedition.steps || 0) + (elapsedMins * 110)
          })
        });
        await fetchStats();
        const res = await fetch(`/api/expeditions/${activeExpedition.id}`);
        activeExpedition = await res.json();
        setActiveExpedition(activeExpedition);
      }
    });
  }

  // Sighting Modal
  const addSightingBtn = document.getElementById('btn-add-sighting');
  const modalSighting = document.getElementById('modal-sighting');
  const closeSightingBtn = document.getElementById('close-modal-sighting');
  const formSighting = document.getElementById('form-sighting');

  if (addSightingBtn && modalSighting) {
    addSightingBtn.addEventListener('click', () => {
      modalSighting.style.display = 'flex';
    });
    closeSightingBtn.addEventListener('click', () => {
      modalSighting.style.display = 'none';
    });

    formSighting.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!activeExpedition) return;
      const data = {
        common_name: document.getElementById('in-sight-name').value,
        category: document.getElementById('in-sight-cat').value,
        notes: document.getElementById('in-sight-notes').value,
        edibility: document.getElementById('in-sight-edibility').value
      };

      await fetch(`/api/expeditions/${activeExpedition.id}/sightings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      const res = await fetch(`/api/expeditions/${activeExpedition.id}`);
      activeExpedition = await res.json();
      setActiveExpedition(activeExpedition);
      await fetchStats();
      modalSighting.style.display = 'none';
      formSighting.reset();
    });
  }

  // Finish Expedition & Generate Naturalist Journal
  const finishBtn = document.getElementById('btn-finish-expedition');
  if (finishBtn) {
    finishBtn.addEventListener('click', async () => {
      if (!activeExpedition) return;
      finishBtn.disabled = true;
      finishBtn.innerHTML = `<em>🌿 Generating reflection with Gemma 2...</em>`;

      try {
        const res = await fetch(`/api/expeditions/${activeExpedition.id}/journal`, {
          method: 'POST'
        });
        const data = await res.json();
        const journalBox = document.getElementById('exp-journal-box');
        journalBox.style.display = 'block';
        journalBox.innerHTML = `<strong>Naturalist Reflection (${data.model}):</strong><br><em>"${data.journal_entry}"</em>`;
        if (window.natureAudio) window.natureAudio.playTrailChime();
        await fetchStats();
      } catch (err) {
        alert("Failed to generate reflection.");
      } finally {
        finishBtn.disabled = false;
        finishBtn.innerHTML = `📜 Finish & Reflect`;
      }
    });
  }

  // Export 1-Click Offline Field Guide HTML
  const exportBtn = document.getElementById('btn-export-guide');
  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      if (!activeExpedition) return;
      window.open(`/api/expeditions/${activeExpedition.id}/export`, '_blank');
    });
  }

  // Why Open AI Modal
  const whyBtn = document.getElementById('btn-why-open');
  const whyModal = document.getElementById('modal-why-open');
  const whyClose = document.getElementById('close-modal-why');

  if (whyBtn && whyModal) {
    whyBtn.addEventListener('click', () => whyModal.style.display = 'flex');
    whyClose.addEventListener('click', () => whyModal.style.display = 'none');
  }
}
