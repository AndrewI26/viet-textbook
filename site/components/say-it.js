// <say-it>: record yourself saying a word and check its tone.
//
//   <say-it>[[má]]</say-it>
//
// The target tone comes from the word's tone mark. Your pitch is tracked in the
// browser (nothing is uploaded), compared with the Southern tone shapes, and
// drawn on a chart against the target. Works on one syllable at a time.
//
// The first use asks for a flat "a" to learn your normal voice level.

const TONES = {
  ngang: { name: "Ngang", hint: "flat, in the middle of your voice" },
  sac: { name: "Sắc", hint: "rises high" },
  huyen: { name: "Huyền", hint: "low, falling gently" },
  hoi: { name: "Hỏi", hint: "dips down, then rises" },
  nga: { name: "Ngã", hint: "dips down, then rises (same as hỏi in the South)" },
  nang: { name: "Nặng", hint: "low and heavy, with a small dip" },
};

// Southern tone shapes, in semitones relative to your normal (ngang) level.
// Points are [time 0–1, semitones]. Hỏi and ngã share one shape in the South.
// Measured from eight Southern voices (averaged), then smoothed.
const SHAPES = {
  ngang: [[0, 0.2], [0.55, 0.3], [1, -1.2]],
  sac: [[0, 0], [0.45, 0.2], [1, 6]],
  huyen: [[0, -1], [0.6, -3.9], [1, -4.2]],
  hoi: [[0, -1.5], [0.5, -3.4], [1, 3.5]],
  nang: [[0, 0], [0.25, -0.5], [0.6, -3.6], [1, -1]],
};
const shapeFor = (tone) => SHAPES[tone === "nga" ? "hoi" : tone];

// What to say when the target was A but it sounded like B.
const ADVICE = {
  "ngang>sac": "Your voice rose. Keep it level for ngang.",
  "ngang>huyen": "Your voice dropped. Hold it steady for ngang.",
  "ngang>hoi": "Your voice dipped. Keep it flat and steady.",
  "ngang>nang": "That went low. Stay at your normal level.",
  "sac>ngang": "It stayed flat. Let it climb higher toward the end.",
  "sac>hoi": "You dipped first. Start in the middle and go straight up.",
  "sac>huyen": "It went down. Sắc goes up, like a surprised \"What?!\"",
  "sac>nang": "It went down. Sắc goes up, like a surprised \"What?!\"",
  "huyen>ngang": "Too flat. Let your voice fall, like the end of a sentence.",
  "huyen>nang": "Close, but it dipped. Fall smoothly and gently.",
  "huyen>hoi": "It came back up. Huyền only falls.",
  "huyen>sac": "It went up. Huyền falls, like the end of a sentence.",
  "hoi>sac": "It rose without dipping. Go down first, then up.",
  "hoi>nang": "Good dip. Now rise higher at the end.",
  "hoi>huyen": "It fell but didn't come back up. Dip, then rise.",
  "hoi>ngang": "Too flat. Dip down, then rise, like a question.",
  "nang>hoi": "Too much rise at the end. Keep nặng low.",
  "nang>huyen": "Go a little lower, with a small dip at the end.",
  "nang>ngang": "Too high and flat. Start low and dip.",
  "nang>sac": "It went up. Nặng stays low and heavy.",
};

const TONE_MARKS = { "́": "sac", "̀": "huyen", "̉": "hoi", "̃": "nga", "̣": "nang" };

function toneOf(word) {
  for (const ch of word.normalize("NFD")) if (TONE_MARKS[ch]) return TONE_MARKS[ch];
  return "ngang";
}

// A "stopped" syllable ends in -p, -t, -c or -ch. It can only carry sắc or nặng, and
// it's short, so its tones look different (see classify).
function isChecked(word) {
  const plain = word.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");
  return /(p|t|c|ch)[.!?,]*$/.test(plain);
}

// ---------- Pitch tracking (YIN) ----------

const RATE = 16000;
let audioContext;
const getContext = () => (audioContext ??= new AudioContext());

