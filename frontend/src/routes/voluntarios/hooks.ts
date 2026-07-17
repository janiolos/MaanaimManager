import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Voluntario } from "./types";

export function useVoluntarios() {
  return useQuery<Voluntario[]>({
    queryKey: ["voluntarios"],
    queryFn: async () => {
      const { data } = await api.get<Voluntario[]>("/voluntarios");
      return data;
    },
    staleTime: 30_000,
  });
}

export function useVoluntario(id?: string | number) {
  return useQuery<Voluntario>({
    queryKey: ["voluntarios", id],
    queryFn: async () => {
      const { data } = await api.get<Voluntario>(`/voluntarios/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useCriarVoluntario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Omit<Voluntario, "id">) => {
      const { data } = await api.post("/voluntarios", payload);
      return data as Voluntario;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["voluntarios"] }),
  });
}

export function useAtualizarVoluntario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Omit<Voluntario, "id">> }) => {
      const { data } = await api.patch(`/voluntarios/${id}`, payload);
      return data as Voluntario;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["voluntarios"] }),
  });
}

export function useDeletarVoluntario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/voluntarios/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["voluntarios"] }),
  });
}
