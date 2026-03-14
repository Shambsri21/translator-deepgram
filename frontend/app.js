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
  // Reset UI
  asrText.textContent = "";
  englishText.textContent = "";
  czechText.textContent = "";

  ws = new WebSocket("ws://localhost:8000/ws/live");
  ws.binaryType = "arraybuffer";

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);

    if (msg.type === "asr") {
      asrText.textContent = msg.hindi;
    }

    if (msg.type === "translation") {
      englishText.textContent += msg.english + " ";
      czechText.textContent += msg.czech + " ";
    }
  };

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

  audioCtx = new AudioContext({ sampleRate: 16000 });
  const source = audioCtx.createMediaStreamSource(stream);

  processor = audioCtx.createScriptProcessor(4096, 1, 1);
  source.connect(processor);
  processor.connect(audioCtx.destination);

  processor.onaudioprocess = (e) => {
    const input = e.inputBuffer.getChannelData(0);
    const pcm = new Int16Array(input.length);

    for (let i = 0; i < input.length; i++) {
      pcm[i] = Math.max(-1, Math.min(1, input[i])) * 32767;
    }

    if (ws.readyState === WebSocket.OPEN) {
      ws.send(pcm.buffer);
    }
  };

  startBtn.classList.add("hidden");
  stopBtn.classList.remove("hidden");
};

// ================= LIVE STOP =================

stopBtn.onclick = () => {
  if (processor) processor.disconnect();
  if (audioCtx) audioCtx.close();
  if (ws) ws.close();

  processor = null;
  audioCtx = null;
  ws = null;

  stopBtn.classList.add("hidden");
  startBtn.classList.remove("hidden");
};
