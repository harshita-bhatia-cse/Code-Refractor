import API_BASE from "./config.js?v=20260305a";
import { requireAuth } from "./auth.js?v=20260305a";

const codeBox = document.getElementById("codeBox");
const originalBox = document.getElementById("originalBox");
const refactoredBox = document.getElementById("refactoredBox");
const analysisBox = document.getElementById("analysisBox");
const qualitySummary = document.getElementById("qualitySummary");
const qualityBadges = document.getElementById("qualityBadges");
let refactorBox = document.getElementById("refactorBox");

const analysisState = document.getElementById("analysisState");
const refactorState = document.getElementById("refactorState");

const retryAnalysisBtn = document.getElementById("retryAnalysisBtn");
const retryRefactorBtn = document.getElementById("retryRefactorBtn");
const rerunAllBtn = document.getElementById("rerunAllBtn");
const acceptRefactorBtn = document.getElementById("acceptRefactorBtn");
const rejectRefactorBtn = document.getElementById("rejectRefactorBtn");
const downloadPatchBtn = document.getElementById("downloadPatchBtn");

let activeToken = "";
let activeRawUrl = "";
let activeFilename = "snippet.txt";
let sourceCodeOriginal = "";
let latestRefactoredCode = "";
let runInProgress = false;
let autoRunEnabled = true;

function setChip(el, text, tone = "idle") {
  if (!el) return;
  el.textContent = text;
  el.className = `status-chip status-${tone}`;
}

function setRefactorText(text) {
  if (!refactorBox) return;
  refactorBox.textContent = text;
}

function setAnalysisText(text) {
  if (!analysisBox) return;
  analysisBox.textContent = text;
}

function setQuality(data) {
  if (!qualitySummary || !qualityBadges) return;

  const score = data?.overall_quality_score;
  const grade = data?.overall_grade;
  const badges = Array.isArray(data?.overall_risk_badges) ? data.overall_risk_badges : [];

  if (typeof score !== "number" || !grade) {
    qualitySummary.textContent = "Quality score unavailable for this file.";
    qualityBadges.innerHTML = "";
    return;
  }

  qualitySummary.textContent = `Score: ${score}/100 • Grade: ${grade}`;
  qualityBadges.innerHTML = badges
    .map((tag) => `<span class="risk-badge">${tag}</span>`)
    .join("");
}

function updateDownloadButtonState() {
  if (!downloadPatchBtn) return;
  downloadPatchBtn.disabled = !sourceCodeOriginal || !latestRefactoredCode;
}

async function loadCode(rawUrl) {
  try {
    const res = await fetch(rawUrl);
    if (!res.ok) throw new Error("Failed to load code");
    const text = await res.text();
    sourceCodeOriginal = text;
    if (codeBox) codeBox.textContent = text;
    if (originalBox) originalBox.textContent = text;
    if (refactoredBox) refactoredBox.textContent = "Waiting for refactor...";
    updateDownloadButtonState();
  } catch {
    if (codeBox) codeBox.textContent = "Failed to load source code.";
    if (originalBox) originalBox.textContent = "";
    sourceCodeOriginal = "";
    updateDownloadButtonState();
  }
}

async function runAnalysis(rawUrl, token) {
  try {
    setChip(analysisState, "Running", "loading");
    setAnalysisText("Running AI analysis...");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120000);

    const res = await fetch(`${API_BASE}/analyze/?raw_url=${encodeURIComponent(rawUrl)}`, {
      signal: controller.signal,
      headers: { Authorization: `Bearer ${token}` },
    });
    clearTimeout(timeout);

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt);
    }

    const data = await res.json();
    setAnalysisText(JSON.stringify(data, null, 2) || "AI analysis returned empty response.");
    setQuality(data);
    setChip(analysisState, "Completed", "ok");
  } catch (err) {
    const msg =
      err && err.name === "AbortError"
        ? "AI analysis timed out after 120 seconds."
        : (err.message || String(err));
    setAnalysisText(`AI analysis failed.\n${msg}`);
    setChip(analysisState, "Failed", "error");
  }
}

