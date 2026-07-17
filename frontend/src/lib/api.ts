import type { AxiosInstance, AxiosRequestConfig } from "axios";
import axios from "axios";

import { useAuthStore } from "@/stores/auth-store";
import { useEventoStore } from "@/stores/evento-store";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

let refreshPromise: Promise<string> | null = null;
let isRefreshing = false;

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;
  isRefreshing = true;
  refreshPromise = axios
    .post<{ access_token: string }>(`${BASE_URL}/auth/refresh`, null, {
      withCredentials: true,
    })
    .then((res) => {
      const token = res.data.access_token;
      useAuthStore.getState().setAccessToken(token);
      return token;
    })
    .finally(() => {
      isRefreshing = false;
      refreshPromise = null;
    });
  return refreshPromise;
}

// Request: anexa Authorization + X-Evento-Id
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const eventoId = useEventoStore.getState().eventoId;
  if (eventoId !== null) {
    config.headers["X-Evento-Id"] = String(eventoId);
  }
  return config;
});

// Response: em 401 tenta refresh uma vez
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as AxiosRequestConfig & { _retried?: boolean };
    if (
      error.response?.status === 401 &&
      !original._retried &&
      !isRefreshing &&
      !original.url?.includes("/auth/login")
    ) {
      try {
        const newToken = await refreshAccessToken();
        original._retried = true;
        original.headers = original.headers ?? {};
        (original.headers as Record<string, string>).Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  },
);