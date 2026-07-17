import { useState } from "react";
import { toast } from "sonner";
import { ChevronDown, ChevronUp, Printer, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useDeletarVenda, useFamilias, useLocais, useVendas, usePosLocalAtual } from "@/routes/pos/hooks";
import { PAGAMENTO_LABELS, PAGAMENTO_COLORS } from "@/routes/pos/types";
import { formatBRL } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { POSNav } from "./pos-nav";

export function VendasListPage() {
  const { data: locais } = useLocais();
  const { localId, setLocalId } = usePosLocalAtual();
  const [page, setPage] = useState(1);
  const [familiaFiltro, setFamiliaFiltro] = useState("");
  const [produtoFiltro, setProdutoFiltro] = useState("");
  const { data: familias } = useFamilias(localId ?? 0);
  const { data } = useVendas(localId ?? undefined, page, {
    familia: familiaFiltro,
    produto: produtoFiltro,
  });
  const deletarVenda = useDeletarVenda();
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const locaisFiltrados = locais?.filter((l) => l.modulo_vendas && l.ativo) ?? [];

  const toggleExpand = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const vendas = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageSize = data?.page_size ?? 20;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const imprimirExtrato = (venda: any) => {
    const win = window.open("", "_blank", "width=400,height=600");
    if (!win) return;
    const html = `
      <html><head><title>Extrato #${venda.id}</title></head>
      <body style="font-family:monospace;width:300px;margin:0 auto;color:#000;padding:16px;">
        <h3 style="text-align:center;margin-bottom:4px;font-size:16px;">${venda.local_nome ?? "PDV"}</h3>
        <p style="text-align:center;margin-top:0;font-size:12px;">
          ${new Date(venda.data_hora).toLocaleString("pt-BR")}<br>
          Cupom Não Fiscal — Ref: ${venda.id_referencia.slice(0, 8)}
        </p>
        <hr style="border-top:1px dashed #000;margin:8px 0;">
        <table style="width:100%;font-size:12px;">
          <thead><tr><th style="text-align:left;">Item</th><th>Qtd</th><th style="text-align:right;">Total</th></tr></thead>
          <tbody>
            ${venda.itens
              .map(
                (i: any) =>
                  `<tr>
                    <td style="text-align:left;">${i.nome_produto}</td>
                    <td style="text-align:center;">${i.quantidade}</td>
                    <td style="text-align:right;">${formatBRL(Number(i.total_item))}</td>
                  </tr>`
              )
              .join("")}
          </tbody>
        </table>
        <hr style="border-top:1px dashed #000;margin:8px 0;">
        <div style="display:flex;justify-content:space-between;font-weight:bold;font-size:14px;">
          <span>TOTAL</span>
          <span>${formatBRL(Number(venda.total))}</span>
        </div>
        <div style="margin-top:8px;font-size:11px;">
          ${venda.pagamentos
            .map(
              (p: any) =>
                `<div style="display:flex;justify-content:space-between;">
                  <span>${PAGAMENTO_LABELS[p.tipo] ?? p.tipo}</span>
                  <span>${formatBRL(Number(p.valor))}</span>
                </div>`
            )
            .join("")}
        </div>
      </body></html>
    `;
    win.document.write(html);
    win.document.close();
    setTimeout(() => win.print(), 250);
  };

  const excluirVenda = async (venda: any) => {
    const ref = venda.id_referencia?.slice(0, 8) ?? venda.id;
    if (!confirm(`Excluir venda ${ref}? O estoque local será recomposto e os lançamentos financeiros do POS serão removidos.`)) {
      return;
    }
    try {
      await deletarVenda.mutateAsync(venda.id);
      setExpanded((prev) => {
        const next = new Set(prev);
        next.delete(venda.id);
        return next;
      });
      toast.success("Venda excluída e estoque recomposto");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao excluir venda");
    }
  };

  return (
    <div className="space-y-4">
      <POSNav />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Histórico de Vendas</h1>
        <select
          className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={localId ?? ""}
          onChange={(e) => {
            setLocalId(e.target.value ? Number(e.target.value) : null);
            setFamiliaFiltro("");
            setPage(1);
          }}
        >
          <option value="">Todos os locais</option>
          {locaisFiltrados.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nome}
            </option>
          ))}
        </select>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Vendas ({total})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid gap-2 md:grid-cols-[220px_1fr]">
            <select
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={familiaFiltro}
              onChange={(e) => {
                setFamiliaFiltro(e.target.value);
                setPage(1);
              }}
              disabled={!localId}
            >
              <option value="">Todas as famílias</option>
              {familias?.map((familia) => (
                <option key={familia.id} value={familia.nome}>
                  {familia.nome}
                </option>
              ))}
            </select>
            <Input
              value={produtoFiltro}
              onChange={(e) => {
                setProdutoFiltro(e.target.value);
                setPage(1);
              }}
              placeholder="Buscar produto ou código na venda"
            />
          </div>

          {vendas.length === 0 && (
            <p className="text-sm text-mm-muted text-center py-8">Nenhuma venda encontrada</p>
          )}

          {vendas.map((v: any) => {
            const isOpen = expanded.has(v.id);
            return (
              <div key={v.id} className="rounded border border-border overflow-hidden">
                <button
                  onClick={() => toggleExpand(v.id)}
                  className="w-full flex items-center justify-between p-3 text-left hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {isOpen ? (
                      <ChevronUp className="h-4 w-4 text-mm-muted" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-mm-muted" />
                    )}
                    <div>
                      <p className="text-sm font-medium">
                        Ref: {v.id_referencia.slice(0, 8)} —{" "}
                        {new Date(v.data_hora).toLocaleString("pt-BR")}
                      </p>
                      <p className="text-xs text-mm-muted">
                        {v.itens.length} itens — {v.forma_pagamento}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-mm-accent">
                      {formatBRL(Number(v.total))}
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 px-2"
                      onClick={(e) => {
                        e.stopPropagation();
                        imprimirExtrato(v);
                      }}
                    >
                      <Printer className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 px-2 text-destructive"
                      disabled={deletarVenda.isPending}
                      onClick={(e) => {
                        e.stopPropagation();
                        excluirVenda(v);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </button>

                {isOpen && (
                  <div className="border-t border-border bg-muted/20 px-4 py-3 space-y-3">
                    {/* Itens */}
                    <div>
                      <p className="text-xs font-semibold uppercase text-mm-muted mb-1">Itens</p>
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-xs text-mm-muted border-b border-border">
                            <th className="text-left py-1">Produto</th>
                            <th className="text-center py-1">Qtd</th>
                            <th className="text-right py-1">Unit.</th>
                            <th className="text-right py-1">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {v.itens.map((item: any) => (
                            <tr key={item.id} className="border-b border-border/50">
                              <td className="py-1">{item.nome_produto}</td>
                              <td className="text-center py-1">{item.quantidade}</td>
                              <td className="text-right py-1">
                                {formatBRL(Number(item.preco_unitario))}
                              </td>
                              <td className="text-right py-1 font-medium">
                                {formatBRL(Number(item.total_item))}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Pagamentos */}
                    <div>
                      <p className="text-xs font-semibold uppercase text-mm-muted mb-1">
                        Pagamentos
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {v.pagamentos.map((p: any) => (
                          <Badge
                            key={p.id}
                            className={cn("text-xs", PAGAMENTO_COLORS[p.tipo])}
                          >
                            {PAGAMENTO_LABELS[p.tipo] ?? p.tipo}: {formatBRL(Number(p.valor))}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {/* Paginação */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <Button
                size="sm"
                variant="outline"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Anterior
              </Button>
              <span className="text-sm text-mm-muted">
                Página {page} de {totalPages}
              </span>
              <Button
                size="sm"
                variant="outline"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Próxima
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
