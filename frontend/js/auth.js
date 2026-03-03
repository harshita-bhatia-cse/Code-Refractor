// frontend/js/auth.js

export function requireAuth() {
  const params = new URLSearchParams(window.location.search);

  // Save token on first redirect
  if (params.get("token")) {
    const token = params.get("token");
    const user = params.get("user");
    sessionStorage.setItem("jwt_token", token);
    sessionStorage.setItem("github_user", user || "");
    localStorage.setItem("jwt_token", token);
    localStorage.setItem("github_user", user || "");

    history.replaceState({}, "", location.pathname);
  }

  const token = localStorage.getItem("jwt_token") || sessionStorage.getItem("jwt_token");
  const user = localStorage.getItem("github_user") || sessionStorage.getItem("github_user");
  if (token) {
    sessionStorage.setItem("jwt_token", token);
    localStorage.setItem("jwt_token", token);
  }
  if (user) {
    sessionStorage.setItem("github_user", user);
    localStorage.setItem("github_user", user);
  }

  if (!token) {
    window.location.href = "index.html";
    throw new Error("No auth token");
  }

  return token;
}
