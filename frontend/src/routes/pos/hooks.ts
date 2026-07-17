import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useEventoStore } from "@/stores/evento-store";
import type {
  EntradaEstoqueLocalCreate,
  TransferenciaEstoqueLocalCreate,
  FamiliaVenda,
  FamiliaVendaCreate,
  LocalVenda,
  LocalVendaCreate,
  LocalVendaUpdate,
  PDVDashboard,
  ProdutoLocal,
  ProdutoLocalCreate,
  ProdutoLocalUpdate,
  VendaOut,
  VendaPayload,
} from "@/routes/pos/types";

const POS_LOCAL_STORAGE_KEY = "maanaim-pos-local";

// Locais
export function useLocais() {
  return useQuery<LocalVenda[]>({
    queryKey: ["pos", "locais"],
    queryFn: async () => {
      const { data } = await api.get("/pos/locais");
      return data;
    },
  });
}

export function usePosLocalAtual() {
  const { data: locais } = useLocais();
  const [localId, setLocalIdState] = useState<number | null>(() => {
    if (typeof window === "undefined") return null;
    const raw = window.localStorage.getItem(POS_LOCAL_STORAGE_KEY);
    return raw ? Number(raw) : null;
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(POS_LOCAL_STORAGE_KEY);
    setLocalIdState(raw ? Number(raw) : null);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (localId === null) {
      window.localStorage.removeItem(POS_LOCAL_STORAGE_KEY);
    } else {
      window.localStorage.setItem(POS_LOCAL_STORAGE_KEY, String(localId));
    }
  }, [localId]);

  const localAtual = useMemo(
    () => locais?.find((local) => local.id === localId) ?? null,
    [locais, localId],
  );

  useEffect(() => {
    if (!locais || localId === null) return;
    if (!locais.some((local) => local.id === localId)) {
      setLocalIdState(null);
    }
  }, [locais, localId]);

  const setLocalId = (next: number | null) => {
    setLocalIdState(next);
  };

  return { localId, setLocalId, localAtual, locais: locais ?? [] };
}

export function useCriarLocal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LocalVendaCreate) => {
      const { data } = await api.post("/pos/locais", payload);
      return data as LocalVenda;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pos", "locais"] }),
  });
}

export function useAtualizarLocal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: LocalVendaUpdate }) => {
      const { data } = await api.patch(`/pos/locais/${id}`, payload);
      return data as LocalVenda;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pos", "locais"] }),
  });
}

export function useAbrirCaixa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (localId: number) => {
      const { data } = await api.post(`/pos/locais/${localId}/abrir-caixa`);
      return data as LocalVenda;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pos", "locais"] }),
  });
}

export function useFecharCaixa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (localId: number) => {
      const { data } = await api.post(`/pos/locais/${localId}/fechar-caixa`);
      return data as LocalVenda;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pos", "locais"] }),
  });
}

// Famílias
export function useFamilias(localId: number) {
  return useQuery<FamiliaVenda[]>({
    queryKey: ["pos", "familias", localId],
    queryFn: async () => {
      const { data } = await api.get(`/pos/locais/${localId}/familias`);
      return data;
    },
    enabled: !!localId,
  });
}

export function useCriarFamilia() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ localId, payload }: { localId: number; payload: FamiliaVendaCreate }) => {
      const { data } = await api.post(`/pos/locais/${localId}/familias`, payload);
      return data as FamiliaVenda;
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["pos", "familias", vars.localId] }),
  });
}

export function useDeletarFamilia() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ localId, familiaId }: { localId: number; familiaId: number }) => {
      await api.delete(`/pos/locais/${localId}/familias/${familiaId}`);
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["pos", "familias", vars.localId] }),
  });
}

// Produtos do local
export function useProdutosLocal(localId: number) {
  return useQuery<ProdutoLocal[]>({
    queryKey: ["pos", "produtos", localId],
    queryFn: async () => {
      const { data } = await api.get(`/pos/locais/${localId}/produtos`);
      return data;
    },
    enabled: !!localId,
  });
}

export function useCriarProdutoLocal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ localId, payload }: { localId: number; payload: ProdutoLocalCreate }) => {
      const { data } = await api.post(`/pos/locais/${localId}/produtos`, payload);
      return data as ProdutoLocal;
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["pos", "produtos", vars.localId] }),
  });
}

export function useAtualizarProdutoLocal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ProdutoLocalUpdate }) => {
      const { data } = await api.patch(`/pos/produtos-locais/${id}`, payload);
      return data as ProdutoLocal;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pos", "produtos"] }),
  });
}

export function useDeletarProdutoLocal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/pos/produtos-locais/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pos", "produtos"] }),
  });
}

// Entradas de estoque local
export function useCriarEntradaLocal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: EntradaEstoqueLocalCreate) => {
      const { data } = await api.post("/pos/entradas", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pos"] }),
  });
}

export function useCriarTransferenciaLocal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TransferenciaEstoqueLocalCreate) => {
      const { data } = await api.post("/pos/transferencias", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pos"] });
      qc.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
}

// Dashboard PDV
export function usePDVDashboard(localId?: number, mes?: string, eventoFiltroId?: number | null) {
  const eventoId = useEventoStore((s) => s.eventoId);
  return useQuery<PDVDashboard>({
    queryKey: ["pos", "dashboard", eventoId, localId, mes, eventoFiltroId],
    queryFn: async () => {
      const { data } = await api.get("/pos/dashboard", {
        params: {
          ...(localId ? { local_id: localId } : {}),
          ...(mes ? { mes } : {}),
          ...(eventoFiltroId ? { evento_filtro_id: eventoFiltroId } : {}),
        },
      });
      return data;
    },
    enabled: eventoId !== null,
  });
}

// Criar venda
export function useCriarVenda() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: VendaPayload) => {
      const { data } = await api.post("/pos/vendas", payload);
      return data as VendaOut;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pos"] });
    },
  });
}

// Listar vendas
export function useVendas(
  localId?: number,
  page = 1,
  filters: { familia?: string; produto?: string } = {},
) {
  const eventoId = useEventoStore((s) => s.eventoId);
  return useQuery({
    queryKey: ["pos", "vendas", eventoId, localId, page, filters.familia ?? "", filters.produto ?? ""],
    queryFn: async () => {
      const { data } = await api.get("/pos/vendas", {
        params: {
          page,
          page_size: 20,
          ...(localId ? { local_id: localId } : {}),
          ...(filters.familia ? { familia: filters.familia } : {}),
          ...(filters.produto ? { produto: filters.produto } : {}),
        },
      });
      return data;
    },
    enabled: eventoId !== null,
  });
}

export function useDeletarVenda() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vendaId: number) => {
      await api.delete(`/pos/vendas/${vendaId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pos"] });
      qc.invalidateQueries({ queryKey: ["finance"] });
    },
  });
}

export interface CaixaAtualOut {
  caixa_aberto: boolean;
  aberto_em: string | null;
  total_vendas: number;
  soma_total: number;
  por_forma: Record<string, number>;
}

export function useCaixaAtual(localId: number) {
  return useQuery<CaixaAtualOut>({
    queryKey: ["pos", "caixa-atual", localId],
    queryFn: async () => {
      const { data } = await api.get(`/pos/locais/${localId}/caixa-atual`);
      return data;
    },
    enabled: !!localId,
  });
}
