// frontend/js/auth.js

export function requireAuth() {
  const params = new URLSearchParams(window.location.search);

  // Save token on first redirect
  if (params.get("token")) {
    localStorage.setItem("jwt_token", params.get("token"));
    localStorage.setItem("github_user", params.get("user"));

    history.replaceState({}, "", location.pathname);
  }

  const token = localStorage.getItem("jwt_token");

  if (!token) {
    window.location.href = "index.html";
    throw new Error("No auth token");
  }

  return token;
}
