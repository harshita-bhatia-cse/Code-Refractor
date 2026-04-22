import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getApiBase } from "../config.js";
import { getToken, ingestAuthFromHash } from "../lib/auth.js";

export function LoginPage() {
  const navigate = useNavigate();
  const apiBase = useMemo(() => getApiBase(), []);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const ingested = ingestAuthFromHash();
    const token = getToken();
    if (token) {
      // If we just ingested from hash, land on dashboard.
      if (ingested.didIngest) navigate("/dashboard", { replace: true });
    }
  }, [navigate]);

  function onLogin() {
    setLoading(true);
    // Keep your existing backend flow.
    window.location.href = `${apiBase}/auth/github/login`;
  }

  useEffect(() => {
    const cards = document.querySelectorAll(".feature-card");
    if (!cards.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("show");
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );

    cards.forEach((c) => observer.observe(c));
    return () => observer.disconnect();
  }, []);

  return (
    <div className="login-page">
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            The future of{" "}
            <span
              style={{
                background: "linear-gradient(90deg, #3b82f6, #22c55e)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              code analysis
            </span>{" "}
            starts here
          </h1>
          <p className="hero-subtitle">
            Analyze, refactor, and improve your code with AI-powered insights.
          </p>
        </div>
      </section>

      <div className="login-container">
        <div className={`center-box login-card ${loading ? "loading" : ""}`}>
          <div className="logo">🐙</div>

          <h2>Sign in with GitHub</h2>
          <p>Login to analyze and refactor your code</p>

          <button className="btn github-btn" onClick={onLogin} disabled={loading}>
            Continue with GitHub
          </button>

          <p className="hint">Secure login powered by GitHub</p>
        </div>
      </div>

      <section className="features-section">
        <div className="features-container">
          <h2 className="section-title">What this project does</h2>
          <div className="features-grid">
            <div className="feature-card">
              <h3>GitHub OAuth + Repo Browser</h3>
              <p>Sign in with GitHub, list your repos, and browse files securely (public and private).</p>
            </div>
            <div className="feature-card">
              <h3>Metrics + Quality Scoring</h3>
              <p>Run rule-based metrics across languages and get an overall quality score and risk badges.</p>
            </div>
            <div className="feature-card">
              <h3>RAG-powered Refactoring</h3>
              <p>Generate refactor suggestions with retrieved context so results stay relevant and consistent.</p>
            </div>
            <div className="feature-card">
              <h3>Review + Export</h3>
              <p>Compare original vs refactored code and download the result for review before applying changes.</p>
            </div>
          </div>
        </div>
      </section>

      <footer className="footer">
        <p>&copy; 2026 CodeRefractor. All rights reserved.</p>
      </footer>
    </div>
  );
}

