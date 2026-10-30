/**
 * Naturalist & Trail Dispatch Client for TerraScout AI
 */

const API_BASE = '';

document.addEventListener('DOMContentLoaded', () => {
  initNaturalist();
});

async function initNaturalist() {
  await fetchCompendium();
  setupDispatchForm();
  setupOracleForm();
}

async function fetchCompendium() {
  try {
    const res = await fetch(`${API_BASE}/api/compendium`);
    const items = await res.json();
    renderCompendium(items);
  } catch (err) {
    console.error('Failed to load compendium:', err);
  }
}

function renderCompendium(items) {
  const container = document.getElementById('compendium-list');
  if (!container) return;
  container.innerHTML = '';

  items.forEach(it => {
    const card = document.createElement('div');
    card.className = 'specimen-card';

    let badgeClass = 'badge-edible';
    if (it.category === 'toxic_danger' || (it.edibility && it.edibility.includes('POISON'))) {
      badgeClass = 'badge-danger';
    } else if (it.category === 'bird') {
      badgeClass = 'badge-bird';
    }

    card.innerHTML = `
      <div class="specimen-top">
        <div>
          <span class="specimen-title">${it.common_name}</span>
          <span class="specimen-latin">${it.scientific_name}</span>
        </div>
        <span class="badge ${badgeClass}">${it.edibility || it.category}</span>
      </div>
      <div class="specimen-body">
        <div><strong>Habitat:</strong> ${it.habitat} &bull; <strong>Season:</strong> ${it.season}</div>
        <div style="margin-top:4px;">${it.key_features || it.call_mnemonic || ''}</div>
      </div>
      ${it.toxic_lookalike ? `<div class="danger-lookalike">⚠️ <strong>Toxic Lookalike:</strong> ${it.toxic_lookalike}</div>` : ''}
    `;
    container.appendChild(card);
  });
}

function setupDispatchForm() {
  const form = document.getElementById('form-dispatch');
  const resultBox = document.getElementById('dispatch-result');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const activity = document.getElementById('dispatch-activity').value;
    const biome = document.getElementById('dispatch-biome').value;
    const season = document.getElementById('dispatch-season').value;
    const minutes = document.getElementById('dispatch-minutes').value;

    resultBox.style.display = 'block';
    resultBox.innerHTML = `<em>🌲 Consulting local Gemma 2 naturalist engine...</em>`;

    try {
      const res = await fetch(`${API_BASE}/api/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity: activity,
          biome: biome,
          season: season,
          target_minutes: minutes
        })
      });
      const data = await res.json();
      resultBox.innerHTML = `
        <div style="font-weight:bold;color:#74c69d;margin-bottom:6px;">✦ Field Dispatch (${data.model})</div>
        <div>${formatMarkdown(data.dispatch)}</div>
        <div style="font-size:0.75rem;color:#8da399;margin-top:8px;">${data.offline_guarantee || 'Local offline execution'}</div>
      `;
      if (window.natureAudio) window.natureAudio.playTrailChime();
    } catch (err) {
      resultBox.textContent = "Error communicating with field engine. Please retry.";
    }
  });
}

function setupOracleForm() {
  const form = document.getElementById('form-oracle');
  const outputBox = document.getElementById('oracle-output');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const desc = document.getElementById('oracle-desc').value.trim();
    const cat = document.getElementById('oracle-cat').value;
    const terrain = document.getElementById('oracle-terrain').value;

    if (!desc) return;

    outputBox.style.display = 'block';
    outputBox.innerHTML = `<em>🔍 Analyzing field specimen with local Gemma weights...</em>`;

    try {
      const res = await fetch(`${API_BASE}/api/identify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: desc,
          category: cat,
          terrain: terrain
        })
      });
      const data = await res.json();
      outputBox.innerHTML = `
        <div style="font-weight:bold;color:#f4a261;margin-bottom:6px;">✦ Naturalist Analysis (${data.model})</div>
        <div>${formatMarkdown(data.analysis)}</div>
        <div style="font-size:0.75rem;color:#8da399;margin-top:8px;">${data.offline_guarantee || 'Offline air-gap verified'}</div>
      `;
    } catch (err) {
      outputBox.textContent = "Field engine query failed. Verify backend server is running.";
    }
  });
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}
