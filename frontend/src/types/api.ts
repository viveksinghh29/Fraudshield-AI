// Types mirroring the backend's Pydantic schemas (app/schemas/*.py).
// Kept in sync manually -- if a backend schema changes, update here too.

export type UserRole = "admin" | "analyst" | "viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

// ---- Prediction ----

export interface TransactionInput {
  Time: number;
  Amount: number;
  V1: number; V2: number; V3: number; V4: number; V5: number; V6: number; V7: number;
  V8: number; V9: number; V10: number; V11: number; V12: number; V13: number; V14: number;
  V15: number; V16: number; V17: number; V18: number; V19: number; V20: number; V21: number;
  V22: number; V23: number; V24: number; V25: number; V26: number; V27: number; V28: number;
}

export type PredictedClass = "fraud" | "legitimate";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface PredictionResponse {
  transaction_id: string;
  predicted_class: PredictedClass;
  fraud_probability: number;
  risk_level: RiskLevel;
  model_version: string;
  threshold_used: number;
  explanation_available: boolean;
}

export interface BatchUploadResponse {
  batch_id: string;
  transaction_count: number;
  task_id: string;
  status: string;
}

export interface BatchStatusResponse {
  batch_id: string;
  status: "queued" | "processing" | "completed";
  total_transactions: number;
  processed_transactions: number;
  fraud_count: number | null;
}

// ---- Transactions ----

export interface PredictionSummary {
  id: string;
  predicted_class: PredictedClass;
  fraud_probability: number;
  risk_level: RiskLevel;
  created_at: string;
}

export interface TransactionSummary {
  id: string;
  time: number;
  amount: number;
  batch_id: string | null;
  created_at: string;
  prediction: PredictionSummary | null;
}

export interface TransactionDetail extends TransactionSummary {
  v1: number; v2: number; v3: number; v4: number; v5: number; v6: number; v7: number;
  v8: number; v9: number; v10: number; v11: number; v12: number; v13: number; v14: number;
  v15: number; v16: number; v17: number; v18: number; v19: number; v20: number; v21: number;
  v22: number; v23: number; v24: number; v25: number; v26: number; v27: number; v28: number;
}

export interface TransactionListResponse {
  items: TransactionSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface TransactionListFilters {
  page?: number;
  page_size?: number;
  risk_level?: RiskLevel;
  predicted_class?: PredictedClass;
  batch_id?: string;
}

// ---- Explanation ----

export interface TopFeature {
  feature: string;
  shap_value: number;
  direction: "increases_fraud_probability" | "decreases_fraud_probability";
}

export interface ExplanationResponse {
  transaction_id: string;
  prediction_id: string;
  predicted_class: PredictedClass;
  fraud_probability: number;
  risk_level: RiskLevel;
  base_value: number;
  value_space: "probability" | "log_odds";
  top_features: TopFeature[];
  narrative_summary: string | null;
}

// ---- Model ----

export interface ConfusionMatrix {
  true_negative: number;
  false_positive: number;
  false_negative: number;
  true_positive: number;
}

export interface ThresholdOptimization {
  optimal_threshold: number;
  precision_at_optimal: number;
  recall_at_optimal: number;
  f1_at_optimal: number;
  test_set_metrics_at_optimal_threshold?: Record<string, unknown>;
}

export interface CalibrationData {
  mean_predicted_probability: number[];
  observed_fraud_fraction: number[];
  mean_calibration_error: number;
}

export interface ShapGlobalImportance {
  global_feature_importance: Record<string, number>;
  top_10_features: string[];
  sample_size_used: number;
  value_space: "probability" | "log_odds";
}

export interface ModelMetrics {
  threshold: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  pr_auc: number;
  confusion_matrix: ConfusionMatrix;
  threshold_optimization: ThresholdOptimization;
  calibration: CalibrationData;
  native_feature_importance: Record<string, number>;
  shap_global_importance: ShapGlobalImportance;
}

export interface ModelInfoResponse {
  version_tag: string;
  algorithm: string;
  is_active: boolean;
  trained_at: string;
  metrics: ModelMetrics;
}

// ---- Dashboard / Analytics ----

export interface DashboardResponse {
  total_transactions: number;
  fraud_count: number;
  legitimate_count: number;
  fraud_rate_pct: number;
  risk_distribution: Record<RiskLevel, number>;
  recent_predictions: TransactionSummary[];
  active_model_version: string | null;
  active_model_algorithm: string | null;
}

export interface FraudTrendPoint {
  date: string;
  total_transactions: number;
  fraud_count: number;
}

export interface AnalyticsResponse {
  fraud_trend: FraudTrendPoint[];
  risk_distribution: Record<RiskLevel, number>;
  avg_fraud_probability: number;
  avg_prediction_confidence: number;
  total_predictions: number;
}

// ---- Audit ----

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  log_metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

// ---- Chat / Analyst Assistant ----

export interface ChatRequest {
  message: string;
  transaction_id?: string | null;
}

export interface ChatResponse {
  message: string;
  grounded: boolean;
  context_used: Record<string, unknown> | null;
}

export interface ChatHistoryTurn {
  role: "user" | "assistant";
  message: string;
  created_at: string;
}

export interface ChatHistoryResponse {
  transaction_id: string | null;
  turns: ChatHistoryTurn[];
}

// ---- API error shape (matches the global FastAPI exception handler) ----

export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
