import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FraudTrendPoint } from "@/types/api";

export function FraudTrendChart({ data }: { data: FraudTrendPoint[] }) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-500">No prediction activity yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="totalGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="fraudGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#EF4444" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#EF4444" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
        <XAxis
          dataKey="date"
          stroke="#6B7280"
          fontSize={11}
          tickFormatter={(v: string) => v.slice(5)}
          tickLine={false}
          axisLine={false}
        />
        <YAxis stroke="#6B7280" fontSize={11} tickLine={false} axisLine={false} allowDecimals={false} />
        <Tooltip
          contentStyle={{
            background: "#0B0F1A",
            border: "1px solid #1F2937",
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: "#9CA3AF" }}
        />
        <Area
          type="monotone"
          dataKey="total_transactions"
          name="Total transactions"
          stroke="#3B82F6"
          fill="url(#totalGradient)"
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="fraud_count"
          name="Fraud detected"
          stroke="#EF4444"
          fill="url(#fraudGradient)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
