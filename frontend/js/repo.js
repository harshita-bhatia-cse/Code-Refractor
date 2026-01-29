import API from "./config.js";
import { requireAuth } from "./auth.js";

const token = requireAuth();
const repoList = document.getElementById("repoList");

// DEBUG: confirm token
console.log("JWT Token:", token);

async function loadRepos() {
  try {
    const res = await fetch(`${API}/repos/`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    console.log("Repos response status:", res.status);

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
      localStorage.clear();
      window.location.href = "index.html";
    } else {
      repoList.innerHTML =
        "<li style='color:red'>Failed to load repositories</li>";
    }
  }
}

window.openRepo = repo => {
  localStorage.setItem("selected_repo", repo);
  window.location.href = "files.html";
};

loadRepos();
