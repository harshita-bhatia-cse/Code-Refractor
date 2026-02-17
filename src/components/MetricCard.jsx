function MetricCard({ title, value, icon: Icon, gradient }) {
  return (
    <div className="group animate-floatIn rounded-2xl border border-slate-200/70 bg-white p-5 shadow-soft transition-all duration-300 hover:-translate-y-1 hover:shadow-lg dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex items-center justify-between">
        <div className={`rounded-xl bg-gradient-to-br p-3 ${gradient}`}>
          <Icon className="text-white" size={20} />
        </div>
      </div>
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
      <p className="mt-1 text-2xl font-extrabold text-slate-900 dark:text-slate-100">
        {value}
      </p>
    </div>
  );
}

export default MetricCard;
