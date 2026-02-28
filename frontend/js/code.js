import API_BASE from "./config.js";
import { requireAuth } from "./auth.js";

const codeBox = document.getElementById("codeBox");
const analysisBox = document.getElementById("analysisBox");
let refactorBox = document.getElementById("refactorBox");

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
    const res = await fetch(
      `${API_BASE}/analyze/?raw_url=${encodeURIComponent(rawUrl)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt);
    }

    const data = await res.json();
    analysisBox.textContent = JSON.stringify(data, null, 2);

  } catch (err) {
    console.error(err);
    analysisBox.textContent = "AI analysis failed.";
  }
}

// run LLM refactor
async function runRefactor(rawUrl, token) {
  try {
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

  } catch (err) {
    console.error(err);
    const msg = err && err.name === "AbortError"
      ? "LLM refactor request timed out after 45 seconds."
      : (err.message || String(err));
    setRefactorText(`LLM refactor failed.\n${msg}`);
  }
}

async function initPage() {
  try {
    setRefactorText("Initializing...");

    const token = requireAuth();
    const params = new URLSearchParams(window.location.search);
    const rawUrl = params.get("raw_url");

    if (!rawUrl || !rawUrl.startsWith("http")) {
      analysisBox.textContent = "Invalid file URL";
      setRefactorText("LLM refactor failed.\nInvalid raw_url");
      return;
    }

    await loadCode(rawUrl);
    await runAnalysis(rawUrl, token);
    await runRefactor(rawUrl, token);
  } catch (err) {
    console.error(err);
    setRefactorText(`Initialization failed.\n${err.message || err}`);
  }
}

initPage();
