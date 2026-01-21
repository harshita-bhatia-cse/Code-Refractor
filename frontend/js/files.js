// // frontend/js/files.js

// // 1️⃣ Get repo name (from localStorage FIRST)
// let repo = localStorage.getItem("selected_repo");

// // Optional fallback (future-proof)
// if (!repo) {
//   const params = new URLSearchParams(window.location.search);
//   repo = params.get("repo");
// }

// // 2️⃣ If still not found → go back to repo list
// if (!repo) {
//   alert("Repository not selected");
//   window.location.href = "repo.html";
// }

// // 3️⃣ Load files
// async function loadFiles() {
//   try {
//     const res = await fetch(
//       `http://127.0.0.1:8000/files/${encodeURIComponent(repo)}`,
//       {
//         headers: authHeader()
//       }
//     );

//     if (!res.ok) {
//       throw new Error("Failed to fetch files");
//     }

//     const files = await res.json();
//     const ul = document.getElementById("fileList");
//     ul.innerHTML = "";

//     files.forEach(file => {
//       const li = document.createElement("li");
//       li.innerHTML = `
//         <a href="code.html?url=${encodeURIComponent(file.url)}">
//           ${file.name}
//         </a>
//       `;
//       ul.appendChild(li);
//     });

//   } catch (err) {
//     console.error(err);
//     alert("Session expired. Please login again.");
//     localStorage.clear();
//     window.location.href = "index.html";
//   }
// }

// // 4️⃣ Call loader
// loadFiles();

// frontend/js/files.js

// 1️⃣ Get repo ONLY from localStorage (this is your design)
const repo = localStorage.getItem("selected_repo");

if (!repo) {
  alert("Repository not selected");
  window.location.href = "repo.html";
}

// 2️⃣ Load files
async function loadFiles() {
  try {
    const res = await fetch(
      `http://127.0.0.1:8000/files/${encodeURIComponent(repo)}`,
      {
        headers: authHeader()
      }
    );

    if (!res.ok) {
      throw new Error("Failed to fetch files");
    }

    const files = await res.json();
    const ul = document.getElementById("fileList");
    ul.innerHTML = "";

    files.forEach(file => {
      const li = document.createElement("li");
      li.innerHTML = `
        <a href="code.html?url=${encodeURIComponent(file.url)}">
          ${file.name}
        </a>
      `;
      ul.appendChild(li);
    });

  } catch (err) {
    console.error(err);
    alert("Session expired. Please login again.");
    localStorage.clear();
    window.location.href = "index.html";
  }
}

// 3️⃣ Run
loadFiles();
