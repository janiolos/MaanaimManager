/** Tipos do módulo finance - espelham os schemas Pydantic do backend. */

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

export interface Lancamento {
  id: number;
  evento_id: number;
  tipo: "RECEITA" | "DESPESA";
  categoria_id: number;
  conta_id: number;
  data: string;
  descricao: string;
  valor: string;
  forma_pagamento: "DINHEIRO" | "PIX" | "CARTAO" | "OUTRO";
  criado_por_id: number;
  criado_em: string;
  atualizado_por_id: number | null;
  atualizado_em: string;
  setor_origem: string | null;
  pessoa: string | null;
  assinatura_b64: string | null;
  anexos: AnexoLancamento[];
}

export interface AnexoLancamento {
  id: number;
  lancamento_id: number;
  arquivo: string;
  descricao: string;
  enviado_por_id: number;
  enviado_em: string;
}

export interface PaginatedLancamentos {
  items: Lancamento[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardKPIs {
  receitas: string;
  despesas: string;
  saldo: string;
  total_lancamentos: number;
  por_forma_pagamento: Record<string, string>;
  por_categoria: Record<string, string>;
}

export const TIPO_LABELS: Record<string, string> = {
  RECEITA: "Receita",
  DESPESA: "Despesa",
};

export const FORMA_PAGAMENTO_LABELS: Record<string, string> = {
  DINHEIRO: "Dinheiro",
  PIX: "PIX",
  CARTAO: "Cartão",
  OUTRO: "Outro",
};

export const FORMA_PAGAMENTO_COLORS: Record<string, string> = {
  DINHEIRO: "bg-emerald-500/10 text-emerald-600",
  PIX: "bg-violet-500/10 text-violet-600",
  CARTAO: "bg-blue-500/10 text-blue-600",
  OUTRO: "bg-gray-500/10 text-gray-600",
};

// --------------------------- Relatórios ---------------------------

export interface DRELine {
  categoria: string;
  total: string;
}

export interface DREOut {
  data_inicio: string | null;
  data_fim: string | null;
  total_receitas: string;
  total_despesas: string;
  resultado_liquido: string;
  margem_percentual: number | null;
  receitas_por_categoria: DRELine[];
  despesas_por_categoria: DRELine[];
}

export interface CashFlowLine {
  data: string;
  receitas: string;
  despesas: string;
  saldo_dia: string;
  saldo_acumulado: string;
}

export interface CashFlowOut {
  linhas: CashFlowLine[];
  total_receitas: string;
  total_despesas: string;
  saldo_final: string;
}

export interface ConciliacaoLine {
  forma_pagamento: string;
  receitas: string;
  despesas: string;
  total: string;
}

export interface ConciliacaoOut {
  linhas: ConciliacaoLine[];
  total_receitas: string;
  total_despesas: string;
  saldo: string;
}

export interface OfficialReportLine {
  id: number;
  data: string;
  descricao: string;
  categoria: string;
  valor: string;
  forma_pagamento: string;
}

export interface OfficialReportOut {
  receitas: OfficialReportLine[];
  despesas: OfficialReportLine[];
  total_receitas: string;
  total_despesas: string;
  saldo: string;
  data_inicio: string | null;
  data_fim: string | null;
}