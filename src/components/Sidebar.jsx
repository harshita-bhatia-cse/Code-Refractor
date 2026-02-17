const navItems = [
  "Overview",
  "Refactor Metrics",
  "Before vs After",
  "Reports",
  "Settings",
];

function Sidebar({ activeSection, onSelect }) {
  return (
    <aside className="w-full shrink-0 border-b border-slate-200/80 bg-white/85 p-4 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/70 lg:h-screen lg:w-64 lg:border-b-0 lg:border-r">
      <div className="mb-5 hidden text-sm font-semibold uppercase tracking-[0.25em] text-slate-500 dark:text-slate-400 lg:block">
        Navigation
      </div>
      <nav className="flex gap-2 overflow-x-auto lg:flex-col">
        {navItems.map((item) => {
          const active = activeSection === item;
          return (
            <button
              key={item}
              onClick={() => onSelect(item)}
              className={`whitespace-nowrap rounded-xl px-4 py-2 text-left text-sm font-semibold transition-all duration-300 ${
                active
                  ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-soft"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
              }`}
            >
              {item}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;
