/* Tipos TypeScript do módulo POS (PDV). */

export interface LocalVenda {
  id: number;
  evento_id: number | null;
  nome: string;
  ativo: boolean;
  modulo_dashboard: boolean;
  modulo_pdv: boolean;
  modulo_vendas: boolean;
  modulo_produtos: boolean;
  modulo_estoque: boolean;
  permite_desconto: boolean;
  desconto_maximo_perc: number;
  permite_pagamento_misto: boolean;
  is_deposito_interno: boolean;
  caixa_aberto: boolean;
  caixa_aberto_em: string | null;
  caixa_aberto_por_id: number | null;
  criado_em: string;
}

export interface LocalVendaCreate {
  nome: string;
  ativo?: boolean;
  modulo_dashboard?: boolean;
  modulo_pdv?: boolean;
  modulo_vendas?: boolean;
  modulo_produtos?: boolean;
  modulo_estoque?: boolean;
  permite_desconto?: boolean;
  desconto_maximo_perc?: number;
  permite_pagamento_misto?: boolean;
}

export interface LocalVendaUpdate {
  nome?: string;
  ativo?: boolean;
  modulo_dashboard?: boolean;
  modulo_pdv?: boolean;
  modulo_vendas?: boolean;
  modulo_produtos?: boolean;
  modulo_estoque?: boolean;
  permite_desconto?: boolean;
  desconto_maximo_perc?: number;
  permite_pagamento_misto?: boolean;
}

export interface FamiliaVenda {
  id: number;
  local_id: number;
  nome: string;
}

export interface FamiliaVendaCreate {
  nome: string;
}

export interface ProdutoLocal {
  id: number;
  produto_id: number;
  local_id: number;
  familia_id: number | null;
  preco_venda: string;
  estoque_atual: string;
  estoque_minimo: string;
  ponto_reabastecimento: string;
  estoque_maximo: string;
  ativo: boolean;
  criado_em: string;
  produto_nome: string;
  produto_sku: string;
  familia_nome: string;
}

export interface ProdutoLocalCreate {
  produto_id: number;
  familia_id?: number | null;
  preco_venda?: string;
  estoque_atual?: string;
  estoque_minimo?: string;
  ponto_reabastecimento?: string;
  estoque_maximo?: string;
  ativo?: boolean;
}

export interface ProdutoLocalUpdate {
  familia_id?: number | null;
  preco_venda?: string;
  estoque_minimo?: string;
  ponto_reabastecimento?: string;
  estoque_maximo?: string;
  ativo?: boolean;
}

export interface EntradaEstoqueLocalCreate {
  produto_local_id: number;
  quantidade: string;
  preco_custo: string;
  preco_venda: string;
  data: string;
  observacao?: string;
}

export interface TransferenciaEstoqueLocalCreate {
  produto_local_id: number;
  quantidade: string;
  data: string;
  observacao?: string;
}

export interface ItemVendaPayload {
  produto_local_id: number | null;
  nome_produto: string;
  codigo_produto: string;
  familia_produto: string;
  quantidade: number;
  preco_unitario: string;
  desconto_perc: string;
}

export interface PagamentoPayload {
  tipo: "DINHEIRO" | "PIX" | "DÉBITO" | "CRÉDITO";
  valor: string;
}

export interface VendaPayload {
  local_id: number | null;
  id_referencia: string;
  itens: ItemVendaPayload[];
  pagamentos: PagamentoPayload[];
}

export interface ItemVendaOut {
  id: number;
  produto_local_id: number | null;
  nome_produto: string;
  codigo_produto: string;
  familia_produto: string;
  quantidade: number;
  preco_unitario: string;
  desconto_perc: string;
  total_item: string;
}

export interface PagamentoOut {
  id: number;
  tipo: string;
  valor: string;
}

export interface VendaOut {
  id: number;
  id_referencia: string;
  evento_id: number;
  local_id: number | null;
  vendedor_id: number;
  data_hora: string;
  total: string;
  forma_pagamento: string;
  itens: ItemVendaOut[];
  pagamentos: PagamentoOut[];
}

export interface TopProdutoDash {
  nome: string;
  qtd: number;
  receita: number;
}

export interface BaixoEstoqueDash {
  codigo: string;
  nome: string;
  familia: string;
  status: string;
  estoque: number;
}

export interface MargemProdutoDash {
  nome: string;
  margem: number;
}

export interface PDVDashboard {
  total_vendas_hoje: string;
  quantidade_vendas_hoje: number;
  ticket_medio: string;
  top_produtos: TopProdutoDash[];
  vendas_por_pagamento: Record<string, string>;

  // Geral Tab
  receita_total: number;
  itens_vendidos: number;
  itens_estoque: number;
  valor_estoque_venda: number;
  faturamento_por_evento: Record<string, number>;
  vendas_por_mes: Record<string, number>;
  top_10_mais_vendidos: TopProdutoDash[];
  top_10_menos_vendidos: TopProdutoDash[];

  // Vendas Tab
  lucro_liquido: number;
  receita_operacional: number;
  total_vendas: number;
  receita_por_familia: Record<string, number>;
  ranking_mais_vendidos: TopProdutoDash[];
  top_10_margem_lucro: MargemProdutoDash[];

  // Estoque Tab
  custo_total_estoque: number;
  itens_fisicos_totais: number;
  valor_potencial_venda: number;
  estoque_por_familia_qtd: Record<string, number>;
  custo_por_familia_valor: Record<string, number>;
  produtos_baixo_estoque: BaixoEstoqueDash[];
}

export const PAGAMENTO_LABELS: Record<string, string> = {
  DINHEIRO: "Dinheiro",
  PIX: "PIX",
  "DÉBITO": "Débito",
  "CRÉDITO": "Crédito",
  MISTO: "Misto",
};

export const PAGAMENTO_COLORS: Record<string, string> = {
  DINHEIRO: "bg-emerald-500/20 text-emerald-700",
  PIX: "bg-violet-500/20 text-violet-700",
  "DÉBITO": "bg-blue-500/20 text-blue-700",
  "CRÉDITO": "bg-amber-500/20 text-amber-700",
  MISTO: "bg-gray-500/20 text-gray-700",
};
