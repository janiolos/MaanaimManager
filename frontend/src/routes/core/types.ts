export interface CentroCusto {
  id: number;
  nome: string;
  codigo: string;
  ativo: boolean;
}

export interface CategoriaFinanceira {
  id: number;
  nome: string;
  tipo: "RECEITA" | "DESPESA";
}

export interface ContaCaixa {
  id: number;
  nome: string;
  ativo: boolean;
}

export interface Fornecedor {
  id: number;
  nome: string;
  documento: string;
  contato: string;
  telefone: string;
  email: string;
  ativo: boolean;
  criado_em: string;
}

export interface UserSimple {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
}

export interface Group {
  id: number;
  name: string;
}

export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_staff: boolean;
  groups: Group[];
}

export interface Evento {
  id: number;
  nome: string;
  data_inicio: string;
  data_fim: string;
  ativo: boolean;
  status: "PLANEJADO" | "EM_ANDAMENTO" | "ENCERRADO";
  fechado: boolean;
  taxa_base: string;
  taxa_trabalhador: string;
  adicional_chale: string;
  prev_participantes: number | null;
  prev_trabalhadores: number | null;
  observacoes: string;
  responsavel_geral_id: number | null;
  centro_custo_id: number | null;
  responsavel_geral?: UserSimple | null;
  centro_custo?: CentroCusto | null;
}

export const STATUS_EVENTO_LABELS: Record<string, string> = {
  PLANEJADO: "Planejado",
  EM_ANDAMENTO: "Em andamento",
  ENCERRADO: "Encerrado",
};

export interface Permission {
  id: number;
  scope: string;
  nome: string;
  descricao: string;
  categoria: string;
  ativo: boolean;
}

export interface Role {
  id: number;
  nome: string;
  descricao: string;
  ativo: boolean;
  permissions?: Permission[];
}

export interface UserPermissionsOut {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  scopes: string[];
  roles: Role[];
  permissions: Permission[];
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  user_name: string | null;
  method: string;
  path: string;
  view_name: string;
  status_code: number;
  ip_address: string | null;
  user_agent: string;
  created_at: string;
}

export interface PaginatedAuditLogs {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
}

export interface OrdemCompra {
  id: number;
  numero: string;
  cotacao_id: number;
  fornecedor_id: number;
  fornecedor_nome: string;
  mensagem: string;
  valor_total: number;
  status_envio: string;
  enviada_em: string | null;
  criado_por_id: number;
  criado_por_nome: string;
  evento_id: number | null;
  criado_em: string;
}

export interface PaginatedOrdensCompra {
  items: OrdemCompra[];
  total: number;
  page: number;
  page_size: number;
}
