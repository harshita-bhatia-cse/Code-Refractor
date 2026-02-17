import { useEffect, useMemo, useState } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import { useRefactorData } from "./hooks/useRefactorData";
import BeforeAfterSection from "./sections/BeforeAfterSection";
import OverviewSection from "./sections/OverviewSection";
import RefactorMetricsSection from "./sections/RefactorMetricsSection";
import ReportsSection from "./sections/ReportsSection";
import SettingsSection from "./sections/SettingsSection";

const sectionKeyMap = {
  Overview: "overview",
  "Refactor Metrics": "metrics",
  "Before vs After": "comparison",
  Reports: "reports",
  Settings: "settings",
};

function App() {
  const data = useRefactorData();
  const [activeSection, setActiveSection] = useState("Overview");
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem("theme");
    if (stored) return stored === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const content = useMemo(() => {
    switch (sectionKeyMap[activeSection]) {
      case "overview":
        return <OverviewSection overview={data.overview} />;
      case "metrics":
        return (
          <RefactorMetricsSection
            complexityTrend={data.complexityTrend}
            duplicateCodeTrend={data.duplicateCodeTrend}
          />
        );
      case "comparison":
        return <BeforeAfterSection data={data.beforeAfter} />;
      case "reports":
        return <ReportsSection rows={data.reports} />;
      case "settings":
        return (
          <SettingsSection
            darkMode={darkMode}
            onToggleTheme={() => setDarkMode((prev) => !prev)}
          />
        );
      default:
        return null;
    }
  }, [activeSection, darkMode, data]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-cyan-50 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Main app shell: responsive sidebar + dashboard content */}
      <div className="flex min-h-screen flex-col lg:flex-row">
        <Sidebar activeSection={activeSection} onSelect={setActiveSection} />

        <main className="flex-1">
          <Header
            projectName={data.projectName}
            darkMode={darkMode}
            onToggleTheme={() => setDarkMode((prev) => !prev)}
          />

          {/* Active dashboard section content */}
          <div className="p-4 md:p-6">{content}</div>
        </main>
      </div>
    </div>
  );
}

export default App;
