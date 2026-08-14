import { useAnalytics, useDashboard } from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";
import { FraudTrendChart } from "@/components/charts/FraudTrendChart";
import { RiskDistributionChart } from "@/components/charts/RiskDistributionChart";

const RISK_COLORS: Record<string, string> = {
  low: "text-risk-low",
  medium: "text-risk-medium",
  high: "text-risk-high",
  critical: "text-risk-critical",
};

export default function Dashboard() {
  const { data, isLoading, error } = useDashboard();
  const { data: analytics } = useAnalytics(14);

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Live fraud detection overview
          {data?.active_model_version && (
            <>
              {" "}
              · Active model: <span className="text-gray-300">{data.active_model_version}</span> (
              {data.active_model_algorithm})
            </>
          )}
        </p>
      </header>

      {isLoading && <p className="text-sm text-gray-500">Loading dashboard...</p>}

      {error && (
        <p className="rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-4 py-3 text-sm text-risk-critical">
          {getApiErrorMessage(error)}
        </p>
      )}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Total Transactions" value={data.total_transactions.toLocaleString()} />
            <KpiCard label="Fraud Detected" value={data.fraud_count.toLocaleString()} accent="critical" />
            <KpiCard label="Legitimate" value={data.legitimate_count.toLocaleString()} accent="low" />
            <KpiCard label="Fraud Rate" value={`${data.fraud_rate_pct}%`} />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card title="Fraud Trend (last 14 days)" className="lg:col-span-2">
              <FraudTrendChart data={analytics?.fraud_trend ?? []} />
            </Card>

            <Card title="Risk Distribution">
              <RiskDistributionChart data={data.risk_distribution} />
            </Card>
          </div>

          <div className="mt-6">
            <Card title="Recent Predictions">
              {data.recent_predictions.length === 0 ? (
                <p className="text-sm text-gray-500">No predictions yet.</p>
              ) : (
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="text-xs uppercase text-gray-500">
                      <th className="pb-2 font-medium">Amount</th>
                      <th className="pb-2 font-medium">Class</th>
                      <th className="pb-2 font-medium">Risk</th>
                      <th className="pb-2 font-medium">Probability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_predictions.map((txn) => (
                      <tr key={txn.id} className="border-t border-border-subtle/60">
                        <td className="py-2 text-gray-300">${txn.amount.toFixed(2)}</td>
                        <td className="py-2 capitalize text-gray-300">
                          {txn.prediction?.predicted_class ?? "—"}
                        </td>
                        <td
                          className={`py-2 capitalize ${
                            txn.prediction ? RISK_COLORS[txn.prediction.risk_level] : "text-gray-500"
                          }`}
                        >
                          {txn.prediction?.risk_level ?? "—"}
                        </td>
                        <td className="py-2 text-gray-300">
                          {txn.prediction ? `${(txn.prediction.fraud_probability * 100).toFixed(1)}%` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function KpiCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: "critical" | "low";
}) {
  const valueClass = accent === "critical" ? "text-risk-critical" : accent === "low" ? "text-risk-low" : "text-white";
  return (
    <div className="rounded-2xl border border-border-subtle bg-background-surface p-5">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${valueClass}`}>{value}</p>
    </div>
  );
}
