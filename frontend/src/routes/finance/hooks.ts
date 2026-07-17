import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  CashFlowOut,
  CategoriaFinanceira,
  ConciliacaoOut,
  ContaCaixa,
  DREOut,
  OfficialReportOut,
} from "@/routes/finance/types";

export function useCategorias(tipo?: "RECEITA" | "DESPESA") {
  return useQuery<CategoriaFinanceira[]>({
    queryKey: ["finance", "categorias", tipo ?? "all"],
    queryFn: async () => {
      const { data } = await api.get<CategoriaFinanceira[]>("/finance/categorias", {
        params: tipo ? { tipo } : undefined,
      });
      return data;
    },
    staleTime: 60_000,
  });
}

export function useContas() {
  return useQuery<ContaCaixa[]>({
    queryKey: ["finance", "contas"],
    queryFn: async () => {
      const { data } = await api.get<ContaCaixa[]>("/finance/contas");
      return data;
    },
    staleTime: 60_000,
  });
}

// --------------------------- Relatórios ---------------------------

export function useDRE(dataInicio?: string, dataFim?: string) {
  return useQuery<DREOut>({
    queryKey: ["finance", "relatorios", "dre", dataInicio, dataFim],
    queryFn: async () => {
      const { data } = await api.get<DREOut>("/finance/relatorios/dre", {
        params: { data_inicio: dataInicio || undefined, data_fim: dataFim || undefined },
      });
      return data;
    },
  });
}

export function useCashFlow(dataInicio?: string, dataFim?: string) {
  return useQuery<CashFlowOut>({
    queryKey: ["finance", "relatorios", "fluxo-caixa", dataInicio, dataFim],
    queryFn: async () => {
      const { data } = await api.get<CashFlowOut>("/finance/relatorios/fluxo-caixa", {
        params: { data_inicio: dataInicio || undefined, data_fim: dataFim || undefined },
      });
      return data;
    },
  });
}

export function useConciliacao(dataInicio?: string, dataFim?: string) {
  return useQuery<ConciliacaoOut>({
    queryKey: ["finance", "relatorios", "conciliacao", dataInicio, dataFim],
    queryFn: async () => {
      const { data } = await api.get<ConciliacaoOut>("/finance/relatorios/conciliacao", {
        params: { data_inicio: dataInicio || undefined, data_fim: dataFim || undefined },
      });
      return data;
    },
  });
}

export function useOfficialReport(dataInicio?: string, dataFim?: string) {
  return useQuery<OfficialReportOut>({
    queryKey: ["finance", "relatorios", "oficial", dataInicio, dataFim],
    queryFn: async () => {
      const { data } = await api.get<OfficialReportOut>("/finance/relatorios/oficial", {
        params: { data_inicio: dataInicio || undefined, data_fim: dataFim || undefined },
      });
      return data;
    },
  });
}