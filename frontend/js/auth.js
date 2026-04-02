// frontend/js/auth.js

export function requireAuth() {
  const hash = window.location.hash.startsWith("#") ? window.location.hash.slice(1) : "";
  const params = new URLSearchParams(hash);

  if (params.get("token")) {
    const token = params.get("token");
    const user = params.get("user");
    sessionStorage.setItem("jwt_token", token);
    sessionStorage.setItem("github_user", user || "");
    history.replaceState({}, "", location.pathname + location.search);
  }

  const token = sessionStorage.getItem("jwt_token");
  const currentPage = window.location.pathname.split("/").pop();

  if (!token) {
    if (currentPage && currentPage !== "index.html") {
      window.location.href = "index.html";
    }
    throw new Error("No auth token");
  }

  return token;
}