async function runRefactor(rawUrl, token) {
  try {
    setChip(refactorState, "Running", "loading");
    setRefactorText("Running LLM refactor...");

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 300000);

    const res = await fetch(`${API_BASE}/refactor/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      signal: controller.signal,
      body: JSON.stringify({ raw_url: rawUrl }),
    });
    clearTimeout(timeout);

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Refactor API failed (${res.status}): ${txt}`);
    }

    const data = await res.json();
    const llm = data.llm_refactor || {};
    const ok = llm.ok === true;
    latestRefactoredCode = llm.refactored_code || "";

    if (refactoredBox) {
      refactoredBox.textContent = latestRefactoredCode || "No refactored code returned";
    }

    updateDownloadButtonState();

    setRefactorText(
      `Status: ${ok ? "OK" : "FAILED"}
${llm.error ? `Error: ${llm.error}\n` : ""}Summary:
${llm.summary || "No summary provided"}

Issues:
${Array.isArray(llm.issues) && llm.issues.length ? llm.issues.map((x, i) => `${i + 1}. ${x}`).join("\n") : "No issues listed"}`
    );

    setChip(refactorState, ok ? "Completed" : "Failed", ok ? "ok" : "error");
  } catch (err) {
    const msg =
      err && err.name === "AbortError"
        ? "LLM refactor request timed out after 300 seconds."
        : (err.message || String(err));
    setRefactorText(`LLM refactor failed.\n${msg}`);
    if (refactoredBox) refactoredBox.textContent = "Refactor unavailable.";
    latestRefactoredCode = "";
    updateDownloadButtonState();
    setChip(refactorState, "Failed", "error");
  }
}

function generateUnifiedPatch(oldText, newText, filename) {
  const oldLines = (oldText || "").split("\n");
  const newLines = (newText || "").split("\n");
  const header = `--- a/${filename}\n+++ b/${filename}\n@@ -1,${oldLines.length} +1,${newLines.length} @@`;
  const removed = oldLines.map((line) => `-${line}`).join("\n");
  const added = newLines.map((line) => `+${line}`).join("\n");
  return `${header}\n${removed}\n${added}\n`;
}

function downloadTextFile(filename, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function runAll() {
  if (!activeRawUrl || !activeToken) return;
  if (runInProgress) {
    console.log("runAll skipped; already in progress");
    return;
  }

  runInProgress = true;
  try {
    await loadCode(activeRawUrl);
    await runAnalysis(activeRawUrl, activeToken);
    await runRefactor(activeRawUrl, activeToken);
  } finally {
    runInProgress = false;
  }
}

async function initPage() {
  try {
    if (downloadPatchBtn) downloadPatchBtn.disabled = true;

    setChip(analysisState, "Initializing", "loading");
    setChip(refactorState, "Initializing", "loading");
    setAnalysisText("Initializing...");
    setRefactorText("Initializing...");

    activeToken = requireAuth();
    const params = new URLSearchParams(window.location.search);
    activeRawUrl = params.get("raw_url") || "";
    activeFilename = (activeRawUrl.split("/").pop() || "snippet.txt").split("?")[0];

    if (!activeRawUrl || !activeRawUrl.startsWith("http")) {
      setAnalysisText("Invalid file URL");
      setRefactorText("LLM refactor failed.\nInvalid raw_url");
      setChip(analysisState, "Invalid URL", "error");
      setChip(refactorState, "Invalid URL", "error");
      return;
    }

    if (autoRunEnabled) {
      await runAll();
      autoRunEnabled = false;
    }
  } catch (err) {
    setRefactorText(`Initialization failed.\n${err.message || err}`);
    setChip(refactorState, "Failed", "error");
  }
}

if (retryAnalysisBtn) {
  retryAnalysisBtn.addEventListener("click", async () => {
    if (!activeRawUrl || !activeToken) return;
    await runAnalysis(activeRawUrl, activeToken);
  });
}

if (retryRefactorBtn) {
  retryRefactorBtn.addEventListener("click", async () => {
    if (!activeRawUrl || !activeToken) return;
    await runRefactor(activeRawUrl, activeToken);
  });
}

if (rerunAllBtn) {
  rerunAllBtn.addEventListener("click", async () => {
    await runAll();
  });
}

if (acceptRefactorBtn) {
  acceptRefactorBtn.addEventListener("click", () => {
    if (!latestRefactoredCode) return;
    if (codeBox) codeBox.textContent = latestRefactoredCode;
  });
}

if (rejectRefactorBtn) {
  rejectRefactorBtn.addEventListener("click", () => {
    if (codeBox) codeBox.textContent = sourceCodeOriginal || "";
  });
}

if (downloadPatchBtn) {
  downloadPatchBtn.addEventListener("click", () => {
    if (!sourceCodeOriginal) {
      alert("Source code is not loaded yet. Please run the analysis first.");
      return;
    }
    if (!latestRefactoredCode) {
      alert("Refactored code is not ready yet. Please run refactor first.");
      return;
    }

    const patch = generateUnifiedPatch(sourceCodeOriginal, latestRefactoredCode, activeFilename);
    downloadTextFile(`${activeFilename}.diff`, patch);
  });
}

initPage();