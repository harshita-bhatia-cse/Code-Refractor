import { CheckCircle2, Code2, FileCode2, Layers3 } from "lucide-react";
import MetricCard from "../components/MetricCard";

function OverviewSection({ overview }) {
  // Main overview cards with key project-level outcomes.
  const metrics = [
    {
      title: "Total Files",
      value: overview.totalFiles,
      icon: FileCode2,
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      title: "Lines of Code (Before)",
      value: overview.locBefore.toLocaleString(),
      icon: Layers3,
      gradient: "from-rose-500 to-orange-500",
    },
    {
      title: "Lines of Code (After)",
      value: overview.locAfter.toLocaleString(),
      icon: Code2,
      gradient: "from-emerald-500 to-teal-500",
    },
    {
      title: "Refactor Success Rate (%)",
      value: `${overview.successRate}%`,
      icon: CheckCircle2,
      gradient: "from-violet-500 to-indigo-600",
    },
  ];

  return (
    <section id="overview">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.title} {...metric} />
        ))}
      </div>
    </section>
  );
}

export default OverviewSection;
