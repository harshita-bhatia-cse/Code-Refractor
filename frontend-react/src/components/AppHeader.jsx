import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getApiBase } from "../config.js";
import { clearAuth, getToken, getUser } from "../lib/auth.js";
import { fetchJson } from "../lib/http.js";

export function AppHeader({ title, subtitle, rightSlot }) {
  const navigate = useNavigate();
  const apiBase = useMemo(() => getApiBase(), []);
  const user = getUser();
  const [loggingOut, setLoggingOut] = useState(false);

  async function logout() {
    const token = getToken();
    setLoggingOut(true);
    try {
      await fetchJson(`${apiBase}/auth/github/logout`, {
        method: "POST",
        timeoutMs: 15000,
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // If backend is down, we still clear local auth.
    } finally {
      clearAuth();
      localStorage.removeItem("selected_repo");
      localStorage.removeItem("selected_repo_owner");
      localStorage.removeItem("selected_repo_full_name");
      sessionStorage.removeItem("selected_repo");
      sessionStorage.removeItem("selected_repo_owner");
      sessionStorage.removeItem("selected_repo_full_name");
      setLoggingOut(false);
      navigate("/", { replace: true });
    }
  }

  return (
    <header className="app-header card">
      <div className="app-header__top">
        <div className="app-header__left">
          <Link className="app-brand" to="/dashboard">
            <span className="app-brand__mark" aria-hidden="true">
              🐙
            </span>
            <span className="app-brand__name">CodeRefractor</span>
          </Link>

          {user ? (
            <span className="pill pill--muted" title="Signed in user">
              @{user}
            </span>
          ) : null}
        </div>

        <div className="app-header__right">
          <nav className="app-nav" aria-label="Primary">
            <Link className="app-nav__link" to="/repos">
              Repos
            </Link>
            <Link className="app-nav__link" to="/files">
              Files
            </Link>
          </nav>
          {rightSlot}
          <button className="btn btn--ghost" onClick={logout} disabled={loggingOut}>
            {loggingOut ? "Logging out…" : "Logout"}
          </button>
        </div>
      </div>

      <div className="app-header__bottom">
        <h1 className="app-title__h">{title}</h1>
        {subtitle ? <p className="app-title__sub">{subtitle}</p> : null}
      </div>
    </header>
  );
}

