import { useQuery } from "@tanstack/react-query";
import {
  TrendingDown,
  TrendingUp,
  Wallet,
  Calendar,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  PiggyBank,
  CreditCard,
  Coins,
  Receipt,
  ArrowRight,
} from "lucide-react";
import { useState, useMemo } from "react";
import { Link, useLocation } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { formatBRL, formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import {
  FORMA_PAGAMENTO_LABELS,
  type PaginatedLancamentos,
} from "@/routes/finance/types";
import { useCategorias } from "@/routes/finance/hooks";

export function FinanceDashboardPage() {
  const location = useLocation();
  
  // Date filters
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  
  // Hovered state for custom SVG chart tooltip
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Fetch full list of transactions (up to 200 for full client-side stats & charting)
  const { data: lancamentosData } = useQuery<PaginatedLancamentos>({
    queryKey: ["finance", "lancamentos", "dashboard-full"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedLancamentos>("/finance/lancamentos", {
        params: { page_size: 200 },
      });
      return data;
    },
  });

  const { data: categorias } = useCategorias();

  const allLancamentos = lancamentosData?.items || [];

  // Filter transactions based on selected date ranges
  const filteredLancamentos = useMemo(() => {
    return allLancamentos.filter((l) => {
      if (dataInicio && l.data < dataInicio) return false;
      if (dataFim && l.data > dataFim) return false;
      return true;
    });
  }, [allLancamentos, dataInicio, dataFim]);

  // Compute metrics dynamically from the filtered transaction list
  const metrics = useMemo(() => {
    let receitas = 0;
    let despesas = 0;
    
    const porForma: Record<string, number> = {};
    const porCat: Record<string, number> = {};

    filteredLancamentos.forEach((l) => {
      const valor = parseFloat(l.valor) || 0;
      if (l.tipo === "RECEITA") {
        receitas += valor;
      } else {
        despesas += valor;
      }

      // Group by payment method
      porForma[l.forma_pagamento] = (porForma[l.forma_pagamento] || 0) + valor;

      // Group by category name (lookup from loaded categories list or ID)
      const catObj = categorias?.find((c) => c.id === l.categoria_id);
      const catName = catObj ? catObj.nome : `#${l.categoria_id}`;
      porCat[catName] = (porCat[catName] || 0) + valor;
    });

    return {
      receitas,
      despesas,
      saldo: receitas - despesas,
      totalLancamentos: filteredLancamentos.length,
      porForma,
      porCategoria: porCat,
    };
  }, [filteredLancamentos, categorias]);

  // Daily aggregate stats & cash flow cumulative balance
  const chartData = useMemo(() => {
    const dailyRevenues: Record<string, number> = {};
    const dailyExpenses: Record<string, number> = {};

    filteredLancamentos.forEach((l) => {
      const v = parseFloat(l.valor) || 0;
      if (l.tipo === "RECEITA") {
        dailyRevenues[l.data] = (dailyRevenues[l.data] || 0) + v;
      } else {
        dailyExpenses[l.data] = (dailyExpenses[l.data] || 0) + v;
      }
    });

    const uniqueDates = Array.from(new Set(filteredLancamentos.map((l) => l.data))).sort();
    
    let runningBalance = 0;
    return uniqueDates.map((date) => {
      const rev = dailyRevenues[date] || 0;
      const exp = dailyExpenses[date] || 0;
      runningBalance += (rev - exp);
      return {
        date,
        label: date.split("-").reverse().slice(0, 2).join("/"), // DD/MM
        balance: runningBalance,
        revenue: rev,
        expense: exp,
      };
    });
  }, [filteredLancamentos]);

  // Clean filters
  const handleResetFilters = () => {
    setDataInicio("");
    setDataFim("");
  };

  // Render variables
  const hasData = filteredLancamentos.length > 0;

  // Custom SVG chart layout properties
  const svgWidth = 600;
  const svgHeight = 240;
  const padding = { top: 20, bottom: 40, left: 60, right: 20 };

  const chartScale = useMemo(() => {
    if (chartData.length === 0) return { points: [], yZero: 0, gridLines: [] };

    const balances = chartData.map((d) => d.balance);
    const minYRaw = Math.min(0, ...balances);
    const maxYRaw = Math.max(100, ...balances);
    
    const yRange = maxYRaw - minYRaw;
    const minY = minYRaw - (yRange * 0.1 || 10);
    const maxY = maxYRaw + (yRange * 0.1 || 10);

    const getX = (index: number) => {
      if (chartData.length <= 1) return padding.left + (svgWidth - padding.left - padding.right) / 2;
      return padding.left + (index / (chartData.length - 1)) * (svgWidth - padding.left - padding.right);
    };

    const getY = (value: number) => {
      const heightScale = svgHeight - padding.top - padding.bottom;
      return svgHeight - padding.bottom - ((value - minY) / (maxY - minY)) * heightScale;
    };

    const points = chartData.map((d, i) => ({
      x: getX(i),
      y: getY(d.balance),
      raw: d,
    }));

    const yZero = getY(0);

    // Build 4 reference grid lines
    const gridLines = [];
    for (let i = 0; i <= 3; i++) {
      const val = minY + (i / 3) * (maxY - minY);
      gridLines.push({
        value: val,
        y: getY(val),
      });
    }

    return { points, yZero, gridLines };
  }, [chartData]);

  // Generate Area SVG path d attribute
  const svgPathD = useMemo(() => {
    const { points } = chartScale;
    if (points.length === 0) return { line: "", area: "" };

    let linePath = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      linePath += ` L ${points[i].x} ${points[i].y}`;
    }

    const areaPath = `${linePath} L ${points[points.length - 1].x} ${svgHeight - padding.bottom} L ${points[0].x} ${svgHeight - padding.bottom} Z`;
    return { line: linePath, area: areaPath };
  }, [chartScale]);

  return (
    <div className="space-y-6">
      {/* Header and Secondary Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display">Módulo Financeiro</h1>
          <p className="text-sm text-mm-muted">Visão consolidada e fluxo de caixa</p>
        </div>
        <Button asChild>
          <Link to="/finance/novo">
            <TrendingUp className="mr-2" size={16} /> Novo lançamento
          </Link>
        </Button>
      </div>

      {/* Module Navigation Tabs */}
      <div className="flex border-b border-mm-border mb-4">
        <Link
          to="/finance/dashboard"
          className={cn(
            "px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200",
            location.pathname === "/finance/dashboard"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-mm-muted hover:text-foreground"
          )}
        >
          Painel Geral
        </Link>
          <Link
            to="/finance"
            className={cn(
              "px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200",
              location.pathname === "/finance"
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-mm-muted hover:text-foreground"
            )}
          >
            Lançamentos
          </Link>
          <Link
            to="/finance/relatorios"
            className={cn(
              "px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200",
              location.pathname.startsWith("/finance/relatorios")
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-mm-muted hover:text-foreground"
            )}
          >
            Relatórios
          </Link>
      </div>

      {/* Interactive Date Filter Bar */}
      <Card className="border-mm-border shadow-mm hover:shadow-mm-md transition-shadow">
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1.5 flex-1 min-w-[200px]">
              <label htmlFor="data_inicio" className="text-xs font-semibold text-mm-muted flex items-center gap-1.5">
                <Calendar size={14} /> Data Início
              </label>
              <Input
                id="data_inicio"
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="w-full"
              />
            </div>
            <div className="space-y-1.5 flex-1 min-w-[200px]">
              <label htmlFor="data_fim" className="text-xs font-semibold text-mm-muted flex items-center gap-1.5">
                <Calendar size={14} /> Data Fim
              </label>
              <Input
                id="data_fim"
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="w-full"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleResetFilters}
                disabled={!dataInicio && !dataFim}
                className="flex items-center gap-1.5"
              >
                <RotateCcw size={15} /> Limpar
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main KPI metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Receitas */}
        <Card className="border-l-4 border-l-green-500 shadow-mm hover:shadow-mm-lg transition-all duration-300">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-mm-muted">Receitas</CardTitle>
            <div className="p-2 bg-green-500/10 rounded-full">
              <TrendingUp className="size-5 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-green-600 tracking-tight">
              {formatBRL(metrics.receitas)}
            </div>
            <p className="text-xs text-mm-muted mt-1.5">
              Acumulado no período selecionado
            </p>
          </CardContent>
        </Card>

        {/* Despesas */}
        <Card className="border-l-4 border-l-rose-500 shadow-mm hover:shadow-mm-lg transition-all duration-300">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-mm-muted">Despesas</CardTitle>
            <div className="p-2 bg-rose-500/10 rounded-full">
              <TrendingDown className="size-5 text-rose-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-rose-600 tracking-tight">
              {formatBRL(metrics.despesas)}
            </div>
            <p className="text-xs text-mm-muted mt-1.5">
              Total gasto no período selecionado
            </p>
          </CardContent>
        </Card>

        {/* Saldo */}
        <Card className={cn(
          "border-l-4 shadow-mm hover:shadow-mm-lg transition-all duration-300",
          metrics.saldo >= 0 ? "border-l-primary text-primary" : "border-l-destructive"
        )}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-mm-muted">Saldo Líquido</CardTitle>
            <div className={cn(
              "p-2 rounded-full",
              metrics.saldo >= 0 ? "bg-primary/10 text-primary" : "bg-destructive/10 text-destructive"
            )}>
              <Wallet className="size-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className={cn(
              "text-3xl font-extrabold tracking-tight",
              metrics.saldo >= 0 ? "text-primary" : "text-destructive"
            )}>
              {formatBRL(metrics.saldo)}
            </div>
            <div className="text-xs mt-1.5 flex items-center gap-1.5 text-mm-muted">
              {metrics.saldo >= 0 ? (
                <>
                  <CheckCircle2 size={13} className="text-green-600" />
                  <span>Operação com saldo positivo</span>
                </>
              ) : (
                <>
                  <AlertCircle size={13} className="text-destructive" />
                  <span>Saldo total deficitário</span>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Visual Charts Layout */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Cash Flow Line/Area Chart */}
        <Card className="lg:col-span-8 shadow-mm hover:shadow-mm-md transition-shadow">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <PiggyBank className="text-primary" size={18} />
              <span>Evolução do Fluxo de Caixa</span>
            </CardTitle>
            <CardDescription>Visualização diária do saldo acumulado</CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            {!hasData ? (
              <div className="h-[240px] flex flex-col items-center justify-center border-2 border-dashed border-mm-border rounded-lg text-mm-muted">
                <Receipt className="size-10 mb-2 opacity-50" />
                <p className="text-sm">Sem lançamentos no período filtrado.</p>
              </div>
            ) : (
              <div className="relative">
                <svg
                  width="100%"
                  viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                  preserveAspectRatio="xMidYMid meet"
                  className="overflow-visible"
                >
                  <defs>
                    <linearGradient id="chart-area-grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.25" />
                      <stop offset="100%" stopColor="var(--primary)" stopOpacity="0.0" />
                    </linearGradient>
                  </defs>

                  {/* Horizontal Grid lines & values */}
                  {chartScale.gridLines.map((line, idx) => (
                    <g key={idx} className="opacity-40">
                      <line
                        x1={padding.left}
                        y1={line.y}
                        x2={svgWidth - padding.right}
                        y2={line.y}
                        stroke="#cbd5e1"
                        strokeDasharray="4 4"
                      />
                      <text
                        x={padding.left - 8}
                        y={line.y + 4}
                        textAnchor="end"
                        className="text-[10px] font-mono fill-mm-muted"
                      >
                        {formatBRL(line.value)}
                      </text>
                    </g>
                  ))}

                  {/* Baseline (Y=0) */}
                  {chartScale.yZero >= padding.top && chartScale.yZero <= svgHeight - padding.bottom && (
                    <line
                      x1={padding.left}
                      y1={chartScale.yZero}
                      x2={svgWidth - padding.right}
                      y2={chartScale.yZero}
                      stroke="#c0392b"
                      strokeWidth="1"
                      strokeDasharray="2 2"
                      className="opacity-70"
                    />
                  )}

                  {/* Shaded Area */}
                  {svgPathD.area && (
                    <path d={svgPathD.area} fill="url(#chart-area-grad)" />
                  )}

                  {/* Line */}
                  {svgPathD.line && (
                    <path
                      d={svgPathD.line}
                      fill="none"
                      stroke="hsl(var(--primary))"
                      strokeWidth="2.5"
                    />
                  )}

                  {/* Interactive dots & hover zones */}
                  {chartScale.points.map((pt, idx) => (
                    <g key={idx}>
                      <circle
                        cx={pt.x}
                        cy={pt.y}
                        r={hoveredIndex === idx ? 5 : 3.5}
                        fill={hoveredIndex === idx ? "hsl(var(--primary))" : "#ffffff"}
                        stroke="hsl(var(--primary))"
                        strokeWidth="2"
                        className="transition-all duration-150 cursor-pointer"
                        onMouseEnter={() => setHoveredIndex(idx)}
                        onMouseLeave={() => setHoveredIndex(null)}
                      />

                      {/* Invisible hover trigger column */}
                      <rect
                        x={pt.x - 10}
                        y={padding.top}
                        width={20}
                        height={svgHeight - padding.top - padding.bottom}
                        fill="transparent"
                        className="cursor-pointer"
                        onMouseEnter={() => setHoveredIndex(idx)}
                        onMouseLeave={() => setHoveredIndex(null)}
                      />
                    </g>
                  ))}

                  {/* X Axis Labels */}
                  {chartScale.points.map((pt, idx) => {
                    // Reduce labels to avoid clutter
                    const divisor = Math.max(1, Math.ceil(chartScale.points.length / 8));
                    if (idx % divisor !== 0 && idx !== chartScale.points.length - 1) return null;

                    return (
                      <text
                        key={idx}
                        x={pt.x}
                        y={svgHeight - padding.bottom + 16}
                        textAnchor="middle"
                        className="text-[10px] font-medium fill-mm-muted"
                      >
                        {pt.raw.label}
                      </text>
                    );
                  })}
                </svg>

                {/* Hover Tooltip display card overlay */}
                {hoveredIndex !== null && chartScale.points[hoveredIndex] && (
                  <div className="absolute top-2 right-2 bg-white/95 backdrop-blur-sm border border-mm-border p-3 rounded-lg shadow-lg text-xs space-y-1 z-10 transition-opacity">
                    <div className="font-semibold border-b pb-1 text-primary">
                      Data: {formatDate(chartScale.points[hoveredIndex].raw.date)}
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-mm-muted">Saldo Acumulado:</span>
                      <span className="font-semibold text-primary">
                        {formatBRL(chartScale.points[hoveredIndex].raw.balance)}
                      </span>
                    </div>
                    <div className="flex justify-between gap-4 text-[11px] text-green-600">
                      <span>Entradas do Dia:</span>
                      <span className="font-mono">
                        +{formatBRL(chartScale.points[hoveredIndex].raw.revenue)}
                      </span>
                    </div>
                    <div className="flex justify-between gap-4 text-[11px] text-rose-600">
                      <span>Saídas do Dia:</span>
                      <span className="font-mono">
                        -{formatBRL(chartScale.points[hoveredIndex].raw.expense)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Payment Methods Distribution */}
        <Card className="lg:col-span-4 shadow-mm hover:shadow-mm-md transition-shadow">
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <CreditCard className="text-primary" size={18} />
              <span>Meios de Pagamento</span>
            </CardTitle>
            <CardDescription>Volume total transacionado por canal</CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            {!hasData ? (
              <div className="h-[240px] flex items-center justify-center border-2 border-dashed border-mm-border rounded-lg text-mm-muted">
                <p className="text-sm">Sem dados de pagamento.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {Object.entries(metrics.porForma).map(([forma, valor]) => {
                  const totalVolume = Object.values(metrics.porForma).reduce((a, b) => a + b, 0);
                  const pct = totalVolume > 0 ? (valor / totalVolume) * 100 : 0;
                  
                  // Icon picker based on method
                  const Icon = forma === "PIX" ? Coins : forma === "CARTAO" ? CreditCard : Receipt;

                  return (
                    <div key={forma} className="space-y-1.5">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium flex items-center gap-1.5 text-mm-ink">
                          <Icon size={14} className="text-mm-muted" />
                          {FORMA_PAGAMENTO_LABELS[forma] ?? forma}
                        </span>
                        <div className="text-right">
                          <span className="font-semibold text-mm-ink">{formatBRL(valor)}</span>
                          <span className="text-xs text-mm-muted ml-1.5">({pct.toFixed(1)}%)</span>
                        </div>
                      </div>
                      {/* Bar indicator */}
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Categories Breakdown and Recent Feed */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Categories Breakdown */}
        <Card className="shadow-mm hover:shadow-mm-md transition-shadow">
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Coins className="text-primary" size={18} />
              <span>Categorias de Destaque</span>
            </CardTitle>
            <CardDescription>Divisão proporcional de lançamentos por categoria</CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            {!hasData ? (
              <div className="h-[200px] flex items-center justify-center border-2 border-dashed border-mm-border rounded-lg text-mm-muted">
                <p className="text-sm">Nenhuma categoria encontrada.</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                {Object.entries(metrics.porCategoria)
                  .sort((a, b) => b[1] - a[1]) // Sort descending
                  .map(([name, valor]) => {
                    const totalVal = Object.values(metrics.porCategoria).reduce((a, b) => a + b, 0);
                    const pct = totalVal > 0 ? (valor / totalVal) * 100 : 0;
                    
                    return (
                      <div key={name} className="space-y-1">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-mm-ink">{name}</span>
                          <div className="space-x-1 font-mono">
                            <span>{formatBRL(valor)}</span>
                            <span className="text-mm-muted font-normal">({pct.toFixed(1)}%)</span>
                          </div>
                        </div>
                        <div className="w-full bg-muted rounded-full h-1.5">
                          <div
                            className="bg-mm-accent h-1.5 rounded-full transition-all duration-500"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Transactions list */}
        <Card className="shadow-mm hover:shadow-mm-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Receipt className="text-primary" size={18} />
                <span>Últimos Lançamentos</span>
              </CardTitle>
              <CardDescription>Fluxo mais recente de entradas e saídas</CardDescription>
            </div>
            <Button asChild variant="ghost" size="sm" className="text-xs">
              <Link to="/finance" className="flex items-center gap-1">
                Ver todos <ArrowRight size={13} />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="pt-2">
            {!hasData ? (
              <div className="h-[200px] flex items-center justify-center border-2 border-dashed border-mm-border rounded-lg text-mm-muted">
                <p className="text-sm">Nenhum lançamento recente.</p>
              </div>
            ) : (
              <div className="divide-y divide-mm-border">
                {filteredLancamentos.slice(0, 5).map((l) => {
                  const isReceita = l.tipo === "RECEITA";
                  const catObj = categorias?.find((c) => c.id === l.categoria_id);
                  const catName = catObj ? catObj.nome : `#${l.categoria_id}`;

                  return (
                    <div key={l.id} className="py-3 flex items-center justify-between text-sm transition-colors hover:bg-muted/10">
                      <div className="space-y-0.5">
                        <div className="font-semibold text-mm-ink flex items-center gap-1.5">
                          <span>{l.descricao}</span>
                          <Badge variant={isReceita ? "success" : "destructive"} className="text-[10px] px-1 py-0 font-normal">
                            {catName}
                          </Badge>
                        </div>
                        <div className="text-[11px] text-mm-muted">
                          {formatDate(l.data)} · {FORMA_PAGAMENTO_LABELS[l.forma_pagamento] ?? l.forma_pagamento}
                        </div>
                      </div>
                      <div className={cn(
                        "font-mono font-bold text-right",
                        isReceita ? "text-green-600" : "text-rose-600"
                      )}>
                        {isReceita ? "+" : "-"} {formatBRL(l.valor)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}