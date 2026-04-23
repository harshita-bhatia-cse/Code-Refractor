import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getApiBase } from "../config.js";
import { getToken } from "../lib/auth.js";
import { fetchJson } from "../lib/http.js";

function inferFilename(rawUrl) {
  if (!rawUrl) return "snippet.txt";
  try {
    const url = new URL(rawUrl);
    const segments = url.pathname.split("/").filter(Boolean);
    return segments[segments.length - 1] || "snippet.txt";
  } catch {
    return "snippet.txt";
  }
}

function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function CodePage() {
  const navigate = useNavigate();
  const apiBase = useMemo(() => getApiBase(), []);
  const [params] = useSearchParams();
  const rawUrl = params.get("raw_url") || "";
  const activeFilename = useMemo(() => inferFilename(rawUrl), [rawUrl]);
  const activeRepo = localStorage.getItem("selected_repo") || sessionStorage.getItem("selected_repo") || "";
  const activeStyleProfile = useMemo(() => loadStyleProfile(activeRepo), [activeRepo]);

  const [analysisState, setAnalysisState] = useState({ text: "Idle", tone: "idle" });
  const [refactorState, setRefactorState] = useState({ text: "Idle", tone: "idle" });
  const [qualitySummary, setQualitySummary] = useState("");
  const [qualityBadges, setQualityBadges] = useState([]);

  const [sourceCodeOriginal, setSourceCodeOriginal] = useState("");
  const [refactoredCode, setRefactoredCode] = useState("");
  const [analysisText, setAnalysisText] = useState("");
  const [refactorText, setRefactorText] = useState("");

  const [runningAll, setRunningAll] = useState(false);

  useEffect(() => {
    if (!rawUrl) {
      navigate("/files", { replace: true });
    }
  }, [rawUrl, navigate]);

  async function loadCode() {
    const res = await fetch(rawUrl);
    const text = await res.text();
    setSourceCodeOriginal(text);
    setRefactoredCode("Waiting for refactor...");
  }

  async function runAnalysis() {
    setAnalysisState({ text: "Running", tone: "loading" });
    try {
      const token = getToken();
      const { res, body } = await fetchJson(
        `${apiBase}/analyze/?raw_url=${encodeURIComponent(rawUrl)}`,
        { timeoutMs: 15000, headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Analysis failed");
      setAnalysisText(JSON.stringify(body, null, 2));

      const score = body?.overall_quality_score;
      const grade = body?.overall_grade;
      const badges = body?.overall_risk_badges || [];
      if (typeof score === "number") {
        setQualitySummary(`Score: ${score}/100 • Grade: ${grade}`);
        setQualityBadges(Array.isArray(badges) ? badges : []);
      }

      setAnalysisState({ text: "Completed", tone: "ok" });
    } catch {
      setAnalysisText("Analysis failed");
      setAnalysisState({ text: "Failed", tone: "error" });
    }
  }

  async function runRefactor() {
    setRefactorState({ text: "Running", tone: "loading" });
    setRefactorText("Running LLM refactor...");
    try {
      const token = getToken();
      const payload = { raw_url: rawUrl };
      if (activeStyleProfile) {
        payload.style_profile = activeStyleProfile;
      }

      const { res, body } = await fetchJson(`${apiBase}/refactor/`, {
        method: "POST",
        timeoutMs: 30000,
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Refactor failed");

      const llm = body?.llm_refactor || {};
      const isSuccess = llm.ok === true;
      const isSkipped = llm.skipped === true;
      const isFallback = llm.fallback === true;

      const latest = llm.refactored_code || sourceCodeOriginal;
      setRefactoredCode(latest);

      let status = "Completed";
      let tone = "ok";
      if (isSkipped) {
        status = "Skipped";
        tone = "idle";
      } else if (isFallback) {
        status = "Fallback";
        tone = "idle";
      } else if (!isSuccess) {
        status = "Failed";
        tone = "error";
      }

      setRefactorText(
        `Status: ${status}\n` +
          `${llm.reason ? "Reason: " + llm.reason + "\n\n" : "\n"}` +
          `Style Profile: ${
            activeStyleProfile ? "GitHub repository profile applied" : "inferred from current file only"
          }\n\n` +
          `Summary:\n${llm.summary || "No summary"}\n\n` +
          `Issues:\n${(llm.issues || []).join("\n") || "None"}`
      );
      setRefactorState({ text: status, tone });
    } catch (err) {
      setRefactorText(
        `⚠️ Refactor unavailable\n\nReason:\n${err?.message || String(err)}\n\n👉 Showing original code`
      );
      setRefactoredCode(sourceCodeOriginal);
      setRefactorState({ text: "Unavailable", tone: "idle" });
    }
  }

  async function runAll() {
    if (runningAll) return;
    setRunningAll(true);
    try {
      await loadCode();
      await runAnalysis();
      await runRefactor();
    } finally {
      setRunningAll(false);
    }
  }

  useEffect(() => {
    if (!rawUrl) return;
    // Avoid calling state-updaters synchronously inside an effect body.
    const id = setTimeout(() => {
      runAll();
    }, 0);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rawUrl]);

  function acceptRefactor() {
    if (!refactoredCode) return;
    setSourceCodeOriginal(refactoredCode);
    setRefactorText("Accepted refactored code as the current version.");
    setRefactorState({ text: "Accepted", tone: "ok" });
  }

  function rejectRefactor() {
    if (!sourceCodeOriginal) return;
    setRefactoredCode(sourceCodeOriginal);
    setRefactorText("Rejected refactor suggestions. Restored original code.");
    setRefactorState({ text: "Rejected", tone: "idle" });
  }

  function downloadPatch() {
    const content = refactoredCode || sourceCodeOriginal;
    if (!content) return;
    const filename = (activeFilename || "snippet.txt").replace(/(\.[^.]+)?$/, ".refactored$1");
    downloadTextFile(filename, content);
    setRefactorText(`Downloaded ${filename}`);
  }

  const analysisChipClass = `status-chip status-${analysisState.tone}`;
  const refactorChipClass = `status-chip status-${refactorState.tone}`;

  return (
    <div className="code-page">
      <div className="code-layout">
        <aside className="code-sidebar">
          <div className="sidebar-header">
            <h1>CodeRefractor</h1>
            <p>Analyze and refactor code with AI</p>
          </div>

          <div className="sidebar-actions">
            <button className="sidebar-btn primary" onClick={runAll} disabled={runningAll}>
              <span className="btn-icon">🔁</span> Rerun All
            </button>
            <button className="sidebar-btn info" onClick={runAnalysis}>
              <span className="btn-icon">🔍</span> Retry Analysis
            </button>
            <button className="sidebar-btn info" onClick={runRefactor}>
              <span className="btn-icon">🧠</span> Retry Refactor
            </button>
            <button className="sidebar-btn success" onClick={acceptRefactor}>
              <span className="btn-icon">✅</span> Accept Refactor
            </button>
            <button className="sidebar-btn danger" onClick={rejectRefactor}>
              <span className="btn-icon">❌</span> Reject Refactor
            </button>
            <button className="sidebar-btn primary" onClick={downloadPatch}>
              <span className="btn-icon">⬇️</span> Download Patch
            </button>
            <button className="sidebar-btn danger" onClick={() => navigate("/files")}>
              <span className="btn-icon">←</span> Back to Files
            </button>
          </div>
        </aside>

        <main className="code-content">
          <header className="code-header">
            <h2>Code Viewer</h2>
            <p>{activeFilename}</p>
          </header>

          <section className="quality-section">
            <div className="section-title-bar">
              <h3>Quality Summary</h3>
              <div className="section-right">
                <span id="analysisState" className={analysisChipClass}>
                  {analysisState.text}
                </span>
                <span id="refactorState" className={refactorChipClass}>
                  {refactorState.text}
                </span>
              </div>
            </div>
            <div className="quality-card big-card">
              <div id="qualitySummary" className="quality-score">
                {qualitySummary || "Score: —"}
              </div>
              <div id="qualityBadges" className="badge-row">
                {qualityBadges.map((b) => (
                  <span key={b} className="risk-badge">
                    {b}
                  </span>
                ))}
              </div>
            </div>
          </section>

          <section className="code-section">
            <div className="section-title-bar">
              <h3>Original Code</h3>
            </div>
            <pre id="originalBox" className="panel-pre">
              {sourceCodeOriginal || "Loading code..."}
            </pre>
          </section>

          <section className="diff-section">
            <div className="section-title-bar">
              <h3>Refactored Code</h3>
            </div>
            <pre id="refactoredBox" className="panel-pre panel-pre-success">
              {refactoredCode || "Waiting for refactor..."}
            </pre>
          </section>

          <section className="analysis-section">
            <div className="section-title-bar">
              <h3>Analysis JSON</h3>
            </div>
            <pre id="analysisBox" className="panel-pre panel-pre-info">
              {analysisText || "Waiting for analysis..."}
            </pre>
          </section>

          <section className="refactor-section">
            <div className="section-title-bar">
              <h3>Refactor Notes</h3>
            </div>
            <pre id="refactorBox" className="panel-pre panel-pre-info">
              {refactorText || "Waiting for refactor..."}
            </pre>
          </section>
        </main>
      </div>
    </div>
  );
}

function loadStyleProfile(repo) {
  if (!repo) return null;

  const rawProfile =
    sessionStorage.getItem(`style_profile:${repo}`) ||
    localStorage.getItem(`style_profile:${repo}`);

  if (!rawProfile) return null;

  try {
    return JSON.parse(rawProfile);
  } catch {
    return null;
  }
}

