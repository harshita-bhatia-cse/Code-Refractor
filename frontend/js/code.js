import API_BASE from "./config.js";
import { requireAuth } from "./auth.js";

const token = requireAuth();

// read raw_url from query params
const params = new URLSearchParams(window.location.search);
const rawUrl = params.get("raw_url");

const codeBox = document.getElementById("codeBox");
const analysisBox = document.getElementById("analysisBox");

// safety check
if (!rawUrl || !rawUrl.startsWith("http")) {
  analysisBox.textContent = "Invalid file URL";
  throw new Error("Invalid raw_url");
}

// load source code
async function loadCode() {
  try {
    const res = await fetch(rawUrl);
    if (!res.ok) throw new Error("Failed to load code");
    codeBox.textContent = await res.text();
  } catch (err) {
    codeBox.textContent = "Failed to load source code.";
  }
}

// run AI analysis
async function runAnalysis() {
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

loadCode();
runAnalysis();
