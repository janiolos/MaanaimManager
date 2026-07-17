/** Tipos do módulo lodging - espelham schemas Pydantic do backend. */

export const CHALE_STATUS_LABELS: Record<string, string> = {
  ATIVO: "Ativo",
  MANUTENCAO: "Manutenção",
  INATIVO: "Inativo",
};

export const RESERVA_STATUS_LABELS: Record<string, string> = {
  PRE_RESERVA: "Pré-reserva",
  CONFIRMADA: "Confirmada",
  CANCELADA: "Cancelada",
};

export const RESERVA_STATUS_ATIVOS = ["PRE_RESERVA", "CONFIRMADA"];

export const ACAO_TIPO_LABELS: Record<string, string> = {
  BLOQUEIO: "Bloqueio",
  MANUTENCAO: "Manutenção",
};

export const FORMA_PAGAMENTO_LABELS: Record<string, string> = {
  DINHEIRO: "Dinheiro",
  PIX: "PIX",
  CARTAO: "Cartão",
  OUTRO: "Outro",
};

export interface Chale {
  id: number;
  codigo: string;
  capacidade: number;
  status: string;
  acessivel_cadeirante: boolean;
  observacoes: string;
}

export interface Reserva {
  id: number;
  evento_id: number;
  chale_id: number;
  data_entrada: string | null;
  data_saida: string | null;
  responsavel_nome: string;
  qtd_pessoas: number;
  qtd_criancas: number;
  idades_criancas: string;
  possui_necessidade_especial: boolean;
  detalhes_necessidade_especial: string;
  status: string;
  valor_adicional: string;
  pago: boolean;
  forma_pagamento: string;
  conta_id: number | null;
  lancamento_financeiro_id: number | null;
  observacoes: string;
  criado_por_id: number;
  criado_em: string;
  atualizado_por_id: number | null;
  atualizado_em: string;
}

export interface Acao {
  id: number;
  evento_id: number;
  chale_id: number;
  tipo: string;
  titulo: string;
  data_inicio: string;
  data_fim: string;
  descricao: string;
  ativo: boolean;
  criado_por_id: number;
  criado_em: string;
}

export interface LodgingDashboard {
  total_chales: number;
  chales_ativos: number;
  chales_manutencao: number;
  reservas_ativas: number;
  reservas_confirmadas: number;
  acoes_ativas: number;
}

export interface MapaCell {
  chale_id: number;
  chale_codigo: string;
  data: string;
  tipo: "RESERVA" | "ACAO" | "LIVRE";
  label: string;
  reserva_id: number | null;
  acao_id: number | null;
}

export interface MapaResponse {
  chales: Chale[];
  dias: string[];
  celulas: MapaCell[][];
}

export interface PaginatedReservas {
  items: Reserva[];
  total: number;
  page: number;
  page_size: number;
}

export interface PaginatedAcoes {
  items: Acao[];
  total: number;
  page: number;
  page_size: number;
}