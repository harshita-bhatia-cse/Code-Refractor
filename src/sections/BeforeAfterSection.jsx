import SectionCard from "../components/SectionCard";

function BeforeAfterSection({ data }) {
  const complexityDrop = data.complexityBefore - data.complexityAfter;
  const locDrop = data.locBefore - data.locAfter;

  return (
    <section id="before-after" className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <SectionCard
        title="Code Snapshot Comparison"
        subtitle="Side-by-side comparison of legacy and refactored logic"
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-900/40 dark:bg-rose-950/30">
            <p className="mb-2 text-sm font-semibold text-rose-700 dark:text-rose-300">
              Before
            </p>
            <pre className="overflow-x-auto text-xs leading-6 text-rose-900 dark:text-rose-100">
              <code>{data.beforeCode}</code>
            </pre>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/30">
            <p className="mb-2 text-sm font-semibold text-emerald-700 dark:text-emerald-300">
              After
            </p>
            <pre className="overflow-x-auto text-xs leading-6 text-emerald-900 dark:text-emerald-100">
              <code>{data.afterCode}</code>
            </pre>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Improvement Summary"
        subtitle="Quantified impact of refactoring pass"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/50">
            <p className="text-sm text-slate-500 dark:text-slate-400">Complexity</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {data.complexityBefore} to {data.complexityAfter}
            </p>
            <p className="mt-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
              {complexityDrop} points reduced
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/50">
            <p className="text-sm text-slate-500 dark:text-slate-400">Lines of Code</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {data.locBefore.toLocaleString()} to {data.locAfter.toLocaleString()}
            </p>
            <p className="mt-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
              {locDrop.toLocaleString()} lines removed
            </p>
          </div>
        </div>
      </SectionCard>
    </section>
  );
}

export default BeforeAfterSection;
