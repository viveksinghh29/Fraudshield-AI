import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { getStoredAccessToken, getStoredRefreshToken, useAuthStore } from "@/store/authStore";
import type { AccessTokenResponse, ApiErrorResponse } from "@/types/api";

export const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 20_000,
  headers: { "Content-Type": "application/json" },
});

// ---- Attach the access token to every request ----
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getStoredAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---- Refresh-on-401: a single in-flight refresh shared by any requests that race into it ----
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }
  const { data } = await axios.post<AccessTokenResponse>("/api/v1/auth/refresh", {
    refresh_token: refreshToken,
  });
  useAuthStore.getState().setAccessToken(data.access_token);
  return data.access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    const isAuthEndpoint = originalRequest?.url?.includes("/auth/");
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      try {
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        const newAccessToken = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

/** Extracts a human-readable message from the backend's standard error shape. */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiErrorResponse | undefined;
    if (data?.message) return data.message;
    if (error.response?.status === 401) return "Session expired. Please log in again.";
    if (error.message === "Network Error") return "Could not reach the server.";
  }
  return "Something went wrong. Please try again.";
}
