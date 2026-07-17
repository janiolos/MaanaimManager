import { Download } from "lucide-react";
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useDRE } from "@/routes/finance/hooks";
import { cn, formatBRL } from "@/lib/utils";

export function DREPage() {
  const location = useLocation();
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isDownloadingCsv, setIsDownloadingCsv] = useState(false);

  const { data, isLoading } = useDRE(dataInicio || undefined, dataFim || undefined);

  const handleDownloadPDF = async () => {
    try {
      setIsDownloadingPdf(true);
      const response = await api.get("/finance/relatorios/dre/pdf", {
        params: {
          data_inicio: dataInicio || undefined,
          data_fim: dataFim || undefined,
        },
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `dre_${dataInicio || "inicio"}_${dataFim || "fim"}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Erro ao baixar PDF:", error);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleDownloadCSV = async () => {
    try {
      setIsDownloadingCsv(true);
      const response = await api.get("/finance/relatorios/dre/csv", {
        params: {
          data_inicio: dataInicio || undefined,
          data_fim: dataFim || undefined,
        },
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "text/csv;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `dre_${dataInicio || "inicio"}_${dataFim || "fim"}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Erro ao baixar CSV:", error);
    } finally {
      setIsDownloadingCsv(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display">DRE</h1>
          <p className="text-sm text-mm-muted">Demonstrativo do Resultado do Exercício</p>
        </div>
      </div>

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

      {/* Filtro de período */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1.5">
              <Label>Data início</Label>
              <Input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Data fim</Label>
              <Input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading */}
      {isLoading && <p className="text-mm-muted text-sm">Carregando...</p>}

      {data && (
        <>
          {/* KPIs */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-mm-muted">Receitas</CardTitle></CardHeader>
              <CardContent><p className="text-2xl font-bold text-green-600">{formatBRL(data.total_receitas)}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-mm-muted">Despesas</CardTitle></CardHeader>
              <CardContent><p className="text-2xl font-bold text-rose-600">{formatBRL(data.total_despesas)}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-mm-muted">Resultado</CardTitle></CardHeader>
              <CardContent>
                <p className={`text-2xl font-bold ${Number(data.resultado_liquido) >= 0 ? "text-primary" : "text-destructive"}`}>
                  {formatBRL(data.resultado_liquido)}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-mm-muted">Margem</CardTitle></CardHeader>
              <CardContent>
                <p className={`text-2xl font-bold ${data.margem_percentual !== null && data.margem_percentual >= 0 ? "text-primary" : "text-destructive"}`}>
                  {data.margem_percentual !== null ? `${data.margem_percentual.toFixed(1)}%` : "—"}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Export buttons */}
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleDownloadPDF} disabled={isDownloadingPdf}>
              <Download className="mr-2" size={16} /> {isDownloadingPdf ? "Gerando..." : "PDF"}
            </Button>
            <Button variant="outline" onClick={handleDownloadCSV} disabled={isDownloadingCsv}>
              <Download className="mr-2" size={16} /> {isDownloadingCsv ? "Gerando..." : "CSV"}
            </Button>
          </div>

          {/* Tabelas */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle className="text-base">Receitas por Categoria</CardTitle></CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead><tr className="border-b text-left text-xs uppercase text-mm-muted">
                    <th className="px-4 py-2">Categoria</th><th className="px-4 py-2 text-right">Valor</th>
                  </tr></thead>
                  <tbody>
                    {data.receitas_por_categoria.map((r) => (
                      <tr key={r.categoria} className="border-b">
                        <td className="px-4 py-2">{r.categoria}</td>
                        <td className="px-4 py-2 text-right font-mono text-green-600">{formatBRL(r.total)}</td>
                      </tr>
                    ))}
                    <tr className="font-bold border-t-2">
                      <td className="px-4 py-2">TOTAL</td>
                      <td className="px-4 py-2 text-right font-mono">{formatBRL(data.total_receitas)}</td>
                    </tr>
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-base">Despesas por Categoria</CardTitle></CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead><tr className="border-b text-left text-xs uppercase text-mm-muted">
                    <th className="px-4 py-2">Categoria</th><th className="px-4 py-2 text-right">Valor</th>
                  </tr></thead>
                  <tbody>
                    {data.despesas_por_categoria.map((r) => (
                      <tr key={r.categoria} className="border-b">
                        <td className="px-4 py-2">{r.categoria}</td>
                        <td className="px-4 py-2 text-right font-mono text-rose-600">{formatBRL(r.total)}</td>
                      </tr>
                    ))}
                    <tr className="font-bold border-t-2">
                      <td className="px-4 py-2">TOTAL</td>
                      <td className="px-4 py-2 text-right font-mono">{formatBRL(data.total_despesas)}</td>
                    </tr>
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