async function decode(arrayBuffer) {
  const buffer = await getContext().decodeAudioData(arrayBuffer);
  const offline = new OfflineAudioContext(1, Math.ceil(buffer.duration * RATE), RATE);
  const source = offline.createBufferSource();
  source.buffer = buffer;
  source.connect(offline.destination);
  source.start();
  return (await offline.startRendering()).getChannelData(0);
}

function yin(samples, { rate = RATE, frame = 1024, hop = 160, fmin = 65, fmax = 500, threshold = 0.2 } = {}) {
  const tauMin = Math.floor(rate / fmax);
  const tauMax = Math.ceil(rate / fmin);
  const width = frame - tauMax;
  const cmnd = new Float32Array(tauMax + 1);
  const frames = [];
  for (let start = 0; start + frame <= samples.length; start += hop) {
    let energy = 0;
    for (let i = 0; i < frame; i++) energy += samples[start + i] ** 2;
    let running = 0;
    cmnd[0] = 1;
    for (let tau = 1; tau <= tauMax; tau++) {
      let sum = 0;
      for (let i = 0; i < width; i++) {
        const diff = samples[start + i] - samples[start + i + tau];
        sum += diff * diff;
      }
      running += sum;
      cmnd[tau] = running ? (sum * tau) / running : 1;
    }
    // First dip under the threshold; if none, the deepest dip if it's still clearly periodic.
    let best = -1;
    let deepest = tauMin;
    for (let tau = tauMin; tau <= tauMax; tau++) {
      if (cmnd[tau] < cmnd[deepest]) deepest = tau;
      if (cmnd[tau] < threshold) {
        while (tau + 1 <= tauMax && cmnd[tau + 1] < cmnd[tau]) tau++;
        best = tau;
        break;
      }
    }
    if (best < 0 && cmnd[deepest] < 0.35) best = deepest;
    let f0 = 0;
    let confidence = 0;
    if (best > 0) {
      const [a, b, c] = [cmnd[best - 1], cmnd[best], cmnd[best + 1] ?? cmnd[best]];
      const shift = (a - c) / (2 * (a - 2 * b + c) || 1);
      f0 = rate / (best + (Math.abs(shift) < 1 ? shift : 0));
      confidence = 1 - b;
    }
    frames.push({ time: (start + frame / 2) / rate, f0, confidence, rms: Math.sqrt(energy / frame) });
  }
  return frames;
}

// Pitch of the latest stretch of microphone audio, for the live line.
// Averages groups of samples down to ~16 kHz first so it's cheap enough to run every frame.
function livePitch(buffer, sampleRate) {
  const factor = Math.max(1, Math.round(sampleRate / RATE));
  const n = Math.floor(buffer.length / factor);
  const down = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    let sum = 0;
    for (let k = 0; k < factor; k++) sum += buffer[i * factor + k];
    down[i] = sum / factor;
  }
  const frame = Math.min(1024, n);
  return yin(down.subarray(n - frame), { rate: sampleRate / factor, frame, hop: frame })[0];
}

const median = (values) => {
  const sorted = [...values].sort((x, y) => x - y);
  return sorted.length ? sorted[Math.floor(sorted.length / 2)] : 0;
};

