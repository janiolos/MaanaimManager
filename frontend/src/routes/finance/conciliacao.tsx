import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useConciliacao } from "@/routes/finance/hooks";
import { FORMA_PAGAMENTO_COLORS, FORMA_PAGAMENTO_LABELS } from "@/routes/finance/types";
import { cn, formatBRL } from "@/lib/utils";

export function ConciliacaoPage() {
  const location = useLocation();
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");

  const { data, isLoading } = useConciliacao(dataInicio || undefined, dataFim || undefined);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold font-display">Conciliação</h1>
        <p className="text-sm text-mm-muted">Receitas e despesas por forma de pagamento</p>
      </div>

      <div className="flex border-b border-mm-border mb-4">
        <Link to="/finance/dashboard" className={cn("px-4 py-2 border-b-2 font-medium text-sm", location.pathname === "/finance/dashboard" ? "border-primary text-primary" : "border-transparent text-mm-muted")}>Painel Geral</Link>
        <Link to="/finance" className={cn("px-4 py-2 border-b-2 font-medium text-sm", location.pathname === "/finance" ? "border-primary text-primary" : "border-transparent text-mm-muted")}>Lançamentos</Link>
        <Link to="/finance/relatorios" className={cn("px-4 py-2 border-b-2 font-medium text-sm", location.pathname.startsWith("/finance/relatorios") ? "border-primary text-primary" : "border-transparent text-mm-muted")}>Relatórios</Link>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1.5"><Label>Data início</Label><Input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Data fim</Label><Input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} /></div>
          </div>
        </CardContent>
      </Card>

      {isLoading && <p className="text-mm-muted text-sm">Carregando...</p>}

      {data && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-mm-muted">Total Receitas</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-600">{formatBRL(data.total_receitas)}</p></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-mm-muted">Total Despesas</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-rose-600">{formatBRL(data.total_despesas)}</p></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-mm-muted">Saldo</CardTitle></CardHeader><CardContent><p className={`text-2xl font-bold ${Number(data.saldo) >= 0 ? "text-primary" : "text-destructive"}`}>{formatBRL(data.saldo)}</p></CardContent></Card>
          </div>

          <Card>
            <CardHeader><CardTitle className="text-base">Por Forma de Pagamento</CardTitle></CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead><tr className="border-b text-left text-xs uppercase text-mm-muted">
                  <th className="px-4 py-2">Forma</th>
                  <th className="px-4 py-2 text-right">Receitas</th>
                  <th className="px-4 py-2 text-right">Despesas</th>
                  <th className="px-4 py-2 text-right">Saldo</th>
                </tr></thead>
                <tbody>
                  {data.linhas.map((l) => (
                    <tr key={l.forma_pagamento} className="border-b hover:bg-muted/30">
                      <td className="px-4 py-2">
                        <Badge className={cn("text-xs", FORMA_PAGAMENTO_COLORS[l.forma_pagamento])}>
                          {FORMA_PAGAMENTO_LABELS[l.forma_pagamento] ?? l.forma_pagamento}
                        </Badge>
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-green-600">{formatBRL(l.receitas)}</td>
                      <td className="px-4 py-2 text-right font-mono text-rose-600">{formatBRL(l.despesas)}</td>
                      <td className={`px-4 py-2 text-right font-mono font-bold ${Number(l.total) >= 0 ? "text-primary" : "text-destructive"}`}>{formatBRL(l.total)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="font-bold border-t-2">
                    <td className="px-4 py-2">TOTAL</td>
                    <td className="px-4 py-2 text-right">{formatBRL(data.total_receitas)}</td>
                    <td className="px-4 py-2 text-right">{formatBRL(data.total_despesas)}</td>
                    <td className={`px-4 py-2 text-right ${Number(data.saldo) >= 0 ? "text-primary" : "text-destructive"}`}>{formatBRL(data.saldo)}</td>
                  </tr>
                </tfoot>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
