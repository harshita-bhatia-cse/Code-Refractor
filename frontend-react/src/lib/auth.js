export function ingestAuthFromHash() {
  const hash = window.location.hash?.startsWith("#") ? window.location.hash.slice(1) : "";
  if (!hash) return { didIngest: false };

  const params = new URLSearchParams(hash);
  const token = params.get("token");
  if (!token) return { didIngest: false };

  const user = params.get("user") || "";
  sessionStorage.setItem("jwt_token", token);
  sessionStorage.setItem("github_user", user);

  history.replaceState({}, "", window.location.pathname + window.location.search);
  return { didIngest: true, token, user };
}

export function getToken() {
  return sessionStorage.getItem("jwt_token") || "";
}

export function getUser() {
  return sessionStorage.getItem("github_user") || "";
}

export function clearAuth() {
  sessionStorage.removeItem("jwt_token");
  sessionStorage.removeItem("github_user");
}

