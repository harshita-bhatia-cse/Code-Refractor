import SectionCard from "../components/SectionCard";

function SettingsSection({ darkMode, onToggleTheme }) {
  return (
    <section id="settings">
      <SectionCard
        title="Dashboard Settings"
        subtitle="Runtime preferences and integration readiness"
      >
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Theme Mode
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Switch between light and dark mode for your workspace.
            </p>
          </div>
          <button
            onClick={onToggleTheme}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-300"
          >
            {darkMode ? "Use Light Theme" : "Use Dark Theme"}
          </button>
        </div>
      </SectionCard>
    </section>
  );
}

export default SettingsSection;
