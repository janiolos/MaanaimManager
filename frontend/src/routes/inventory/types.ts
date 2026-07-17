/** Tipos do módulo inventory - espelham schemas Pydantic do backend. */

export const CATEGORIA_LABELS: Record<string, string> = {
  MATERIA_PRIMA: "Matéria-prima",
  PRODUTO_ACABADO: "Produto acabado",
  COMPONENTE: "Componente",
};

export const REQUISICAO_STATUS_LABELS: Record<string, string> = {
  ABERTA: "Aberta",
  FINALIZADA: "Finalizada",
  CANCELADA: "Cancelada",
};

export const REQUISICAO_AREA_LABELS: Record<string, string> = {
  COZINHA: "Cozinha",
  COPA: "Copa",
  CANTINA: "Cantina",
  COPA_PASTORES: "Copa Pastores",
  SECRETARIA: "Secretaria",
};

export const COTACAO_STATUS_LABELS: Record<string, string> = {
  ABERTA: "Aberta",
  FECHADA: "Fechada",
  CANCELADA: "Cancelada",
};

export const FORMA_PAGAMENTO_LABELS: Record<string, string> = {
  DINHEIRO: "Dinheiro",
  PIX: "PIX",
  CARTAO: "Cartão",
  OUTRO: "Outro",
};

export interface Produto {
  id: number;
  nome: string;
  sku: string;
  categoria: string;
  unidade: string;
  estoque_atual: string;
  estoque_minimo: string;
  estoque_reabastecimento: string;
  estoque_maximo: string;
  valor_estoque_atual: string;
  custo_medio_atual: string;
  ativo: boolean;
}

export interface PaginatedProdutos {
  items: Produto[];
  total: number;
  page: number;
  page_size: number;
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

export interface RequisicaoItem {
  id: number;
  requisicao_id: number;
  produto_id: number;
  quantidade: string;
  custo_medio_unitario: string;
  custo_total: string;
  saldo_antes: string;
  saldo_depois: string;
}

export interface Requisicao {
  id: number;
  numero: string;
  evento_id: number;
  area: string;
  data_solicitacao: string;
  status: string;
  observacao: string;
  protocolo: string;
  finalizado_em: string | null;
  finalizado_por_id: number | null;
  criado_por_id: number;
  criado_em: string;
  itens: RequisicaoItem[];
}

export interface CotacaoPreco {
  id: number;
  fornecedor_id: number;
  valor_unitario: string;
  valor_total: string;
}

export interface CotacaoItem {
  id: number;
  produto_id: number;
  quantidade: string;
  precos: CotacaoPreco[];
}

export interface Cotacao {
  id: number;
  numero: string;
  evento_id: number;
  status: string;
  observacao: string;
  criado_por_id: number;
  criado_em: string;
  fornecedor_aprovado_id: number | null;
  valor_aprovado: string | null;
  aprovado_em: string | null;
  aprovado_por_id: number | null;
  fechado_em: string | null;
  fechado_por_id: number | null;
  lancamento_financeiro_id: number | null;
  itens: CotacaoItem[];
}

export interface InventoryDashboard {
  total_produtos: number;
  produtos_ativos: number;
  estoque_baixo: number;
  estoque_reabastecer: number;
  valor_total_estoque: string;
  requisicoes_abertas: number;
  cotacoes_abertas: number;
}

export interface PaginatedRequisicoes {
  items: Requisicao[];
  total: number;
  page: number;
  page_size: number;
}

export interface PaginatedCotacoes {
  items: Cotacao[];
  total: number;
  page: number;
  page_size: number;
}