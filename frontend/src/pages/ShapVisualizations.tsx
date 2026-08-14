import { useActiveModelInfo } from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";
import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";

export default function ShapVisualizations() {
  const { data, isLoading, error } = useActiveModelInfo();
  const shap = data?.metrics.shap_global_importance;

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-xl font-semibold">SHAP Visualizations</h1>
        <p className="mt-1 text-sm text-gray-500">
          Global feature importance for the active model, computed via SHAP
        </p>
      </header>

      {isLoading && <p className="text-sm text-gray-500">Loading SHAP data...</p>}
      {error && (
        <p className="rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-4 py-3 text-sm text-risk-critical">
          {getApiErrorMessage(error)}
        </p>
      )}

      {shap && (
        <>
          <Card
            title="Top Contributing Features"
            subtitle={`Mean |SHAP value| across ${shap.sample_size_used} sampled predictions, in ${shap.value_space === "probability" ? "probability" : "log-odds"} space`}
          >
            <FeatureImportanceChart data={shap.global_feature_importance} limit={15} />
          </Card>

          <div className="mt-6">
            <Card title="Native Feature Importance" subtitle="Model-native importance, for comparison against SHAP">
              <FeatureImportanceChart data={data.metrics.native_feature_importance} limit={15} />
            </Card>
          </div>

          <div className="mt-6 rounded-2xl border border-border-subtle bg-background-surface p-5">
            <p className="text-xs leading-relaxed text-gray-500">
              <span className="font-medium text-gray-400">Reading this chart: </span>
              features with a higher mean |SHAP value| have a bigger typical influence on the model's
              fraud predictions, in either direction. This is a global view across many transactions —
              for a single transaction's specific explanation, see that transaction's detail page.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
