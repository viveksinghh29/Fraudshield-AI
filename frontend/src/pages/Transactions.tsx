import { useState } from "react";
import { X } from "lucide-react";
import { useExplainTransaction, useTransactionDetail, useTransactions } from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";
import { RiskBadge } from "@/components/layout/RiskBadge";
import { ExplanationPanel } from "@/components/layout/ExplanationPanel";
import type { PredictedClass, RiskLevel } from "@/types/api";

const PAGE_SIZE = 15;

export default function Transactions() {
  const [page, setPage] = useState(1);
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "">("");
  const [classFilter, setClassFilter] = useState<PredictedClass | "">("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data, isLoading, error } = useTransactions({
    page,
    page_size: PAGE_SIZE,
    risk_level: riskFilter || undefined,
    predicted_class: classFilter || undefined,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="p-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Transactions</h1>
          <p className="mt-1 text-sm text-gray-500">Browse every scored transaction</p>
        </div>

        <div className="flex gap-2">
          <select
            value={riskFilter}
            onChange={(e) => {
              setRiskFilter(e.target.value as RiskLevel | "");
              setPage(1);
            }}
            className="rounded-lg border border-border-subtle bg-background-surface px-3 py-1.5 text-xs text-gray-300 outline-none focus:border-accent"
          >
            <option value="">All risk levels</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>

          <select
            value={classFilter}
            onChange={(e) => {
              setClassFilter(e.target.value as PredictedClass | "");
              setPage(1);
            }}
            className="rounded-lg border border-border-subtle bg-background-surface px-3 py-1.5 text-xs text-gray-300 outline-none focus:border-accent"
          >
            <option value="">All classes</option>
            <option value="fraud">Fraud</option>
            <option value="legitimate">Legitimate</option>
          </select>
        </div>
      </header>

      {isLoading && <p className="text-sm text-gray-500">Loading transactions...</p>}
      {error && (
        <p className="rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-4 py-3 text-sm text-risk-critical">
          {getApiErrorMessage(error)}
        </p>
      )}

      {data && (
        <Card>
          {data.items.length === 0 ? (
            <p className="py-6 text-center text-sm text-gray-500">No transactions match these filters.</p>
          ) : (
            <>
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase text-gray-500">
                    <th className="pb-2 font-medium">Date</th>
                    <th className="pb-2 font-medium">Amount</th>
                    <th className="pb-2 font-medium">Class</th>
                    <th className="pb-2 font-medium">Risk</th>
                    <th className="pb-2 font-medium">Probability</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((txn) => (
                    <tr
                      key={txn.id}
                      onClick={() => setSelectedId(txn.id)}
                      className="cursor-pointer border-t border-border-subtle/60 hover:bg-background-elevated"
                    >
                      <td className="py-2.5 text-gray-400">
                        {new Date(txn.created_at).toLocaleString()}
                      </td>
                      <td className="py-2.5 text-gray-300">${txn.amount.toFixed(2)}</td>
                      <td className="py-2.5 capitalize text-gray-300">
                        {txn.prediction?.predicted_class ?? "—"}
                      </td>
                      <td className="py-2.5">
                        {txn.prediction ? <RiskBadge level={txn.prediction.risk_level} /> : "—"}
                      </td>
                      <td className="py-2.5 text-gray-300">
                        {txn.prediction ? `${(txn.prediction.fraud_probability * 100).toFixed(1)}%` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
                <span>
                  Page {page} of {totalPages} · {data.total} total
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="rounded-lg border border-border-subtle px-3 py-1 disabled:opacity-40"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="rounded-lg border border-border-subtle px-3 py-1 disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </Card>
      )}

      {selectedId && <TransactionDetailPanel transactionId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}

function TransactionDetailPanel({ transactionId, onClose }: { transactionId: string; onClose: () => void }) {
  const { data: detail, isLoading } = useTransactionDetail(transactionId);
  const { data: explanation, isLoading: isExplaining } = useExplainTransaction(transactionId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div
        className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-border-subtle bg-background-surface p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium text-gray-300">Transaction Detail</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300">
            <X className="h-5 w-5" />
          </button>
        </div>

        {isLoading && <p className="text-sm text-gray-500">Loading...</p>}

        {detail && (
          <>
            <div className="mb-4 flex items-center justify-between rounded-xl border border-border-subtle bg-background p-4">
              <div>
                <p className="text-xs text-gray-500">Amount</p>
                <p className="text-lg font-semibold text-white">${detail.amount.toFixed(2)}</p>
              </div>
              {detail.prediction && (
                <div className="text-right">
                  <RiskBadge level={detail.prediction.risk_level} />
                  <p className="mt-1 text-xs text-gray-400">
                    {(detail.prediction.fraud_probability * 100).toFixed(2)}% fraud probability
                  </p>
                </div>
              )}
            </div>

            <div className="mb-4">
              <h3 className="mb-2 text-xs font-medium text-gray-400">Why? (SHAP Explanation)</h3>
              {isExplaining && <p className="text-xs text-gray-500">Computing explanation...</p>}
              {explanation && (
                <ExplanationPanel
                  topFeatures={explanation.top_features}
                  baseValue={explanation.base_value}
                  valueSpace={explanation.value_space}
                />
              )}
            </div>

            <details className="text-xs text-gray-500">
              <summary className="cursor-pointer font-medium text-gray-400">Raw PCA feature values</summary>
              <div className="mt-2 grid grid-cols-4 gap-2 sm:grid-cols-7">
                {Array.from({ length: 28 }, (_, i) => `v${i + 1}` as const).map((key) => (
                  <div key={key} className="rounded border border-border-subtle bg-background px-2 py-1">
                    <p className="text-[10px] uppercase text-gray-600">{key}</p>
                    <p className="text-gray-300">{(detail as unknown as Record<string, number>)[key].toFixed(3)}</p>
                  </div>
                ))}
              </div>
            </details>
          </>
        )}
      </div>
    </div>
  );
}
