export function getApiBase() {
  const hostname = window.location.hostname;
  if (hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1") {
    return "http://127.0.0.1:8000";
  }
  return "https://code-refractor-1.onrender.com";
}

