const hostname = window.location.hostname;

const API_BASE =
  hostname === "localhost" ||
  hostname === "127.0.0.1" ||
  hostname === "::1"
    ? "http://127.0.0.1:8000"
    : "https://YOUR-BACKEND-URL.onrender.com";

export default API_BASE;
