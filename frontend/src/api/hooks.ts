import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import type { ChatRequest, TransactionInput, TransactionListFilters } from "@/types/api";

// ---- Auth ----

export function useLogin() {
  const setTokens = useAuthStore((s) => s.setTokens);
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      api.login(email, password),
    onSuccess: (data) => setTokens(data.access_token, data.refresh_token),
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: api.register,
  });
}

export function useCurrentUser() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setUser = useAuthStore((s) => s.setUser);
  return useQuery({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const user = await api.fetchCurrentUser();
      setUser(user);
      return user;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60_000,
  });
}

export function useLogout() {
  const { refreshToken, logout: clearAuth } = useAuthStore();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await api.logout(refreshToken);
      }
    },
    onSettled: () => {
      clearAuth();
      queryClient.clear();
    },
  });
}

// ---- Prediction ----

export function usePredictTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TransactionInput) => api.predictTransaction(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUploadTransactionsCsv() {
  return useMutation({
    mutationFn: (file: File) => api.uploadTransactionsCsv(file),
  });
}

export function useTriggerBatchPrediction() {
  return useMutation({
    mutationFn: (batchId: string) => api.triggerBatchPrediction(batchId),
  });
}

export function useBatchStatus(batchId: string | null, options?: { pollWhileProcessing?: boolean }) {
  return useQuery({
    queryKey: ["batchStatus", batchId],
    queryFn: () => api.fetchBatchStatus(batchId as string),
    enabled: Boolean(batchId),
    refetchInterval: (query) => {
      if (!options?.pollWhileProcessing) return false;
      return query.state.data?.status === "completed" ? false : 2000;
    },
  });
}

// ---- Transactions ----

export function useTransactions(filters: TransactionListFilters = {}) {
  return useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => api.fetchTransactions(filters),
  });
}

export function useTransactionDetail(transactionId: string | null) {
  return useQuery({
    queryKey: ["transaction", transactionId],
    queryFn: () => api.fetchTransactionDetail(transactionId as string),
    enabled: Boolean(transactionId),
  });
}

// ---- Explanation ----

export function useExplainTransaction(transactionId: string | null) {
  return useQuery({
    queryKey: ["explanation", transactionId],
    queryFn: () => api.explainTransaction(transactionId as string),
    enabled: Boolean(transactionId),
    staleTime: Infinity, // explanations are cached server-side too; no need to refetch
  });
}

// ---- Model ----

export function useActiveModelInfo() {
  return useQuery({
    queryKey: ["modelInfo"],
    queryFn: api.fetchActiveModelInfo,
  });
}

// ---- Dashboard / Analytics ----

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: api.fetchDashboard,
    refetchInterval: 30_000,
  });
}

export function useAnalytics(days = 30) {
  return useQuery({
    queryKey: ["analytics", days],
    queryFn: () => api.fetchAnalytics(days),
  });
}

// ---- Audit ----

export function useAuditLogs(page = 1, pageSize = 50) {
  return useQuery({
    queryKey: ["auditLogs", page, pageSize],
    queryFn: () => api.fetchAuditLogs(page, pageSize),
  });
}

// ---- Analyst AI Assistant ----

export function useSendChatMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ChatRequest) => api.sendChatMessage(payload),
    onSuccess: (_data, variables) => {
      if (variables.transaction_id) {
        queryClient.invalidateQueries({ queryKey: ["chatHistory", variables.transaction_id] });
      }
    },
  });
}

export function useChatHistory(transactionId: string | null) {
  return useQuery({
    queryKey: ["chatHistory", transactionId],
    queryFn: () => api.fetchChatHistory(transactionId as string),
    enabled: Boolean(transactionId),
  });
}
