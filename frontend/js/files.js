import API_BASE from "./config.js?v=20260301g";
import { requireAuth } from "./auth.js?v=20260301g";

const repo = localStorage.getItem("selected_repo") || sessionStorage.getItem("selected_repo");
const token = requireAuth();

const fileList = document.getElementById("fileList");
const llmBox = document.getElementById("llmBox");

let currentPath = "";

if (!repo) {
  alert("Repository not selected");
  window.location.href = "repo.html";
}

// ==========================================
// 📂 LOAD FILES (folders + files)
// ==========================================
async function loadFiles() {
  try {
    const url = currentPath
      ? `${API_BASE}/files/${encodeURIComponent(repo)}?path=${encodeURIComponent(currentPath)}`
      : `${API_BASE}/files/${encodeURIComponent(repo)}`;

    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (!res.ok) throw new Error("Failed to fetch files");

    const files = await res.json();
    fileList.innerHTML = "";

    // 🔙 Back button
    if (currentPath) {
      const back = document.createElement("li");
      back.textContent = "🔙 Back";
      back.style.cursor = "pointer";
      back.onclick = () => {
        currentPath = currentPath.split("/").slice(0, -1).join("/");
        loadFiles();
      };
      fileList.appendChild(back);
    }

    files.forEach(item => {
      const li = document.createElement("li");

      if (item.type === "dir") {
        li.textContent = `📁 ${item.name}`;
        li.style.cursor = "pointer";
        li.onclick = () => {
          currentPath = currentPath
            ? `${currentPath}/${item.name}`
            : item.name;
          loadFiles();
        };
      } else {
        const qs = new URLSearchParams({
          raw_url: item.raw_url
        });
        li.innerHTML = `
          📄 <a href="code.html?${qs.toString()}">
            ${item.name}
          </a>
        `;
      }

      fileList.appendChild(li);
    });

  } catch (err) {
    console.error(err);
    fileList.innerHTML =
      "<li style='color:red'>Failed to load files</li>";
  }
}

// ==========================================
// 🤖 RUN LLM REPO ANALYSIS
// ==========================================
async function analyzeRepo() {
  try {
    llmBox.innerHTML = "<p>Running AI analysis...</p>";

    const response = await fetch(
      `${API_BASE}/analyze-repo/?repo_path=${encodeURIComponent(repo)}`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (!response.ok) {
      const txt = await response.text();
      throw new Error(txt);
    }

    const data = await response.json();
    const ai = data.result.ai_analysis;

    llmBox.innerHTML = `
      <h3>🤖 AI Repository Analysis</h3>
      <p><b>Maintainability Score:</b> ${ai.maintainability_score}</p>
      <p><b>Complexity Level:</b> ${ai.complexity_level}</p>
      <p><b>Architecture Type:</b> ${ai.architecture_type}</p>

      <p><b>Strengths:</b></p>
      <ul>${ai.strengths.map(s => `<li>${s}</li>`).join("")}</ul>

      <p><b>Weaknesses:</b></p>
      <ul>${ai.weaknesses.map(w => `<li>${w}</li>`).join("")}</ul>

      <p><b>Recommendations:</b></p>
      <ul>${ai.recommendations.map(r => `<li>${r}</li>`).join("")}</ul>
    `;

  } catch (err) {
    console.error("AI Analysis failed:", err);
    llmBox.innerHTML =
      "<p style='color:red'>AI analysis failed.</p>";
  }
}

// ==========================================
// 🚀 INIT
// ==========================================
loadFiles();
analyzeRepo();
