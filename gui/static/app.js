const form = document.querySelector("#generateForm");
const promptEl = document.querySelector("#prompt");
const imagePathEl = document.querySelector("#imagePath");
const widthEl = document.querySelector("#width");
const heightEl = document.querySelector("#height");
const framesEl = document.querySelector("#frames");
const stage1El = document.querySelector("#stage1Steps");
const stage2El = document.querySelector("#stage2Steps");
const frameRateEl = document.querySelector("#frameRate");
const lowRamEl = document.querySelector("#lowRam");
const enhancePromptEl = document.querySelector("#enhancePrompt");
const seedEl = document.querySelector("#seed");
const generateButton = document.querySelector("#generateButton");
const randomSeed = document.querySelector("#randomSeed");
const serverState = document.querySelector("#serverState");
const runtime = document.querySelector("#runtime");
const logEl = document.querySelector("#log");
const player = document.querySelector("#player");
const downloadLink = document.querySelector("#downloadLink");
const outputTitle = document.querySelector("#outputTitle");
const historyEl = document.querySelector("#history");
const rootPath = document.querySelector("#rootPath");
const refreshHistory = document.querySelector("#refreshHistory");

let activeJobId = null;
let pollTimer = null;

function setState(text, kind = "") {
  serverState.textContent = text;
  serverState.className = `system-pill ${kind}`.trim();
}

function formatSize(bytes) {
  if (bytes > 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function setVideo(url, filename) {
  player.src = url;
  outputTitle.textContent = filename;
  downloadLink.href = url;
  downloadLink.download = filename;
  downloadLink.classList.remove("disabled");
}

function renderHistory(outputs) {
  historyEl.innerHTML = "";
  if (!outputs.length) {
    const empty = document.createElement("div");
    empty.className = "render-item";
    empty.innerHTML = "<strong>No renders yet</strong><span>Generated MP4s will appear here.</span>";
    historyEl.append(empty);
    return;
  }

  outputs.forEach((item) => {
    const button = document.createElement("button");
    button.className = "render-item";
    button.type = "button";
    const date = new Date(item.created_at * 1000);
    const detail = [date.toLocaleString(), item.resolution, item.frames ? `${item.frames}f` : "", formatSize(item.size)]
      .filter(Boolean)
      .join(" - ");
    button.innerHTML = `<strong>${item.filename}</strong><span>${detail}</span>`;
    if (item.prompt) {
      const prompt = document.createElement("em");
      prompt.textContent = item.prompt;
      button.append(prompt);
    }
    button.addEventListener("click", () => setVideo(item.video_url, item.filename));
    historyEl.append(button);
  });
}

function setLog(lines) {
  logEl.textContent = lines.length ? lines.join("\n") : "Starting generation.";
  logEl.scrollTop = logEl.scrollHeight;
}

async function loadStatus() {
  const response = await fetch("/api/status");
  const data = await response.json();
  rootPath.textContent = data.root;
  renderHistory(data.outputs || []);
  if (!data.runtime_ready) {
    setState("Setup Needed", "error");
    logEl.textContent = "Run ./install.sh -y before generating.";
  }
  if (data.active_job && !activeJobId) {
    activeJobId = data.active_job.id;
    pollJob();
  }
}

async function loadHistory() {
  const response = await fetch("/api/history");
  const data = await response.json();
  renderHistory(data.outputs || []);
}

async function pollJob() {
  if (!activeJobId) return;
  const response = await fetch(`/api/jobs/${activeJobId}`);
  const data = await response.json();
  const job = data.job;
  if (!job) return;

  setLog(job.logs || []);
  if (job.status === "running" || job.status === "queued") {
    setState("Generating", "running");
    runtime.textContent = "Running";
    generateButton.disabled = true;
    pollTimer = setTimeout(pollJob, 1000);
    return;
  }

  generateButton.disabled = false;
  activeJobId = null;
  clearTimeout(pollTimer);

  if (job.status === "done") {
    setState("Ready", "done");
    runtime.textContent = `${job.duration}s`;
    setVideo(job.video_url, job.filename);
    loadHistory();
  } else {
    setState("Error", "error");
    runtime.textContent = "Failed";
    if (job.error) logEl.textContent += `\n\n${job.error}`;
  }
}

function payloadFromForm() {
  return {
    prompt: promptEl.value,
    image: imagePathEl.value,
    width: Number(widthEl.value),
    height: Number(heightEl.value),
    frames: Number(framesEl.value),
    stage1_steps: Number(stage1El.value),
    stage2_steps: Number(stage2El.value),
    frame_rate: Number(frameRateEl.value),
    low_ram: lowRamEl.checked,
    enhance_prompt: enhancePromptEl.checked,
    seed: Number(seedEl.value)
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  generateButton.disabled = true;
  setState("Queued", "running");
  runtime.textContent = "Queued";
  logEl.textContent = "Queued.";
  downloadLink.classList.add("disabled");

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payloadFromForm())
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Generation failed.");
    activeJobId = data.job.id;
    pollJob();
  } catch (error) {
    generateButton.disabled = false;
    setState("Error", "error");
    runtime.textContent = "Failed";
    logEl.textContent = error.message;
  }
});

randomSeed.addEventListener("click", () => {
  seedEl.value = Math.floor(Math.random() * 2147483647);
});

refreshHistory.addEventListener("click", loadHistory);

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    promptEl.value = button.dataset.prompt;
  });
});

loadStatus().catch((error) => {
  setState("Offline", "error");
  logEl.textContent = error.message;
});
