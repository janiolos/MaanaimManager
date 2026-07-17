import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCashFlow } from "@/routes/finance/hooks";
import { cn, formatBRL, formatDate } from "@/lib/utils";

export function FluxoCaixaPage() {
  const location = useLocation();
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");

  const { data, isLoading } = useCashFlow(dataInicio || undefined, dataFim || undefined);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold font-display">Fluxo de Caixa</h1>
        <p className="text-sm text-mm-muted">Movimentação diária com saldo acumulado</p>
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
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-mm-muted">Saldo Final</CardTitle></CardHeader><CardContent><p className={`text-2xl font-bold ${Number(data.saldo_final) >= 0 ? "text-primary" : "text-destructive"}`}>{formatBRL(data.saldo_final)}</p></CardContent></Card>
          </div>

          <Card>
            <CardHeader><CardTitle className="text-base">Movimentação Diária</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-background"><tr className="border-b text-left text-xs uppercase text-mm-muted">
                    <th className="px-4 py-2">Data</th>
                    <th className="px-4 py-2 text-right">Receitas</th>
                    <th className="px-4 py-2 text-right">Despesas</th>
                    <th className="px-4 py-2 text-right">Saldo Dia</th>
                    <th className="px-4 py-2 text-right">Saldo Acum.</th>
                  </tr></thead>
                  <tbody>
                    {data.linhas.map((l) => (
                      <tr key={l.data} className="border-b hover:bg-muted/30">
                        <td className="px-4 py-2">{formatDate(l.data)}</td>
                        <td className="px-4 py-2 text-right font-mono text-green-600">{formatBRL(l.receitas)}</td>
                        <td className="px-4 py-2 text-right font-mono text-rose-600">{formatBRL(l.despesas)}</td>
                        <td className={`px-4 py-2 text-right font-mono ${Number(l.saldo_dia) >= 0 ? "text-primary" : "text-destructive"}`}>{formatBRL(l.saldo_dia)}</td>
                        <td className={`px-4 py-2 text-right font-mono font-bold ${Number(l.saldo_acumulado) >= 0 ? "text-primary" : "text-destructive"}`}>{formatBRL(l.saldo_acumulado)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
