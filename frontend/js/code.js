// frontend/js/code.js

const params = new URLSearchParams(window.location.search);
const rawUrl = params.get("url");

if (!rawUrl) {
  alert("Invalid file URL");
  window.location.href = "dashboard.html";
}

async function loadCode() {
  try {
    const res = await fetch(
      `http://localhost:8000/code?raw_url=${encodeURIComponent(rawUrl)}`,
      {
        headers: authHeader()
      }
    );

    if (!res.ok) {
      throw new Error("Failed to load code");
    }

    const data = await res.json();
    document.getElementById("codeBox").innerText = data.code;
  } catch (err) {
    alert("Session expired. Please login again.");
    localStorage.clear();
    window.location.href = "index.html";
  }
}

loadCode();
