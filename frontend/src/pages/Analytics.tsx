import { useState } from "react";
import { useAnalytics } from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";
import { FraudTrendChart } from "@/components/charts/FraudTrendChart";
import { RiskDistributionChart } from "@/components/charts/RiskDistributionChart";

const RANGE_OPTIONS = [
  { label: "7 days", value: 7 },
  { label: "14 days", value: 14 },
  { label: "30 days", value: 30 },
  { label: "90 days", value: 90 },
];

export default function Analytics() {
  const [days, setDays] = useState(30);
  const { data, isLoading, error } = useAnalytics(days);

  return (
    <div className="p-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">Fraud trend, risk distribution, and prediction confidence</p>
        </div>
        <div className="flex gap-1 rounded-lg border border-border-subtle bg-background-surface p-1">
          {RANGE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setDays(opt.value)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                days === opt.value
                  ? "bg-accent/20 text-accent-soft"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </header>

      {isLoading && <p className="text-sm text-gray-500">Loading analytics...</p>}
      {error && (
        <p className="rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-4 py-3 text-sm text-risk-critical">
          {getApiErrorMessage(error)}
        </p>
      )}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Total Predictions" value={data.total_predictions.toLocaleString()} />
            <StatCard
              label="Avg. Fraud Probability"
              value={`${(data.avg_fraud_probability * 100).toFixed(2)}%`}
            />
            <StatCard
              label="Avg. Prediction Confidence"
              value={`${(data.avg_prediction_confidence * 100).toFixed(2)}%`}
            />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card title={`Fraud Trend (last ${days} days)`} className="lg:col-span-2">
              <FraudTrendChart data={data.fraud_trend} />
            </Card>
            <Card title="Risk Distribution">
              <RiskDistributionChart data={data.risk_distribution} />
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border-subtle bg-background-surface p-5">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}
