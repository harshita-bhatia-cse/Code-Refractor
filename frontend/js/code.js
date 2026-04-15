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

// =========================
// UI HELPERS
// =========================
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
  const score = data?.overall_quality_score;
  const grade = data?.overall_grade;
  const badges = data?.overall_risk_badges || [];

  if (typeof score !== "number") return;

  qualitySummary.textContent = `Score: ${score}/100 • Grade: ${grade}`;
  qualityBadges.innerHTML = badges.map(b => `<span class="risk-badge">${b}</span>`).join("");
}

function inferFilename(rawUrl) {
  if (!rawUrl) return "snippet.txt";
  try {
    const url = new URL(rawUrl);
    const segments = url.pathname.split("/").filter(Boolean);
    return segments[segments.length - 1] || "snippet.txt";
  } catch {
    return "snippet.txt";
  }
}

function updateCodeViews(code) {
  codeBox.textContent = code;
  originalBox.textContent = code;
  refactoredBox.textContent = code;
}

function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// =========================
// LOAD CODE
// =========================
async function loadCode(rawUrl) {
  try {
    const res = await fetch(rawUrl);
    const text = await res.text();

    activeFilename = inferFilename(rawUrl);
    sourceCodeOriginal = text;
    codeBox.textContent = text;
    originalBox.textContent = text;
    refactoredBox.textContent = "Waiting for refactor...";

  } catch {
    codeBox.textContent = "Failed to load code";
  }
}

// =========================
// ANALYSIS
// =========================
async function runAnalysis(rawUrl, token) {
  try {
    setChip(analysisState, "Running", "loading");

    const res = await fetch(`${API_BASE}/analyze/?raw_url=${encodeURIComponent(rawUrl)}`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    const data = await res.json();

    setAnalysisText(JSON.stringify(data, null, 2));
    setQuality(data);

    setChip(analysisState, "Completed", "ok");

  } catch (err) {
    setAnalysisText("Analysis failed");
    setChip(analysisState, "Failed", "error");
  }
}

// =========================
// 🔥 FIXED REFACTOR
// =========================
async function runRefactor(rawUrl, token) {
  try {
    setChip(refactorState, "Running", "loading");
    setRefactorText("Running LLM refactor...");

    const res = await fetch(`${API_BASE}/refactor/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ raw_url: rawUrl }),
    });

    console.log("STATUS:", res.status);

    const data = await res.json();
    console.log("RESPONSE:", data);

    const llm = data.llm_refactor || {};

    const isSuccess = llm.ok === true;
    const isSkipped = llm.skipped === true;
    const isFallback = llm.fallback === true;

    latestRefactoredCode = llm.refactored_code || sourceCodeOriginal;

    refactoredBox.textContent = latestRefactoredCode;

    // 🔥 SMART STATUS
    let status = "Completed";
    let tone = "ok";

    if (isSkipped) {
      status = "Skipped";
      tone = "idle";
    } else if (isFallback) {
      status = "Fallback";
      tone = "idle";
    } else if (!isSuccess) {
      status = "Failed";
      tone = "error";
    }

    setRefactorText(`
Status: ${status}
${llm.reason ? "Reason: " + llm.reason : ""}

Summary:
${llm.summary || "No summary"}

Issues:
${(llm.issues || []).join("\n") || "None"}
    `);

    setChip(refactorState, status, tone);

  } catch (err) {
    console.error("ERROR:", err);

    // 🔥 NO MORE HARD FAIL
    setRefactorText(`
⚠️ Refactor unavailable

Reason:
${err.message}

👉 Showing original code
    `);

    refactoredBox.textContent = sourceCodeOriginal;

    setChip(refactorState, "Unavailable", "idle");
  }
}

// =========================
// MAIN FLOW
// =========================
async function runAll() {
  runInProgress = true;
  await loadCode(activeRawUrl);
  await runAnalysis(activeRawUrl, activeToken);
  await runRefactor(activeRawUrl, activeToken);
  runInProgress = false;
}

// =========================
// INIT
// =========================
async function initPage() {
  activeToken = requireAuth();

  const params = new URLSearchParams(window.location.search);
  activeRawUrl = params.get("raw_url");

  if (!activeRawUrl) {
    alert("Invalid URL");
    return;
  }

  await runAll();
}

// =========================
// BUTTONS
// =========================
retryRefactorBtn?.addEventListener("click", () => runRefactor(activeRawUrl, activeToken));
retryAnalysisBtn?.addEventListener("click", () => runAnalysis(activeRawUrl, activeToken));
rerunAllBtn?.addEventListener("click", runAll);
acceptRefactorBtn?.addEventListener("click", () => {
  if (!latestRefactoredCode) return;
  sourceCodeOriginal = latestRefactoredCode;
  updateCodeViews(latestRefactoredCode);
  setRefactorText("Accepted refactored code as the current version.");
  setChip(refactorState, "Accepted", "ok");
});
rejectRefactorBtn?.addEventListener("click", () => {
  if (!sourceCodeOriginal) return;
  refactoredBox.textContent = sourceCodeOriginal;
  setRefactorText("Rejected refactor suggestions. Restored original code.");
  setChip(refactorState, "Rejected", "idle");
});
downloadPatchBtn?.addEventListener("click", () => {
  const content = latestRefactoredCode || sourceCodeOriginal;
  if (!content) return;
  const filename = (activeFilename || "snippet.txt").replace(/(\.[^.]+)?$/, ".refactored$1");
  downloadTextFile(filename, content);
  setRefactorText(`Downloaded ${filename}`);
});

initPage();