// The pitch of the main voiced stretch, in Hz, cleaned up.
function voicedPitch(frames) {
  const loudest = Math.max(...frames.map((f) => f.rms), 1e-9);
  const voiced = frames.map((f) => f.f0 > 0 && f.confidence > 0.6 && f.rms > loudest * 0.1);

  // The whole syllable: from the first to the last voiced frame.
  const first = voiced.indexOf(true);
  const last = voiced.lastIndexOf(true);
  if (first < 0 || last - first < 10) return [];
  const span = frames.slice(first, last + 1).map((f, i) => (voiced[first + i] ? f.f0 : 0));
  if (span.filter(Boolean).length < 8) return [];

  // Fix octave errors: a frame about twice (or half) the pitch of its neighbours is a
  // tracking mistake. Real pitch never moves that much in a tenth of a second.
  const raw = [...span];
  for (let i = 0; i < span.length; i++) {
    if (!span[i]) continue;
    const local = median(raw.slice(Math.max(0, i - 5), i + 6).filter(Boolean));
    while (span[i] > local * 1.6) span[i] /= 2;
    while (span[i] < local / 1.6) span[i] *= 2;
  }

  // Southern speakers often go creaky at the bottom of a dip, where pitch can't be
  // measured. Fill those gaps at the lower edge so the dip survives.
  for (let i = 0; i < span.length; i++) {
    if (span[i]) continue;
    let j = i;
    while (!span[j]) j++;
    const low = Math.min(span[i - 1], span[j]);
    for (let k = i; k < j; k++) span[k] = low;
    i = j;
  }
  const smooth = span.map((_, i) => median(span.slice(Math.max(0, i - 2), i + 3)));
  // The first moments of a syllable (the consonant) track least reliably. Keep the end:
  // that's where sắc and hỏi do their rising.
  return smooth.slice(Math.max(1, Math.round(smooth.length * 0.06)));
}

async function pitchOf(arrayBuffer) {
  return voicedPitch(yin(await decode(arrayBuffer)));
}

// ---------- Comparing with the tone shapes ----------

const POINTS = 24;

function resample(values, n = POINTS) {
  return Array.from({ length: n }, (_, i) => {
    const x = (i / (n - 1)) * (values.length - 1);
    const lo = Math.floor(x);
    const hi = Math.min(lo + 1, values.length - 1);
    return values[lo] + (values[hi] - values[lo]) * (x - lo);
  });
}

function shapePoints(points, n = POINTS) {
  return Array.from({ length: n }, (_, i) => {
    const t = i / (n - 1);
    const k = points.findIndex(([x], j) => j > 0 && t <= x);
    const [[x0, y0], [x1, y1]] = [points[k - 1], points[k]];
    return y0 + ((y1 - y0) * (t - x0)) / (x1 - x0);
  });
}

const toSemitones = (hz, baseline) => 12 * Math.log2(hz / baseline);

const mean = (values) => values.reduce((s, v) => s + v, 0) / values.length;

// Measurements of a pitch contour (semitones relative to your normal voice).
function measure(contour) {
  const n = contour.length;
  const low = Math.min(...contour);
  const start = mean(contour.slice(0, Math.ceil(n * 0.2)));
  const end = mean(contour.slice(Math.floor(n * 0.8)));
  return {
    start,
    end,
    low,
    lowAt: contour.indexOf(low) / (n - 1),
    dip: start - low, // how far it falls before the bottom
    rise: end - low, // how far it climbs back up from the bottom
    average: mean(contour),
  };
}

// Decide which Southern tone a contour sounds like. Returns { tone, m }.
// Keep in sync with src/textbook/tones.py, which checks the audio clips the same way.
function classify(contour, checked = false) {
  const m = measure(contour);
  if (checked) {
    // Stopped syllables: sắc sits high and rises; nặng sits low and drops, with no rise.
    let tone = "ngang";
    if (m.average >= 1.5 || m.end - m.start >= 2.5) tone = "sac";
    else if (m.average <= -0.5 || m.start - m.end >= 1.5) tone = "nang";
    return { tone, m };
  }
  let tone = "ngang";
  if (m.low <= -1.8 && m.rise >= 3.5 && m.end >= -1) tone = "hoi"; // dips low, then climbs well up
  else if (m.end - m.start >= 2.5) tone = "sac"; // climbs without a real dip
  else if (m.rise >= 1.2 && m.dip >= 1.5 && m.lowAt > 0.3 && m.lowAt < 0.9 && m.end < 0.5) tone = "nang"; // dips, comes back up a little
  else if (m.start - m.end >= 2.5 || m.average <= -2.5) tone = "huyen"; // falls clearly, or sits low
  return { tone, m };
}

// ---------- Recording ----------

