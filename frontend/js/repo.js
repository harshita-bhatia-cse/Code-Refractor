import API from "./config.js?v=20260304c";
import { requireAuth } from "./auth.js?v=20260304c";

const token = requireAuth();
const repoList = document.getElementById("repoList");
const repoStatus = document.getElementById("repoStatus");
const retryRepoBtn = document.getElementById("retryRepoBtn");

function setStatus(text, color = "") {
  if (!repoStatus) return;
  repoStatus.textContent = text;
  repoStatus.style.color = color || "#e2e8f0";
}

async function loadRepos() {
  try {
    setStatus("Loading repositories...");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    const res = await fetch(`${API}/repos/`, {
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    clearTimeout(timeout);

    if (res.status === 401) {
      throw new Error("UNAUTHORIZED");
    }

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt);
    }

    const repos = await res.json();

    repoList.innerHTML = "";

    if (!Array.isArray(repos) || repos.length === 0) {
      setStatus("No repositories found.");
      repoList.innerHTML = "<li>No repositories found</li>";
      return;
    }
    setStatus(`Loaded ${repos.length} repositories.`);

    repos.forEach(repo => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${repo.name}</strong>
        <button onclick="openRepo('${repo.name}')">Open</button>
      `;
      repoList.appendChild(li);
    });

  } catch (err) {
    console.error("Repo load failed:", err);
    const msg = err && err.name === "AbortError"
      ? "Repository request timed out after 15 seconds."
      : "Failed to load repositories.";

    if (err.message === "UNAUTHORIZED") {
      setStatus("Session expired. Redirecting to login...", "#b91c1c");
      sessionStorage.clear();
      localStorage.removeItem("jwt_token");
      localStorage.removeItem("github_user");
      localStorage.removeItem("selected_repo");
      window.location.href = "index.html";
    } else {
      setStatus(msg, "#b91c1c");
      repoList.innerHTML =
        "<li style='color:red'>Failed to load repositories</li>";
    }
  }
}

if (retryRepoBtn) {
  retryRepoBtn.addEventListener("click", () => {
    loadRepos();
  });
}

window.openRepo = repo => {
  sessionStorage.setItem("selected_repo", repo);
  localStorage.setItem("selected_repo", repo);
  window.location.href = "files.html";   // go to repo page
};

loadRepos();
