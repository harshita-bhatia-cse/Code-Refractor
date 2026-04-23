import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getApiBase } from "../config.js";
import { getToken } from "../lib/auth.js";
import { fetchJson } from "../lib/http.js";
import { AppHeader } from "../components/AppHeader.jsx";

export function FilesPage() {
  const navigate = useNavigate();
  const apiBase = useMemo(() => getApiBase(), []);
  const repo = localStorage.getItem("selected_repo") || sessionStorage.getItem("selected_repo") || "";

  const [currentPath, setCurrentPath] = useState("");
  const [filter, setFilter] = useState("");
  const [fileStatus, setFileStatus] = useState("Loading files...");
  const [fileStatusColor, setFileStatusColor] = useState("");
  const [items, setItems] = useState([]);

  const [llmHtml, setLlmHtml] = useState("<p>Loading AI analysis...</p>");
  const [llmIsError, setLlmIsError] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  useEffect(() => {
    if (!repo) {
      navigate("/repos", { replace: true });
    }
  }, [repo, navigate]);

  async function loadFiles(nextPath = currentPath) {
    setLoadingFiles(true);
    setFileStatus(nextPath ? `Loading /${nextPath} ...` : "Loading repository root...");
    setFileStatusColor("");

    try {
      const token = getToken();
      const url = nextPath
        ? `${apiBase}/files/${encodeURIComponent(repo)}?path=${encodeURIComponent(nextPath)}`
        : `${apiBase}/files/${encodeURIComponent(repo)}`;

      const { res, body } = await fetchJson(url, {
        timeoutMs: 15000,
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch files");

      setItems(Array.isArray(body) ? body : []);
      setFileStatus(
        `Loaded ${(Array.isArray(body) ? body.length : 0)} item(s)${
          nextPath ? ` from /${nextPath}` : ""
        }.`
      );
    } catch (err) {
      const msg =
        err?.name === "AbortError"
          ? "File request timed out after 15 seconds."
          : "Failed to load files.";
      setFileStatus(msg);
      setFileStatusColor("#b91c1c");
      setItems([]);
    } finally {
      setLoadingFiles(false);
    }
  }

  async function analyzeRepo() {
    setLoadingAnalysis(true);
    setLlmIsError(false);
    setLlmHtml("<p>Running AI analysis...</p>");

    try {
      const token = getToken();
      const { res, body } = await fetchJson(
        `${apiBase}/analyze-repo/?repo_path=${encodeURIComponent(repo)}`,
        {
          method: "POST",
          timeoutMs: 30000,
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!res.ok) throw new Error(typeof body === "string" ? body : "AI analysis failed");

      const ai = body?.result?.ai_analysis;
      const styleProfile = body?.result?.style_profile;
      if (!ai) throw new Error("Unexpected analyze-repo response format.");

      if (styleProfile) {
        localStorage.setItem(`style_profile:${repo}`, JSON.stringify(styleProfile));
        sessionStorage.setItem(`style_profile:${repo}`, JSON.stringify(styleProfile));
      }

      const styleHtml = styleProfile
        ? `
        <h3>Detected Coding Style</h3>
        <p><b>Naming:</b> ${styleProfile.naming}</p>
        <p><b>Indentation:</b> ${styleProfile.indentation}</p>
        <p><b>Comments:</b> ${styleProfile.comments}</p>
        <p><b>Structure:</b> ${styleProfile.structure}</p>
        <p><b>Function Style:</b> ${styleProfile.function_style}</p>
      `
        : "";

      const html = `
        <h3>🤖 AI Repository Analysis</h3>
        <p><b>Maintainability Score:</b> ${ai.maintainability_score}</p>
        <p><b>Complexity Level:</b> ${ai.complexity_level}</p>
        <p><b>Architecture Type:</b> ${ai.architecture_type}</p>

        <p><b>Strengths:</b></p>
        <ul>${(ai.strengths || []).map((s) => `<li>${s}</li>`).join("")}</ul>

        <p><b>Weaknesses:</b></p>
        <ul>${(ai.weaknesses || []).map((w) => `<li>${w}</li>`).join("")}</ul>

        <p><b>Recommendations:</b></p>
        <ul>${(ai.recommendations || []).map((r) => `<li>${r}</li>`).join("")}</ul>

        ${styleHtml}
      `;

      setLlmHtml(html);
    } catch (err) {
      const msg =
        err?.name === "AbortError"
          ? "AI analysis timed out after 30 seconds."
          : `AI analysis failed: ${err?.message || String(err)}`;
      setLlmIsError(true);
      setLlmHtml(`<p>${msg}</p>`);
    } finally {
      setLoadingAnalysis(false);
    }
  }

  useEffect(() => {
    if (!repo) return;
    // Avoid calling state-updaters synchronously inside an effect body.
    const id = setTimeout(() => {
      loadFiles("");
      analyzeRepo();
    }, 0);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repo]);

  function goDir(dirName) {
    const next = currentPath ? `${currentPath}/${dirName}` : dirName;
    setCurrentPath(next);
    loadFiles(next);
  }

  function goBack() {
    const next = currentPath.split("/").slice(0, -1).join("/");
    setCurrentPath(next);
    loadFiles(next);
  }

  function openFile(rawUrl) {
    navigate(`/code?raw_url=${encodeURIComponent(rawUrl)}`);
  }

  const crumbs = currentPath ? currentPath.split("/").filter(Boolean) : [];
  const filteredItems = items.filter((it) => {
    const q = filter.trim().toLowerCase();
    if (!q) return true;
    return String(it?.name || "").toLowerCase().includes(q);
  });

  return (
    <div className="app-page">
      <div className="app-container">
        <AppHeader
          title="Files"
          subtitle={repo ? `Browsing ${repo}` : "Pick a repository to start browsing files."}
          rightSlot={
            <button className="btn btn--ghost" onClick={() => navigate("/repos")}>
              ← Repos
            </button>
          }
        />

        <div className="split">
          <section className="card split__left">
            <div className="section-head">
              <div className="section-head__left">
                <h2 className="h2">Repository tree</h2>
                <span className="status-chip" style={{ color: fileStatusColor || undefined }}>
                  {fileStatus}
                </span>
              </div>

              <div className="section-head__right">
                <div className="breadcrumbs" aria-label="Path breadcrumb">
                  <button className="crumb" onClick={() => loadFiles("")} disabled={loadingFiles}>
                    {repo || "root"}
                  </button>
                  {crumbs.map((c, idx) => {
                    const path = crumbs.slice(0, idx + 1).join("/");
                    return (
                      <button key={path} className="crumb" onClick={() => loadFiles(path)} disabled={loadingFiles}>
                        {c}
                      </button>
                    );
                  })}
                </div>

                <div className="input input--search">
                  <span className="input__icon" aria-hidden="true">
                    ⌕
                  </span>
                  <input
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    placeholder="Filter files…"
                    aria-label="Filter files"
                  />
                </div>

                <button className="btn btn--primary" onClick={() => loadFiles(currentPath)} disabled={loadingFiles}>
                  {loadingFiles ? "Loading…" : "Reload"}
                </button>
              </div>
            </div>

            <ul className="file-list">
              {currentPath ? (
                <li>
                  <button className="file-row file-row--nav" onClick={goBack}>
                    <span>↩</span>
                    <span>Up one level</span>
                  </button>
                </li>
              ) : null}

              {filteredItems.map((item) => {
                if (item?.type === "dir") {
                  return (
                    <li key={`dir:${item.path}`}>
                      <button className="file-row" onClick={() => goDir(item.name)}>
                        <span className="file-row__icon" aria-hidden="true">
                          📁
                        </span>
                        <span className="file-row__name">{item.name}</span>
                        <span className="file-row__action">Open →</span>
                      </button>
                    </li>
                  );
                }
                return (
                  <li key={`file:${item.path}`}>
                    <div className="file-row file-row--file">
                      <span className="file-row__icon" aria-hidden="true">
                        📄
                      </span>
                      <span className="file-row__name mono">{item.name}</span>
                      <button className="btn btn--small" onClick={() => openFile(item.raw_url)}>
                        View
                      </button>
                    </div>
                  </li>
                );
              })}

              {!loadingFiles && filteredItems.length === 0 ? (
                <li className="muted" style={{ padding: "10px 2px" }}>
                  No matching items.
                </li>
              ) : null}
            </ul>
          </section>

          <aside className="card split__right">
            <div className="section-head">
              <div className="section-head__left">
                <h2 className="h2">AI repository summary</h2>
                <span className={`pill ${llmIsError ? "pill--danger" : "pill--muted"}`}>
                  {loadingAnalysis ? "Running…" : llmIsError ? "Error" : "Ready"}
                </span>
              </div>
              <div className="section-head__right">
                <button className="btn btn--primary" onClick={analyzeRepo} disabled={loadingAnalysis}>
                  {loadingAnalysis ? "Analyzing…" : "Re-run analysis"}
                </button>
              </div>
            </div>

            <div
              className="prose"
              style={{ color: llmIsError ? "#fecaca" : undefined }}
              dangerouslySetInnerHTML={{ __html: llmHtml }}
            />
          </aside>
        </div>
      </div>
    </div>
  );
}

