import API_BASE from "./config.js";
import { requireAuth } from "./auth.js";

const repo = localStorage.getItem("selected_repo");
const token = requireAuth();
const fileList = document.getElementById("fileList");

let currentPath = "";

if (!repo) {
  alert("Repository not selected");
  window.location.href = "repo.html";
}

// 🔥 Load files (folders + files)
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
        li.innerHTML = `
          📄 <a href="code.html?raw_url=${encodeURIComponent(item.raw_url)}">
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

loadFiles();
