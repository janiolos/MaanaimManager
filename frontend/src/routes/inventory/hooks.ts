import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  Fornecedor,
  InventoryDashboard,
  PaginatedProdutos,
  Produto,
} from "@/routes/inventory/types";

export function useProdutos(opts: {
  ativo?: boolean;
  busca?: string;
  categoria?: string;
  status?: string;
  page?: number;
  page_size?: number;
} = {}) {
  return useQuery<PaginatedProdutos>({
    queryKey: ["inventory", "produtos", opts],
    queryFn: async () => {
      const { data } = await api.get<PaginatedProdutos>("/inventory/produtos", {
        params: {
          ativo: opts.ativo,
          busca: opts.busca || undefined,
          categoria: opts.categoria || undefined,
          status: opts.status || undefined,
          page: opts.page ?? 1,
          page_size: opts.page_size ?? 12,
        },
      });
      return data;
    },
    staleTime: 30_000,
  });
}

export function useProduto(id?: string | number) {
  return useQuery<Produto>({
    queryKey: ["inventory", "produtos", id],
    queryFn: async () => {
      const { data } = await api.get<Produto>(`/inventory/produtos/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useFornecedores(ativo?: boolean) {
  return useQuery<Fornecedor[]>({
    queryKey: ["inventory", "fornecedores", ativo],
    queryFn: async () => {
      const { data } = await api.get<Fornecedor[]>("/inventory/fornecedores", {
        params: { ativo },
      });
      return data;
    },
    staleTime: 60_000,
  });
}

export function useInventoryDashboard() {
  return useQuery<InventoryDashboard>({
    queryKey: ["inventory", "dashboard"],
    queryFn: async () => {
      const { data } = await api.get<InventoryDashboard>("/inventory/dashboard");
      return data;
    },
    staleTime: 30_000,
  });
}