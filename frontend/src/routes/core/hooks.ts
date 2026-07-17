import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { CentroCusto, Evento, PaginatedAuditLogs, PaginatedOrdensCompra, UserSimple, User, Group, Permission, Role, UserPermissionsOut, CategoriaFinanceira, ContaCaixa, Fornecedor } from "@/routes/core/types";

export function useEventos(apenasAtivos: boolean = false) {
  return useQuery<Evento[]>({
    queryKey: ["core", "eventos", { apenasAtivos }],
    queryFn: async () => {
      const { data } = await api.get<Evento[]>("/core/eventos", {
        params: { apenas_ativos: apenasAtivos },
      });
      return data;
    },
    staleTime: 30_000,
  });
}

export function useEvento(id?: string | number) {
  return useQuery<Evento>({
    queryKey: ["core", "eventos", id],
    queryFn: async () => {
      const { data } = await api.get<Evento>(`/core/eventos/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useCentrosCusto() {
  return useQuery<CentroCusto[]>({
    queryKey: ["core", "centros-custo"],
    queryFn: async () => {
      const { data } = await api.get<CentroCusto[]>("/core/centros-custo");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useUsers() {
  return useQuery<UserSimple[]>({
    queryKey: ["core", "users"],
    queryFn: async () => {
      const { data } = await api.get<UserSimple[]>("/core/users");
      return data;
    },
    staleTime: 60_000,
  });
}

// Admin hooks
export function useAdminUsers() {
  return useQuery<User[]>({
    queryKey: ["admin", "users"],
    queryFn: async () => {
      const { data } = await api.get<User[]>("/core/users");
      return data;
    },
    staleTime: 30_000,
  });
}

export function useAdminGrupos() {
  return useQuery<Group[]>({
    queryKey: ["admin", "grupos"],
    queryFn: async () => {
      const { data } = await api.get<Group[]>("/core/grupos");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useCriarUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Omit<User, "id" | "groups"> & { password: string; group_ids: number[] }) => {
      const { data } = await api.post("/core/users", payload);
      return data as User;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "users"] }),
  });
}

export function useAtualizarUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Omit<User, "id" | "groups"> & { group_ids?: number[] }> }) => {
      const { data } = await api.patch(`/core/users/${id}`, payload);
      return data as User;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "users"] }),
  });
}

export function useDeletarUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/core/users/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "users"] }),
  });
}

export function useResetPasswordUser() {
  return useMutation({
    mutationFn: async ({ id, password }: { id: number; password: string }) => {
      await api.post(`/core/users/${id}/reset-password`, { password });
    },
  });
}

// Permissões v2 hooks
export function usePermissions() {
  return useQuery<Permission[]>({
    queryKey: ["admin", "permissions"],
    queryFn: async () => {
      const { data } = await api.get<Permission[]>("/core/permissions");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useRoles() {
  return useQuery<Role[]>({
    queryKey: ["admin", "roles"],
    queryFn: async () => {
      const { data } = await api.get<Role[]>("/core/roles");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useUserPermissions(userId?: number) {
  return useQuery<UserPermissionsOut>({
    queryKey: ["admin", "user-permissions", userId],
    queryFn: async () => {
      const { data } = await api.get<UserPermissionsOut>(`/core/users/${userId}/permissions`);
      return data;
    },
    enabled: !!userId,
    staleTime: 30_000,
  });
}

export function useAddUserPermission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, permissionId }: { userId: number; permissionId: number }) => {
      await api.post(`/core/users/${userId}/permissions`, { permission_id: permissionId });
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["admin", "user-permissions", vars.userId] }),
  });
}

export function useRemoveUserPermission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, permissionId }: { userId: number; permissionId: number }) => {
      await api.delete(`/core/users/${userId}/permissions/${permissionId}`);
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["admin", "user-permissions", vars.userId] }),
  });
}

export function useAddUserRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, roleId }: { userId: number; roleId: number }) => {
      await api.post(`/core/users/${userId}/roles`, { role_id: roleId });
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["admin", "user-permissions", vars.userId] }),
  });
}

export function useRemoveUserRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, roleId }: { userId: number; roleId: number }) => {
      await api.delete(`/core/users/${userId}/roles/${roleId}`);
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["admin", "user-permissions", vars.userId] }),
  });
}

export function useSyncRolePermissions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ roleId, permissionIds }: { roleId: number; permissionIds: number[] }) => {
      await api.patch(`/core/roles/${roleId}/permissions`, { permission_ids: permissionIds });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "roles"] }),
  });
}

// ============================ Centros de Custo ============================

export function useAdminCentrosCusto() {
  return useQuery<CentroCusto[]>({
    queryKey: ["admin", "centros-custo"],
    queryFn: async () => {
      const { data } = await api.get<CentroCusto[]>("/core/centros-custo");
      return data;
    },
    staleTime: 30_000,
  });
}

export function useCriarCentroCusto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Omit<CentroCusto, "id">) => {
      const { data } = await api.post("/core/centros-custo", payload);
      return data as CentroCusto;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "centros-custo"] }),
  });
}

export function useAtualizarCentroCusto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Omit<CentroCusto, "id">> }) => {
      const { data } = await api.patch(`/core/centros-custo/${id}`, payload);
      return data as CentroCusto;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "centros-custo"] }),
  });
}

export function useDeletarCentroCusto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/core/centros-custo/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "centros-custo"] }),
  });
}

// ============================ Categorias Financeiras ============================

export function useAdminCategorias() {
  return useQuery<CategoriaFinanceira[]>({
    queryKey: ["admin", "categorias"],
    queryFn: async () => {
      const { data } = await api.get<CategoriaFinanceira[]>("/finance/categorias");
      return data;
    },
    staleTime: 30_000,
  });
}

export function useCriarCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Omit<CategoriaFinanceira, "id">) => {
      const { data } = await api.post("/finance/categorias", payload);
      return data as CategoriaFinanceira;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "categorias"] }),
  });
}

export function useAtualizarCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Omit<CategoriaFinanceira, "id">> }) => {
      const { data } = await api.patch(`/finance/categorias/${id}`, payload);
      return data as CategoriaFinanceira;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "categorias"] }),
  });
}

export function useDeletarCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/finance/categorias/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "categorias"] }),
  });
}

// ============================ Contas Caixa ============================

export function useAdminContas() {
  return useQuery<ContaCaixa[]>({
    queryKey: ["admin", "contas"],
    queryFn: async () => {
      const { data } = await api.get<ContaCaixa[]>("/finance/contas", { params: { apenas_ativos: false } });
      return data;
    },
    staleTime: 30_000,
  });
}

export function useCriarConta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Omit<ContaCaixa, "id">) => {
      const { data } = await api.post("/finance/contas", payload);
      return data as ContaCaixa;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "contas"] }),
  });
}

export function useAtualizarConta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Omit<ContaCaixa, "id">> }) => {
      const { data } = await api.patch(`/finance/contas/${id}`, payload);
      return data as ContaCaixa;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "contas"] }),
  });
}

export function useDeletarConta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/finance/contas/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "contas"] }),
  });
}

// ============================ Fornecedores ============================

export function useAdminFornecedores() {
  return useQuery<Fornecedor[]>({
    queryKey: ["admin", "fornecedores"],
    queryFn: async () => {
      const { data } = await api.get<Fornecedor[]>("/inventory/fornecedores");
      return data;
    },
    staleTime: 30_000,
  });
}

export function useCriarFornecedor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Omit<Fornecedor, "id" | "criado_em">) => {
      const { data } = await api.post("/inventory/fornecedores", payload);
      return data as Fornecedor;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "fornecedores"] }),
  });
}

export function useAtualizarFornecedor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Omit<Fornecedor, "id" | "criado_em">> }) => {
      const { data } = await api.patch(`/inventory/fornecedores/${id}`, payload);
      return data as Fornecedor;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "fornecedores"] }),
  });
}

export function useDeletarFornecedor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/inventory/fornecedores/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "fornecedores"] }),
  });
}

// ============================ Audit Logs ============================

type AuditLogFilters = {
  page?: number;
  page_size?: number;
  user_id?: number;
  method?: string;
  status_code?: number;
  data_inicio?: string;
  data_fim?: string;
};

export function useAuditLogs(filters: AuditLogFilters = {}) {
  return useQuery<PaginatedAuditLogs>({
    queryKey: ["admin", "audit-logs", filters],
    queryFn: async () => {
      const { data } = await api.get<PaginatedAuditLogs>("/core/audit-logs", { params: filters });
      return data;
    },
    staleTime: 15_000,
  });
}

// ============================ Ordens de Compra ============================

export function useOrdensCompra(page: number = 1, page_size: number = 50) {
  return useQuery<PaginatedOrdensCompra>({
    queryKey: ["admin", "ordens-compra", { page, page_size }],
    queryFn: async () => {
      const { data } = await api.get<PaginatedOrdensCompra>("/inventory/ordens-compra", { params: { page, page_size } });
      return data;
    },
    staleTime: 30_000,
  });
}

// ============================ Locais de Venda (Admin) ============================

export function useAdminLocaisVenda() {
  return useQuery<any[]>({
    queryKey: ["admin", "locais-venda"],
    queryFn: async () => {
      const { data } = await api.get("/pos/locais", { params: { apenas_ativos: false } });
      return data;
    },
    staleTime: 30_000,
  });
}

export function useCriarLocalVenda() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { nome: string }) => {
      const { data } = await api.post("/pos/locais", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "locais-venda"] }),
  });
}

export function useAtualizarLocalVenda() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Record<string, any> }) => {
      const { data } = await api.patch(`/pos/locais/${id}`, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "locais-venda"] }),
  });
}

// ============================ Famílias (Admin) ============================

export function useAdminFamilias(localId: number | null) {
  return useQuery<any[]>({
    queryKey: ["admin", "familias", localId],
    queryFn: async () => {
      const { data } = await api.get(`/pos/locais/${localId}/familias`);
      return data;
    },
    enabled: !!localId,
    staleTime: 30_000,
  });
}

export function useCriarFamilia() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ localId, nome }: { localId: number; nome: string }) => {
      const { data } = await api.post(`/pos/locais/${localId}/familias`, { nome });
      return data;
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["admin", "familias", vars.localId] }),
  });
}

export function useDeletarFamilia() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ localId, familiaId }: { localId: number; familiaId: number }) => {
      await api.delete(`/pos/locais/${localId}/familias/${familiaId}`);
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["admin", "familias", vars.localId] }),
  });
}
