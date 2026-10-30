/**
 * Procedural Backcountry Soundscape Engine for TerraScout AI
 * Generates mountain breeze, leaf rustle, and procedural birdsong chirps.
 * 100% mathematical Web Audio API synthesis — zero MP3s or network requests.
 */

class NatureAudioEngine {
  constructor() {
    this.ctx = null;
    this.isPlaying = false;
    this.windGain = null;
    this.birdInterval = null;
  }

  init() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioContext();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  toggle() {
    this.init();
    if (this.isPlaying) {
      this.stop();
      return false;
    } else {
      this.start();
      return true;
    }
  }

  start() {
    if (!this.ctx) this.init();
    this.isPlaying = true;

    // Master Nature Gain
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.setValueAtTime(0.25, this.ctx.currentTime);
    this.masterGain.connect(this.ctx.destination);

    // 1. Forest Breeze
    this.startBreeze();

    // 2. Procedural Bird Chirps
    this.startBirdChirps();
  }

  stop() {
    this.isPlaying = false;
    if (this.windGain) {
      this.windGain.gain.linearRampToValueAtTime(0.001, this.ctx.currentTime + 1.0);
    }
    if (this.birdInterval) {
      clearInterval(this.birdInterval);
    }
  }

  startBreeze() {
    const bufferSize = this.ctx.sampleRate * 2;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let lastOut = 0.0;

    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      output[i] = (lastOut + 0.02 * white) / 1.02;
      lastOut = output[i];
      output[i] *= 3.5;
    }

    const brownNoise = this.ctx.createBufferSource();
    brownNoise.buffer = noiseBuffer;
    brownNoise.loop = true;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(340, this.ctx.currentTime);

    // Subtle wind sway LFO
    const lfo = this.ctx.createOscillator();
    lfo.frequency.setValueAtTime(0.12, this.ctx.currentTime);
    const lfoGain = this.ctx.createGain();
    lfoGain.gain.setValueAtTime(120, this.ctx.currentTime);
    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);

    this.windGain = this.ctx.createGain();
    this.windGain.gain.setValueAtTime(0.3, this.ctx.currentTime);

    brownNoise.connect(filter);
    filter.connect(this.windGain);
    this.windGain.connect(this.masterGain);

    brownNoise.start();
    lfo.start();
  }

  startBirdChirps() {
    this.birdInterval = setInterval(() => {
      if (!this.isPlaying || !this.ctx) return;
      if (Math.random() > 0.4) return;

      this.playBirdChirp();
    }, 2800);
  }

  playBirdChirp() {
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    // Natural warbler sweep
    const baseFreq = 2200 + Math.random() * 800;
    osc.type = 'sine';
    osc.frequency.setValueAtTime(baseFreq, now);
    osc.frequency.exponentialRampToValueAtTime(baseFreq * 1.5, now + 0.08);
    osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.9, now + 0.16);

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.06, now + 0.04);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.18);
  }

  playTrailChime() {
    if (!this.ctx) this.init();
    if (this.ctx.state === 'suspended') this.ctx.resume();

    const now = this.ctx.currentTime;
    [520, 1040, 1560].forEach((f, i) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(f, now);

      gain.gain.setValueAtTime(0.15 / (i + 1), now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 2.0);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 2.0);
    });
  }
}

window.natureAudio = new NatureAudioEngine();
