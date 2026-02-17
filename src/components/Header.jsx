import { Moon, Sun } from "lucide-react";

function Header({ projectName, darkMode, onToggleTheme }) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/80 px-6 py-4 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/70">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 md:text-2xl">
            {projectName}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Real-time dashboard for refactoring outcomes
          </p>
        </div>

        <button
          onClick={onToggleTheme}
          className="group flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-slate-500"
          aria-label="Toggle theme"
        >
          {darkMode ? (
            <Sun size={16} className="text-amber-400" />
          ) : (
            <Moon size={16} className="text-blue-500" />
          )}
          {darkMode ? "Light" : "Dark"}
        </button>
      </div>
    </header>
  );
}

export default Header;
