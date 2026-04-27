import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getUser } from "../lib/auth.js";
import { AppHeader } from "../components/AppHeader.jsx";

export function DashboardPage() {
  const navigate = useNavigate();
  const user = getUser();
  const [loadingRepos, setLoadingRepos] = useState(false);

  function goRepos() {
    setLoadingRepos(true);
    navigate("/repos");
  }

  return (
    <div className="app-page">
      <div className="app-container">
        <AppHeader
          title="Dashboard"
          subtitle={user ? `Welcome back, ${user}.` : "Welcome back."}
          rightSlot={
            <span className="pill pill--muted mono" title="Build tag">
              build 20260301b
            </span>
          }
        />

        <div className="grid grid--2">
          <div className="card">
            <h2 className="h2">Start here</h2>
            <p className="muted" style={{ marginTop: 6 }}>
              Select a repository, browse files, run metrics, then generate an AI-assisted refactor with RAG context.
            </p>

            <div className="card__actions">
              <button
                className={`btn btn--primary ${loadingRepos ? "is-loading" : ""}`}
                onClick={goRepos}
                disabled={loadingRepos}
              >
                {loadingRepos ? "Opening…" : "View repositories"}
              </button>
            </div>
          </div>

          <div className="card">
            <h2 className="h2">What you can do</h2>
            <ul className="checklist">
              <li>
                <span className="checklist__dot" aria-hidden="true">
                  ✓
                </span>
                Browse GitHub repos (public/private) with OAuth
              </li>
              <li>
                <span className="checklist__dot" aria-hidden="true">
                  ✓
                </span>
                Run multi-language metrics and quality scoring
              </li>
              <li>
                <span className="checklist__dot" aria-hidden="true">
                  ✓
                </span>
                Generate refactors with context retrieval (RAG)
              </li>
              <li>
                <span className="checklist__dot" aria-hidden="true">
                  ✓
                </span>
                Download the refactored patch and review changes
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

