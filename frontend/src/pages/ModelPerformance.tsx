import { useActiveModelInfo } from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";
import { ConfusionMatrixGrid } from "@/components/charts/ConfusionMatrixGrid";
import { CalibrationChart } from "@/components/charts/CalibrationChart";

export default function ModelPerformance() {
  const { data, isLoading, error } = useActiveModelInfo();

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-xl font-semibold">Model Performance</h1>
        <p className="mt-1 text-sm text-gray-500">
          Evaluation metrics for the currently active model
        </p>
      </header>

      {isLoading && <p className="text-sm text-gray-500">Loading model info...</p>}
      {error && (
        <p className="rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-4 py-3 text-sm text-risk-critical">
          {getApiErrorMessage(error)}
        </p>
      )}

      {data && (
        <>
          <Card className="mb-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs text-gray-500">Active Model</p>
                <p className="mt-1 text-lg font-semibold text-white">{data.version_tag}</p>
                <p className="text-sm capitalize text-gray-400">{data.algorithm.replace(/_/g, " ")}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">Trained</p>
                <p className="mt-1 text-sm text-gray-300">
                  {new Date(data.trained_at).toLocaleString()}
                </p>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <MetricCard label="Precision" value={data.metrics.precision} />
            <MetricCard label="Recall" value={data.metrics.recall} />
            <MetricCard label="F1 Score" value={data.metrics.f1_score} />
            <MetricCard label="ROC-AUC" value={data.metrics.roc_auc} />
            <MetricCard label="PR-AUC" value={data.metrics.pr_auc} accent />
            <MetricCard label="Threshold" value={data.metrics.threshold} format="raw" />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card
              title="Confusion Matrix"
              subtitle={`At the default ${data.metrics.threshold} decision threshold`}
            >
              <ConfusionMatrixGrid matrix={data.metrics.confusion_matrix} />
            </Card>

            <Card
              title="Calibration Curve"
              subtitle="How well predicted probabilities match real-world fraud rates"
            >
              <CalibrationChart data={data.metrics.calibration} />
            </Card>
          </div>

          <div className="mt-6">
            <Card
              title="Optimal Threshold (validation-selected)"
              subtitle="The decision cutoff that maximizes F1 on held-out validation data, used instead of the naive 0.5 default"
            >
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <MetricCard
                  label="Optimal Threshold"
                  value={data.metrics.threshold_optimization.optimal_threshold}
                  format="raw"
                />
                <MetricCard
                  label="Precision @ Optimal"
                  value={data.metrics.threshold_optimization.precision_at_optimal}
                />
                <MetricCard
                  label="Recall @ Optimal"
                  value={data.metrics.threshold_optimization.recall_at_optimal}
                />
                <MetricCard
                  label="F1 @ Optimal"
                  value={data.metrics.threshold_optimization.f1_at_optimal}
                />
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  accent,
  format = "percent",
}: {
  label: string;
  value: number;
  accent?: boolean;
  format?: "percent" | "raw";
}) {
  const displayValue = format === "percent" ? `${(value * 100).toFixed(2)}%` : value.toFixed(4);
  return (
    <div
      className={`rounded-2xl border p-4 ${
        accent ? "border-accent/40 bg-accent/10" : "border-border-subtle bg-background-surface"
      }`}
    >
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${accent ? "text-accent-soft" : "text-white"}`}>
        {displayValue}
      </p>
    </div>
  );
}