class Recorder {
  async start({ onLevel, onPitch } = {}) {
    const ctx = getContext();
    await ctx.resume();
    this.stream = await navigator.mediaDevices.getUserMedia({
      // Automatic gain evens out quiet microphones (it changes volume, not pitch).
      // Noise suppression stays off: it can smear the harmonics pitch tracking needs.
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: true },
    });
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 4096; // ~85 ms: enough for the pitch of a low voice
    ctx.createMediaStreamSource(this.stream).connect(analyser);
    this.media = new MediaRecorder(this.stream);
    const chunks = [];
    this.media.ondataavailable = (e) => chunks.push(e.data);
    this.done = new Promise((resolve) => {
      this.media.onstop = () => resolve(new Blob(chunks, { type: this.media.mimeType }));
    });
    this.media.start();

    // Stop automatically shortly after you finish speaking (or after 3 seconds).
    const buffer = new Float32Array(analyser.fftSize);
    const began = performance.now();
    let noise = 0;
    let peak = 0;
    let spoke = false;
    let quietSince = 0;
    const tick = () => {
      if (this.media.state !== "recording") return clearInterval(timer);
      analyser.getFloatTimeDomainData(buffer);
      const recent = buffer.subarray(buffer.length - 1024);
      const rms = Math.sqrt(recent.reduce((s, v) => s + v * v, 0) / recent.length);
      const now = performance.now();
      // "Speaking" is judged against the room's noise and against how loud you've been
      // so far, so quiet microphones work too.
      if (now - began < 150) noise = Math.min(0.01, Math.max(noise, rms));
      peak = Math.max(peak, rms);
      const loud = rms > Math.max(0.002, noise * 2.5, peak * 0.12);
      onLevel?.(Math.min(1, rms / Math.max(peak, 0.02)));
      if (onPitch) {
        const { f0, confidence } = livePitch(buffer, ctx.sampleRate);
        onPitch({ time: (now - began) / 1000, f0: loud && confidence > 0.5 ? f0 : 0 });
      }
      if (loud) {
        spoke = true;
        quietSince = 0;
      } else if (spoke && !quietSince) {
        quietSince = now;
      }
      if (now - began > 3000 || (spoke && quietSince && now - quietSince > 400)) this.stop();
    };
    // A timer rather than requestAnimationFrame, so recording still stops if the
    // page is hidden (animation frames pause in background tabs).
    const timer = setInterval(tick, 25);
    setTimeout(() => this.stop(), 3500);
    return this.done;
  }

  stop() {
    if (this.media?.state === "recording") this.media.stop();
    this.stream?.getTracks().forEach((t) => t.stop());
  }
}

// ---------- Your voice level (shared by every <say-it> on the site) ----------

const BASELINE_KEY = "tone-baseline-hz";

function savedBaseline() {
  try {
    const value = Number(localStorage.getItem(BASELINE_KEY));
    return value > 50 && value < 600 ? value : null;
  } catch (e) {
    return null;
  }
}

function saveBaseline(hz) {
  try {
    localStorage.setItem(BASELINE_KEY, String(Math.round(hz)));
  } catch (e) {}
  window.dispatchEvent(new CustomEvent("tone-baseline"));
}

// ---------- The element ----------

