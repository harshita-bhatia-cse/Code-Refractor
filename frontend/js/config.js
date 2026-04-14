
const hostname = window.location.hostname;

let API_BASE;

if (
  hostname === "localhost" ||
  hostname === "127.0.0.1" ||
  hostname === "::1"
) {
  API_BASE = "http://127.0.0.1:8000";
} else {
  API_BASE = "https://YOUR-BACKEND-URL.onrender.com";
}

// 🔥 DEBUG LOG
console.log("API_BASE:", API_BASE);

export default API_BASE;