import { ArrowDownUp } from "lucide-react";
import { useMemo, useState } from "react";
import SectionCard from "../components/SectionCard";

const columns = [
  { key: "fileName", label: "File Name" },
  { key: "issuesFixed", label: "Issues Fixed" },
  { key: "complexityBefore", label: "Complexity Before" },
  { key: "complexityAfter", label: "Complexity After" },
  { key: "locBefore", label: "LOC Before" },
  { key: "locAfter", label: "LOC After" },
];

function ReportsSection({ rows }) {
  const [sortConfig, setSortConfig] = useState({
    key: "issuesFixed",
    direction: "desc",
  });

  const sortedRows = useMemo(() => {
    const output = [...rows];
    output.sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (aValue < bValue) return sortConfig.direction === "asc" ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    });
    return output;
  }, [rows, sortConfig]);

  const handleSort = (key) => {
    setSortConfig((current) => {
      if (current.key === key) {
        return { key, direction: current.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: "desc" };
    });
  };

  return (
    <section id="reports">
      <SectionCard
        title="Refactored File Reports"
        subtitle="Sortable breakdown of improvements by file"
      >
        <div className="overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-y-2">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column.key}
                    className="px-3 py-2 text-left text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400"
                  >
                    <button
                      onClick={() => handleSort(column.key)}
                      className="inline-flex items-center gap-1"
                    >
                      {column.label}
                      <ArrowDownUp size={12} />
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row) => (
                <tr
                  key={row.fileName}
                  className="rounded-lg bg-slate-50 text-sm transition-colors hover:bg-slate-100 dark:bg-slate-800/40 dark:hover:bg-slate-800"
                >
                  <td className="rounded-l-lg px-3 py-3 font-medium text-slate-800 dark:text-slate-200">
                    {row.fileName}
                  </td>
                  <td className="px-3 py-3">{row.issuesFixed}</td>
                  <td className="px-3 py-3">{row.complexityBefore}</td>
                  <td className="px-3 py-3 text-emerald-600 dark:text-emerald-400">
                    {row.complexityAfter}
                  </td>
                  <td className="px-3 py-3">{row.locBefore}</td>
                  <td className="rounded-r-lg px-3 py-3 text-emerald-600 dark:text-emerald-400">
                    {row.locAfter}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </section>
  );
}

export default ReportsSection;