const SVG = "http://www.w3.org/2000/svg";
const CHART = { width: 600, height: 190, left: 60, right: 16, top: 14, bottom: 14, range: 11 };
const x = (t) => CHART.left + t * (CHART.width - CHART.left - CHART.right);
const y = (st) => {
  const clamped = Math.max(-CHART.range, Math.min(CHART.range, st));
  return CHART.top + ((CHART.range - clamped) / (2 * CHART.range)) * (CHART.height - CHART.top - CHART.bottom);
};
const path = (values) => values.map((v, i) => `${i ? "L" : "M"}${x(i / (values.length - 1)).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

function svg(tag, attrs, parent) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  parent?.append(node);
  return node;
}

class SayIt extends HTMLElement {
  connectedCallback() {
    if (this.built) return;
    this.built = true;
    this.word = this.querySelector(".say");
    const text = this.word?.querySelector(".say-text")?.textContent.trim() ?? "";
    this.tone = toneOf(text);
    this.checked = isChecked(text);

    const head = document.createElement("div");
    head.className = "sayit-head";
    const label = document.createElement("span");
    label.className = "sayit-tone";
    label.innerHTML = `<strong>${TONES[this.tone].name}</strong> · ${TONES[this.tone].hint}`;
    if (this.word) head.append(this.word);
    head.append(label);

    this.chart = svg("svg", { class: "sayit-chart", viewBox: `0 0 ${CHART.width} ${CHART.height}`, role: "img" });
    for (const [st, name] of [[5, "high"], [0, "your voice"], [-5, "low"]]) {
      svg("line", { class: "sayit-grid", x1: CHART.left, x2: CHART.width - CHART.right, y1: y(st), y2: y(st) }, this.chart);
      const label = svg("text", { class: "sayit-axis", x: CHART.left - 18, y: y(st) + 4, "text-anchor": "end" }, this.chart);
      label.textContent = name === "your voice" ? "mid" : name;
    }
    const target = shapePoints(shapeFor(this.tone));
    svg("path", { class: "sayit-target-band", d: path(target) }, this.chart);
    svg("path", { class: "sayit-target", d: path(target) }, this.chart);
    this.mine = svg("path", { class: "sayit-mine", d: "" }, this.chart);
    this.chart.setAttribute("aria-label", `Target pitch for ${TONES[this.tone].name}: ${TONES[this.tone].hint}`);

    const bar = document.createElement("div");
    bar.className = "drill-bar";
    this.recordButton = this.button("Record", "btn-primary", () => this.record());
    this.playButton = this.button("Play mine", "btn-ghost", () => this.recording && playAudio(this.recording));
    this.playButton.hidden = true;
    this.status = document.createElement("span");
    this.status.className = "drill-status";
    bar.append(this.recordButton, this.playButton, this.status);

    this.foot = document.createElement("p");
    this.foot.className = "sayit-foot";

    this.replaceChildren(head, this.chart, bar, this.foot);
    this.updateFoot();
    window.addEventListener("tone-baseline", () => this.updateFoot());

    if (!window.isSecureContext || !navigator.mediaDevices || !window.MediaRecorder) {
      this.recordButton.disabled = true;
      this.setStatus("Recording needs a secure (https) page and a browser with microphone support.");
    } else if (/\s/.test(text)) {
      this.recordButton.disabled = true;
      this.setStatus("The tone check works on one syllable at a time.");
    }
  }

  button(label, kind, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `btn btn-sm ${kind}`;
    b.textContent = label;
    b.addEventListener("click", onClick);
    return b;
  }

  setStatus(text, tone = "") {
    this.status.textContent = text;
    this.status.className = `drill-status${tone ? ` is-${tone}` : ""}`;
  }

  updateFoot() {
    const baseline = savedBaseline();
    this.foot.replaceChildren();
    const text = document.createElement("span");
    text.textContent = baseline
      ? `Your normal voice level: ${baseline} Hz. `
      : "First time? You'll be asked to say a flat \"a\" so the checker learns your voice. ";
    this.foot.append(text);
    if (baseline) {
      const again = document.createElement("button");
      again.type = "button";
      again.className = "sayit-link";
      again.textContent = "Set it again";
      again.addEventListener("click", () => this.calibrate());
      this.foot.append(again);
    }
  }

  async listen(prompt) {
    if (this.recorder) {
      this.recorder.stop();
      return null;
    }
    Say.stop();
    this.recorder = new Recorder();
    this.recordButton.textContent = "Stop";
    this.setStatus(prompt);
    this.live = { points: [], start: null, base: savedBaseline() };
    this.mine.setAttribute("d", "");
    try {
      return await this.recorder.start({
        onLevel: (level) => this.style.setProperty("--level", level.toFixed(2)),
        onPitch: (sample) => this.drawLive(sample),
      });
    } catch (error) {
      const messages = {
        NotAllowedError: "Microphone access is blocked. Allow it in your browser's site settings.",
        NotFoundError: "No microphone found. Plug one in and try again.",
      };
      this.setStatus(messages[error?.name] ?? "Couldn't start the microphone.", "bad");
      return null;
    } finally {
      this.recorder = null;
      this.recordButton.textContent = "Record";
      this.style.setProperty("--level", "0");
    }
  }

  // Draw your pitch as you speak. The line starts when your voice starts and
  // stretches across the chart; when you stop, check() replaces it with the
  // aligned comparison.
  drawLive({ time, f0 }) {
    const live = this.live;
    if (f0) {
      const previous = live.points.findLast((p) => p.hz)?.hz;
      let hz = f0;
      if (previous) {
        while (hz > previous * 1.6) hz /= 2;
        while (hz < previous / 1.6) hz *= 2;
      }
      live.base ??= hz; // while calibrating, draw relative to where you started
      live.start ??= time;
      live.points.push({ time, hz });
    } else if (live.start !== null) {
      live.points.push({ time, hz: 0 }); // a gap in the line
    }
    if (live.start === null) return;

    const voiced = live.points.filter((p) => p.hz);
    const span = Math.max(0.6, voiced[voiced.length - 1].time - live.start);
    let d = "";
    voiced.forEach((p, i) => {
      // Join across short gaps; lift the pen only for a real pause.
      const pause = i === 0 || p.time - voiced[i - 1].time > 0.15;
      // Light smoothing: median of this point and its neighbours.
      const nearby = voiced.slice(Math.max(0, i - 1), i + 2).map((q) => q.hz);
      const px = x(Math.min(1, (p.time - live.start) / span));
      const py = y(toSemitones(median(nearby), live.base));
      d += `${pause ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)} `;
    });
    this.mine.setAttribute("d", d);
  }

  async calibrate() {
    const blob = await this.listen("Say a long, flat \"aaa\" in your normal voice…");
    if (!blob) return false;
    const pitch = await pitchOf(await blob.arrayBuffer());
    if (pitch.length < 8) {
      this.setStatus("I couldn't hear a clear voice. Try again a little louder.", "bad");
      return false;
    }
    saveBaseline(median(pitch));
    this.setStatus("Got it. Now press Record and say the word.", "good");
    return true;
  }

  async record() {
    if (!this.recorder && !savedBaseline()) {
      if (!(await this.calibrate())) return;
      return;
    }
    const blob = await this.listen(`Say "${this.word?.textContent.trim()}"…`);
    if (blob) await this.check(blob);
  }

  // Analyse a recording (any audio Blob) and show the result.
  async check(blob) {
    if (this.recording) URL.revokeObjectURL(this.recording);
    this.recording = URL.createObjectURL(blob);
    this.playButton.hidden = false;
    this.setStatus("Checking…");

    const pitch = await pitchOf(await blob.arrayBuffer());
    if (pitch.length < 8) {
      this.mine.setAttribute("d", "");
      this.setStatus("I couldn't hear a clear voice. Try again, a bit closer to the microphone.", "bad");
      return;
    }
    const contour = resample(pitch.map((hz) => toSemitones(hz, savedBaseline())));
    this.mine.setAttribute("d", path(contour));
    this.feedback(classify(contour, this.checked));
  }

  feedback({ tone: heard }) {
    const target = this.tone === "nga" ? "hoi" : this.tone;
    if (heard === target) {
      this.setStatus(`That's ${TONES[this.tone].name}. Nice!`, "good");
    } else {
      const stopped = this.checked && target === "nang" ? "Drop lower, and keep it short and heavy." : null;
      const advice = stopped ?? ADVICE[`${target}>${heard}`] ?? `That sounded more like ${TONES[heard].name}.`;
      this.setStatus(advice, "bad");
    }
  }
}

customElements.define("say-it", SayIt);

// For testing and for other components.
window.ToneCheck = { pitchOf, decode, yin, voicedPitch, toSemitones, resample, classify, measure, toneOf, isChecked, median, SHAPES };
