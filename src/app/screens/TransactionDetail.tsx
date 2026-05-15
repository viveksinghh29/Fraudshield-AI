import { useParams, useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { RiskGauge } from "../components/RiskGauge";
import { WaterfallExplanation } from "../components/WaterfallExplanation";
import { ExplanationChat } from "../components/ExplanationChat";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "../components/ui/tooltip";
import { ArrowLeft, AlertTriangle, CheckCircle2, HelpCircle } from "lucide-react";
import {
  transactions,
  getWaterfallForTransaction,
  getModelConfidence,
  getFraudProbabilityPercent,
} from "../data/mockData";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from "recharts";

export function TransactionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const transaction = transactions.find((t) => t.id === id);

  if (!transaction) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh]">
        <p className="text-muted-foreground">Transaction not found</p>
        <Button onClick={() => navigate("/transactions")} className="mt-4">
          Back to Transactions
        </Button>
      </div>
    );
  }

  const getStatusInfo = (status: string) => {
    switch (status) {
      case "fraud":
        return {
          prediction: "Fraud",
          label: "FRAUD",
          color: "text-red-600 dark:text-red-400",
          bg: "bg-red-100 dark:bg-red-950",
          icon: AlertTriangle,
        };
      case "warning":
        return {
          prediction: "Review required",
          label: "WARNING",
          color: "text-amber-600 dark:text-amber-400",
          bg: "bg-amber-100 dark:bg-amber-950",
          icon: AlertTriangle,
        };
      default:
        return {
          prediction: "Not fraud",
          label: "LEGIT",
          color: "text-emerald-600 dark:text-emerald-400",
          bg: "bg-emerald-100 dark:bg-emerald-950",
          icon: CheckCircle2,
        };
    }
  };

  const statusInfo = getStatusInfo(transaction.status);
  const StatusIcon = statusInfo.icon;
  const modelConfidence = getModelConfidence(transaction);
  const fraudProbability = getFraudProbabilityPercent(transaction);
  const { baseline, steps } = getWaterfallForTransaction(transaction);

  const features = transaction.features || [
    { name: "Amount", value: 0.45 },
    { name: "Time of Day", value: 0.32 },
    { name: "Location Anomaly", value: 0.55 },
    { name: "Merchant Category", value: 0.28 },
    { name: "Velocity", value: 0.41 },
  ];

  const featureData = features.map((f) => ({
    name: f.name,
    importance: f.value,
  }));

  const chatSeed = `Summary: **${statusInfo.prediction}** (risk score **${transaction.riskScore}**/100). Fraud probability is estimated at **${fraudProbability}%** with model confidence **${modelConfidence.toFixed(1)}%**. The strongest drivers are amount and geography versus this customer’s baseline.`;

  const chatContext = `Amount at $${transaction.amount.toLocaleString()}, merchant ${transaction.merchant}, and location ${transaction.location} drove most of the lift.`;

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/transactions")}
            className="shrink-0"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              AI explanation panel
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5 font-mono">
              {transaction.id}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm">
            Mark as Legit
          </Button>
          <Button variant="destructive" size="sm">
            Block transaction
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-7 space-y-6">
          <Card className="hover:shadow-[var(--fs-card-shadow-hover)] transition-shadow">
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  Prediction & scores
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className="text-muted-foreground hover:text-foreground"
                        aria-label="About scores"
                      >
                        <HelpCircle className="w-4 h-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs text-balance">
                      Risk score is the calibrated model output. Confidence reflects
                      agreement across trees; fraud probability is the positive-class
                      estimate.
                    </TooltipContent>
                  </Tooltip>
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Machine learning output plus GenAI narrative on the right.
                </p>
              </div>
              <Badge className={`${statusInfo.bg} ${statusInfo.color} border-0`}>
                {statusInfo.label}
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row items-center gap-8">
                <RiskGauge score={transaction.riskScore} size="lg" />
                <div className="flex-1 w-full space-y-4">
                  <div className="flex items-center gap-2">
                    <StatusIcon className={`w-6 h-6 ${statusInfo.color}`} />
                    <span className={`text-xl font-semibold ${statusInfo.color}`}>
                      {statusInfo.prediction}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="rounded-xl border border-border bg-muted/30 p-4">
                      <p className="text-xs text-muted-foreground uppercase tracking-wide">
                        Confidence
                      </p>
                      <p className="text-2xl font-semibold tabular-nums text-foreground mt-1">
                        {modelConfidence.toFixed(1)}%
                      </p>
                    </div>
                    <div className="rounded-xl border border-border bg-muted/30 p-4">
                      <p className="text-xs text-muted-foreground uppercase tracking-wide">
                        Fraud probability
                      </p>
                      <p className="text-2xl font-semibold tabular-nums text-foreground mt-1">
                        {fraudProbability}%
                      </p>
                    </div>
                    <div className="rounded-xl border border-border bg-muted/30 p-4">
                      <p className="text-xs text-muted-foreground uppercase tracking-wide">
                        Risk score
                      </p>
                      <p className="text-2xl font-semibold tabular-nums text-foreground mt-1">
                        {transaction.riskScore}
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-lg border border-border/80 p-3">
                      <p className="text-xs text-muted-foreground">Model</p>
                      <p className="font-medium text-foreground mt-0.5">
                        Random Forest v2.4.1
                      </p>
                    </div>
                    <div className="rounded-lg border border-border/80 p-3">
                      <p className="text-xs text-muted-foreground">Latency</p>
                      <p className="font-medium text-foreground mt-0.5">34 ms</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Transaction</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground">Amount</p>
                  <p className="text-xl font-semibold text-foreground mt-1">
                    ${transaction.amount.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Merchant</p>
                  <p className="text-lg font-medium text-foreground mt-1">
                    {transaction.merchant}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Location</p>
                  <p className="text-lg font-medium text-foreground mt-1">
                    {transaction.location}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Time</p>
                  <p className="text-lg font-medium text-foreground mt-1">
                    {transaction.time}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                SHAP feature importance
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" className="text-muted-foreground">
                      <HelpCircle className="w-4 h-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    Approximate SHAP magnitudes for this prediction (normalized 0–1).
                  </TooltipContent>
                </Tooltip>
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Drivers ranked by impact on the fraud score.
              </p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={featureData} layout="vertical" margin={{ left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis type="number" domain={[0, 1]} className="text-xs" />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={140}
                    className="text-xs"
                  />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: "var(--card)",
                      border: "1px solid var(--border)",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar
                    dataKey="importance"
                    radius={[0, 6, 6, 0]}
                    fill={`url(#shap-${transaction.id})`}
                  />
                  <defs>
                    <linearGradient id={`shap-${transaction.id}`} x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#6366f1" />
                      <stop offset="100%" stopColor="#7c3aed" />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Waterfall explanation</CardTitle>
              <p className="text-sm text-muted-foreground">
                How each feature group pushes the score from baseline to the final
                value.
              </p>
            </CardHeader>
            <CardContent>
              <WaterfallExplanation baseline={baseline} steps={steps} />
            </CardContent>
          </Card>
        </div>

        <div className="xl:col-span-5 space-y-6">
          <Card className="xl:sticky xl:top-4">
            <CardHeader>
              <CardTitle>LLM explanation</CardTitle>
              <p className="text-sm text-muted-foreground">
                Conversational audit trail for analysts and compliance.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <ExplanationChat
                initialAssistantMessage={chatSeed}
                contextHint={chatContext}
              />
              <div className="grid gap-2">
                <Button variant="outline" className="w-full justify-start text-sm">
                  View similar transactions
                </Button>
                <Button variant="outline" className="w-full justify-start text-sm">
                  Export SAR-ready summary
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
