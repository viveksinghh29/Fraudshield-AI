import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CalibrationData } from "@/types/api";

export function CalibrationChart({ data }: { data: CalibrationData }) {
  const chartData = data.mean_predicted_probability.map((predicted, i) => ({
    predicted,
    observed: data.observed_fraud_fraction[i],
    perfect: predicted, // the y=x reference line: perfectly calibrated would match predicted exactly
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={chartData} margin={{ top: 8, right: 16, left: -16, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
          <XAxis
            dataKey="predicted"
            stroke="#6B7280"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => v.toFixed(2)}
            label={{ value: "Mean predicted probability", position: "insideBottom", offset: -4, fontSize: 11, fill: "#6B7280" }}
          />
          <YAxis
            stroke="#6B7280"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => v.toFixed(2)}
            label={{ value: "Observed fraud rate", angle: -90, position: "insideLeft", fontSize: 11, fill: "#6B7280" }}
          />
          <Tooltip
            contentStyle={{ background: "#0B0F1A", border: "1px solid #1F2937", borderRadius: 8, fontSize: 12 }}
            formatter={(value: number) => value.toFixed(4)}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="perfect"
            name="Perfect calibration"
            stroke="#6B7280"
            strokeDasharray="4 4"
            dot={false}
            strokeWidth={1.5}
          />
          <Line
            type="monotone"
            dataKey="observed"
            name="This model"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ r: 3, fill: "#3B82F6" }}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="mt-2 text-center text-xs text-gray-500">
        Mean calibration error: {data.mean_calibration_error.toFixed(4)} — closer to 0 means predicted
        probabilities match real-world fraud rates more closely.
      </p>
    </div>
  );
}
