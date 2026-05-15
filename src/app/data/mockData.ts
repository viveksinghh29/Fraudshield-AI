import type { WaterfallStep } from "../components/WaterfallExplanation";

export interface Transaction {
  id: string;
  amount: number;
  time: string;
  location: string;
  merchant: string;
  riskScore: number;
  status: "fraud" | "legit" | "warning";
  features?: {
    name: string;
    value: number;
  }[];
}

/** Model confidence in the displayed label (0–100), distinct from risk score. */
export function getModelConfidence(t: Transaction): number {
  const floor = t.status === "fraud" ? 91 : t.status === "warning" ? 78 : 86;
  const jitter = (t.riskScore % 7) * 0.4;
  return Math.min(99.2, Math.max(floor, floor + jitter));
}

/** Estimated fraud probability for narrative and real-time card (0–100). */
export function getFraudProbabilityPercent(t: Transaction): number {
  if (t.status === "fraud") return Math.min(99, Math.round(t.riskScore * 1.03));
  if (t.status === "warning") return Math.round(38 + t.riskScore * 0.4);
  return Math.round(2 + t.riskScore * 0.2);
}

/** SHAP-style waterfall steps; deltas are tuned so the explained score aligns with risk score. */
export function getWaterfallForTransaction(t: Transaction): {
  baseline: number;
  steps: WaterfallStep[];
} {
  const target = t.riskScore;
  const baseline =
    t.status === "legit" ? 28 : t.status === "warning" ? 22 : 14;
  const amt =
    t.amount > 3000 ? (t.status === "fraud" ? 34 : 18) : t.amount > 500 ? 8 : -6;
  const loc =
    t.location.includes("USA") || t.location.includes("Canada")
      ? t.status === "legit"
        ? -12
        : -4
      : t.status === "fraud"
        ? 32
        : 14;
  const vel = t.status === "fraud" ? 22 : t.status === "warning" ? 10 : -8;
  const time = t.status === "legit" ? -6 : 4;
  const merchant = t.merchant.toLowerCase().includes("wire")
    ? 18
    : t.merchant.toLowerCase().includes("coffee") ||
        t.merchant.toLowerCase().includes("grocery")
      ? -10
      : 2;

  const steps: WaterfallStep[] = [
    { label: "Amount vs. baseline", delta: amt },
    { label: "Location distance", delta: loc },
    { label: "Velocity / recency", delta: vel },
    { label: "Time-of-day pattern", delta: time },
    { label: "Merchant / MCC risk", delta: merchant },
  ];

  const raw = baseline + steps.reduce((s, x) => s + x.delta, 0);
  const diff = target - raw;
  if (Math.abs(diff) > 0.5) {
    steps.push({ label: "Other features (net)", delta: diff });
  }

  return { baseline, steps };
}

export const transactions: Transaction[] = [
  {
    id: "TXN-001",
    amount: 4850.00,
    time: "2026-03-27 14:32:15",
    location: "Lagos, Nigeria",
    merchant: "Electronics Store XYZ",
    riskScore: 92,
    status: "fraud",
    features: [
      { name: "Amount", value: 0.85 },
      { name: "Time of Day", value: 0.72 },
      { name: "Location Anomaly", value: 0.91 },
      { name: "Merchant Category", value: 0.45 },
      { name: "Velocity", value: 0.88 },
    ],
  },
  {
    id: "TXN-002",
    amount: 45.99,
    time: "2026-03-27 14:28:42",
    location: "New York, USA",
    merchant: "Coffee Shop",
    riskScore: 12,
    status: "legit",
    features: [
      { name: "Amount", value: 0.15 },
      { name: "Time of Day", value: 0.22 },
      { name: "Location Anomaly", value: 0.08 },
      { name: "Merchant Category", value: 0.12 },
      { name: "Velocity", value: 0.10 },
    ],
  },
  {
    id: "TXN-003",
    amount: 2340.50,
    time: "2026-03-27 14:15:33",
    location: "London, UK",
    merchant: "Luxury Retailer",
    riskScore: 58,
    status: "warning",
    features: [
      { name: "Amount", value: 0.68 },
      { name: "Time of Day", value: 0.45 },
      { name: "Location Anomaly", value: 0.52 },
      { name: "Merchant Category", value: 0.61 },
      { name: "Velocity", value: 0.48 },
    ],
  },
  {
    id: "TXN-004",
    amount: 129.00,
    time: "2026-03-27 13:45:21",
    location: "San Francisco, USA",
    merchant: "Restaurant",
    riskScore: 8,
    status: "legit",
  },
  {
    id: "TXN-005",
    amount: 8900.00,
    time: "2026-03-27 13:22:10",
    location: "Mumbai, India",
    merchant: "Wire Transfer",
    riskScore: 95,
    status: "fraud",
  },
  {
    id: "TXN-006",
    amount: 67.50,
    time: "2026-03-27 12:58:33",
    location: "Toronto, Canada",
    merchant: "Gas Station",
    riskScore: 15,
    status: "legit",
  },
  {
    id: "TXN-007",
    amount: 3200.00,
    time: "2026-03-27 12:34:55",
    location: "Berlin, Germany",
    merchant: "Tech Store",
    riskScore: 73,
    status: "warning",
  },
  {
    id: "TXN-008",
    amount: 22.99,
    time: "2026-03-27 11:45:12",
    location: "Sydney, Australia",
    merchant: "Grocery Store",
    riskScore: 5,
    status: "legit",
  },
];

export const dashboardStats = {
  totalTransactions: 12847,
  fraudDetected: 3.2,
  averageRiskScore: 34.5,
  blockedAmount: 287450,
};

export const fraudTrendData = [
  { date: "Mar 20", fraud: 45, legit: 1240 },
  { date: "Mar 21", fraud: 38, legit: 1320 },
  { date: "Mar 22", fraud: 52, legit: 1180 },
  { date: "Mar 23", fraud: 61, legit: 1450 },
  { date: "Mar 24", fraud: 48, legit: 1390 },
  { date: "Mar 25", fraud: 55, legit: 1510 },
  { date: "Mar 26", fraud: 43, legit: 1420 },
  { date: "Mar 27", fraud: 39, legit: 1380 },
];

export const transactionTrendData = [
  { time: "00:00", volume: 120 },
  { time: "04:00", volume: 45 },
  { time: "08:00", volume: 380 },
  { time: "12:00", volume: 620 },
  { time: "16:00", volume: 540 },
  { time: "20:00", volume: 420 },
];

export const riskDistributionData = [
  { name: "Low Risk", value: 7842, color: "#10b981" },
  { name: "Medium Risk", value: 3124, color: "#f59e0b" },
  { name: "High Risk", value: 1881, color: "#ef4444" },
];

export const modelMetrics = {
  accuracy: 98.7,
  precision: 96.3,
  recall: 94.8,
  f1Score: 95.5,
  rocAuc: 99.2,
};

export const confusionMatrix = [
  [9450, 120],
  [85, 2192],
];

export const featureImportance = [
  { feature: "Transaction Amount", importance: 0.32 },
  { feature: "Location Anomaly", importance: 0.28 },
  { feature: "Transaction Velocity", importance: 0.18 },
  { feature: "Time of Day", importance: 0.12 },
  { feature: "Merchant Category", importance: 0.10 },
];
