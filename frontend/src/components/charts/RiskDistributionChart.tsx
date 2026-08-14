import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { RiskLevel } from "@/types/api";

const RISK_COLORS: Record<RiskLevel, string> = {
  low: "#22C55E",
  medium: "#EAB308",
  high: "#F97316",
  critical: "#EF4444",
};

export function RiskDistributionChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data).map(([level, count]) => ({
    name: level,
    value: count,
  }));

  const total = chartData.reduce((sum, d) => sum + d.value, 0);
  if (total === 0) {
    return <p className="py-8 text-center text-sm text-gray-500">No predictions yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          innerRadius={55}
          outerRadius={80}
          paddingAngle={2}
        >
          {chartData.map((entry) => (
            <Cell key={entry.name} fill={RISK_COLORS[entry.name as RiskLevel] ?? "#6B7280"} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "#0B0F1A",
            border: "1px solid #1F2937",
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(value: number, name: string) => [value, name]}
        />
        <Legend
          verticalAlign="bottom"
          height={28}
          iconType="circle"
          iconSize={8}
          formatter={(value: string) => <span className="text-xs capitalize text-gray-400">{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
