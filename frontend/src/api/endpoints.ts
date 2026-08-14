import { apiClient } from "@/api/client";
import type {
  AnalyticsResponse,
  AuditLogListResponse,
  BatchStatusResponse,
  BatchUploadResponse,
  ChatHistoryResponse,
  ChatRequest,
  ChatResponse,
  DashboardResponse,
  ExplanationResponse,
  ModelInfoResponse,
  PredictionResponse,
  TokenPair,
  TransactionDetail,
  TransactionInput,
  TransactionListFilters,
  TransactionListResponse,
  User,
} from "@/types/api";

// ---- Auth ----

export async function login(email: string, password: string): Promise<TokenPair> {
  const { data } = await apiClient.post<TokenPair>("/auth/login", { email, password });
  return data;
}

export async function register(payload: {
  email: string;
  password: string;
  full_name: string;
  role?: string;
}): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", payload);
  return data;
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post("/auth/logout", { refresh_token: refreshToken });
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/users/me");
  return data;
}

// ---- Health ----

export interface HealthResponse {
  status: string;
  service: string;
  database: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}

// ---- Prediction ----

export async function predictTransaction(payload: TransactionInput): Promise<PredictionResponse> {
  const { data } = await apiClient.post<PredictionResponse>("/predict", payload);
  return data;
}

export async function uploadTransactionsCsv(file: File): Promise<BatchUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<BatchUploadResponse>("/transactions/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function triggerBatchPrediction(batchId: string): Promise<BatchUploadResponse> {
  const { data } = await apiClient.post<BatchUploadResponse>(
    `/predict/batch?batch_id=${encodeURIComponent(batchId)}`
  );
  return data;
}

export async function fetchBatchStatus(batchId: string): Promise<BatchStatusResponse> {
  const { data } = await apiClient.get<BatchStatusResponse>(`/predict/batch/${batchId}/status`);
  return data;
}

// ---- Transactions ----

export async function fetchTransactions(
  filters: TransactionListFilters = {}
): Promise<TransactionListResponse> {
  const { data } = await apiClient.get<TransactionListResponse>("/transactions", { params: filters });
  return data;
}

export async function fetchTransactionDetail(transactionId: string): Promise<TransactionDetail> {
  const { data } = await apiClient.get<TransactionDetail>(`/transactions/${transactionId}`);
  return data;
}

// ---- Explanation ----

export async function explainTransaction(transactionId: string): Promise<ExplanationResponse> {
  const { data } = await apiClient.post<ExplanationResponse>("/explain", {
    transaction_id: transactionId,
  });
  return data;
}

// ---- Model ----

export async function fetchActiveModelInfo(): Promise<ModelInfoResponse> {
  const { data } = await apiClient.get<ModelInfoResponse>("/model/info");
  return data;
}

// ---- Dashboard / Analytics ----

export async function fetchDashboard(): Promise<DashboardResponse> {
  const { data } = await apiClient.get<DashboardResponse>("/dashboard");
  return data;
}

export async function fetchAnalytics(days = 30): Promise<AnalyticsResponse> {
  const { data } = await apiClient.get<AnalyticsResponse>("/analytics", { params: { days } });
  return data;
}

// ---- Audit ----

export async function fetchAuditLogs(page = 1, pageSize = 50): Promise<AuditLogListResponse> {
  const { data } = await apiClient.get<AuditLogListResponse>("/audit-logs", {
    params: { page, page_size: pageSize },
  });
  return data;
}

// ---- Analyst AI Assistant ----

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>("/chat", payload);
  return data;
}

export async function fetchChatHistory(transactionId: string): Promise<ChatHistoryResponse> {
  const { data } = await apiClient.get<ChatHistoryResponse>(`/chat/history/${transactionId}`);
  return data;
}
