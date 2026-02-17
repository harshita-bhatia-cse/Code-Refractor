import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import SectionCard from "../components/SectionCard";

function RefactorMetricsSection({ complexityTrend, duplicateCodeTrend }) {
  return (
    <section id="refactor-metrics" className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <SectionCard
        title="Complexity Reduction Over Time"
        subtitle="Average cyclomatic complexity trend by sprint"
      >
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={complexityTrend}>
              <CartesianGrid strokeDasharray="4 4" strokeOpacity={0.15} />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="complexityBefore"
                name="Before"
                stroke="#f97316"
                strokeWidth={3}
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="complexityAfter"
                name="After"
                stroke="#06b6d4"
                strokeWidth={3}
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>

      <SectionCard
        title="Duplicate Code Reduction"
        subtitle="Duplicated block percentage by module"
      >
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={duplicateCodeTrend}>
              <CartesianGrid strokeDasharray="4 4" strokeOpacity={0.15} />
              <XAxis dataKey="module" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="before" name="Before" fill="#ef4444" radius={[6, 6, 0, 0]} />
              <Bar dataKey="after" name="After" fill="#10b981" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>
    </section>
  );
}

export default RefactorMetricsSection;
