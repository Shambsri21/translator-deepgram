// ================= DOM REFERENCES =================

// MODE BUTTONS
const modeLive = document.getElementById("modeLive");
const modeUpload = document.getElementById("modeUpload");

// CONTROL SECTIONS
const liveControls = document.getElementById("liveControls");
const uploadControls = document.getElementById("uploadControls");

// LIVE BUTTONS
const startBtn = document.getElementById("startLive");
const stopBtn = document.getElementById("stopLive");

// OUTPUT AREAS
const asrText = document.getElementById("asrText");
const englishText = document.getElementById("englishText");
const czechText = document.getElementById("czechText");

// AUDIO / SOCKET
let ws = null;
let processor = null;
let audioCtx = null;
let analyser = null;
let animFrameId = null;
let micStream = null;

// ACCUMULATED TRANSCRIPT STATE
let finalHindi = "";
let finalEnglish = "";
let finalCzech = "";

// ================= WAVEFORM =================

function startWaveform() {
  const canvas = document.getElementById("waveCanvas");
  if (!canvas || !analyser) return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);
  let phase = 0;

  function draw() {
    animFrameId = requestAnimationFrame(draw);
    analyser.getByteTimeDomainData(dataArray);

    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      const value = dataArray[i] / 128.0 - 1.0;
      sum += value * value;
    }
    const rms = Math.sqrt(sum / bufferLength);
    const amplitude = Math.min(height * 0.42, Math.max(height * 0.045, rms * height * 3.2));

    ctx.clearRect(0, 0, width, height);
    phase += 0.038;

    const waves = [
      { color: "rgba(200, 225, 255, 0.95)", lineWidth: 2.6, frequency: 1.3, phaseOffset: 0, amount: 1.0 },
      { color: "rgba(74, 137, 255, 0.72)", lineWidth: 2.0, frequency: 2.2, phaseOffset: 1.1, amount: 0.7 },
      { color: "rgba(150, 200, 255, 0.48)", lineWidth: 1.5, frequency: 0.7, phaseOffset: 2.5, amount: 0.5 },
    ];

    for (const wave of waves) {
      ctx.beginPath();
      ctx.strokeStyle = wave.color;
      ctx.lineWidth = wave.lineWidth;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";

      for (let x = 0; x <= width; x++) {
        const t = (x / width) * Math.PI * 2 * wave.frequency + phase + wave.phaseOffset;
        const y = height / 2 + Math.sin(t) * amplitude * wave.amount;
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    }
  }

  draw();
}

function stopWaveform() {
  if (animFrameId) {
    cancelAnimationFrame(animFrameId);
    animFrameId = null;
  }

  const canvas = document.getElementById("waveCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.beginPath();
  ctx.strokeStyle = "rgba(152, 190, 255, 0.28)";
  ctx.lineWidth = 1.5;
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();
}

stopWaveform();

// ================= MODE SWITCH =================

modeLive.onclick = () => {
  modeLive.classList.add("active");
  modeUpload.classList.remove("active");
  liveControls.classList.remove("hidden");
  uploadControls.classList.add("hidden");
};

modeUpload.onclick = () => {
  modeUpload.classList.add("active");
  modeLive.classList.remove("active");
  uploadControls.classList.remove("hidden");
  liveControls.classList.add("hidden");
};

// ================= LIVE START =================

startBtn.onclick = async () => {
  // Reset accumulated state
  finalHindi = "";
  finalEnglish = "";
  finalCzech = "";
  asrText.textContent = "";
  englishText.textContent = "";
  czechText.textContent = "";

  ws = new WebSocket("ws://localhost:8000/ws/live");
  ws.binaryType = "arraybuffer";

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);

    if (msg.type === "asr_interim") {
      // Show accumulated finals + live interim in faded style
      asrText.innerHTML =
        (finalHindi ? finalHindi + " " : "") +
        `<span class="interim">${msg.hindi}</span>`;
      asrText.scrollTop = asrText.scrollHeight;
    }

    if (msg.type === "asr_final") {
      // Commit this sentence to the final transcript
      finalHindi += (finalHindi ? " " : "") + msg.hindi;
      asrText.textContent = finalHindi;
      asrText.scrollTop = asrText.scrollHeight;
    }

    if (msg.type === "translation") {
      finalEnglish += (finalEnglish ? " " : "") + msg.english;
      finalCzech += (finalCzech ? " " : "") + msg.czech;
      englishText.textContent = finalEnglish;
      czechText.textContent = finalCzech;
      englishText.scrollTop = englishText.scrollHeight;
      czechText.scrollTop = czechText.scrollHeight;
    }
  };

  micStream = await navigator.mediaDevices.getUserMedia({ audio: true });

  audioCtx = new AudioContext({ sampleRate: 16000 });
  const source = audioCtx.createMediaStreamSource(micStream);

  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 1024;
  source.connect(analyser);

  processor = audioCtx.createScriptProcessor(4096, 1, 1);
  source.connect(processor);
  processor.connect(audioCtx.destination);

  processor.onaudioprocess = (e) => {
    const input = e.inputBuffer.getChannelData(0);
    const pcm = new Int16Array(input.length);

    for (let i = 0; i < input.length; i++) {
      pcm[i] = Math.max(-1, Math.min(1, input[i])) * 32767;
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(pcm.buffer);
    }
  };

  startWaveform();
  startBtn.classList.add("hidden");
  stopBtn.classList.remove("hidden");
};

// ================= LIVE STOP =================

stopBtn.onclick = () => {
  if (processor) processor.disconnect();
  if (audioCtx) audioCtx.close();
  if (ws) ws.close();
  if (micStream) {
    micStream.getTracks().forEach((track) => track.stop());
  }

  processor = null;
  audioCtx = null;
  ws = null;
  analyser = null;
  micStream = null;

  stopWaveform();
  stopBtn.classList.add("hidden");
  startBtn.classList.remove("hidden");
};
