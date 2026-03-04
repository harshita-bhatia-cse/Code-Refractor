import API_BASE from "./config.js?v=20260304c";
import { requireAuth } from "./auth.js?v=20260304c";

const codeBox = document.getElementById("codeBox");
const analysisBox = document.getElementById("analysisBox");
let refactorBox = document.getElementById("refactorBox");
const analysisState = document.getElementById("analysisState");
const refactorState = document.getElementById("refactorState");
const retryAnalysisBtn = document.getElementById("retryAnalysisBtn");
const retryRefactorBtn = document.getElementById("retryRefactorBtn");
const rerunAllBtn = document.getElementById("rerunAllBtn");

let activeToken = "";
let activeRawUrl = "";

function setChip(el, text, tone = "idle") {
  if (!el) return;
  el.textContent = text;
  el.className = `status-chip status-${tone}`;
}

function setRefactorText(text) {
  if (!refactorBox) {
    refactorBox = document.createElement("pre");
    refactorBox.id = "refactorBox";
    refactorBox.style.background = "#0f172a";
    refactorBox.style.color = "#e2e8f0";
    refactorBox.style.padding = "10px";
    refactorBox.style.whiteSpace = "pre-wrap";
    document.body.appendChild(refactorBox);
  }
  if (refactorBox) {
    refactorBox.textContent = text;
  }
}

function setAnalysisText(text) {
  if (analysisBox) {
    analysisBox.textContent = text;
  }
}

// load source code
async function loadCode(rawUrl) {
  try {
    const res = await fetch(rawUrl);
    if (!res.ok) throw new Error("Failed to load code");
    codeBox.textContent = await res.text();
  } catch (err) {
    codeBox.textContent = "Failed to load source code.";
  }
}

// run AI analysis
async function runAnalysis(rawUrl, token) {
  try {
    setChip(analysisState, "Running", "loading");
    setAnalysisText("Running AI analysis...");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);

    const res = await fetch(
      `${API_BASE}/analyze/?raw_url=${encodeURIComponent(rawUrl)}`,
      {
        signal: controller.signal,
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    clearTimeout(timeout);

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt);
    }

    const data = await res.json();
    const text = JSON.stringify(data, null, 2);
    setAnalysisText(text || "AI analysis returned empty response.");
    setChip(analysisState, "Completed", "ok");

  } catch (err) {
    console.error(err);
    const msg = err && err.name === "AbortError"
      ? "AI analysis timed out after 20 seconds."
      : (err.message || String(err));
    setAnalysisText(`AI analysis failed.\n${msg}`);
    setChip(analysisState, "Failed", "error");
  }
}

// run LLM refactor
async function runRefactor(rawUrl, token) {
  try {
    setChip(refactorState, "Running", "loading");
    setRefactorText("Running LLM refactor...");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 45000);

    const res = await fetch(`${API_BASE}/refactor/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      signal: controller.signal,
      body: JSON.stringify({
        raw_url: rawUrl
      })
    });
    clearTimeout(timeout);

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Refactor API failed (${res.status}): ${txt}`);
    }

    const data = await res.json();
    const llm = data.llm_refactor || {};
    const ok = llm.ok === true;

    setRefactorText(
`Status: ${ok ? "OK" : "FAILED"}
${llm.error ? `Error: ${llm.error}\n` : ""}Summary:
${llm.summary || "No summary provided"}

Issues:
${Array.isArray(llm.issues) && llm.issues.length ? llm.issues.map((x, i) => `${i + 1}. ${x}`).join("\n") : "No issues listed"}

Refactored Code:
${llm.refactored_code || "No refactored code returned"}`
    );
    setChip(refactorState, ok ? "Completed" : "Failed", ok ? "ok" : "error");

  } catch (err) {
    console.error(err);
    const msg = err && err.name === "AbortError"
      ? "LLM refactor request timed out after 45 seconds."
      : (err.message || String(err));
    setRefactorText(`LLM refactor failed.\n${msg}`);
    setChip(refactorState, "Failed", "error");
  }
}

async function runAll() {
  if (!activeRawUrl || !activeToken) return;
  await loadCode(activeRawUrl);
  await runAnalysis(activeRawUrl, activeToken);
  await runRefactor(activeRawUrl, activeToken);
}

async function initPage() {
  try {
    setChip(analysisState, "Initializing", "loading");
    setChip(refactorState, "Initializing", "loading");
    setAnalysisText("Initializing...");
    setRefactorText("Initializing...");

    const token = requireAuth();
    const params = new URLSearchParams(window.location.search);
    const rawUrl = params.get("raw_url");
    activeToken = token;
    activeRawUrl = rawUrl || "";

    if (!rawUrl || !rawUrl.startsWith("http")) {
      setAnalysisText("Invalid file URL");
      setRefactorText("LLM refactor failed.\nInvalid raw_url");
      setChip(analysisState, "Invalid URL", "error");
      setChip(refactorState, "Invalid URL", "error");
      return;
    }

    await runAll();
  } catch (err) {
    console.error(err);
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

initPage();
