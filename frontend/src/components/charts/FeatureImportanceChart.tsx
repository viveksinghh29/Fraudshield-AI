import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function FeatureImportanceChart({
  data,
  limit = 10,
}: {
  data: Record<string, number>;
  limit?: number;
}) {
  const chartData = Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([feature, value]) => ({ feature, value }))
    .reverse(); // reverse so the highest-importance feature renders at the top of the horizontal chart

  if (chartData.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-500">No feature importance data available.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 34)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" horizontal={false} />
        <XAxis type="number" stroke="#6B7280" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis
          type="category"
          dataKey="feature"
          stroke="#6B7280"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          width={90}
        />
        <Tooltip
          contentStyle={{ background: "#0B0F1A", border: "1px solid #1F2937", borderRadius: 8, fontSize: 12 }}
          formatter={(value: number) => value.toFixed(6)}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={entry.feature} fill={index >= chartData.length - 3 ? "#3B82F6" : "#1E3A8A"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
