// async function loadRepos() {
//   console.log("loadRepos() called");

//   const token = localStorage.getItem("jwt_token");
//   console.log("JWT token:", token);

//   if (!token) {
//     alert("NO TOKEN FOUND");
//     return;
//   }

//   try {
//     const res = await fetch("http://127.0.0.1:8000/repos/", {
//       method: "GET",
//       headers: {
//         "Authorization": "Bearer " + token
//       }
//     });

//     console.log("Response status:", res.status);

//     const text = await res.text();
//     console.log("Raw response:", text);

//     if (!res.ok) {
//       alert("API FAILED: " + res.status);
//       return;
//     }

//     const repos = JSON.parse(text);
//     const ul = document.getElementById("repoList");
//     ul.innerHTML = "";

//     repos.forEach(repo => {
//       const li = document.createElement("li");
//       li.innerText = repo.name;
//       ul.appendChild(li);
//     });

//   } catch (err) {
//     console.error("FETCH ERROR:", err);
//     alert("Fetch error – check console");
//   }
// }

// loadRepos();


// repo.js - Fetch and display GitHub repositories

const API_BASE = "http://127.0.0.1:8000";


async function loadRepos() {
  const token = localStorage.getItem("jwt_token");
  
  if (!token) {
    alert("Please login first");
    window.location.href = "index.html";
    return;
  }

  const repoList = document.getElementById("repoList");
  repoList.innerHTML = "<li>Loading repositories...</li>";

  try {
    const response = await fetch(`${API_BASE}/repos/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        alert("Session expired. Please login again.");
        localStorage.clear();
        window.location.href = "index.html";
        return;
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const repos = await response.json();

    if (repos.length === 0) {
      repoList.innerHTML = "<li>No repositories found</li>";
      return;
    }

    repoList.innerHTML = "";
    repos.forEach((repo) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <div class="repo-item">
          <strong>${repo.name}</strong>
          ${repo.private ? '<span class="badge">Private</span>' : '<span class="badge public">Public</span>'}
          <br />
          <a href="${repo.url}" target="_blank">View on GitHub</a>
          <button onclick="viewFiles('${repo.name}')">Browse Files</button>
        </div>
      `;
      repoList.appendChild(li);
    });
  } catch (error) {
    console.error("Error loading repos:", error);
    repoList.innerHTML = `<li style="color: red;">Error loading repositories: ${error.message}</li>`;
  }
}

function viewFiles(repoName) {
  localStorage.setItem("selected_repo", repoName);
  window.location.href = "files.html";
}

// Load repos when page loads
window.addEventListener("DOMContentLoaded", loadRepos);