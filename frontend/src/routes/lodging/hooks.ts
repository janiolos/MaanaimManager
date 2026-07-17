import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Chale, LodgingDashboard, MapaResponse } from "@/routes/lodging/types";

export function useChales(status?: string) {
  return useQuery<Chale[]>({
    queryKey: ["lodging", "chales", status ?? "all"],
    queryFn: async () => {
      const { data } = await api.get<Chale[]>("/lodging/chales", {
        params: status ? { status } : undefined,
      });
      return data;
    },
    staleTime: 30_000,
  });
}

export function useLodgingDashboard() {
  return useQuery<LodgingDashboard>({
    queryKey: ["lodging", "dashboard"],
    queryFn: async () => {
      const { data } = await api.get<LodgingDashboard>("/lodging/dashboard");
      return data;
    },
    staleTime: 30_000,
  });
}

export function useMapa(dias = 14) {
  return useQuery<MapaResponse>({
    queryKey: ["lodging", "mapa", dias],
    queryFn: async () => {
      const { data } = await api.get<MapaResponse>("/lodging/mapa", { params: { dias } });
      return data;
    },
    staleTime: 30_000,
  });
}