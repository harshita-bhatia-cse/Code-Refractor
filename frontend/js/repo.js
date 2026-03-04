import API from "./config.js?v=20260301g";
import { requireAuth } from "./auth.js?v=20260301g";

const token = requireAuth();
const repoList = document.getElementById("repoList");

console.log("JWT Token:", token);

async function loadRepos() {
  try {
    const res = await fetch(`${API}/repos/`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

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
      repoList.innerHTML = "<li>No repositories found</li>";
      return;
    }

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

    if (err.message === "UNAUTHORIZED") {
      sessionStorage.clear();
      localStorage.removeItem("jwt_token");
      localStorage.removeItem("github_user");
      localStorage.removeItem("selected_repo");
      window.location.href = "index.html";
    } else {
      repoList.innerHTML =
        "<li style='color:red'>Failed to load repositories</li>";
    }
  }
}

window.openRepo = repo => {
  sessionStorage.setItem("selected_repo", repo);
  localStorage.setItem("selected_repo", repo);
  window.location.href = "files.html";   // go to repo page
};

loadRepos();
