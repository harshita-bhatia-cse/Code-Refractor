import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getApiBase } from "../config.js";
import { clearAuth, getToken } from "../lib/auth.js";
import { fetchJson } from "../lib/http.js";
import { AppHeader } from "../components/AppHeader.jsx";

export function ReposPage() {
  const navigate = useNavigate();
  const apiBase = useMemo(() => getApiBase(), []);

  const [status, setStatus] = useState("Loading repositories...");
  const [statusColor, setStatusColor] = useState("");
  const [loading, setLoading] = useState(true);
  const [repos, setRepos] = useState([]);
  const [query, setQuery] = useState("");

  async function loadRepos() {
    setLoading(true);
    setStatus("Loading repositories...");
    setStatusColor("");

    try {
      const token = getToken();
      const { res, body } = await fetchJson(`${apiBase}/repos/`, {
        timeoutMs: 15000,
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 401) throw new Error("UNAUTHORIZED");
      if (!res.ok) throw new Error(typeof body === "string" ? body : "Failed to load repositories.");

      if (!Array.isArray(body) || body.length === 0) {
        setRepos([]);
        setStatus("No repositories found.");
      } else {
        setRepos(body);
        setStatus(`Loaded ${body.length} repositories.`);
      }
    } catch (err) {
      if (err?.message === "UNAUTHORIZED") {
        setStatus("Session expired. Redirecting to login...");
        setStatusColor("#b91c1c");
        clearAuth();
        localStorage.removeItem("selected_repo");
        navigate("/", { replace: true });
        return;
      }

      const msg =
        err?.name === "AbortError"
          ? "Repository request timed out after 15 seconds."
          : "Failed to load repositories.";
      setStatus(msg);
      setStatusColor("#b91c1c");
      setRepos([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Avoid calling state-updaters synchronously inside an effect body.
    const id = setTimeout(() => {
      loadRepos();
    }, 0);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function openRepo(repo) {
    const repoName = repo?.name || "";
    const repoOwner = repo?.owner || "";
    const repoFullName = repo?.full_name || (repoOwner && repoName ? `${repoOwner}/${repoName}` : repoName);

    sessionStorage.setItem("selected_repo", repoName);
    localStorage.setItem("selected_repo", repoName);
    sessionStorage.setItem("selected_repo_owner", repoOwner);
    localStorage.setItem("selected_repo_owner", repoOwner);
    sessionStorage.setItem("selected_repo_full_name", repoFullName);
    localStorage.setItem("selected_repo_full_name", repoFullName);
    navigate("/files");
  }

  const filtered = repos.filter((r) => {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    const hay = `${r?.full_name || ""} ${r?.name || ""}`.toLowerCase();
    return hay.includes(q);
  });

  return (
    <div className="app-page">
      <div className="app-container">
        <AppHeader
          title="Repositories"
          subtitle="Pick a repo to browse files, run metrics, and generate refactor suggestions."
          rightSlot={
            <button className="btn btn--ghost" onClick={() => navigate("/dashboard")}>
              ← Dashboard
            </button>
          }
        />

        <div className="toolbar card">
          <div className="toolbar__left">
            <span className="status-chip" style={{ color: statusColor || undefined }}>
              {status}
            </span>
          </div>
          <div className="toolbar__right">
            <div className="input input--search">
              <span className="input__icon" aria-hidden="true">
                ⌕
              </span>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search repositories…"
                aria-label="Search repositories"
              />
            </div>
            <button className="btn btn--primary" onClick={loadRepos} disabled={loading}>
              {loading ? "Loading…" : "Reload"}
            </button>
          </div>
        </div>

        <div className="repo-grid">
          {loading ? (
            <div className="card card--center">
              <div className="loading-spinner" />
              <p>Loading your repositories…</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="card card--center">
              <h3 style={{ marginBottom: 6, color: "var(--text)" }}>No repositories</h3>
              <p className="muted">Try a different search, or check GitHub permissions.</p>
            </div>
          ) : (
            filtered.map((repo) => (
              <button
                key={repo?.full_name || repo?.name}
                className="repo-card"
                onClick={() => openRepo(repo)}
              >
                <div className="repo-card__top">
                  <div className="repo-card__name">
                    <span aria-hidden="true">📦</span> {repo?.name}
                  </div>
                  <div className="repo-card__badges">
                    {repo?.private ? <span className="pill pill--warn">Private</span> : <span className="pill">Public</span>}
                    {repo?.owner ? <span className="pill pill--muted">{repo.owner}</span> : null}
                  </div>
                </div>
                <div className="repo-card__meta">
                  <span className="muted mono">{repo?.full_name || repo?.name}</span>
                  <span className="repo-card__cta">Open →</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

