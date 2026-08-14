import { useState, type FormEvent } from "react";
import { Bot, Send, ShieldAlert, User as UserIcon, X } from "lucide-react";
import { useChatHistory, useSendChatMessage, useTransactions } from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";

interface LocalTurn {
  role: "user" | "assistant";
  message: string;
  grounded?: boolean;
}

export default function Assistant() {
  const [transactionId, setTransactionId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [localTurns, setLocalTurns] = useState<LocalTurn[]>([]);

  const { data: recentTransactions } = useTransactions({ page: 1, page_size: 10 });
  const { data: history } = useChatHistory(transactionId);
  const { mutate: send, isPending, error } = useSendChatMessage();

  const turns: LocalTurn[] = transactionId
    ? (history?.turns.map((t) => ({ role: t.role, message: t.message })) ?? [])
    : localTurns;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = message;
    setMessage("");
    setLocalTurns((prev) => [...prev, { role: "user", message: userMessage }]);

    send(
      { message: userMessage, transaction_id: transactionId },
      {
        onSuccess: (data) => {
          setLocalTurns((prev) => [
            ...prev,
            { role: "assistant", message: data.message, grounded: data.grounded },
          ]);
        },
      }
    );
  }

  return (
    <div className="flex h-screen flex-col p-8">
      <header className="mb-4">
        <h1 className="text-xl font-semibold">Analyst AI Assistant</h1>
        <p className="mt-1 text-sm text-gray-500">
          Ask about a specific transaction, or ask general questions about the fraud system
        </p>
      </header>

      <div className="mb-4 flex items-center gap-3">
        {transactionId ? (
          <div className="flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-3 py-1.5 text-xs text-accent-soft">
            <ShieldAlert className="h-3.5 w-3.5" />
            Discussing transaction {transactionId.slice(0, 8)}...
            <button onClick={() => setTransactionId(null)} className="ml-1 hover:text-white">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <select
            onChange={(e) => setTransactionId(e.target.value || null)}
            value=""
            className="rounded-lg border border-border-subtle bg-background-surface px-3 py-1.5 text-xs text-gray-300 outline-none focus:border-accent"
          >
            <option value="">Reference a transaction (optional)...</option>
            {recentTransactions?.items.map((txn) => (
              <option key={txn.id} value={txn.id}>
                ${txn.amount.toFixed(2)} — {txn.prediction?.predicted_class ?? "unscored"} (
                {txn.prediction?.risk_level ?? "—"})
              </option>
            ))}
          </select>
        )}
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 space-y-4 overflow-y-auto pr-1">
          {turns.length === 0 && (
            <div className="flex h-full items-center justify-center text-center text-sm text-gray-600">
              {transactionId
                ? "Ask why this transaction was flagged, what its top contributing features are, or what to investigate next."
                : "Ask a general question, or select a transaction above to get a grounded, data-backed explanation."}
            </div>
          )}

          {turns.map((turn, i) => (
            <div key={i} className={`flex gap-3 ${turn.role === "user" ? "justify-end" : ""}`}>
              {turn.role === "assistant" && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/20">
                  <Bot className="h-4 w-4 text-accent-soft" />
                </div>
              )}
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                  turn.role === "user"
                    ? "bg-accent text-white"
                    : "border border-border-subtle bg-background text-gray-200"
                }`}
              >
                <p className="whitespace-pre-wrap">{turn.message}</p>
                {turn.role === "assistant" && turn.grounded !== undefined && (
                  <p className="mt-1.5 text-[10px] uppercase tracking-wide text-gray-500">
                    {turn.grounded ? "✓ Grounded in real transaction data" : "General response, not transaction-specific"}
                  </p>
                )}
              </div>
              {turn.role === "user" && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-background-elevated">
                  <UserIcon className="h-4 w-4 text-gray-400" />
                </div>
              )}
            </div>
          ))}

          {isPending && (
            <div className="flex gap-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/20">
                <Bot className="h-4 w-4 text-accent-soft" />
              </div>
              <div className="rounded-2xl border border-border-subtle bg-background px-4 py-2.5 text-sm text-gray-500">
                Thinking...
              </div>
            </div>
          )}
        </div>

        {error && (
          <p className="mt-3 rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
            {getApiErrorMessage(error)}
          </p>
        )}

        <form onSubmit={handleSubmit} className="mt-4 flex gap-2 border-t border-border-subtle pt-4">
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask the assistant..."
            className="input flex-1"
          />
          <button
            type="submit"
            disabled={isPending || !message.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-soft disabled:opacity-60"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </Card>
    </div>
  );
}
