import type { TopFeature } from "@/types/api";

export function ExplanationPanel({
  topFeatures,
  baseValue,
  valueSpace,
}: {
  topFeatures: TopFeature[];
  baseValue: number;
  valueSpace: "probability" | "log_odds";
}) {
  const maxAbs = Math.max(...topFeatures.map((f) => Math.abs(f.shap_value)), 0.0001);

  return (
    <div>
      <p className="mb-3 text-xs text-gray-500">
        Base value: <span className="text-gray-300">{baseValue.toFixed(6)}</span> (
        {valueSpace === "probability" ? "probability" : "log-odds"} space)
      </p>
      <div className="space-y-2.5">
        {topFeatures.map((feature) => {
          const widthPct = (Math.abs(feature.shap_value) / maxAbs) * 100;
          const isPositive = feature.shap_value > 0;
          return (
            <div key={feature.feature} className="flex items-center gap-3">
              <span className="w-16 shrink-0 text-xs font-medium text-gray-400">{feature.feature}</span>
              <div className="relative h-5 flex-1 rounded bg-background">
                <div
                  className={`absolute h-full rounded ${
                    isPositive ? "bg-risk-critical/60" : "bg-risk-low/60"
                  }`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
              <span
                className={`w-20 shrink-0 text-right text-xs ${
                  isPositive ? "text-risk-critical" : "text-risk-low"
                }`}
              >
                {feature.shap_value > 0 ? "+" : ""}
                {feature.shap_value.toFixed(4)}
              </span>
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-risk-critical/60" /> Increases fraud probability
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-risk-low/60" /> Decreases fraud probability
        </span>
      </div>
    </div>
  );
}
