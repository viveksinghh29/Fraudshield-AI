import { useState } from "react";
import { Dices, ShieldCheck } from "lucide-react";
import { usePredictTransaction, useExplainTransaction } from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";
import { RiskBadge } from "@/components/layout/RiskBadge";
import { ExplanationPanel } from "@/components/layout/ExplanationPanel";
import type { TransactionInput } from "@/types/api";

const V_FIELDS = Array.from({ length: 28 }, (_, i) => `V${i + 1}` as keyof TransactionInput);

function emptyForm(): TransactionInput {
  const form = { Time: 0, Amount: 0 } as TransactionInput;
  for (const key of V_FIELDS) {
    (form as unknown as Record<string, number>)[key] = 0;
  }
  return form;
}

function randomSample(): TransactionInput {
  const form = {
    Time: Math.round(Math.random() * 172_800),
    Amount: Math.round(Math.random() * 2000 * 100) / 100,
  } as TransactionInput;
  for (const key of V_FIELDS) {
    (form as unknown as Record<string, number>)[key] = Math.round((Math.random() * 6 - 3) * 1000) / 1000;
  }
  return form;
}

export default function SinglePrediction() {
  const [form, setForm] = useState<TransactionInput>(emptyForm);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [predictedTransactionId, setPredictedTransactionId] = useState<string | null>(null);

  const { mutate: predict, data: result, isPending, error, reset } = usePredictTransaction();
  const {
    data: explanation,
    isLoading: isExplaining,
    error: explainError,
  } = useExplainTransaction(predictedTransactionId);

  function updateField(key: keyof TransactionInput, value: string) {
    setForm((prev) => ({ ...prev, [key]: value === "" ? 0 : Number(value) }));
  }

  function handleFillRandom() {
    setForm(randomSample());
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    reset();
    setPredictedTransactionId(null);
    predict(form, {
      onSuccess: (data) => setPredictedTransactionId(data.transaction_id),
    });
  }

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-xl font-semibold">Single Transaction Prediction</h1>
        <p className="mt-1 text-sm text-gray-500">
          Score one transaction against the active model and see its SHAP explanation
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Transaction Details">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Time (seconds elapsed)">
                <input
                  type="number"
                  step="any"
                  value={form.Time}
                  onChange={(e) => updateField("Time", e.target.value)}
                  className="input"
                  required
                />
              </Field>
              <Field label="Amount ($)">
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.Amount}
                  onChange={(e) => updateField("Amount", e.target.value)}
                  className="input"
                  required
                />
              </Field>
            </div>

            <div>
              <button
                type="button"
                onClick={() => setShowAdvanced((v) => !v)}
                className="text-xs font-medium text-accent-soft hover:underline"
              >
                {showAdvanced ? "Hide" : "Show"} PCA features (V1–V28)
              </button>

              {showAdvanced && (
                <div className="mt-3 grid grid-cols-4 gap-2 rounded-lg border border-border-subtle bg-background p-3 sm:grid-cols-7">
                  {V_FIELDS.map((key) => (
                    <div key={key}>
                      <label className="mb-1 block text-[10px] text-gray-500">{key}</label>
                      <input
                        type="number"
                        step="any"
                        value={form[key]}
                        onChange={(e) => updateField(key, e.target.value)}
                        className="w-full rounded border border-border-subtle bg-background-surface px-1.5 py-1 text-xs text-white outline-none focus:border-accent"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={handleFillRandom}
                className="flex items-center gap-1.5 rounded-lg border border-border-subtle px-3 py-2 text-xs font-medium text-gray-400 hover:bg-background-elevated"
              >
                <Dices className="h-3.5 w-3.5" />
                Fill random sample
              </button>
              <button
                type="submit"
                disabled={isPending}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white hover:bg-accent-soft disabled:opacity-60"
              >
                <ShieldCheck className="h-4 w-4" />
                {isPending ? "Scoring..." : "Score Transaction"}
              </button>
            </div>

            {error && (
              <p className="rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
                {getApiErrorMessage(error)}
              </p>
            )}
          </form>
        </Card>

        <div className="space-y-6">
          {result && (
            <Card title="Prediction Result">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Predicted Class</p>
                  <p className="mt-1 text-xl font-semibold capitalize text-white">
                    {result.predicted_class}
                  </p>
                </div>
                <RiskBadge level={result.risk_level} />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4 border-t border-border-subtle pt-4">
                <div>
                  <p className="text-xs text-gray-500">Fraud Probability</p>
                  <p className="mt-1 text-lg font-medium text-white">
                    {(result.fraud_probability * 100).toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Model Version</p>
                  <p className="mt-1 text-sm text-gray-300">{result.model_version}</p>
                </div>
              </div>
            </Card>
          )}

          {predictedTransactionId && (
            <Card title="Why? (SHAP Explanation)">
              {isExplaining && <p className="text-sm text-gray-500">Computing explanation...</p>}
              {explainError && (
                <p className="text-sm text-risk-critical">{getApiErrorMessage(explainError)}</p>
              )}
              {explanation && (
                <ExplanationPanel
                  topFeatures={explanation.top_features}
                  baseValue={explanation.base_value}
                  valueSpace={explanation.value_space}
                />
              )}
            </Card>
          )}

          {!result && (
            <div className="flex h-full items-center justify-center rounded-2xl border border-dashed border-border-subtle p-8 text-center text-sm text-gray-600">
              Fill in the transaction details and click "Score Transaction" to see a prediction here.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-gray-400">{label}</label>
      {children}
    </div>
  );
}
