import React, { useState } from "react";
import { useLocais, usePDVDashboard, usePosLocalAtual } from "@/routes/pos/hooks";
import { useEventos } from "@/routes/core/hooks";
import { useEventoStore } from "@/stores/evento-store";
import { formatBRL } from "@/lib/utils";
import { POSNav } from "./pos-nav";
import { ShoppingCart, Package } from "lucide-react";

// --- Custom SPA Chart Components matching PDV Maanaim Design ---

interface VerticalBarChartProps {
  data: Record<string, number>;
  color: string;
}

function VerticalBarChart({ data, color }: VerticalBarChartProps) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-xs text-cyan-200/50">
        Sem dados
      </div>
    );
  }

  const values = entries.map(([_, val]) => Number(val));
  const maxVal = Math.max(...values, 1);

  return (
    <div className="flex items-end justify-between gap-2 h-44 px-2 py-4 overflow-x-auto select-none">
      {entries.map(([label, val], idx) => {
        const numVal = Number(val);
        const percent = (numVal / maxVal) * 100;
        const formatVal = numVal > 1000 ? (numVal / 1000).toFixed(1) + "k" : numVal.toFixed(0);
        const isHighlight = idx === 0;

        return (
          <div key={label} className="flex flex-col items-center flex-1 min-w-[40px] h-full group justify-end">
            <div className="text-[10px] text-cyan-100 font-bold mb-1 opacity-80 group-hover:opacity-100 transition-opacity">
              {formatVal}
            </div>
            <div className="w-full relative rounded-t transition-all duration-500 hover:brightness-110" style={{ height: `${percent}%` }}>
              <div
                className="w-full h-full rounded-t"
                style={{
                  backgroundColor: isHighlight ? "#3bd671" : color,
                  boxShadow: isHighlight ? "0 0 8px rgba(59, 214, 113, 0.4)" : "none",
                }}
              />
            </div>
            <div
              className="text-[10px] text-cyan-200/60 mt-1 max-w-[50px] truncate text-center"
              title={label}
            >
              {label}
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface DoubleBarChartProps {
  data: Array<{ nome: string; qtd: number; receita: number }>;
}

function DoubleBarChart({ data }: DoubleBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-xs text-cyan-200/50">
        Sem dados
      </div>
    );
  }

  const maxQtd = Math.max(...data.map((d) => d.qtd), 1);
  const maxRec = Math.max(...data.map((d) => d.receita), 1);

  return (
    <div className="flex flex-col justify-evenly gap-2.5 py-1">
      {data.map((d) => {
        const percQtd = (d.qtd / maxQtd) * 100;
        const percRec = (d.receita / maxRec) * 100;

        return (
          <div key={d.nome} className="flex items-center gap-2">
            <div
              className="text-xs text-cyan-200/80 font-medium w-24 truncate"
              title={d.nome}
            >
              {d.nome}
            </div>
            <div className="flex-1 h-5 bg-white/5 border border-white/10 rounded overflow-hidden relative">
              <div
                className="h-full bg-[#1f756e] absolute left-0 top-0 transition-all duration-500"
                style={{ width: `${percQtd}%` }}
              />
              <div
                className="h-1 bg-[#3bd671] absolute left-0 top-2 transition-all duration-500 rounded-full"
                style={{ width: `${percRec}%` }}
              />
              <div className="absolute right-2 top-0 leading-5 text-[9px] font-bold text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]">
                {d.qtd} UN | R$ {Number(d.receita).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface HorizontalMarginChartProps {
  data: Array<{ nome: string; margem: number }>;
}

function HorizontalMarginChart({ data }: HorizontalMarginChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-xs text-cyan-200/50">
        Sem dados
      </div>
    );
  }

  const maxMargem = Math.max(...data.map((d) => d.margem), 100);

  return (
    <div className="flex flex-col justify-evenly gap-2.5 py-1">
      {data.map((d) => {
        const percent = Math.min((d.margem / maxMargem) * 100, 100);

        return (
          <div key={d.nome} className="flex items-center gap-2">
            <div
              className="text-xs text-cyan-200/80 font-medium w-24 truncate"
              title={d.nome}
            >
              {d.nome}
            </div>
            <div className="flex-1 h-4 bg-white/5 border border-white/10 rounded overflow-hidden relative">
              <div
                className="h-full bg-[#3bd671] absolute left-0 top-0 transition-all duration-500"
                style={{ width: `${percent}%` }}
              />
              <div className="absolute right-2 top-0 leading-4 text-[9px] font-bold text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]">
                {d.margem.toFixed(1)}%
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface PieChartProps {
  data: Record<string, string | number>;
}

function PieChart({ data }: PieChartProps) {
  const entries = Object.entries(data).map(([k, v]) => [k, Number(v)] as [string, number]);
  const total = entries.reduce((acc, [_, v]) => acc + v, 0);

  if (total === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-xs text-cyan-200/50">
        Sem dados
      </div>
    );
  }

  const colors: Record<string, string> = {
    DINHEIRO: "#3bd671",
    DÉBITO: "#248A85",
    CRÉDITO: "#1f756e",
    PIX: "#a1c8d1",
  };

  const gradientSlices: string[] = [];
  const labelElements: React.ReactNode[] = [];
  const legendElements: React.ReactNode[] = [];

  let cur = 0;
  entries.forEach(([tipo, val]) => {
    if (val > 0) {
      const perc = (val / total) * 100;
      const color = colors[tipo.toUpperCase()] || "#cccccc";

      gradientSlices.push(`${color} ${cur}% ${cur + perc}%`);

      const midAngle = ((cur + perc / 2) / 100) * 2 * Math.PI;
      const x = 50 + Math.sin(midAngle) * 28;
      const y = 50 - Math.cos(midAngle) * 28;

      if (perc >= 5) {
        labelElements.push(
          <div
            key={tipo}
            className="absolute text-[8px] font-bold text-white pointer-events-none select-none drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]"
            style={{
              left: `${x}%`,
              top: `${y}%`,
              transform: "translate(-50%, -50%)",
            }}
          >
            {perc.toFixed(1)}%
          </div>
        );
      }

      legendElements.push(
        <div key={tipo} className="flex items-center gap-2 text-xs text-[#E2F1F8]">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
          <span>
            {tipo}: R$ {val.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      );

      cur += perc;
    }
  });

  const pieBg = `conic-gradient(${gradientSlices.join(", ")})`;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-around gap-6 py-2">
      <div
        className="relative w-32 h-32 rounded-full shadow-lg border border-white/10 flex-shrink-0"
        style={{ background: pieBg }}
      >
        {labelElements}
      </div>
      <div className="flex flex-col gap-1.5 justify-center">
        {legendElements}
      </div>
    </div>
  );
}

// --- Main Dashboard Page Component ---

const MONTHS = [
  { value: "Todos", label: "Filtrar por Mês: Todos" },
  { value: "01", label: "Janeiro" },
  { value: "02", label: "Fevereiro" },
  { value: "03", label: "Março" },
  { value: "04", label: "Abril" },
  { value: "05", label: "Maio" },
  { value: "06", label: "Junho" },
  { value: "07", label: "Julho" },
  { value: "08", label: "Agosto" },
  { value: "09", label: "Setembro" },
  { value: "10", label: "Outubro" },
  { value: "11", label: "Novembro" },
  { value: "12", label: "Dezembro" },
];

export function PDVDashboardPage() {
  const { data: locais } = useLocais();
  const { localId, setLocalId } = usePosLocalAtual();
  const defaultEventoId = useEventoStore((s) => s.eventoId);
  const [selectedEventoId, setSelectedEventoId] = useState<number | null>(defaultEventoId);
  const [selectedMonth, setSelectedMonth] = useState<string>("Todos");
  const [activeTab, setActiveTab] = useState<"geral" | "vendas" | "estoque">("geral");

  const { data: eventos } = useEventos();

  const { data: dash, isLoading } = usePDVDashboard(
    localId ?? undefined,
    selectedMonth === "Todos" ? undefined : selectedMonth,
    selectedEventoId
  );

  const locaisFiltrados = locais?.filter((l) => l.modulo_dashboard && l.ativo) ?? [];

  return (
    <div className="space-y-4 text-[#E2F1F8]">
      <POSNav />

      {/* Top Controls & Filter Panel */}
      <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-md">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[#3bd671]">Dashboard PDV Maanaim</h1>
          <p className="text-xs text-cyan-200/60 mt-0.5">Visão consolidada e análises de desempenho do ponto de venda.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {/* Event Selector */}
          <select
            className="h-10 rounded-md border border-[#1a464f] bg-[#071d22] px-3 py-2 text-sm text-cyan-100 focus:outline-none focus:ring-1 focus:ring-[#3bd671]"
            value={selectedEventoId ?? ""}
            onChange={(e) => setSelectedEventoId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="" className="bg-[#071d22]">Todos os eventos</option>
            {eventos?.map((evt) => (
              <option key={evt.id} value={evt.id} className="bg-[#071d22]">
                {evt.nome} {evt.ativo ? "(Ativo)" : ""}
              </option>
            ))}
          </select>

          {/* Month Selector */}
          <select
            className="h-10 rounded-md border border-[#1a464f] bg-[#071d22] px-3 py-2 text-sm text-cyan-100 focus:outline-none focus:ring-1 focus:ring-[#3bd671]"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
          >
            {MONTHS.map((m) => (
              <option key={m.value} value={m.value} className="bg-[#071d22]">
                {m.label}
              </option>
            ))}
          </select>

          {/* Local Selector */}
          <select
            className="h-10 rounded-md border border-[#1a464f] bg-[#071d22] px-3 py-2 text-sm text-cyan-100 focus:outline-none focus:ring-1 focus:ring-[#3bd671]"
            value={localId ?? ""}
            onChange={(e) => setLocalId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="" className="bg-[#071d22]">Todos os locais</option>
            {locaisFiltrados.map((l) => (
              <option key={l.id} value={l.id} className="bg-[#071d22]">
                {l.nome}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Custom Tabs Switcher */}
      <div className="flex border-b border-[#1a464f] gap-1 bg-[#0c2b33]/40 p-1 rounded-t-md">
        <button
          onClick={() => setActiveTab("geral")}
          className={`flex-1 sm:flex-none px-4 py-2 text-sm font-semibold rounded-md transition-colors ${
            activeTab === "geral"
              ? "bg-[#1f756e] text-white shadow-inner"
              : "text-cyan-200/60 hover:text-cyan-100 hover:bg-white/5"
          }`}
        >
          Visão Geral
        </button>
        <button
          onClick={() => setActiveTab("vendas")}
          className={`flex-1 sm:flex-none px-4 py-2 text-sm font-semibold rounded-md transition-colors ${
            activeTab === "vendas"
              ? "bg-[#1f756e] text-white shadow-inner"
              : "text-cyan-200/60 hover:text-cyan-100 hover:bg-white/5"
          }`}
        >
          Vendas
        </button>
        <button
          onClick={() => setActiveTab("estoque")}
          className={`flex-1 sm:flex-none px-4 py-2 text-sm font-semibold rounded-md transition-colors ${
            activeTab === "estoque"
              ? "bg-[#1f756e] text-white shadow-inner"
              : "text-cyan-200/60 hover:text-cyan-100 hover:bg-white/5"
          }`}
        >
          Estoque
        </button>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#3bd671]"></div>
          <span className="text-sm text-cyan-200/70">Carregando painel analítico...</span>
        </div>
      ) : !dash ? (
        <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-12 text-center text-cyan-200/50">
          Sem dados de vendas ou estoque para os filtros selecionados.
        </div>
      ) : (
        <div className="space-y-4">
          {/* TAB 1: VISÃO GERAL */}
          {activeTab === "geral" && (
            <>
              {/* KPIs Geral */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="bg-[#0c2b33] border-t-4 border-t-[#3bd671] border-x border-b border-[#1a464f] rounded-lg p-4 shadow-sm">
                  <div className="text-2xl font-bold text-cyan-50">
                    {formatBRL(dash.receita_total)}
                  </div>
                  <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-1">
                    Receita Total de Vendas
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-4 shadow-sm flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full border border-cyan-500/20 flex items-center justify-center text-cyan-200/80">
                    <ShoppingCart className="w-5 h-5 text-[#a1c8d1]" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-cyan-50">
                      {dash.itens_vendidos}
                    </div>
                    <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-0.5">
                      Itens Vendidos
                    </div>
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-4 shadow-sm flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full border border-cyan-500/20 flex items-center justify-center text-cyan-200/80">
                    <Package className="w-5 h-5 text-[#a1c8d1]" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-cyan-50">
                      {Number(dash.itens_estoque).toFixed(0)}
                    </div>
                    <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-0.5">
                      Itens em Estoque
                    </div>
                  </div>
                </div>

                <div className="bg-[#0c2b33] border-t-4 border-t-[#1f756e] border-x border-b border-[#1a464f] rounded-lg p-4 shadow-sm">
                  <div className="text-2xl font-bold text-cyan-50">
                    {formatBRL(dash.valor_estoque_venda)}
                  </div>
                  <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-1">
                    Valor do Estoque (Venda)
                  </div>
                </div>
              </div>

              {/* Charts Geral Row 1 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg flex flex-col">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-2 border-b border-[#1a464f] pb-2">
                    Faturamento por Evento (R$)
                  </div>
                  <div className="flex-1 flex flex-col justify-end">
                    <VerticalBarChart data={dash.faturamento_por_evento} color="#47c8a6" />
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg flex flex-col">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-2 border-b border-[#1a464f] pb-2">
                    Vendas por Mês (R$)
                  </div>
                  <div className="flex-1 flex flex-col justify-end">
                    <VerticalBarChart data={dash.vendas_por_mes} color="#248A85" />
                  </div>
                </div>
              </div>

              {/* Charts Geral Row 2 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-3 border-b border-[#1a464f] pb-2">
                    Top 10 Mais Vendidos (Qtd e Receita)
                  </div>
                  <DoubleBarChart data={dash.top_10_mais_vendidos} />
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-3 border-b border-[#1a464f] pb-2">
                    Top 10 Menos Vendidos (Qtd e Receita)
                  </div>
                  <DoubleBarChart data={dash.top_10_menos_vendidos} />
                </div>
              </div>
            </>
          )}

          {/* TAB 2: VENDAS */}
          {activeTab === "vendas" && (
            <>
              {/* KPIs Vendas */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="bg-[#0c2b33] border-l-4 border-l-[#3bd671] border-y border-r border-[#1a464f] rounded-lg p-4 shadow-sm">
                  <div className="text-2xl font-bold text-[#3bd671]">
                    {formatBRL(dash.lucro_liquido)}
                  </div>
                  <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-1">
                    Lucro Líquido
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-4 shadow-sm">
                  <div className="text-2xl font-bold text-cyan-50">
                    {formatBRL(dash.receita_operacional)}
                  </div>
                  <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-1">
                    Receita Operacional
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-4 shadow-sm">
                  <div className="text-2xl font-bold text-cyan-50">
                    {dash.total_vendas}
                  </div>
                  <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-1">
                    Total de Vendas
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-4 shadow-sm">
                  <div className="text-2xl font-bold text-[#3bd671]">
                    {formatBRL(dash.ticket_medio)}
                  </div>
                  <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-1">
                    Ticket Médio
                  </div>
                </div>
              </div>

              {/* Charts Vendas Row 1 */}
              <div className="grid grid-cols-1 md:grid-cols-2.5 gap-4 md:flex">
                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg flex-1">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-2 border-b border-[#1a464f] pb-2">
                    Formas de Pagamento
                  </div>
                  <PieChart data={dash.vendas_por_pagamento} />
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg flex-[1.5]">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-2 border-b border-[#1a464f] pb-2">
                    Receita por Família (R$)
                  </div>
                  <VerticalBarChart data={dash.receita_por_familia} color="#1f7f7d" />
                </div>
              </div>

              {/* Charts Vendas Row 2 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Ranking mais vendidos table */}
                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-3 border-b border-[#1a464f] pb-2">
                    Ranking de Produtos Mais Vendidos
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead>
                        <tr className="border-b border-[#1a464f] text-cyan-200/50">
                          <th className="py-2">PRODUTO</th>
                          <th className="py-2 text-right">QTD VENDIDA</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dash.ranking_mais_vendidos.slice(0, 5).map((p) => (
                          <tr key={p.nome} className="border-b border-[#1a464f]/40 hover:bg-white/5">
                            <td className="py-2 font-medium">{p.nome}</td>
                            <td className="py-2 text-right font-bold text-[#3bd671]">
                              {p.qtd} UN
                            </td>
                          </tr>
                        ))}
                        {dash.ranking_mais_vendidos.length === 0 && (
                          <tr>
                            <td colSpan={2} className="py-8 text-center text-cyan-200/40">
                              Sem registros de vendas
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-3 border-b border-[#1a464f] pb-2">
                    Top 10 Produtos por Margem de Lucro (%)
                  </div>
                  <HorizontalMarginChart data={dash.top_10_margem_lucro} />
                </div>
              </div>
            </>
          )}

          {/* TAB 3: ESTOQUE */}
          {activeTab === "estoque" && (
            <>
              {/* KPIs Estoque */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-4 shadow-sm">
                  <div className="text-2xl font-bold text-cyan-50">
                    {formatBRL(dash.custo_total_estoque)}
                  </div>
                  <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-1">
                    Custo Total em Estoque
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-4 shadow-sm flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full border border-cyan-500/20 flex items-center justify-center text-cyan-200/80">
                    <Package className="w-5 h-5 text-[#a1c8d1]" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-cyan-50">
                      {Number(dash.itens_fisicos_totais).toFixed(0)}
                    </div>
                    <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-0.5">
                      Itens Físicos Totais
                    </div>
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] rounded-lg p-4 shadow-sm">
                  <div className="text-2xl font-bold text-[#3bd671]">
                    {formatBRL(dash.valor_potencial_venda)}
                  </div>
                  <div className="text-[10px] font-bold text-cyan-200/60 uppercase mt-1">
                    Valor Potencial de Venda
                  </div>
                </div>
              </div>

              {/* Charts Estoque Row 1 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg flex flex-col">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-2 border-b border-[#1a464f] pb-2">
                    Itens em Estoque por Família (Unidades)
                  </div>
                  <div className="flex-1 flex flex-col justify-end">
                    <VerticalBarChart data={dash.estoque_por_familia_qtd} color="#47c8a6" />
                  </div>
                </div>

                <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg flex flex-col">
                  <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-2 border-b border-[#1a464f] pb-2">
                    Custo Alocado por Família (R$)
                  </div>
                  <div className="flex-1 flex flex-col justify-end">
                    <VerticalBarChart data={dash.custo_por_familia_valor} color="#1f756e" />
                  </div>
                </div>
              </div>

              {/* Critical Stock Alerts Table */}
              <div className="bg-[#0c2b33] border border-[#1a464f] p-4 rounded-lg">
                <div className="text-xs font-bold text-cyan-100 uppercase tracking-wider mb-3 border-b border-[#1a464f] pb-2">
                  Produtos com Baixo Estoque (Atenção)
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-[#1a464f] text-cyan-200/50">
                        <th className="py-2">CÓDIGO</th>
                        <th className="py-2">PRODUTO</th>
                        <th className="py-2">FAMÍLIA</th>
                        <th className="py-2 text-center">STATUS</th>
                        <th className="py-2 text-right">ESTOQUE ATUAL</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dash.produtos_baixo_estoque.map((p) => {
                        const isRupture = p.status === "Ruptura de Estoque";
                        const textColor = isRupture ? "text-red-400" : "text-yellow-500";
                        return (
                          <tr key={p.codigo + "-" + p.nome} className="border-b border-[#1a464f]/40 hover:bg-white/5">
                            <td className="py-2 font-mono text-[10px] text-cyan-200/60">{p.codigo}</td>
                            <td className="py-2 font-medium">{p.nome}</td>
                            <td className="py-2 text-cyan-200/80">{p.familia}</td>
                            <td className={`py-2 text-center font-bold ${textColor}`}>
                              {p.status}
                            </td>
                            <td className={`py-2 text-right font-bold ${textColor}`}>
                              {Number(p.estoque).toFixed(0)} UN
                            </td>
                          </tr>
                        );
                      })}
                      {dash.produtos_baixo_estoque.length === 0 && (
                        <tr>
                          <td colSpan={5} className="py-8 text-center text-cyan-200/40">
                            Nenhum produto em nível crítico de estoque.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
