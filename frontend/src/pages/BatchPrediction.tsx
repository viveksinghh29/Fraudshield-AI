import { useState, type ChangeEvent } from "react";
import { CheckCircle2, Loader2, UploadCloud } from "lucide-react";
import {
  useBatchStatus,
  useTriggerBatchPrediction,
  useUploadTransactionsCsv,
} from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";

export default function BatchPrediction() {
  const [file, setFile] = useState<File | null>(null);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [triggered, setTriggered] = useState(false);

  const upload = useUploadTransactionsCsv();
  const trigger = useTriggerBatchPrediction();
  const { data: status } = useBatchStatus(batchId, { pollWhileProcessing: triggered });

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    setFile(e.target.files?.[0] ?? null);
    setBatchId(null);
    setTriggered(false);
  }

  function handleUpload() {
    if (!file) return;
    upload.mutate(file, {
      onSuccess: (data) => setBatchId(data.batch_id),
    });
  }

  function handleTrigger() {
    if (!batchId) return;
    trigger.mutate(batchId, {
      onSuccess: () => setTriggered(true),
    });
  }

  const progressPct = status ? Math.round((status.processed_transactions / status.total_transactions) * 100) : 0;

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-xl font-semibold">Batch Prediction</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload a CSV of transactions (Time, Amount, V1–V28 columns) and score them all at once
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="1. Upload CSV">
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border-subtle bg-background px-6 py-10 text-center transition-colors hover:border-accent/50">
            <UploadCloud className="mb-3 h-8 w-8 text-gray-500" />
            <span className="text-sm text-gray-400">
              {file ? file.name : "Click to choose a CSV file"}
            </span>
            <input type="file" accept=".csv" onChange={handleFileChange} className="hidden" />
          </label>

          <button
            onClick={handleUpload}
            disabled={!file || upload.isPending}
            className="mt-4 w-full rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-60"
          >
            {upload.isPending ? "Uploading..." : "Upload"}
          </button>

          {upload.error && (
            <p className="mt-3 rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
              {getApiErrorMessage(upload.error)}
            </p>
          )}

          {upload.data && (
            <div className="mt-4 rounded-lg border border-risk-low/30 bg-risk-low/10 px-3 py-2 text-xs text-risk-low">
              Uploaded {upload.data.transaction_count} transactions. Batch ID: {upload.data.batch_id}
            </div>
          )}
        </Card>

        <Card title="2. Run Prediction">
          {!batchId && (
            <p className="text-sm text-gray-500">Upload a CSV first to enable batch prediction.</p>
          )}

          {batchId && !triggered && (
            <button
              onClick={handleTrigger}
              disabled={trigger.isPending}
              className="w-full rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white hover:bg-accent-soft disabled:opacity-60"
            >
              {trigger.isPending ? "Starting..." : `Predict ${upload.data?.transaction_count ?? ""} Transactions`}
            </button>
          )}

          {trigger.error && (
            <p className="mt-3 rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
              {getApiErrorMessage(trigger.error)}
            </p>
          )}

          {triggered && status && (
            <div>
              <div className="mb-2 flex items-center justify-between text-xs text-gray-400">
                <span className="capitalize">{status.status}</span>
                <span>
                  {status.processed_transactions} / {status.total_transactions}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-background">
                <div
                  className="h-full rounded-full bg-accent transition-all duration-500"
                  style={{ width: `${progressPct}%` }}
                />
              </div>

              {status.status === "completed" ? (
                <div className="mt-4 flex items-center gap-2 rounded-lg border border-risk-low/30 bg-risk-low/10 px-3 py-2 text-sm text-risk-low">
                  <CheckCircle2 className="h-4 w-4" />
                  Done — {status.fraud_count} of {status.total_transactions} flagged as fraud
                </div>
              ) : (
                <div className="mt-4 flex items-center gap-2 text-sm text-gray-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing in the background...
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
